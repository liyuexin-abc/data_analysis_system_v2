# -*- coding: utf-8 -*-
"""
际华国际知识平台 - Python AI 服务
端口: 8100
职责: 智能问数 / 语义解析 / 归因分析 / RAG 向量化与检索
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import qa, semantic, attribution, rag, db
from config import SERVICE_PORT

app = FastAPI(title='知识平台 AI 服务', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


def ok(data):
    return {'code': 0, 'message': 'success', 'data': data}


@app.exception_handler(Exception)
async def err_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={'code': 1, 'message': str(exc), 'data': None})


@app.get('/api/ai/health')
def health():
    return ok({'service': 'kp-ai-service', 'status': 'ok'})


# ---------- 智能问数 ----------
class QARequest(BaseModel):
    question: str


@app.post('/api/ai/qa')
def qa_endpoint(req: QARequest):
    return ok(qa.answer_question(req.question))


@app.post('/api/ai/qa/parse')
def parse_endpoint(req: QARequest):
    """仅语义解析(用于指标语义测试问数)"""
    return ok(semantic.parse_question(req.question))


@app.get('/api/ai/qa/logs')
def qa_logs(page: int = 1, size: int = 20):
    offset = (page - 1) * size
    rows = db.query('SELECT * FROM kp_qa_log ORDER BY id DESC LIMIT %s OFFSET %s', (size, offset))
    total = db.query_one('SELECT COUNT(*) AS c FROM kp_qa_log')['c']
    for r in rows:
        for f in ('matched_terms', 'matched_metrics', 'matched_objects', 'plan', 'knowledge_refs'):
            r[f] = db.pj(r[f], None)
    return ok({'list': rows, 'total': total, 'page': page, 'size': size})


class FeedbackRequest(BaseModel):
    qa_id: int
    feedback: str  # good / bad


@app.post('/api/ai/qa/feedback')
def qa_feedback(req: FeedbackRequest):
    db.execute('UPDATE kp_qa_log SET feedback=%s WHERE id=%s', (req.feedback, req.qa_id))
    return ok(None)


# ---------- 归因分析 ----------
class AttrRequest(BaseModel):
    org_id: str
    period: str | None = None
    compare: str = 'mom'


@app.post('/api/ai/attribution/profit')
def profit_attr(req: AttrRequest):
    result = attribution.profit_attribution(req.org_id, req.period, req.compare)
    db.execute("UPDATE kp_skill SET call_count=call_count+1 WHERE code='SKILL_PROFIT_ATTR'")
    return ok(result)


class ReceiptRequest(BaseModel):
    org_id: str | None = None


@app.post('/api/ai/attribution/receipt-risk')
def receipt_risk(req: ReceiptRequest):
    result = attribution.receipt_risk_analysis(req.org_id)
    db.execute("UPDATE kp_skill SET call_count=call_count+1 WHERE code='SKILL_RECEIPT_RISK'")
    return ok(result)


# ---------- 方法论测试 (PRD 18.5) ----------
class MethodTestRequest(BaseModel):
    method_code: str
    org_id: str = 'ORG_GROUP'
    period: str | None = None
    compare: str = 'mom'


@app.post('/api/ai/method/test')
def method_test(req: MethodTestRequest):
    method = db.query_one('SELECT * FROM kp_method WHERE code=%s', (req.method_code,))
    if not method:
        return JSONResponse(status_code=404, content={'code': 1, 'message': '方法论不存在', 'data': None})
    if req.method_code == 'MTH_Profit_Attribution':
        result = attribution.profit_attribution(req.org_id, req.period, req.compare)
    elif req.method_code == 'MTH_Receipt_Risk':
        result = attribution.receipt_risk_analysis(req.org_id)
    else:
        return ok({'message': f'方法论 {req.method_code} 的测试执行器待二期接入', 'steps': db.pj(method['steps'], [])})
    # 校验: 是否有缺失节点/无数据路径
    validation = {'has_data': 'error' not in result, 'missing': result.get('error')}
    return ok({'result': result, 'validation': validation})


# ---------- RAG ----------
@app.post('/api/ai/rag/vectorize/{doc_id}')
def vectorize(doc_id: int):
    return ok(rag.vectorize_document(doc_id))


class RagQuery(BaseModel):
    question: str
    top_k: int = 4


@app.post('/api/ai/rag/search')
def rag_search(req: RagQuery):
    hits = rag.retrieve(req.question, req.top_k)
    return ok(hits)


@app.post('/api/ai/rag/answer')
def rag_ans(req: RagQuery):
    result = rag.rag_answer(req.question, req.top_k)
    db.execute("UPDATE kp_skill SET call_count=call_count+1 WHERE code='SKILL_REPORT_GEN'")
    return ok(result)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=SERVICE_PORT)
