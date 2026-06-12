/**
 * RAG 知识库路由(文档管理部分)
 * 解析/切片在 Node 完成；向量化/检索代理至 Python AI 服务
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, audit } = require('../utils');
const crudRouter = require('./crudFactory');

const AI_BASE = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8100';

const router = express.Router();

const docRouter = crudRouter({
  table: 'kp_document', type: 'document', module: 'rag',
  codeField: 'id', nameField: 'name',
  searchFields: ['name', 'file_name'],
  filters: ['doc_type', 'security_level', 'parse_status', 'vector_status', 'status'],
  jsonFields: ['scenes', 'domains', 'visible_roles', 'tags'],
});

/** 文本切片: 按段落聚合，每片约 maxLen 字符，带 overlap */
function chunkText(text, maxLen = 500, overlap = 50) {
  const paras = text.split(/\n+/).map(s => s.trim()).filter(Boolean);
  const chunks = [];
  let buf = '';
  for (const p of paras) {
    if (buf.length + p.length + 1 > maxLen && buf) {
      chunks.push(buf);
      buf = buf.slice(Math.max(0, buf.length - overlap)) + '\n' + p;
    } else {
      buf = buf ? buf + '\n' + p : p;
    }
  }
  if (buf) chunks.push(buf);
  return chunks;
}

// 解析 + 切片
docRouter.post('/:id(\\d+)/parse', wrap(async (req, res) => {
  const [[doc]] = await pool.query('SELECT * FROM kp_document WHERE id=?', [req.params.id]);
  if (!doc) return fail(res, '文档不存在', 1, 404);
  if (!doc.content) {
    await pool.query("UPDATE kp_document SET parse_status='failed' WHERE id=?", [doc.id]);
    return fail(res, '文档内容为空，解析失败');
  }
  await pool.query("UPDATE kp_document SET parse_status='parsed', chunk_status='chunking' WHERE id=?", [doc.id]);
  // 切片
  await pool.query('DELETE FROM kp_doc_chunk WHERE doc_id=?', [doc.id]);
  const chunks = chunkText(doc.content);
  for (let i = 0; i < chunks.length; i++) {
    await pool.query(
      'INSERT INTO kp_doc_chunk (doc_id,chunk_index,content,token_count) VALUES (?,?,?,?)',
      [doc.id, i, chunks[i], Math.ceil(chunks[i].length / 2)]);
  }
  await pool.query("UPDATE kp_document SET chunk_status='chunked', chunk_count=? WHERE id=?", [chunks.length, doc.id]);
  await audit('rag', 'run', { type: 'document', code: String(doc.id), name: doc.name, detail: { chunks: chunks.length } });
  ok(res, { chunks: chunks.length });
}));

// 向量化(代理 AI 服务)
docRouter.post('/:id(\\d+)/vectorize', wrap(async (req, res) => {
  const [[doc]] = await pool.query('SELECT * FROM kp_document WHERE id=?', [req.params.id]);
  if (!doc) return fail(res, '文档不存在', 1, 404);
  if (doc.chunk_status !== 'chunked') return fail(res, '请先完成文档解析和切片');
  await pool.query("UPDATE kp_document SET vector_status='vectorizing' WHERE id=?", [doc.id]);
  try {
    const resp = await fetch(`${AI_BASE}/api/ai/rag/vectorize/${doc.id}`, { method: 'POST' });
    const data = await resp.json();
    if (!resp.ok || data.code !== 0) throw new Error(data.message || '向量化失败');
    await pool.query("UPDATE kp_document SET vector_status='vectorized' WHERE id=?", [doc.id]);
    await audit('rag', 'run', { type: 'document', code: String(doc.id), name: doc.name, detail: { action: 'vectorize', ...data.data } });
    ok(res, data.data);
  } catch (e) {
    await pool.query("UPDATE kp_document SET vector_status='failed' WHERE id=?", [doc.id]);
    return fail(res, '向量化失败: ' + e.message, 1, 500);
  }
}));

// 一键处理: 解析→切片→向量化→提交审核
docRouter.post('/:id(\\d+)/process-all', wrap(async (req, res) => {
  const [[doc]] = await pool.query('SELECT * FROM kp_document WHERE id=?', [req.params.id]);
  if (!doc) return fail(res, '文档不存在', 1, 404);
  // parse + chunk
  const chunks = chunkText(doc.content || '');
  if (!chunks.length) return fail(res, '文档内容为空');
  await pool.query('DELETE FROM kp_doc_chunk WHERE doc_id=?', [doc.id]);
  for (let i = 0; i < chunks.length; i++) {
    await pool.query('INSERT INTO kp_doc_chunk (doc_id,chunk_index,content,token_count) VALUES (?,?,?,?)',
      [doc.id, i, chunks[i], Math.ceil(chunks[i].length / 2)]);
  }
  await pool.query(
    "UPDATE kp_document SET parse_status='parsed', chunk_status='chunked', chunk_count=?, vector_status='vectorizing' WHERE id=?",
    [chunks.length, doc.id]);
  // vectorize
  let vec = { vectorized: 0 };
  try {
    const resp = await fetch(`${AI_BASE}/api/ai/rag/vectorize/${doc.id}`, { method: 'POST' });
    const data = await resp.json();
    if (resp.ok && data.code === 0) {
      await pool.query("UPDATE kp_document SET vector_status='vectorized' WHERE id=?", [doc.id]);
      vec = data.data;
    } else throw new Error(data.message || 'AI服务返回错误');
  } catch (e) {
    await pool.query("UPDATE kp_document SET vector_status='failed' WHERE id=?", [doc.id]);
    return fail(res, '向量化失败: ' + e.message, 1, 500);
  }
  ok(res, { chunks: chunks.length, ...vec });
}));

// 切片列表
docRouter.get('/:id(\\d+)/chunks', wrap(async (req, res) => {
  const [rows] = await pool.query('SELECT * FROM kp_doc_chunk WHERE doc_id=? ORDER BY chunk_index', [req.params.id]);
  ok(res, rows);
}));

router.use('/documents', docRouter);

module.exports = router;
