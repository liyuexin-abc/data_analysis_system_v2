# -*- coding: utf-8 -*-
"""AI 服务配置"""
import os

# 大模型服务
LLM_API_KEY = os.getenv('LLM_API_KEY', 'sk-bcebd07345bc4c6ca6b38c029d6a9113')
LLM_API_BASE_URL = os.getenv('LLM_API_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'qwen3-235b-a22b-instruct-2507')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.1'))
LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '4096'))

# Embedding 服务
EMBED_API_KEY = os.getenv('EMBED_API_KEY', LLM_API_KEY)
EMBED_API_BASE_URL = os.getenv('EMBED_API_BASE_URL', LLM_API_BASE_URL)
EMBED_MODEL = os.getenv('EMBED_MODEL', 'text-embedding-v4')

# MySQL
DB_CONFIG = dict(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'kp_user'),
    password=os.getenv('DB_PASSWORD', 'kp_pass_2026'),
    database=os.getenv('DB_NAME', 'knowledge_platform'),
    charset='utf8mb4',
)

# ChromaDB 向量库持久化目录
CHROMA_DIR = os.getenv('CHROMA_DIR', os.path.join(os.path.dirname(__file__), 'chroma_data'))
CHROMA_COLLECTION = 'kp_documents'

SERVICE_PORT = int(os.getenv('AI_SERVICE_PORT', '8100'))
