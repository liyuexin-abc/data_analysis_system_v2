/**
 * 术语词典 / 指标语义 / 规则语义 / 分析方法论 / Skill 路由
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, pj, audit } = require('../utils');
const crudRouter = require('./crudFactory');
const { runRule } = require('../services/ruleEngine');

const router = express.Router();

// ---------- 术语词典 ----------
const termRouter = crudRouter({
  table: 'kp_term', type: 'term', module: 'term', codeField: 'term', nameField: 'term',
  searchFields: ['term', 'map_target', 'map_target_name'],
  filters: ['term_type', 'map_type', 'status'],
  jsonFields: ['scenes'],
});
// 批量导入术语
termRouter.post('/batch-import', wrap(async (req, res) => {
  const { terms } = req.body;
  if (!Array.isArray(terms)) return fail(res, '参数错误');
  let imported = 0;
  for (const t of terms) {
    if (!t.term || !t.map_target) continue;
    await pool.query(
      "INSERT INTO kp_term (term,term_type,map_type,map_target,map_target_name,scenes,confidence,examples,status) VALUES (?,?,?,?,?,?,?,?,'draft')",
      [t.term, t.term_type || 'phrase', t.map_type || 'metric', t.map_target,
       t.map_target_name || null, JSON.stringify(t.scenes || ['经营分析']), t.confidence || 0.8, t.examples || null]);
    imported++;
  }
  await audit('term', 'create', { type: 'term', name: '批量导入术语', detail: { imported } });
  ok(res, { imported });
}));
// 术语命中测试: 给一句话找出命中的术语
termRouter.post('/match-test', wrap(async (req, res) => {
  const { question = '' } = req.body;
  const [terms] = await pool.query("SELECT * FROM kp_term WHERE status='published'");
  const hits = terms
    .filter(t => question.includes(t.term))
    .sort((a, b) => b.term.length - a.term.length || b.confidence - a.confidence)
    .map(t => ({ term: t.term, term_type: t.term_type, map_type: t.map_type,
      map_target: t.map_target, map_target_name: t.map_target_name, confidence: Number(t.confidence) }));
  ok(res, hits);
}));
router.use('/terms', termRouter);

// ---------- 指标语义 ----------
const metricRouter = crudRouter({
  table: 'kp_metric_semantic', type: 'metric', module: 'metric',
  codeField: 'metric_code', nameField: 'metric_name',
  searchFields: ['metric_code', 'metric_name'],
  filters: ['category', 'status', 'security_level'],
  jsonFields: ['synonyms', 'stat_periods', 'dimensions', 'bind_objects', 'charts', 'default_compare'],
});
// 指标引用查看
metricRouter.get('/:id(\\d+)/references', wrap(async (req, res) => {
  const [[m]] = await pool.query('SELECT * FROM kp_metric_semantic WHERE id=?', [req.params.id]);
  if (!m) return fail(res, '指标不存在', 1, 404);
  const { analyzeImpact } = require('../services/impactService');
  const impacts = await analyzeImpact('metric', m.metric_code);
  ok(res, impacts);
}));
// 指标数据预览(用于测试问数)
metricRouter.get('/:code/data', wrap(async (req, res) => {
  const { org_id = 'ORG_GROUP', periods = 12 } = req.query;
  const [rows] = await pool.query(
    `SELECT period, value, budget FROM biz_metric_fact WHERE metric_code=? AND org_id=? AND period_type='month' ORDER BY period DESC LIMIT ?`,
    [req.params.code, org_id, Number(periods)]);
  ok(res, rows.reverse());
}));
router.use('/metrics', metricRouter);

// ---------- 规则语义 ----------
const ruleRouter = crudRouter({
  table: 'kp_rule', type: 'rule', module: 'rule',
  searchFields: ['code', 'name'], filters: ['rule_type', 'monitor_object', 'status', 'run_cycle'],
  jsonFields: ['trigger_cond', 'risk_levels', 'apply_orgs', 'notify_targets', 'actions', 'skills'],
});
// 规则试运行
ruleRouter.post('/:id(\\d+)/test-run', wrap(async (req, res) => {
  const [[rule]] = await pool.query('SELECT code FROM kp_rule WHERE id=?', [req.params.id]);
  if (!rule) return fail(res, '规则不存在', 1, 404);
  const result = await runRule(rule.code, { dryRun: true });
  ok(res, result);
}));
// 规则运行记录
ruleRouter.get('/:id(\\d+)/run-logs', wrap(async (req, res) => {
  const [[rule]] = await pool.query('SELECT code FROM kp_rule WHERE id=?', [req.params.id]);
  if (!rule) return fail(res, '规则不存在', 1, 404);
  const [rows] = await pool.query(
    'SELECT id,rule_code,run_time,run_type,matched,status,message FROM kp_rule_run_log WHERE rule_code=? ORDER BY id DESC LIMIT 30', [rule.code]);
  ok(res, rows);
}));
router.use('/rules', ruleRouter);

// ---------- 分析方法论 ----------
const methodRouter = crudRouter({
  table: 'kp_method', type: 'method', module: 'method',
  searchFields: ['code', 'name'], filters: ['status'],
  jsonFields: ['scenes', 'apply_metrics', 'apply_objects', 'steps', 'decompose_tree', 'graph_paths', 'output_charts', 'bind_skills'],
});
router.use('/methods', methodRouter);

// ---------- Skill ----------
const skillRouter = crudRouter({
  table: 'kp_skill', module: 'skill', searchFields: ['code', 'name'],
  jsonFields: ['depend_knowledge'],
});
// Skill 知识加载预览: 按依赖清单加载知识
skillRouter.get('/:id(\\d+)/knowledge', wrap(async (req, res) => {
  const [[skill]] = await pool.query('SELECT * FROM kp_skill WHERE id=?', [req.params.id]);
  if (!skill) return fail(res, 'Skill不存在', 1, 404);
  const dep = pj(skill.depend_knowledge, {});
  const loaded = {};
  const depStr = JSON.stringify(dep);
  // 加载相关指标
  const [metrics] = await pool.query("SELECT metric_code,metric_name,business_def FROM kp_metric_semantic WHERE status='published'");
  loaded.metrics = metrics.filter(m => depStr.includes(m.metric_code));
  // 加载方法论
  const [methods] = await pool.query("SELECT code,name FROM kp_method WHERE status='published'");
  loaded.methods = methods.filter(m => depStr.includes(m.code));
  // 加载规则
  const [rules] = await pool.query("SELECT code,name FROM kp_rule WHERE status='published'");
  loaded.rules = rules.filter(r => depStr.includes(r.code));
  // 术语/本体按声明类别加载
  if (depStr.includes('术语')) {
    const [[tc]] = await pool.query("SELECT COUNT(*) AS c FROM kp_term WHERE status='published'");
    loaded.term_count = tc.c;
  }
  if (depStr.includes('本体')) {
    const [[oc]] = await pool.query("SELECT COUNT(*) AS c FROM kp_object_type WHERE status='published'");
    loaded.object_count = oc.c;
  }
  ok(res, { skill: { code: skill.code, name: skill.name }, depend_knowledge: dep, loaded });
}));
router.use('/skills', skillRouter);

module.exports = router;
