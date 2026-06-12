/**
 * 图谱中心路由: 模型 / 构建任务 / 浏览 / 路径查询 / 影响分析
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, pageParams } = require('../utils');
const crudRouter = require('./crudFactory');
const graphSvc = require('../services/graphService');
const { audit } = require('../utils');

const router = express.Router();

// 图谱模型 CRUD
router.use('/models', crudRouter({
  table: 'kp_graph_model', type: 'graph', module: 'graph',
  searchFields: ['code', 'name'], filters: ['status', 'scene'],
  jsonFields: ['include_objects', 'include_links'],
}));

// 图谱构建任务 CRUD
const taskRouter = crudRouter({
  table: 'kp_graph_task', module: 'graph', codeField: 'id', nameField: 'name',
  searchFields: ['name', 'graph_code'], filters: ['graph_code', 'last_status', 'status'],
  jsonFields: ['data_sources', 'entity_rules', 'relation_rules', 'dedup_rules', 'disambig_rules', 'quality_rules'],
});

// 立即执行构建
taskRouter.post('/:id(\\d+)/run', wrap(async (req, res) => {
  const result = await graphSvc.buildGraph(req.params.id);
  await audit('graph', 'run', { type: 'graph_task', code: String(req.params.id), name: '图谱构建', detail: result });
  ok(res, result);
}));

// 查看构建日志
taskRouter.get('/:id(\\d+)/logs', wrap(async (req, res) => {
  const [rows] = await pool.query(
    'SELECT * FROM kp_graph_task_log WHERE task_id=? ORDER BY id DESC LIMIT 50', [req.params.id]);
  ok(res, rows);
}));

router.use('/tasks', taskRouter);

// ---------- 图谱浏览 ----------
// 搜索节点
router.get('/explore/search', wrap(async (req, res) => {
  const { graph = 'graph_business_core', keyword = '', object_code } = req.query;
  if (!keyword) return ok(res, []);
  const rows = await graphSvc.searchNodes(graph, keyword, object_code || null);
  ok(res, rows);
}));

// 展开邻居
router.get('/explore/neighbors/:nodeId', wrap(async (req, res) => {
  const { graph = 'graph_business_core', hops = 1 } = req.query;
  const result = await graphSvc.expandNeighbors(graph, req.params.nodeId, Math.min(5, Number(hops)));
  ok(res, result);
}));

// 节点详情
router.get('/explore/node/:nodeId', wrap(async (req, res) => {
  const [[node]] = await pool.query('SELECT * FROM kp_graph_node WHERE id=?', [req.params.nodeId]);
  if (!node) return fail(res, '节点不存在', 1, 404);
  node.props = typeof node.props === 'string' ? JSON.parse(node.props) : node.props;
  const [[obj]] = await pool.query('SELECT name FROM kp_object_type WHERE code=?', [node.object_code]);
  ok(res, { ...node, object_name: obj ? obj.name : node.object_code });
}));

// 图谱统计
router.get('/explore/stats', wrap(async (req, res) => {
  const { graph = 'graph_business_core' } = req.query;
  const [byType] = await pool.query(
    `SELECT n.object_code, o.name AS object_name, COUNT(*) AS count FROM kp_graph_node n
     LEFT JOIN kp_object_type o ON n.object_code=o.code
     WHERE n.graph_code=? GROUP BY n.object_code, o.name ORDER BY count DESC`, [graph]);
  const [byLink] = await pool.query(
    `SELECT e.link_code, l.name AS link_name, COUNT(*) AS count FROM kp_graph_edge e
     LEFT JOIN kp_link_type l ON e.link_code=l.code
     WHERE e.graph_code=? GROUP BY e.link_code, l.name ORDER BY count DESC`, [graph]);
  const [[nodes]] = await pool.query('SELECT COUNT(*) AS c FROM kp_graph_node WHERE graph_code=?', [graph]);
  const [[edges]] = await pool.query('SELECT COUNT(*) AS c FROM kp_graph_edge WHERE graph_code=?', [graph]);
  ok(res, { node_count: nodes.c, edge_count: edges.c, by_type: byType, by_link: byLink });
}));

// ---------- 路径查询 ----------
router.post('/path-query', wrap(async (req, res) => {
  const { graph = 'graph_business_core', start_node_id, end_node_id, end_object_code, max_hops = 3 } = req.body;
  if (!start_node_id) return fail(res, '缺少起点节点');
  if (!end_node_id && !end_object_code) return fail(res, '需指定终点节点或终点对象类型');
  const paths = await graphSvc.findPaths(graph, start_node_id, {
    endNodeId: end_node_id || null, endObjectCode: end_object_code || null,
    maxHops: Math.min(5, Number(max_hops)),
  });
  // 关系名称
  const [links] = await pool.query('SELECT code,name FROM kp_link_type');
  const linkNames = Object.fromEntries(links.map(l => [l.code, l.name]));
  paths.forEach(p => p.links.forEach(l => { l.name = linkNames[l.link] || l.link; }));
  await audit('graph', 'call', { type: 'graph', code: graph, name: '路径查询', detail: { start_node_id, found: paths.length } });
  ok(res, paths);
}));

// ---------- 影响分析 ----------
router.post('/impact-analysis', wrap(async (req, res) => {
  const { graph = 'graph_business_core', node_id, max_hops = 3 } = req.body;
  if (!node_id) return fail(res, '缺少分析节点');
  const result = await graphSvc.impactAnalysis(graph, node_id, Math.min(5, Number(max_hops)));
  await audit('graph', 'call', { type: 'graph', code: graph, name: '影响分析', detail: { node_id } });
  ok(res, result);
}));

module.exports = router;
