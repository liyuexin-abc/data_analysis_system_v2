#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
际华国际经营分析 - 业务假数据生成
组织 / 客户 / 合同 / 订单 / 回款 / 供应商 / 物料 / 采购 / 库存 / 生产 / 风险 / 整改 / 指标事实
"""
import pymysql
import random
import datetime
import json

random.seed(20260612)

DB = dict(host='127.0.0.1', user='kp_user', password='kp_pass_2026',
          database='knowledge_platform', charset='utf8mb4')

TODAY = datetime.date(2026, 6, 12)


def conn():
    return pymysql.connect(**DB)


# ---------------- 组织 ----------------
ORGS = [
    # (org_id, name, level, parent, type, region, leader)
    ('ORG_GROUP', '际华集团股份有限公司', 1, None, 'group', '北京', '陈总'),
    ('ORG_SEG_CLOTH', '职业装板块', 2, 'ORG_GROUP', 'segment', '北京', '李板块长'),
    ('ORG_SEG_SHOE', '职业鞋靴板块', 2, 'ORG_GROUP', 'segment', '北京', '王板块长'),
    ('ORG_SEG_PROTECT', '防护装备板块', 2, 'ORG_GROUP', 'segment', '北京', '张板块长'),
    ('ORG_SEG_TEXTILE', '纺织面料板块', 2, 'ORG_GROUP', 'segment', '北京', '刘板块长'),
    ('ORG_3502', '际华3502职业装公司', 3, 'ORG_SEG_CLOTH', 'company', '河北石家庄', '赵经理'),
    ('ORG_3503', '际华3503职业装公司', 3, 'ORG_SEG_CLOTH', 'company', '江苏南京', '钱经理'),
    ('ORG_3521', '际华3521特种装备公司', 3, 'ORG_SEG_PROTECT', 'company', '湖北武汉', '孙经理'),
    ('ORG_3515', '际华3515强人鞋业公司', 3, 'ORG_SEG_SHOE', 'company', '河南漯河', '周经理'),
    ('ORG_3514', '际华3514面料科技公司', 3, 'ORG_SEG_TEXTILE', 'company', '山西太原', '吴经理'),
    ('ORG_3534', '际华3534制衣公司', 3, 'ORG_SEG_CLOTH', 'company', '山东淄博', '郑经理'),
    ('ORG_3543', '际华3543针织公司', 3, 'ORG_SEG_TEXTILE', 'company', '湖南益阳', '冯经理'),
    ('ORG_7555', '际华7555防护科技公司', 3, 'ORG_SEG_PROTECT', 'company', '重庆', '蒋经理'),
    ('ORG_3502_F1', '3502一分厂', 4, 'ORG_3502', 'factory', '河北石家庄', '韩厂长'),
    ('ORG_3502_F2', '3502二分厂', 4, 'ORG_3502', 'factory', '河北石家庄', '杨厂长'),
    ('ORG_3515_F1', '3515制鞋一厂', 4, 'ORG_3515', 'factory', '河南漯河', '朱厂长'),
]

COMPANIES = ['ORG_3502', 'ORG_3503', 'ORG_3521', 'ORG_3515', 'ORG_3514', 'ORG_3534', 'ORG_3543', 'ORG_7555']
ORG_NAME = {o[0]: o[1] for o in ORGS}

# ---------------- 客户 ----------------
CUSTOMERS = [
    ('CUST_001', '公安部装备财务局', '政府', '北京', 'AAA', 'gov'),
    ('CUST_002', '应急管理部消防救援局', '政府', '北京', 'AAA', 'gov'),
    ('CUST_003', '中国铁路总公司物资部', '交通运输', '北京', 'AAA', 'enterprise'),
    ('CUST_004', '国家电网物资公司', '电力', '北京', 'AAA', 'enterprise'),
    ('CUST_005', '中国石油天然气集团', '能源', '北京', 'AAA', 'enterprise'),
    ('CUST_006', '中国邮政集团', '邮政', '北京', 'AA', 'enterprise'),
    ('CUST_007', '武警后勤保障部', '军队', '北京', 'AAA', 'military'),
    ('CUST_008', '某战区联勤保障中心', '军队', '武汉', 'AAA', 'military'),
    ('CUST_009', '河北省高级人民法院', '政府', '石家庄', 'AA', 'gov'),
    ('CUST_010', '江苏省市场监督管理局', '政府', '南京', 'AA', 'gov'),
    ('CUST_011', '中国南方航空公司', '民航', '广州', 'AA', 'enterprise'),
    ('CUST_012', '顺丰速运集团', '物流', '深圳', 'AA', 'enterprise'),
    ('CUST_013', '中建三局集团', '建筑', '武汉', 'A', 'enterprise'),
    ('CUST_014', '德国UVEX安全集团', '外贸', '海外-欧洲', 'AA', 'export'),
    ('CUST_015', '美国Honeywell安防', '外贸', '海外-北美', 'A', 'export'),
    ('CUST_016', '山西焦煤集团', '煤炭', '太原', 'B', 'enterprise'),
    ('CUST_017', '河南能源化工集团', '化工', '郑州', 'B', 'enterprise'),
    ('CUST_018', '某省监狱管理局', '政府', '济南', 'AA', 'gov'),
    ('CUST_019', '中国中车集团', '装备制造', '北京', 'AA', 'enterprise'),
    ('CUST_020', '东方航空地服公司', '民航', '上海', 'A', 'enterprise'),
]

PRODUCT_LINES = ['职业装', '职业鞋靴', '防护装备', '纺织面料']
ORG_PRODUCT = {
    'ORG_3502': '职业装', 'ORG_3503': '职业装', 'ORG_3534': '职业装',
    'ORG_3515': '职业鞋靴', 'ORG_3521': '防护装备', 'ORG_7555': '防护装备',
    'ORG_3514': '纺织面料', 'ORG_3543': '纺织面料',
}

PRODUCTS = {
    '职业装': ['行政执法制服', '铁路制服', '电力工装', '航空职业装', '邮政制服', '法院制服'],
    '职业鞋靴': ['作训靴', '劳保皮鞋', '消防救援靴', '绝缘靴', '防砸安全鞋'],
    '防护装备': ['防弹衣', '防刺服', '消防战斗服', '防化服', '应急救援包'],
    '纺织面料': ['涤棉混纺面料', '阻燃面料', '防静电面料', '迷彩印染布', '功能针织面料'],
}

SUPPLIERS = [
    ('SUP_001', '鲁泰纺织股份', '面料', '山东', 'A', 12),
    ('SUP_002', '华纺股份', '面料', '山东', 'A', 10),
    ('SUP_003', '浙江富润印染', '面料', '浙江', 'B', 8),
    ('SUP_004', 'YKK拉链(深圳)', '辅料', '广东', 'A', 15),
    ('SUP_005', '伟星纽扣股份', '辅料', '浙江', 'A', 9),
    ('SUP_006', '海宁皮革城供应链', '皮革', '浙江', 'B', 6),
    ('SUP_007', '焦作隆丰皮草', '皮革', '河南', 'B', 7),
    ('SUP_008', '双星橡塑材料', '橡胶', '山东', 'B', 5),
    ('SUP_009', '三力士橡胶', '橡胶', '浙江', 'C', 4),
    ('SUP_010', '杰克缝纫设备', '设备', '浙江', 'A', 11),
    ('SUP_011', '新乡化纤股份', '面料', '河南', 'B', 6),
    ('SUP_012', '际华新材料(内部)', '面料', '河北', 'A', 20),
]

MATERIALS = [
    ('MAT_001', '涤棉混纺坯布', '面料', '米', 18.5),
    ('MAT_002', '阻燃芳纶面料', '面料', '米', 86.0),
    ('MAT_003', '防静电绸', '面料', '米', 32.0),
    ('MAT_004', '迷彩印染布', '面料', '米', 22.0),
    ('MAT_005', '金属拉链', '辅料', '条', 3.5),
    ('MAT_006', '树脂纽扣', '辅料', '粒', 0.4),
    ('MAT_007', '反光织带', '辅料', '米', 2.8),
    ('MAT_008', '头层牛皮', '皮革', '平方英尺', 28.0),
    ('MAT_009', '超纤合成革', '皮革', '米', 45.0),
    ('MAT_010', '橡胶大底', '橡胶', '双', 12.5),
    ('MAT_011', 'EVA中底材料', '橡胶', '双', 6.8),
    ('MAT_012', '凯夫拉纤维布', '面料', '米', 320.0),
]


def months(n=18, end=None):
    """最近 n 个月期间列表 (含当月)"""
    end = end or TODAY
    out = []
    y, m = end.year, end.month
    for _ in range(n):
        out.append(f'{y:04d}-{m:02d}')
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def rand_date(start, end):
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, max(delta, 1)))


def main():
    db = conn()
    cur = db.cursor()

    # 清空
    for t in ['biz_org', 'biz_customer', 'biz_contract', 'biz_order', 'biz_receipt',
              'biz_supplier', 'biz_material', 'biz_purchase_order', 'biz_inventory',
              'biz_prod_task', 'biz_risk', 'biz_rectify_task', 'biz_metric_fact']:
        cur.execute(f'TRUNCATE TABLE {t}')

    cur.executemany(
        'INSERT INTO biz_org (org_id,org_name,org_level,parent_id,org_type,region,leader) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        ORGS)
    cur.executemany(
        'INSERT INTO biz_customer (customer_id,customer_name,industry,region,credit_level,customer_type,contact,created_year) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
        [(c[0], c[1], c[2], c[3], c[4], c[5], f'联系人{i+1:02d}', random.randint(2015, 2024)) for i, c in enumerate(CUSTOMERS)])
    cur.executemany(
        'INSERT INTO biz_supplier (supplier_id,supplier_name,category,region,rating,coop_years) VALUES (%s,%s,%s,%s,%s,%s)',
        SUPPLIERS)
    cur.executemany(
        'INSERT INTO biz_material (material_id,material_name,category,unit,std_price) VALUES (%s,%s,%s,%s,%s)',
        MATERIALS)

    # ---------------- 合同 / 订单 / 回款 ----------------
    contracts, orders, receipts, prod_tasks = [], [], [], []
    cid_seq, oid_seq, rid_seq, tid_seq = 0, 0, 0, 0
    start_date = datetime.date(2025, 1, 1)

    for org in COMPANIES:
        line = ORG_PRODUCT[org]
        n_contract = random.randint(14, 22)
        for _ in range(n_contract):
            cid_seq += 1
            cust = random.choice(CUSTOMERS)
            product = random.choice(PRODUCTS[line])
            cid = f'HT2025{cid_seq:04d}' if cid_seq % 3 else f'HT2026{cid_seq:04d}'
            sign = rand_date(start_date, TODAY - datetime.timedelta(days=30))
            amount = round(random.uniform(80, 3500), 2)
            # 低信用客户合同更易延期
            delay_p = {'AAA': 0.06, 'AA': 0.12, 'A': 0.2, 'B': 0.38, 'C': 0.5}[cust[4]]
            status = random.choices(
                ['executing', 'completed', 'delayed', 'terminated'],
                weights=[0.45, 0.35, delay_p, 0.02])[0]
            fulfill = round(random.uniform(95, 100), 1) if status == 'completed' else \
                round(random.uniform(40, 75), 1) if status == 'delayed' else \
                round(random.uniform(60, 98), 1)
            delivery = sign + datetime.timedelta(days=random.randint(60, 300))
            contracts.append((cid, f'{cust[1]}{product}采购合同', org, cust[0], amount,
                              sign, delivery, status, line, fulfill))

            # 订单 1-4 个
            for _ in range(random.randint(1, 4)):
                oid_seq += 1
                oid = f'DD{oid_seq:06d}'
                o_amt = round(amount / random.randint(2, 5), 2)
                o_date = sign + datetime.timedelta(days=random.randint(3, 40))
                o_status = random.choices(['producing', 'delivered', 'delayed'], weights=[0.35, 0.5, 0.15])[0]
                orders.append((oid, cid, o_amt, o_date, random.randint(500, 50000), product, o_status))
                # 生产任务
                tid_seq += 1
                pq = random.randint(500, 50000)
                t_status = {'producing': 'producing', 'delivered': 'finished', 'delayed': 'delayed'}[o_status]
                dq = pq if t_status == 'finished' else int(pq * random.uniform(0.2, 0.9))
                prod_tasks.append((f'SC{tid_seq:06d}', oid, org, pq, dq, o_date + datetime.timedelta(days=5),
                                   o_date + datetime.timedelta(days=random.randint(30, 120)), t_status))

            # 回款计划 2-5 期
            n_terms = random.randint(2, 5)
            per = round(amount / n_terms, 2)
            for k in range(n_terms):
                rid_seq += 1
                due = sign + datetime.timedelta(days=60 * (k + 1))
                rid = f'HK{rid_seq:06d}'
                if due > TODAY:
                    receipts.append((rid, cid, per, 0, due, None, 0, 0, 'pending'))
                    continue
                overdue_p = {'AAA': 0.08, 'AA': 0.15, 'A': 0.25, 'B': 0.45, 'C': 0.6}[cust[4]]
                roll = random.random()
                if roll < overdue_p:
                    od = random.choices([random.randint(5, 30), random.randint(31, 90),
                                         random.randint(91, 180), random.randint(181, 400)],
                                        weights=[0.3, 0.35, 0.2, 0.15])[0]
                    paid = round(per * random.uniform(0, 0.5), 2)
                    receipts.append((rid, cid, per, paid, due, None, od, round(per - paid, 2), 'overdue'))
                elif roll < overdue_p + 0.15:
                    paid = round(per * random.uniform(0.5, 0.9), 2)
                    rdate = due + datetime.timedelta(days=random.randint(0, 10))
                    receipts.append((rid, cid, per, paid, due, rdate, 0, round(per - paid, 2), 'partial'))
                else:
                    rdate = due - datetime.timedelta(days=random.randint(0, 15))
                    receipts.append((rid, cid, per, per, due, rdate, 0, 0, 'received'))

    cur.executemany(
        'INSERT INTO biz_contract VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', contracts)
    cur.executemany('INSERT INTO biz_order VALUES (%s,%s,%s,%s,%s,%s,%s)', orders)
    cur.executemany('INSERT INTO biz_receipt VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)', receipts)
    cur.executemany('INSERT INTO biz_prod_task VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', prod_tasks)

    # ---------------- 采购 / 库存 ----------------
    pos, invs = [], []
    po_seq, inv_seq = 0, 0
    mat_sup = {  # 物料类别 → 供应商
        '面料': ['SUP_001', 'SUP_002', 'SUP_003', 'SUP_011', 'SUP_012'],
        '辅料': ['SUP_004', 'SUP_005'],
        '皮革': ['SUP_006', 'SUP_007'],
        '橡胶': ['SUP_008', 'SUP_009'],
    }
    for org in COMPANIES:
        for _ in range(random.randint(15, 25)):
            po_seq += 1
            mat = random.choice(MATERIALS)
            sups = mat_sup.get(mat[2], ['SUP_010'])
            sup = random.choice(sups)
            qty = round(random.uniform(1000, 80000), 0)
            # 价格波动：部分供应商涨价(用于演示成本归因)
            factor = random.uniform(0.95, 1.08)
            if sup in ('SUP_009', 'SUP_003', 'SUP_007'):
                factor = random.uniform(1.1, 1.35)  # 涨价供应商
            price = round(mat[4] * factor, 2)
            amt = round(qty * price / 10000, 2)
            pdate = rand_date(start_date, TODAY)
            pstat = random.choices(['ordered', 'received', 'closed'], weights=[0.2, 0.4, 0.4])[0]
            pos.append((f'CG{po_seq:06d}', org, sup, mat[0], amt, price, qty, pdate, pstat))
        for mat in random.sample(MATERIALS, k=random.randint(5, 9)):
            inv_seq += 1
            qty = round(random.uniform(500, 50000), 0)
            invs.append((f'KC{inv_seq:06d}', org, mat[0], f'{ORG_NAME[org][:6]}中心仓',
                         qty, round(qty * mat[4] / 10000, 2),
                         random.choices([random.randint(10, 90), random.randint(91, 180),
                                         random.randint(181, 365), random.randint(366, 720)],
                                        weights=[0.4, 0.3, 0.2, 0.1])[0],
                         round(random.uniform(1.5, 8.0), 2)))
    cur.executemany('INSERT INTO biz_purchase_order VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)', pos)
    cur.executemany('INSERT INTO biz_inventory VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', invs)

    # ---------------- 风险 / 整改 ----------------
    risks, rectifies = [], []
    rk_seq, rt_seq = 0, 0
    # 从逾期回款生成回款风险
    cur.execute("SELECT r.receipt_id, r.contract_id, r.overdue_days, r.overdue_amount, c.org_id, c.contract_name "
                "FROM biz_receipt r JOIN biz_contract c ON r.contract_id=c.contract_id "
                "WHERE r.receipt_status='overdue' ORDER BY r.overdue_amount DESC LIMIT 40")
    for row in cur.fetchall():
        rk_seq += 1
        od, amt = row[2], float(row[3])
        level = 'red' if od > 180 or amt > 1000 else 'orange' if od > 90 or amt > 500 else \
                'yellow' if od > 30 or amt > 100 else 'blue'
        rid = f'RISK{rk_seq:04d}'
        status = random.choices(['open', 'processing', 'closed'], weights=[0.4, 0.35, 0.25])[0]
        risks.append((rid, f'{row[5][:18]}回款逾期{od}天', '回款风险', level, 'Obj_Fin_Receipt',
                      row[0], row[4], 'Rule_Receipt_Overdue',
                      f'合同{row[1]}应收款逾期{od}天，逾期金额{amt}万元，建议启动催收程序。',
                      amt, TODAY - datetime.timedelta(days=random.randint(1, 60)), status))
        if status != 'open':
            rt_seq += 1
            rectifies.append((f'ZG{rt_seq:04d}', rid, row[4], f'{ORG_NAME[row[4]][:8]}财务负责人',
                              f'针对{row[1]}逾期回款开展专项催收，明确回款计划并按周反馈进展。',
                              TODAY + datetime.timedelta(days=random.randint(7, 45)),
                              'done' if status == 'closed' else 'processing'))
    # 履约风险
    cur.execute("SELECT contract_id, contract_name, org_id, contract_amount FROM biz_contract WHERE contract_status='delayed' LIMIT 15")
    for row in cur.fetchall():
        rk_seq += 1
        amt = float(row[3])
        level = 'red' if amt > 2000 else 'orange' if amt > 800 else 'yellow'
        risks.append((f'RISK{rk_seq:04d}', f'{row[1][:18]}履约延期', '履约风险', level,
                      'Obj_Sales_Contract', row[0], row[2], 'Rule_Contract_Delay',
                      f'合同{row[0]}交付延期，合同金额{amt}万元，存在违约风险。', amt,
                      TODAY - datetime.timedelta(days=random.randint(1, 90)),
                      random.choice(['open', 'processing'])))
    # 库存风险
    cur.execute("SELECT inv_id, org_id, amount, age_days FROM biz_inventory WHERE age_days>300 LIMIT 10")
    for row in cur.fetchall():
        rk_seq += 1
        risks.append((f'RISK{rk_seq:04d}', f'{ORG_NAME[row[1]][:10]}库存积压(库龄{row[3]}天)', '库存风险',
                      'yellow' if row[3] < 500 else 'orange', 'Obj_Inv_Inventory', row[0], row[1],
                      'Rule_Inventory_Age', f'库存{row[0]}库龄{row[3]}天，金额{row[2]}万元，建议清理处置。',
                      float(row[2]), TODAY - datetime.timedelta(days=random.randint(1, 30)), 'open'))
    cur.executemany('INSERT INTO biz_risk VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', risks)
    cur.executemany('INSERT INTO biz_rectify_task VALUES (%s,%s,%s,%s,%s,%s,%s)', rectifies)

    # ---------------- 指标事实 ----------------
    # 每公司每月: 收入/成本/费用/利润/回款率/逾期金额/合同额/履约率
    facts = []
    base_rev = {o: random.uniform(2200, 9500) for o in COMPANIES}
    # 设定部分单位利润下滑用于归因演示
    decline_orgs = {'ORG_3521': 0.94, 'ORG_3543': 0.95}
    mlist = months(18)
    for org in COMPANIES:
        rev = base_rev[org]
        for i, p in enumerate(mlist):
            season = 1 + 0.18 * (1 if p.endswith(('-09', '-10', '-11', '-12')) else
                                 -0.4 if p.endswith(('-01', '-02')) else 0.1)
            trend = decline_orgs.get(org, random.uniform(1.0, 1.012)) ** i
            revenue = round(rev * season * trend * random.uniform(0.93, 1.07), 2)
            cost_rate = random.uniform(0.72, 0.80) + (0.03 if org in decline_orgs and i > 9 else 0)
            cost = round(revenue * cost_rate, 2)
            sell_exp = round(revenue * random.uniform(0.035, 0.055), 2)
            admin_exp = round(revenue * random.uniform(0.04, 0.06), 2)
            fin_exp = round(revenue * random.uniform(0.008, 0.018), 2)
            other = round(revenue * random.uniform(0.0, 0.02), 2)
            profit = round(revenue - cost - sell_exp - admin_exp - fin_exp + other, 2)
            receipt_rate = round(random.uniform(72, 96) - (8 if org in decline_orgs and i > 9 else 0), 2)
            overdue_amt = round(revenue * random.uniform(0.02, 0.12), 2)
            contract_amt = round(revenue * random.uniform(0.8, 1.4), 2)
            fulfill = round(random.uniform(85, 99), 2)
            rows = [
                ('revenue_total', revenue, revenue * 1.05),
                ('cost_total', cost, cost * 0.98),
                ('expense_sell', sell_exp, sell_exp),
                ('expense_admin', admin_exp, admin_exp),
                ('expense_fin', fin_exp, fin_exp),
                ('income_other', other, other),
                ('profit_total', profit, profit * 1.1),
                ('receipt_rate', receipt_rate, 90),
                ('overdue_amount', overdue_amt, overdue_amt * 0.7),
                ('contract_amount_sum', contract_amt, contract_amt),
                ('fulfill_rate', fulfill, 95),
            ]
            for mc, v, b in rows:
                facts.append((mc, org, p, 'month', round(v, 2), round(b, 2)))
    # 集团层 = 各公司汇总
    agg = {}
    for mc, org, p, pt, v, b in facts:
        key = (mc, p)
        agg.setdefault(key, [0, 0, 0])
        agg[key][0] += v
        agg[key][1] += b
        agg[key][2] += 1
    for (mc, p), (v, b, n) in agg.items():
        if mc in ('receipt_rate', 'fulfill_rate'):
            facts.append((mc, 'ORG_GROUP', p, 'month', round(v / n, 2), round(b / n, 2)))
        else:
            facts.append((mc, 'ORG_GROUP', p, 'month', round(v, 2), round(b, 2)))
    cur.executemany(
        'INSERT INTO biz_metric_fact (metric_code,org_id,period,period_type,value,budget) VALUES (%s,%s,%s,%s,%s,%s)',
        facts)

    db.commit()
    for t in ['biz_org', 'biz_customer', 'biz_contract', 'biz_order', 'biz_receipt', 'biz_supplier',
              'biz_material', 'biz_purchase_order', 'biz_inventory', 'biz_prod_task', 'biz_risk',
              'biz_rectify_task', 'biz_metric_fact']:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t}: {cur.fetchone()[0]}')
    db.close()


if __name__ == '__main__':
    main()
