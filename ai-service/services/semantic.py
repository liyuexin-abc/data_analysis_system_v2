# -*- coding: utf-8 -*-
"""
语义解析服务: 实现 PRD 第21章 智能问数调用知识流程
用户提问 → 术语词典匹配 → 指标语义识别 → 本体对象识别 → 意图识别(LLM) → 路径规划
"""
import json
import re
import datetime
from . import db
from . import llm


def match_terms(question: str):
    """术语词典匹配: 长词优先"""
    terms = db.query("SELECT * FROM kp_term WHERE status='published'")
    hits = [t for t in terms if t['term'] in question]
    hits.sort(key=lambda t: (-len(t['term']), -float(t['confidence'] or 0)))
    # 更新命中次数
    for t in hits:
        db.execute("UPDATE kp_term SET hit_count=hit_count+1 WHERE id=%s", (t['id'],))
    return hits


def resolve_time(question: str):
    """时间表达解析"""
    today = datetime.date(2026, 6, 12)  # 演示数据基准日期
    cur = f'{today.year}-{today.month:02d}'
    last_m = f'{today.year}-{today.month-1:02d}' if today.month > 1 else f'{today.year-1}-12'

    def shift(months):
        y, m = today.year, today.month
        m -= months
        while m <= 0:
            y, m = y - 1, m + 12
        return f'{y}-{m:02d}'

    if '去年' in question:
        return {'type': 'year', 'period': str(today.year - 1), 'desc': '去年'}
    if '今年' in question or '本年' in question:
        return {'type': 'year', 'period': str(today.year), 'desc': '今年'}
    if '上个月' in question or '上月' in question:
        return {'type': 'month', 'period': last_m, 'desc': '上月'}
    m3 = re.search(r'最近(\d+|三|六|十二)个月', question)
    if m3:
        n = {'三': 3, '六': 6, '十二': 12}.get(m3.group(1)) or int(m3.group(1))
        return {'type': 'range', 'periods': [shift(i) for i in range(n - 1, -1, -1)], 'desc': f'最近{n}个月'}
    mq = re.search(r'(\d{4})年(\d{1,2})月', question)
    if mq:
        return {'type': 'month', 'period': f'{mq.group(1)}-{int(mq.group(2)):02d}', 'desc': mq.group(0)}
    # 默认本月(数据最新月)
    return {'type': 'month', 'period': cur, 'desc': '本月'}


def resolve_org(question: str):
    """组织识别: 在问题中匹配组织名称"""
    orgs = db.query("SELECT org_id, org_name, org_level FROM biz_org")
    hits = []
    for o in orgs:
        name = o['org_name']
        short = name.replace('际华', '').replace('公司', '')
        if name in question or (len(short) >= 4 and short in question):
            hits.append(o)
        else:
            m = re.search(r'(\d{4})', name)
            if m and m.group(1) in question and ('单位' in question or '公司' in question or m.group(1) in question):
                # 编号匹配 e.g. 3521
                if m.group(1) in question:
                    hits.append(o)
    # 去重
    seen, uniq = set(), []
    for h in hits:
        if h['org_id'] not in seen:
            seen.add(h['org_id'])
            uniq.append(h)
    return uniq


def classify_intent(question: str, matched_terms, metrics, objects):
    """LLM 意图识别"""
    metric_list = [{'code': m['map_target'], 'name': m['map_target_name']} for m in metrics]
    object_list = [{'code': o['map_target'], 'name': o['map_target_name']} for o in objects]
    prompt = f"""你是际华国际经营数据分析平台的语义解析引擎。分析用户问题的意图，输出 JSON。

用户问题: {question}

已通过术语词典识别:
- 指标: {json.dumps(metric_list, ensure_ascii=False)}
- 业务对象: {json.dumps(object_list, ensure_ascii=False)}

请输出 JSON，字段:
- intent: 意图类型，取值之一: metric_query(指标查询) / rank(排名对比) / trend(趋势分析) / attribution(原因归因分析) / risk_query(风险查询) / knowledge_qa(制度知识问答) / graph_query(关系穿透查询)
- metric_code: 主要查询的指标编码(若有，从已识别指标中选)
- compare: 对比方式 yoy/mom/budget/none
- need_reason: 是否需要原因分析 true/false
- rank_direction: 若是排名，desc(最高/最多)或asc(最低/最少)
- keywords: 问题中的其他关键信息数组

只输出 JSON。"""
    try:
        raw = llm.chat([{'role': 'user', 'content': prompt}], json_mode=True, max_tokens=500)
        return json.loads(raw)
    except Exception:
        # 降级: 规则判断
        intent = 'metric_query'
        if any(k in question for k in ['为什么', '原因', '归因']):
            intent = 'attribution'
        elif any(k in question for k in ['哪个', '哪些', '排名', '最高', '最低', '最多', 'Top', 'top']):
            intent = 'rank'
        elif any(k in question for k in ['趋势', '变化', '最近']):
            intent = 'trend'
        elif any(k in question for k in ['风险', '预警', '异常', '问题']):
            intent = 'risk_query'
        elif any(k in question for k in ['制度', '规定', '怎么', '如何', '什么是']):
            intent = 'knowledge_qa'
        return {
            'intent': intent,
            'metric_code': metrics[0]['map_target'] if metrics else None,
            'compare': 'yoy' if '同比' in question else 'mom' if '环比' in question else 'none',
            'need_reason': '为什么' in question or '原因' in question,
            'rank_direction': 'asc' if any(k in question for k in ['最低', '最少', '最差']) else 'desc',
            'keywords': [],
        }


def parse_question(question: str):
    """完整语义解析管线"""
    hits = match_terms(question)
    metrics = [h for h in hits if h['map_type'] == 'metric']
    objects = [h for h in hits if h['map_type'] == 'object']
    actions = [h for h in hits if h['map_type'] == 'action']
    time_info = resolve_time(question)
    orgs = resolve_org(question)
    intent = classify_intent(question, hits, metrics, objects)

    # 指标语义加载
    metric_code = intent.get('metric_code') or (metrics[0]['map_target'] if metrics else None)
    metric_semantic = None
    if metric_code:
        metric_semantic = db.query_one(
            "SELECT * FROM kp_metric_semantic WHERE metric_code=%s", (metric_code,))

    # 路径规划: 根据指标归因路径找方法论
    method = None
    if metric_semantic and metric_semantic.get('attribution_path'):
        method = db.query_one("SELECT * FROM kp_method WHERE code=%s", (metric_semantic['attribution_path'],))

    return {
        'question': question,
        'matched_terms': [{'term': h['term'], 'type': h['term_type'], 'map_type': h['map_type'],
                           'target': h['map_target'], 'target_name': h['map_target_name'],
                           'confidence': float(h['confidence'] or 0)} for h in hits],
        'metrics': [{'code': m['map_target'], 'name': m['map_target_name']} for m in metrics],
        'objects': [{'code': o['map_target'], 'name': o['map_target_name']} for o in objects],
        'actions': [{'code': a['map_target'], 'name': a['map_target_name']} for a in actions],
        'time': time_info,
        'orgs': [{'org_id': o['org_id'], 'org_name': o['org_name']} for o in orgs],
        'intent': intent,
        'metric_semantic_loaded': bool(metric_semantic),
        'method': {'code': method['code'], 'name': method['name']} if method else None,
    }
