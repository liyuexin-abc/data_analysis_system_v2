/**
 * 知识治理路由: 审核中心 / 版本管理 / 影响分析 / 质量检查 / 审计日志 / 知识总览
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, pageParams, pj, audit } = require('../utils');
const { transition, REGISTRY } = require('../services/lifecycle');
const { analyzeImpact } = require('../services/impactService');

const router = express.Router();

// ---------- 知识总览(首页) ----------
router.get('/overview', wrap(async (req, res) => {
  const counts = {};
  const queries = [
    ['domain_count', 'SELECT COUNT(*) AS c FROM kp_domain'],
    ['object_count', 'SELECT COUNT(*) AS c FROM kp_object_type'],
    ['link_count', 'SELECT COUNT(*) AS c FROM kp_link_type'],
    ['metric_semantic_count', 'SELECT COUNT(*) AS c FROM kp_metric_semantic'],
    ['term_count', 'SELECT COUNT(*) AS c FROM kp_term'],
    ['rule_count', 'SELECT COUNT(*) AS c FROM kp_rule'],
    ['method_count', 'SELECT COUNT(*) AS c FROM kp_method'],
    ['document_count', 'SELECT COUNT(*) AS c FROM kp_document'],
    ['pending_review_count', "SELECT COUNT(*) AS c FROM kp_review WHERE review_status='pending'"],
    ['skill_count', 'SELECT COUNT(*) AS c FROM kp_skill'],
  ];
  for (const [k, sql] of queries) {
    const [[row]] = await pool.query(sql);
    counts[k] = row.c;
  }

  // 质量概览
  const quality = await computeQuality();

  // 待办事项
  const [pendingReviews] = await pool.query(
    "SELECT review_no, knowledge_type, knowledge_name, applicant, created_at FROM kp_review WHERE review_status='pending' ORDER BY id DESC LIMIT 10");
  const [failedTasks] = await pool.query(
    "SELECT id, name, last_run_at FROM kp_graph_task WHERE last_status='failed' LIMIT 5");

  // 最近变更
  const [recentChanges] = await pool.query(
    "SELECT module, action, knowledge_type, knowledge_code, knowledge_name, operator, created_at FROM kp_audit_log WHERE action IN ('create','update','publish','approve','disable') ORDER BY id DESC LIMIT 12");

  // 调用监控
  const [[qaCalls]] = await pool.query('SELECT COUNT(*) AS c FROM kp_qa_log');
  const [skillCalls] = await pool.query('SELECT code, name, call_count FROM kp_skill ORDER BY call_count DESC');
  const [[docRefs]] = await pool.query('SELECT COALESCE(SUM(ref_count),0) AS c FROM kp_document');

  ok(res, {
    counts, quality,
    todos: { pending_reviews: pendingReviews, failed_graph_tasks: failedTasks },
    recent_changes: recentChanges,
    call_monitor: { qa_calls: qaCalls.c, skill_calls: skillCalls, doc_refs: Number(docRefs.c) },
  });
}));

/** 知识质量检查计算 */
async function computeQuality() {
  // 本体完整率: 对象具备主键属性+映射
  const [objs] = await pool.query("SELECT code FROM kp_object_type WHERE status='published'");
  let completeObjs = 0;
  for (const o of objs) {
    const [[pk]] = await pool.query('SELECT COUNT(*) AS c FROM kp_property WHERE object_code=? AND is_primary=1', [o.code]);
    const [[mp]] = await pool.query('SELECT COUNT(*) AS c FROM kp_mapping WHERE object_code=?', [o.code]);
    if (pk.c > 0 && mp.c > 0) completeObjs++;
  }
  const ontologyRate = objs.length ? Math.round((completeObjs / objs.length) * 100) : 0;

  // 关系完整率: 已发布关系中源/目标对象均已发布
  const [links] = await pool.query("SELECT source_object,target_object FROM kp_link_type WHERE status='published'");
  const pubObjSet = new Set(objs.map(o => o.code));
  const validLinks = links.filter(l => pubObjSet.has(l.source_object) && pubObjSet.has(l.target_object)).length;
  const linkRate = links.length ? Math.round((validLinks / links.length) * 100) : 0;

  // 指标语义覆盖率: 指标事实表中的指标是否有语义
  const [factMetrics] = await pool.query('SELECT DISTINCT metric_code FROM biz_metric_fact');
  const [semMetrics] = await pool.query('SELECT metric_code FROM kp_metric_semantic');
  const semSet = new Set(semMetrics.map(m => m.metric_code));
  const covered = factMetrics.filter(f => semSet.has(f.metric_code)).length;
  const metricRate = factMetrics.length ? Math.round((covered / factMetrics.length) * 100) : 0;

  // 术语覆盖率(命中率近似): 已发布术语占比
  const [[termTotal]] = await pool.query('SELECT COUNT(*) AS c FROM kp_term');
  const [[termPub]] = await pool.query("SELECT COUNT(*) AS c FROM kp_term WHERE status='published'");
  const termRate = termTotal.c ? Math.round((termPub.c / termTotal.c) * 100) : 0;

  // 图谱覆盖率: 应入图对象是否有节点
  const [graphObjs] = await pool.query("SELECT code FROM kp_object_type WHERE in_graph=1 AND status='published'");
  let inGraph = 0;
  for (const g of graphObjs) {
    const [[n]] = await pool.query('SELECT COUNT(*) AS c FROM kp_graph_node WHERE object_code=? LIMIT 1', [g.code]);
    if (n.c > 0) inGraph++;
  }
  const graphRate = graphObjs.length ? Math.round((inGraph / graphObjs.length) * 100) : 0;

  // 规则可执行率
  const [[ruleTotal]] = await pool.query("SELECT COUNT(*) AS c FROM kp_rule WHERE status='published'");
  const [execRules] = await pool.query(
    "SELECT DISTINCT rule_code FROM kp_rule_run_log WHERE status='success'");
  const ruleRate = ruleTotal.c ? Math.min(100, Math.round((execRules.length / ruleTotal.c) * 100)) : 0;

  // 方法论可用率
  const [[mTotal]] = await pool.query("SELECT COUNT(*) AS c FROM kp_method WHERE status='published'");
  const [methods] = await pool.query("SELECT steps FROM kp_method WHERE status='published'");
  const usable = methods.filter(m => (pj(m.steps, []) || []).length > 0).length;
  const methodRate = mTotal.c ? Math.round((usable / mTotal.c) * 100) : 0;

  // RAG 可检索率
  const [[docTotal]] = await pool.query('SELECT COUNT(*) AS c FROM kp_document');
  const [[docVec]] = await pool.query("SELECT COUNT(*) AS c FROM kp_document WHERE vector_status='vectorized'");
  const ragRate = docTotal.c ? Math.round((docVec.c / docTotal.c) * 100) : 0;

  const items = {
    ontology_rate: ontologyRate, link_rate: linkRate, metric_rate: metricRate,
    term_rate: termRate, graph_rate: graphRate, rule_rate: ruleRate,
    method_rate: methodRate, rag_rate: ragRate,
  };
  const score = Math.round(Object.values(items).reduce((a, b) => a + b, 0) / Object.keys(items).length);
  return { ...items, quality_score: score };
}

// ---------- 质量检查 ----------
router.get('/quality', wrap(async (req, res) => {
  const quality = await computeQuality();
  ok(res, quality);
}));
router.post('/quality/run', wrap(async (req, res) => {
  const quality = await computeQuality();
  await pool.query('INSERT INTO kp_quality_check (check_items,total_score) VALUES (?,?)',
    [JSON.stringify(quality), quality.quality_score]);
  await audit('governance', 'run', { type: 'quality', name: '知识质量检查', detail: quality });
  ok(res, quality);
}));
router.get('/quality/history', wrap(async (req, res) => {
  const [rows] = await pool.query('SELECT * FROM kp_quality_check ORDER BY id DESC LIMIT 20');
  ok(res, rows);
}));

// ---------- 审核中心 ----------
router.get('/reviews', wrap(async (req, res) => {
  const { page, size, offset } = pageParams(req);
  const where = []; const params = [];
  if (req.query.review_status) { where.push('review_status=?'); params.push(req.query.review_status); }
  if (req.query.knowledge_type) { where.push('knowledge_type=?'); params.push(req.query.knowledge_type); }
  const whereSql = where.length ? 'WHERE ' + where.join(' AND ') : '';
  const [[{ total }]] = await pool.query(`SELECT COUNT(*) AS total FROM kp_review ${whereSql}`, params);
  const [rows] = await pool.query(
    `SELECT * FROM kp_review ${whereSql} ORDER BY id DESC LIMIT ? OFFSET ?`, [...params, size, offset]);
  ok(res, { list: rows, total, page, size });
}));

// 审核详情(含影响分析与版本对比)
router.get('/reviews/:id(\\d+)', wrap(async (req, res) => {
  const [[review]] = await pool.query('SELECT * FROM kp_review WHERE id=?', [req.params.id]);
  if (!review) return fail(res, '审核单不存在', 1, 404);
  // 当前知识快照
  const reg = REGISTRY[review.knowledge_type];
  let current = null;
  if (reg) {
    const [[row]] = await pool.query(`SELECT * FROM ${reg.table} WHERE id=?`, [review.knowledge_id]);
    current = row || null;
  }
  // 历史版本
  const [versions] = await pool.query(
    'SELECT * FROM kp_version WHERE knowledge_type=? AND knowledge_id=? ORDER BY id DESC LIMIT 5',
    [review.knowledge_type, review.knowledge_id]);
  // 影响分析
  let impacts = [];
  if (review.knowledge_code) {
    try { impacts = await analyzeImpact(review.knowledge_type, review.knowledge_code); } catch { /* */ }
  }
  ok(res, { review, current, versions, impacts });
}));

// 审核通过/驳回 (走生命周期)
router.post('/reviews/:id(\\d+)/approve', wrap(async (req, res) => {
  const [[review]] = await pool.query('SELECT * FROM kp_review WHERE id=?', [req.params.id]);
  if (!review) return fail(res, '审核单不存在', 1, 404);
  if (review.review_status !== 'pending') return fail(res, '该审核单已处理');
  const result = await transition(review.knowledge_type, review.knowledge_id, 'approve',
    { operator: req.body.operator || 'reviewer', comment: req.body.comment || '' });
  ok(res, result);
}));
router.post('/reviews/:id(\\d+)/reject', wrap(async (req, res) => {
  const [[review]] = await pool.query('SELECT * FROM kp_review WHERE id=?', [req.params.id]);
  if (!review) return fail(res, '审核单不存在', 1, 404);
  if (review.review_status !== 'pending') return fail(res, '该审核单已处理');
  const result = await transition(review.knowledge_type, review.knowledge_id, 'reject',
    { operator: req.body.operator || 'reviewer', comment: req.body.comment || '驳回' });
  ok(res, result);
}));

// ---------- 版本管理 ----------
router.get('/versions', wrap(async (req, res) => {
  const { page, size, offset } = pageParams(req);
  const where = []; const params = [];
  if (req.query.knowledge_type) { where.push('knowledge_type=?'); params.push(req.query.knowledge_type); }
  if (req.query.knowledge_code) { where.push('knowledge_code LIKE ?'); params.push(`%${req.query.knowledge_code}%`); }
  const whereSql = where.length ? 'WHERE ' + where.join(' AND ') : '';
  const [[{ total }]] = await pool.query(`SELECT COUNT(*) AS total FROM kp_version ${whereSql}`, params);
  const [rows] = await pool.query(
    `SELECT * FROM kp_version ${whereSql} ORDER BY id DESC LIMIT ? OFFSET ?`, [...params, size, offset]);
  ok(res, { list: rows, total, page, size });
}));

// 版本对比
router.get('/versions/compare', wrap(async (req, res) => {
  const { type, code } = req.query;
  const [rows] = await pool.query(
    'SELECT * FROM kp_version WHERE knowledge_type=? AND knowledge_code=? ORDER BY id DESC LIMIT 2', [type, code]);
  if (rows.length < 2) return ok(res, { versions: rows, diff: [] });
  const newer = pj(rows[0].snapshot, {}); const older = pj(rows[1].snapshot, {});
  const keys = new Set([...Object.keys(newer), ...Object.keys(older)]);
  const diff = [];
  for (const k of keys) {
    const a = JSON.stringify(older[k]); const b = JSON.stringify(newer[k]);
    if (a !== b) diff.push({ field: k, old_value: older[k], new_value: newer[k] });
  }
  ok(res, { versions: rows, diff });
}));

// ---------- 影响分析 ----------
router.get('/impact/:type/:code', wrap(async (req, res) => {
  const impacts = await analyzeImpact(req.params.type, decodeURIComponent(req.params.code));
  ok(res, impacts);
}));

// ---------- 审计日志 ----------
router.get('/audit-logs', wrap(async (req, res) => {
  const { page, size, offset } = pageParams(req);
  const where = []; const params = [];
  if (req.query.module) { where.push('module=?'); params.push(req.query.module); }
  if (req.query.action) { where.push('action=?'); params.push(req.query.action); }
  if (req.query.keyword) {
    where.push('(knowledge_code LIKE ? OR knowledge_name LIKE ? OR operator LIKE ?)');
    params.push(`%${req.query.keyword}%`, `%${req.query.keyword}%`, `%${req.query.keyword}%`);
  }
  const whereSql = where.length ? 'WHERE ' + where.join(' AND ') : '';
  const [[{ total }]] = await pool.query(`SELECT COUNT(*) AS total FROM kp_audit_log ${whereSql}`, params);
  const [rows] = await pool.query(
    `SELECT * FROM kp_audit_log ${whereSql} ORDER BY id DESC LIMIT ? OFFSET ?`, [...params, size, offset]);
  ok(res, { list: rows, total, page, size });
}));

module.exports = router;
