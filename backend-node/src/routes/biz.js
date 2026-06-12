/**
 * 经营业务数据查询路由(只读): 供前端演示和 AI 服务调用
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, pageParams } = require('../utils');

const router = express.Router();

// 组织树
router.get('/orgs/tree', wrap(async (req, res) => {
  const [rows] = await pool.query('SELECT * FROM biz_org ORDER BY org_level, org_id');
  const map = new Map(rows.map(r => [r.org_id, { ...r, children: [] }]));
  const roots = [];
  for (const node of map.values()) {
    if (node.parent_id && map.has(node.parent_id)) map.get(node.parent_id).children.push(node);
    else roots.push(node);
  }
  ok(res, roots);
}));

router.get('/orgs', wrap(async (req, res) => {
  const [rows] = await pool.query('SELECT * FROM biz_org ORDER BY org_level, org_id');
  ok(res, rows);
}));

// 指标事实查询
router.get('/metric-facts', wrap(async (req, res) => {
  const { metric_code, org_id = 'ORG_GROUP', period_type = 'month', limit = 18 } = req.query;
  if (!metric_code) return fail(res, '缺少 metric_code');
  const [rows] = await pool.query(
    'SELECT * FROM biz_metric_fact WHERE metric_code=? AND org_id=? AND period_type=? ORDER BY period DESC LIMIT ?',
    [metric_code, org_id, period_type, Number(limit)]);
  ok(res, rows.reverse());
}));

// 指标排名: 某期间各单位某指标排名
router.get('/metric-rank', wrap(async (req, res) => {
  const { metric_code, period, org_level = 3 } = req.query;
  if (!metric_code) return fail(res, '缺少 metric_code');
  let p = period;
  if (!p) {
    const [[row]] = await pool.query(
      "SELECT MAX(period) AS p FROM biz_metric_fact WHERE metric_code=? AND period_type='month'", [metric_code]);
    p = row.p;
  }
  const [rows] = await pool.query(
    `SELECT f.org_id, o.org_name, f.value, f.budget FROM biz_metric_fact f
     JOIN biz_org o ON f.org_id=o.org_id
     WHERE f.metric_code=? AND f.period=? AND o.org_level=? ORDER BY f.value DESC`,
    [metric_code, p, Number(org_level)]);
  ok(res, { period: p, list: rows });
}));

// 通用业务表分页查询(白名单)
const BIZ_TABLES = {
  customers: 'biz_customer', contracts: 'biz_contract', orders: 'biz_order',
  receipts: 'biz_receipt', suppliers: 'biz_supplier', materials: 'biz_material',
  'purchase-orders': 'biz_purchase_order', inventories: 'biz_inventory',
  'prod-tasks': 'biz_prod_task', risks: 'biz_risk', 'rectify-tasks': 'biz_rectify_task',
};

router.get('/:resource', wrap(async (req, res) => {
  const table = BIZ_TABLES[req.params.resource];
  if (!table) return fail(res, '未知业务资源', 1, 404);
  const { page, size, offset } = pageParams(req);
  const where = []; const params = [];
  // 通用过滤: org_id / 状态字段 / 关键字
  if (req.query.org_id) { where.push('org_id=?'); params.push(req.query.org_id); }
  for (const f of ['contract_status', 'receipt_status', 'risk_level', 'risk_status', 'risk_type', 'order_status', 'task_status', 'po_status']) {
    if (req.query[f]) { where.push(`${f}=?`); params.push(req.query[f]); }
  }
  const whereSql = where.length ? 'WHERE ' + where.join(' AND ') : '';
  const [[{ total }]] = await pool.query(`SELECT COUNT(*) AS total FROM ${table} ${whereSql}`, params);
  const [rows] = await pool.query(`SELECT * FROM ${table} ${whereSql} LIMIT ? OFFSET ?`, [...params, size, offset]);
  ok(res, { list: rows, total, page, size });
}));

module.exports = router;
