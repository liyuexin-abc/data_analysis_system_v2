# -*- coding: utf-8 -*-
"""
RAG 服务: 文档向量化 + 检索 + 引用控制
遵循 PRD 11.4 调用控制: 检索结果带来源、过期文档不参与、按密级标注
"""
import datetime
from . import db
from . import llm
from . import vector_store


def vectorize_document(doc_id: int):
    """对已切片文档执行向量化并写入 ChromaDB"""
    doc = db.query_one("SELECT * FROM kp_document WHERE id=%s", (doc_id,))
    if not doc:
        raise ValueError('文档不存在')
    chunks = db.query("SELECT * FROM kp_doc_chunk WHERE doc_id=%s ORDER BY chunk_index", (doc_id,))
    if not chunks:
        raise ValueError('文档尚未切片')
    texts = [c['content'] for c in chunks]
    embeddings = llm.embed(texts)
    metadatas = [{
        'doc_id': doc_id,
        'doc_name': doc['name'],
        'doc_type': doc['doc_type'],
        'security_level': doc['security_level'],
        'chunk_index': c['chunk_index'],
        'expire_date': str(doc['expire_date']) if doc['expire_date'] else '',
    } for c in chunks]
    ids = vector_store.upsert_chunks(doc_id, texts, embeddings, metadatas)
    # 回写向量 ID
    for c, vid in zip(chunks, ids):
        db.execute("UPDATE kp_doc_chunk SET vector_id=%s WHERE id=%s", (vid, c['id']))
    return {'vectorized': len(ids)}


def retrieve(question: str, top_k: int = 5):
    """向量检索，过滤过期文档"""
    qvec = llm.embed(question)[0]
    hits = vector_store.search(qvec, top_k=top_k * 2)
    today = str(datetime.date.today())
    valid = []
    for h in hits:
        exp = h['metadata'].get('expire_date') or ''
        if exp and exp < today:
            continue  # 已过期文档默认不参与回答
        valid.append(h)
        if len(valid) >= top_k:
            break
    # 引用计数
    doc_ids = {h['metadata']['doc_id'] for h in valid}
    for d in doc_ids:
        db.execute("UPDATE kp_document SET ref_count=ref_count+1 WHERE id=%s", (d,))
    return valid


def rag_answer(question: str, top_k: int = 4):
    """RAG 问答: 检索 + 生成 + 引用来源"""
    hits = retrieve(question, top_k)
    if not hits:
        return {'answer': '知识库中未检索到相关内容。', 'references': []}
    context_parts = []
    for i, h in enumerate(hits):
        context_parts.append(f"[文档{i+1}]《{h['metadata']['doc_name']}》(相关度{h['score']}):\n{h['content']}")
    context = '\n\n'.join(context_parts)
    prompt = f"""你是际华国际经营数据分析平台的知识助手。请基于以下知识库内容回答用户问题。

要求:
1. 只依据知识库内容回答，不编造；
2. 回答末尾标注引用来源(文档名称)；
3. 如果知识库内容不足以回答，请明确说明。

知识库内容:
{context}

用户问题: {question}"""
    answer = llm.chat([{'role': 'user', 'content': prompt}], max_tokens=1500)
    references = [{
        'doc_id': h['metadata']['doc_id'],
        'doc_name': h['metadata']['doc_name'],
        'doc_type': h['metadata']['doc_type'],
        'security_level': h['metadata']['security_level'],
        'chunk_index': h['metadata']['chunk_index'],
        'score': h['score'],
        'excerpt': h['content'][:120],
    } for h in hits]
    return {'answer': answer, 'references': references}
