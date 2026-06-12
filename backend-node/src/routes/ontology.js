/**
 * 本体中心路由: 业务域 / 对象 / 属性 / 关系 / 接口 / 动作 / 函数 / 数据映射
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, pj, audit } = require('../utils');
const crudRouter = require('./crudFactory');
const { analyzeImpact } = require('../services/impactService');

const router = express.Router();

// ---------- 业务域 ----------
const domainRouter = crudRouter({
  table: 'kp_domain', type: 'domain', module: 'ontology',
  searchFields: ['code', 'name'], filters: ['status'],
  hooks: {
    afterList: async (rows) => {
      // 附加对象数量和指标数量
      const [objCounts] = await pool.query(
        'SELECT domain_code, COUNT(*) AS c FROM kp_object_type GROUP BY domain_code');
      const ocMap = Object.fromEntries(objCounts.map(o => [o.domain_code, o.c]));
      const [metrics] = await pool.query('SELECT bind_objects FROM kp_metric_semantic');
      const [objs] = await pool.query('SELECT code, domain_code FROM kp_object_type');
      const objDomain = Object.fromEntries(objs.map(o => [o.code, o.domain_code]));
      const mcMap = {};
      for (const m of metrics) {
        const domains = new Set(pj(m.bind_objects, []).map(b => objDomain[b]).filter(Boolean));
        domains.forEach(d => { mcMap[d] = (mcMap[d] || 0) + 1; });
      }
      return rows.map(r => ({ ...r, object_count: ocMap[r.code] || 0, metric_count: mcMap[r.code] || 0 }));
    },
  },
});
router.use('/domains', domainRouter);

// ---------- 对象类型 ----------
const objectRouter = crudRouter({
  table: 'kp_object_type', type: 'object', module: 'ontology',
  searchFields: ['code', 'name'], filters: ['domain_code', 'status', 'in_graph', 'searchable', 'security_level'],
  hooks: {
    afterList: async (rows) => {
      const [props] = await pool.query('SELECT object_code, COUNT(*) AS c FROM kp_property GROUP BY object_code');
      const pMap = Object.fromEntries(props.map(p => [p.object_code, p.c]));
      const [links] = await pool.query(
        `SELECT source_object AS oc, COUNT(*) AS c FROM kp_link_type GROUP BY source_object
         UNION ALL SELECT target_object, COUNT(*) FROM kp_link_type GROUP BY target_object`);
      const lMap = {};
      links.forEach(l => { lMap[l.oc] = (lMap[l.oc] || 0) + l.c; });
      return rows.map(r => ({ ...r, property_count: pMap[r.code] || 0, link_count: lMap[r.code] || 0 }));
    },
  },
});

// 对象详情聚合: 属性/关系/接口/映射/指标绑定/版本
objectRouter.get('/:id(\\d+)/full', wrap(async (req, res) => {
  const [[obj]] = await pool.query('SELECT * FROM kp_object_type WHERE id=?', [req.params.id]);
  if (!obj) return fail(res, '对象不存在', 1, 404);
  const [properties] = await pool.query('SELECT * FROM kp_property WHERE object_code=? ORDER BY is_primary DESC, id', [obj.code]);
  const [links] = await pool.query(
    `SELECT l.*, so.name AS source_name, to2.name AS target_name FROM kp_link_type l
     LEFT JOIN kp_object_type so ON l.source_object=so.code
     LEFT JOIN kp_object_type to2 ON l.target_object=to2.code
     WHERE l.source_object=? OR l.target_object=?`, [obj.code, obj.code]);
  const [interfaces] = await pool.query(
    `SELECT i.* FROM kp_interface i JOIN kp_object_interface oi ON i.code=oi.interface_code WHERE oi.object_code=?`, [obj.code]);
  const [actions] = await pool.query('SELECT * FROM kp_action WHERE object_code=?', [obj.code]);
  const [functions] = await pool.query('SELECT * FROM kp_function WHERE object_code=?', [obj.code]);
  const [mappings] = await pool.query('SELECT * FROM kp_mapping WHERE object_code=?', [obj.code]);
  const [allMetrics] = await pool.query('SELECT metric_code,metric_name,bind_objects,status FROM kp_metric_semantic');
  const metrics = allMetrics.filter(m => pj(m.bind_objects, []).includes(obj.code));
  const [versions] = await pool.query(
    "SELECT * FROM kp_version WHERE knowledge_type='object' AND knowledge_code=? ORDER BY id DESC", [obj.code]);
  ok(res, { ...obj, properties, links, interfaces, actions, functions, mappings, metrics, versions });
}));

router.use('/objects', objectRouter);

// ---------- 属性 ----------
const propRouter = crudRouter({
  table: 'kp_property', module: 'ontology', codeField: 'code', nameField: 'name',
  searchFields: ['code', 'name'], filters: ['object_code', 'data_type', 'is_sensitive'],
  jsonFields: ['quality_rules'],
});
// 属性删除前影响分析
propRouter.get('/:id(\\d+)/impact', wrap(async (req, res) => {
  const [[prop]] = await pool.query('SELECT * FROM kp_property WHERE id=?', [req.params.id]);
  if (!prop) return fail(res, '属性不存在', 1, 404);
  const impacts = await analyzeImpact('property', `${prop.object_code}.${prop.code}`);
  ok(res, { property: prop, impacts });
}));
// 批量导入属性(从映射表字段)
propRouter.post('/batch-import', wrap(async (req, res) => {
  const { object_code, properties } = req.body;
  if (!object_code || !Array.isArray(properties)) return fail(res, '参数错误');
  let imported = 0;
  for (const p of properties) {
    try {
      await pool.query(
        'INSERT INTO kp_property (object_code,code,name,data_type,source_field) VALUES (?,?,?,?,?)',
        [object_code, p.code, p.name || p.code, p.data_type || 'string', p.source_field || null]);
      imported++;
    } catch (e) { /* duplicates skipped */ }
  }
  await audit('ontology', 'create', { type: 'property', code: object_code, name: '批量导入属性', detail: { imported } });
  ok(res, { imported });
}));
router.use('/properties', propRouter);

// ---------- 关系 ----------
const linkRouter = crudRouter({
  table: 'kp_link_type', type: 'link', module: 'ontology',
  searchFields: ['code', 'name'], filters: ['source_object', 'target_object', 'status', 'in_graph'],
  hooks: {
    afterList: async (rows) => {
      const [objs] = await pool.query('SELECT code,name FROM kp_object_type');
      const m = Object.fromEntries(objs.map(o => [o.code, o.name]));
      return rows.map(r => ({ ...r, source_name: m[r.source_object] || r.source_object, target_name: m[r.target_object] || r.target_object }));
    },
  },
});
// 关系路径预览: 从某对象出发的可达关系链
linkRouter.get('/path-preview/:objectCode', wrap(async (req, res) => {
  const [links] = await pool.query("SELECT * FROM kp_link_type WHERE status='published'");
  const [objs] = await pool.query('SELECT code,name FROM kp_object_type');
  const nameMap = Object.fromEntries(objs.map(o => [o.code, o.name]));
  const adj = {};
  links.forEach(l => { (adj[l.source_object] = adj[l.source_object] || []).push(l); });
  const paths = [];
  const dfs = (cur, path, linkPath, depth) => {
    if (depth >= 3) return;
    for (const l of (adj[cur] || [])) {
      if (path.includes(l.target_object)) continue;
      const np = [...path, l.target_object];
      const nl = [...linkPath, l.name];
      paths.push({ nodes: np.map(c => ({ code: c, name: nameMap[c] || c })), links: nl });
      dfs(l.target_object, np, nl, depth + 1);
    }
  };
  dfs(req.params.objectCode, [req.params.objectCode], [], 0);
  ok(res, paths.slice(0, 30));
}));
router.use('/links', linkRouter);

// ---------- 接口 ----------
const ifRouter = crudRouter({
  table: 'kp_interface', module: 'ontology', searchFields: ['code', 'name'],
  jsonFields: ['required_props', 'support_funcs', 'support_actions', 'perm_required'],
  hooks: {
    afterList: async (rows) => {
      const [oi] = await pool.query(
        `SELECT oi.interface_code, o.code, o.name FROM kp_object_interface oi JOIN kp_object_type o ON oi.object_code=o.code`);
      const m = {};
      oi.forEach(x => { (m[x.interface_code] = m[x.interface_code] || []).push({ code: x.code, name: x.name }); });
      return rows.map(r => ({ ...r, implemented_by: m[r.code] || [] }));
    },
  },
});
// 对象实现/取消接口
ifRouter.post('/implement', wrap(async (req, res) => {
  const { object_code, interface_code } = req.body;
  await pool.query('INSERT IGNORE INTO kp_object_interface (object_code,interface_code) VALUES (?,?)', [object_code, interface_code]);
  await audit('ontology', 'update', { type: 'interface', code: interface_code, name: `对象${object_code}实现接口`, detail: {} });
  ok(res, null);
}));
ifRouter.post('/unimplement', wrap(async (req, res) => {
  const { object_code, interface_code } = req.body;
  await pool.query('DELETE FROM kp_object_interface WHERE object_code=? AND interface_code=?', [object_code, interface_code]);
  ok(res, null);
}));
router.use('/interfaces', ifRouter);

// ---------- 动作 / 函数 ----------
router.use('/actions', crudRouter({
  table: 'kp_action', module: 'ontology', searchFields: ['code', 'name'],
  filters: ['object_code', 'action_type'], jsonFields: ['params'],
}));
router.use('/functions', crudRouter({
  table: 'kp_function', module: 'ontology', searchFields: ['code', 'name'], filters: ['object_code'],
}));

// ---------- 数据映射 ----------
const mappingRouter = crudRouter({
  table: 'kp_mapping', module: 'ontology', codeField: 'property_code', nameField: 'property_code',
  searchFields: ['object_code', 'property_code', 'table_name', 'source_field'],
  filters: ['object_code', 'check_status'],
});
// 映射校验: 按 PRD 13.5 校验逻辑
mappingRouter.post('/validate/:objectCode', wrap(async (req, res) => {
  const objectCode = req.params.objectCode;
  const [[obj]] = await pool.query('SELECT * FROM kp_object_type WHERE code=?', [objectCode]);
  if (!obj) return fail(res, '对象不存在', 1, 404);
  const [props] = await pool.query('SELECT * FROM kp_property WHERE object_code=?', [objectCode]);
  const [maps] = await pool.query('SELECT * FROM kp_mapping WHERE object_code=?', [objectCode]);
  const mapByProp = Object.fromEntries(maps.map(m => [m.property_code, m]));
  const results = [];
  for (const p of props) {
    const m = mapByProp[p.code];
    const errors = [];
    if (p.is_primary && !m) errors.push('主键字段必须映射');
    if (p.is_required && !m) errors.push('必填属性必须映射');
    if (p.is_sensitive && (!p.perm_label || p.perm_label === 'normal')) errors.push('敏感字段必须配置权限标签');
    if (p.aggregatable && !['decimal', 'int'].includes(p.data_type)) errors.push('可聚合字段必须是数值类型');
    if (m) {
      // 校验底层表字段是否存在
      try {
        const [cols] = await pool.query(
          `SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND COLUMN_NAME=?`,
          [m.table_name, m.source_field]);
        if (!cols.length) errors.push(`底层字段 ${m.table_name}.${m.source_field} 不存在`);
        else {
          const dbType = cols[0].DATA_TYPE;
          const compat = { decimal: ['decimal', 'double', 'float', 'int', 'bigint'], int: ['int', 'bigint', 'tinyint', 'decimal'],
            string: ['varchar', 'char', 'text', 'longtext'], date: ['date', 'datetime'], datetime: ['datetime', 'timestamp', 'date'],
            boolean: ['tinyint'] };
          if (compat[p.data_type] && !compat[p.data_type].includes(dbType)) {
            errors.push(`数据类型不兼容: 本体 ${p.data_type} vs 底层 ${dbType}`);
          }
        }
      } catch (e) { errors.push('底层表校验失败: ' + e.message); }
      const status = errors.length ? 'failed' : 'passed';
      await pool.query('UPDATE kp_mapping SET check_status=?, check_message=?, checked_at=NOW() WHERE id=?',
        [status, errors.join('; ') || '校验通过', m.id]);
    }
    results.push({ property: p.code, property_name: p.name, mapped: !!m, errors, passed: !errors.length });
  }
  const passed = results.every(r => r.passed);
  await audit('ontology', 'run', { type: 'mapping', code: objectCode, name: '映射校验', detail: { passed } });
  ok(res, { object_code: objectCode, passed, results });
}));
router.use('/mappings', mappingRouter);

// ---------- 影响分析(通用) ----------
router.get('/impact/:type/:code', wrap(async (req, res) => {
  const impacts = await analyzeImpact(req.params.type, req.params.code);
  ok(res, impacts);
}));

module.exports = router;
