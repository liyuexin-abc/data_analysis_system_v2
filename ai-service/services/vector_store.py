# -*- coding: utf-8 -*-
"""ChromaDB 向量库封装 (开源向量数据库，持久化到本地)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chromadb
from config import CHROMA_DIR, CHROMA_COLLECTION

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={'hnsw:space': 'cosine'},
        )
    return _collection


def upsert_chunks(doc_id, chunks, embeddings, metadatas):
    """写入文档切片向量"""
    col = get_collection()
    ids = [f'doc{doc_id}_chunk{i}' for i in range(len(chunks))]
    col.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return ids


def delete_doc(doc_id):
    col = get_collection()
    col.delete(where={'doc_id': doc_id})


def search(query_embedding, top_k=5, where=None):
    """向量检索"""
    col = get_collection()
    kwargs = dict(query_embeddings=[query_embedding], n_results=top_k)
    if where:
        kwargs['where'] = where
    res = col.query(**kwargs)
    hits = []
    for i in range(len(res['ids'][0])):
        hits.append({
            'id': res['ids'][0][i],
            'content': res['documents'][0][i],
            'metadata': res['metadatas'][0][i],
            'distance': res['distances'][0][i],
            'score': round(1 - res['distances'][0][i], 4),
        })
    return hits
