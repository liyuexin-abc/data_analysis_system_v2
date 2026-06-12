# -*- coding: utf-8 -*-
"""LLM 与 Embedding 客户端封装"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openai import OpenAI
from config import (LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL, LLM_TEMPERATURE,
                    LLM_MAX_TOKENS, EMBED_API_KEY, EMBED_API_BASE_URL, EMBED_MODEL)

_llm_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE_URL, timeout=120)
_embed_client = OpenAI(api_key=EMBED_API_KEY, base_url=EMBED_API_BASE_URL, timeout=60)


def chat(messages, temperature=None, max_tokens=None, json_mode=False):
    """调用 LLM 对话"""
    kwargs = dict(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        max_tokens=max_tokens or LLM_MAX_TOKENS,
    )
    if json_mode:
        kwargs['response_format'] = {'type': 'json_object'}
    resp = _llm_client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def embed(texts):
    """批量向量化，DashScope text-embedding-v4 单批最多 10 条"""
    if isinstance(texts, str):
        texts = [texts]
    vectors = []
    for i in range(0, len(texts), 10):
        batch = texts[i:i + 10]
        resp = _embed_client.embeddings.create(model=EMBED_MODEL, input=batch)
        vectors.extend([d.embedding for d in resp.data])
    return vectors
