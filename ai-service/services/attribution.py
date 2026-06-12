# -*- coding: utf-8 -*-
"""
归因分析服务: 执行 PRD 第10章分析方法论
- 利润归因: 指标拆解树 + 贡献度 + 图谱穿透
- 回款风险分析: 账龄 + 客户穿透
"""
import json
from . import db


def _period_shift(period: str, months: int):
    y, m = map(int, period.split('-'))
    m -= months
    while m <= 0:
        y, m = y - 1, m + 12
    return f'{y}-{m:02d}'


def _yoy_period(period: str):
    y, m = map(int, period.split('-'))
    return f'{y-1}-{m:02d}'


def _fact(metric, org, period):
    row = db.query_one(
        "SELECT value FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period=%s",
        (metric, org, period))
    return float(row['value']) if row else None


def profit_attribution(org_id: str, period: str = None, compare: str = 'mom'):
    """利润归因分析: 按 MTH_Profit_Attribution 方法论执行"""
    method = db.query_one("SELECT * FROM kp_method WHERE code='MTH_Profit_Attribution'")
    tree = db.pj(method['decompose_tree'], {}) if method else {}

    if not period:
        row = db.query_one(
            "SELECT MAX(period) AS p FROM biz_metric_fact WHERE metric_code='profit_total' AND org_id=%s AND period_type='month'",
            (org_id,))
        period = row['p']
    base_period = _yoy_period(period) if compare == 'yoy' else _period_shift(period, 1)

    org = db.query_one("SELECT org_name FROM biz_org WHERE org_id=%s", (org_id,))
    org_name = org['org_name'] if org else org_id

    # Step1: 差异计算
    cur = _fact('profit_total', org_id, period)
    base = _fact('profit_total', org_id, base_period)
    if cur is None or base is None:
        return {'error': f'缺少 {org_id} 在 {period} 或 {base_period} 的利润数据'}
    diff = round(cur - base, 2)
    pct = round(diff / abs(base) * 100, 2) if base else None

    # Step2-3: 因素拆解 + 贡献度
    factors = []
    children = tree.get('children', [
        {'code': 'revenue_total', 'name': '营业收入', 'op': '+'},
        {'code': 'cost_total', 'name': '营业成本', 'op': '-'},
        {'code': 'expense_sell', 'name': '销售费用', 'op': '-'},
        {'code': 'expense_admin', 'name': '管理费用', 'op': '-'},
        {'code': 'expense_fin', 'name': '财务费用', 'op': '-'},
        {'code': 'income_other', 'name': '其他收益', 'op': '+'},
    ])
    for c in children:
        cv = _fact(c['code'], org_id, period)
        bv = _fact(c['code'], org_id, base_period)
        if cv is None or bv is None:
            continue
        change = cv - bv
        # 对利润的影响: 正向因素(+)变化即影响; 负向因素(-)变化取反
        impact = change if c['op'] == '+' else -change
        contribution = round(impact / abs(diff) * 100, 1) if diff else 0
        factors.append({
            'code': c['code'], 'name': c['name'], 'op': c['op'],
            'current': round(cv, 2), 'base': round(bv, 2), 'change': round(change, 2),
            'impact': round(impact, 2), 'contribution': contribution,
        })
    factors.sort(key=lambda f: abs(f['impact']), reverse=True)

    # Step4: 收入下降穿透 → 合同/客户
    drill = {}
    rev = next((f for f in factors if f['code'] == 'revenue_total'), None)
    if rev and rev['impact'] < 0:
        rows = db.query(
            """SELECT c.contract_id, c.contract_name, c.contract_amount, c.contract_status, cu.customer_name
               FROM biz_contract c JOIN biz_customer cu ON c.customer_id=cu.customer_id
               WHERE c.org_id=%s AND c.contract_status IN ('delayed','terminated')
               ORDER BY c.contract_amount DESC LIMIT 5""", (org_id,))
        drill['revenue_decline'] = {
            'desc': '收入下降穿透: 延期/终止合同',
            'path': '组织 → 合同 → 客户',
            'items': [{'id': r['contract_id'], 'name': r['contract_name'],
                       'amount': float(r['contract_amount']), 'status': r['contract_status'],
                       'customer': r['customer_name']} for r in rows],
        }
    # Step5: 成本上升穿透 → 采购/物料/供应商
    cost = next((f for f in factors if f['code'] == 'cost_total'), None)
    if cost and cost['impact'] < 0:
        rows = db.query(
            """SELECT s.supplier_name, m.material_name, m.std_price,
                      ROUND(AVG(p.unit_price),2) AS avg_price,
                      ROUND((AVG(p.unit_price)-m.std_price)/m.std_price*100,1) AS price_up_pct,
                      ROUND(SUM(p.po_amount),2) AS total_amount
               FROM biz_purchase_order p
               JOIN biz_supplier s ON p.supplier_id=s.supplier_id
               JOIN biz_material m ON p.material_id=m.material_id
               WHERE p.org_id=%s
               GROUP BY s.supplier_name, m.material_name, m.std_price
               HAVING price_up_pct > 8 ORDER BY price_up_pct DESC LIMIT 5""", (org_id,))
        drill['cost_increase'] = {
            'desc': '成本上升穿透: 涨价供应商与物料',
            'path': '组织 → 采购单 → 物料 → 供应商',
            'items': [{'supplier': r['supplier_name'], 'material': r['material_name'],
                       'std_price': float(r['std_price']), 'avg_price': float(r['avg_price']),
                       'price_up_pct': float(r['price_up_pct']), 'total_amount': float(r['total_amount'])} for r in rows],
        }

    # Step7: Top 原因
    top_factors = [f for f in factors if (diff < 0 and f['impact'] < 0) or (diff > 0 and f['impact'] > 0)][:3]

    return {
        'method': 'MTH_Profit_Attribution',
        'method_name': '利润归因分析方法',
        'org_id': org_id, 'org_name': org_name,
        'period': period, 'base_period': base_period,
        'compare': compare,
        'current_profit': round(cur, 2), 'base_profit': round(base, 2),
        'diff': diff, 'pct': pct,
        'direction': '下降' if diff < 0 else '上升',
        'factors': factors,
        'top_factors': top_factors,
        'drill': drill,
        'waterfall': [{'name': '基期利润', 'value': round(base, 2)}] +
                     [{'name': f['name'], 'value': f['impact']} for f in factors] +
                     [{'name': '本期利润', 'value': round(cur, 2)}],
    }


def receipt_risk_analysis(org_id: str = None):
    """回款风险分析: 按 MTH_Receipt_Risk 方法论执行"""
    where = "WHERE r.receipt_status='overdue'"
    params = []
    if org_id and org_id != 'ORG_GROUP':
        where += " AND c.org_id=%s"
        params.append(org_id)

    # Step1: 逾期识别 + 账龄分布
    aging = db.query(f"""
        SELECT CASE WHEN r.overdue_days<=30 THEN '30天内' WHEN r.overdue_days<=90 THEN '31-90天'
                    WHEN r.overdue_days<=180 THEN '91-180天' ELSE '180天以上' END AS bucket,
               COUNT(*) AS cnt, ROUND(SUM(r.overdue_amount),2) AS amount
        FROM biz_receipt r JOIN biz_contract c ON r.contract_id=c.contract_id
        {where} GROUP BY bucket""", params)

    # Step2: 风险分级
    levels = db.query(f"""
        SELECT CASE WHEN r.overdue_days>180 OR r.overdue_amount>1000 THEN 'red'
                    WHEN r.overdue_days>90 OR r.overdue_amount>500 THEN 'orange'
                    WHEN r.overdue_days>30 OR r.overdue_amount>100 THEN 'yellow' ELSE 'blue' END AS level,
               COUNT(*) AS cnt, ROUND(SUM(r.overdue_amount),2) AS amount
        FROM biz_receipt r JOIN biz_contract c ON r.contract_id=c.contract_id
        {where} GROUP BY level""", params)

    # Step3: 客户穿透 (组织→合同→回款→客户)
    customers = db.query(f"""
        SELECT cu.customer_id, cu.customer_name, cu.credit_level,
               COUNT(DISTINCT c.contract_id) AS contract_count,
               ROUND(SUM(r.overdue_amount),2) AS overdue_amount,
               MAX(r.overdue_days) AS max_overdue_days
        FROM biz_receipt r
        JOIN biz_contract c ON r.contract_id=c.contract_id
        JOIN biz_customer cu ON c.customer_id=cu.customer_id
        {where} GROUP BY cu.customer_id, cu.customer_name, cu.credit_level
        ORDER BY overdue_amount DESC LIMIT 10""", params)

    # 单位维度
    orgs = db.query(f"""
        SELECT o.org_id, o.org_name, COUNT(*) AS overdue_count,
               ROUND(SUM(r.overdue_amount),2) AS overdue_amount, MAX(r.overdue_days) AS max_days
        FROM biz_receipt r
        JOIN biz_contract c ON r.contract_id=c.contract_id
        JOIN biz_org o ON c.org_id=o.org_id
        {where} GROUP BY o.org_id, o.org_name ORDER BY overdue_amount DESC""", params)

    total = db.query_one(f"""
        SELECT COUNT(*) AS cnt, ROUND(COALESCE(SUM(r.overdue_amount),0),2) AS amount
        FROM biz_receipt r JOIN biz_contract c ON r.contract_id=c.contract_id {where}""", params)

    return {
        'method': 'MTH_Receipt_Risk',
        'method_name': '回款风险分析方法',
        'org_id': org_id or 'ORG_GROUP',
        'total_overdue_count': total['cnt'],
        'total_overdue_amount': float(total['amount']),
        'aging': [dict(a, amount=float(a['amount'])) for a in aging],
        'levels': [dict(l, amount=float(l['amount'])) for l in levels],
        'top_customers': [dict(c, overdue_amount=float(c['overdue_amount'])) for c in customers],
        'org_rank': [dict(o, overdue_amount=float(o['overdue_amount'])) for o in orgs],
        'graph_path': '组织 → 合同 → 回款 → 客户',
    }
