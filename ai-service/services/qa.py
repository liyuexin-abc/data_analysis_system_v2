# -*- coding: utf-8 -*-
"""
智能问数编排服务: 实现 PRD 第21章完整流程
术语匹配 → 语义解析 → 路径规划 → 数据查询 → 方法论分析 → AI 组织回答 → 知识引用记录
"""
import json
import time
from . import db
from . import llm
from . import semantic
from . import attribution
from . import rag


def _metric_data(metric_code, org_id, time_info):
    """按时间语义取数"""
    if time_info['type'] == 'range':
        rows = db.query(
            "SELECT period, value, budget FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period IN %s ORDER BY period",
            (metric_code, org_id, tuple(time_info['periods'])))
        return rows
    if time_info['type'] == 'year':
        rows = db.query(
            "SELECT period, value, budget FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period LIKE %s AND period_type='month' ORDER BY period",
            (metric_code, org_id, time_info['period'] + '-%'))
        return rows
    # month
    row = db.query(
        "SELECT period, value, budget FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period=%s",
        (metric_code, org_id, time_info['period']))
    if not row:
        # 回退最新月
        row = db.query(
            "SELECT period, value, budget FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period_type='month' ORDER BY period DESC LIMIT 1",
            (metric_code, org_id))
    return row


def _compare_values(metric_code, org_id, period):
    """同比环比对比值"""
    y, m = map(int, period.split('-'))
    mom_p = f'{y}-{m-1:02d}' if m > 1 else f'{y-1}-12'
    yoy_p = f'{y-1}-{m:02d}'
    mom = db.query_one("SELECT value FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period=%s",
                       (metric_code, org_id, mom_p))
    yoy = db.query_one("SELECT value FROM biz_metric_fact WHERE metric_code=%s AND org_id=%s AND period=%s",
                       (metric_code, org_id, yoy_p))
    return {
        'mom_period': mom_p, 'mom_value': float(mom['value']) if mom else None,
        'yoy_period': yoy_p, 'yoy_value': float(yoy['value']) if yoy else None,
    }


def answer_question(question: str):
    """完整问数管线"""
    start = time.time()
    parse = semantic.parse_question(question)
    intent = parse['intent']
    intent_type = intent.get('intent', 'metric_query')
    metric_code = intent.get('metric_code') or (parse['metrics'][0]['code'] if parse['metrics'] else None)
    org_id = parse['orgs'][0]['org_id'] if parse['orgs'] else 'ORG_GROUP'
    org_name = parse['orgs'][0]['org_name'] if parse['orgs'] else '际华集团'
    time_info = parse['time']
    knowledge_refs = []
    data_payload = {}

    # 指标语义
    metric_sem = None
    if metric_code:
        metric_sem = db.query_one("SELECT * FROM kp_metric_semantic WHERE metric_code=%s", (metric_code,))
        if metric_sem:
            knowledge_refs.append({'type': '指标语义', 'code': metric_code, 'name': metric_sem['metric_name']})
    for t in parse['matched_terms'][:6]:
        knowledge_refs.append({'type': '术语词典', 'code': t['term'], 'name': f"{t['term']}→{t['target_name']}"})

    # ---------- 按意图执行 ----------
    if intent_type == 'knowledge_qa':
        result = rag.rag_answer(question)
        for r in result['references']:
            knowledge_refs.append({'type': 'RAG文档', 'code': str(r['doc_id']), 'name': r['doc_name']})
        elapsed = int((time.time() - start) * 1000)
        _log_qa(question, parse, {'type': 'knowledge_qa'}, result['answer'], knowledge_refs, elapsed)
        return {
            'question': question, 'intent': 'knowledge_qa', 'parse': parse,
            'answer': result['answer'], 'references': result['references'],
            'knowledge_refs': knowledge_refs, 'duration_ms': elapsed,
        }

    if intent_type == 'attribution' or (intent.get('need_reason') and metric_code == 'profit_total'):
        if metric_code in (None, 'profit_total'):
            period = time_info.get('period') if time_info['type'] == 'month' else None
            attr = attribution.profit_attribution(org_id, period, intent.get('compare') if intent.get('compare') in ('yoy', 'mom') else 'mom')
            data_payload['attribution'] = attr
            knowledge_refs.append({'type': '分析方法论', 'code': 'MTH_Profit_Attribution', 'name': '利润归因分析方法'})
        elif metric_code in ('receipt_rate', 'overdue_amount'):
            attr = attribution.receipt_risk_analysis(org_id)
            data_payload['receipt_risk'] = attr
            knowledge_refs.append({'type': '分析方法论', 'code': 'MTH_Receipt_Risk', 'name': '回款风险分析方法'})

    if intent_type == 'risk_query' or ('回款风险' in question or '逾期' in question and '哪' in question):
        if 'receipt_risk' not in data_payload and ('回款' in question or '逾期' in question or '欠款' in question):
            data_payload['receipt_risk'] = attribution.receipt_risk_analysis(None)
            knowledge_refs.append({'type': '分析方法论', 'code': 'MTH_Receipt_Risk', 'name': '回款风险分析方法'})
        else:
            risks = db.query(
                """SELECT r.risk_id, r.risk_name, r.risk_type, r.risk_level, r.amount, r.risk_status, o.org_name
                   FROM biz_risk r LEFT JOIN biz_org o ON r.org_id=o.org_id
                   ORDER BY FIELD(r.risk_level,'red','orange','yellow','blue'), r.amount DESC LIMIT 15""")
            data_payload['risks'] = [dict(r, amount=float(r['amount'] or 0)) for r in risks]
            knowledge_refs.append({'type': '本体对象', 'code': 'Obj_Gov_Risk', 'name': '风险事项'})

    if intent_type == 'rank' and metric_code:
        period = time_info.get('period') if time_info['type'] == 'month' else None
        if not period:
            row = db.query_one("SELECT MAX(period) AS p FROM biz_metric_fact WHERE metric_code=%s AND period_type='month'", (metric_code,))
            period = row['p']
        order = 'ASC' if intent.get('rank_direction') == 'asc' else 'DESC'
        rows = db.query(
            f"""SELECT f.org_id, o.org_name, f.value, f.budget FROM biz_metric_fact f
                JOIN biz_org o ON f.org_id=o.org_id
                WHERE f.metric_code=%s AND f.period=%s AND o.org_level=3 ORDER BY f.value {order}""",
            (metric_code, period))
        data_payload['rank'] = {'period': period,
                                'list': [dict(r, value=float(r['value']), budget=float(r['budget'] or 0)) for r in rows]}

    if intent_type in ('metric_query', 'trend') and metric_code and 'rank' not in data_payload:
        rows = _metric_data(metric_code, org_id, time_info)
        data_payload['series'] = [dict(r, value=float(r['value']), budget=float(r['budget'] or 0)) for r in rows]
        if rows and time_info['type'] == 'month':
            data_payload['compare'] = _compare_values(metric_code, org_id, rows[-1]['period'] if isinstance(rows, list) else rows[0]['period'])

    # ---------- AI 组织回答 ----------
    sem_block = ''
    if metric_sem:
        sem_block = f"""指标语义(口径解释必须使用):
- 指标: {metric_sem['metric_name']}({metric_code})，单位: {metric_sem['unit']}
- 业务定义: {metric_sem['business_def']}
- 公式: {metric_sem['formula_desc']}
- 解释模板: {metric_sem['answer_template'] or '无'}"""

    prompt = f"""你是际华国际经营数据分析平台的智能问数助手。请基于以下查询结果回答用户问题。

用户问题: {question}
识别意图: {intent_type}
分析对象: {org_name}({org_id})
时间范围: {time_info.get('desc')}

{sem_block}

查询数据(JSON):
{json.dumps(data_payload, ensure_ascii=False, default=str)[:6000]}

回答要求:
1. 用专业、简洁的经营分析语言回答，金额单位万元(保留到个位或一位小数)，比率保留一位小数；
2. 若有归因数据，按贡献度大小列出主要原因，并给出穿透发现(合同/客户/供应商层面)；
3. 若有排名数据，列出 Top5 并点评；
4. 若有风险数据，按风险等级汇总并提示重点；
5. 给出 1-3 条管理建议；
6. 不要编造数据中不存在的数字。"""

    try:
        answer = llm.chat([{'role': 'user', 'content': prompt}], max_tokens=2000)
    except Exception as e:
        answer = f'AI 生成回答失败({e})，以下为原始查询数据摘要: ' + json.dumps(data_payload, ensure_ascii=False, default=str)[:800]

    elapsed = int((time.time() - start) * 1000)
    _log_qa(question, parse, intent, answer, knowledge_refs, elapsed)

    return {
        'question': question, 'intent': intent_type, 'parse': parse,
        'data': data_payload, 'answer': answer,
        'knowledge_refs': knowledge_refs, 'duration_ms': elapsed,
    }


def _log_qa(question, parse, intent, answer, refs, duration):
    try:
        db.execute(
            "INSERT INTO kp_qa_log (question,matched_terms,matched_metrics,matched_objects,plan,answer,knowledge_refs,duration_ms) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (question,
             json.dumps(parse['matched_terms'], ensure_ascii=False),
             json.dumps(parse['metrics'], ensure_ascii=False),
             json.dumps(parse['objects'], ensure_ascii=False),
             json.dumps(intent, ensure_ascii=False, default=str),
             answer,
             json.dumps(refs, ensure_ascii=False),
             duration))
        db.execute("UPDATE kp_skill SET call_count=call_count+1 WHERE code='SKILL_QA'")
    except Exception as e:
        print('qa log failed:', e)
