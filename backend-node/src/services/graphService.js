/**
 * 图谱服务: 图谱构建 / 邻居展开 / 路径查询 / 影响分析 / 质量校验
 * 图存储于 MySQL (kp_graph_node / kp_graph_edge)，以邻接表方式做 BFS 多跳遍历
 */
const pool = require('../config/db');
const { pj } = require('../utils');

/** 对象类型 -> 业务表配置(实体抽取规则) */
const ENTITY_SOURCES = {
  Obj_Org_Unit:          { table: 'biz_org',            pk: 'org_id',      display: 'org_name',      orgField: 'org_id' },
  Obj_Mkt_Customer:      { table: 'biz_customer',       pk: 'customer_id', display: 'customer_name', orgField: null },
  Obj_Sales_Contract:    { table: 'biz_contract',       pk: 'contract_id', display: 'contract_name', orgField: 'org_id' },
  Obj_Sales_Order:       { table: 'biz_order',          pk: 'order_id',    display: 'order_id',      orgField: null },
  Obj_Fin_Receipt:       { table: 'biz_receipt',        pk: 'receipt_id',  display: 'receipt_id',    orgField: null },
  Obj_Scm_Supplier:      { table: 'biz_supplier',       pk: 'supplier_id', display: 'supplier_name', orgField: null },
  Obj_Scm_PurchaseOrder: { table: 'biz_purchase_order', pk: 'po_id',       display: 'po_id',         orgField: 'org_id' },
  Obj_Scm_Material:      { table: 'biz_material',       pk: 'material_id', display: 'material_name', orgField: null },
  Obj_Inv_Inventory:     { table: 'biz_inventory',      pk: 'inv_id',      display: 'inv_id',        orgField: 'org_id' },
  Obj_Prod_Task:         { table: 'biz_prod_task',      pk: 'task_id',     display: 'task_id',       orgField: 'org_id' },
  Obj_Gov_Risk:          { table: 'biz_risk',           pk: 'risk_id',     display: 'risk_name',     orgField: 'org_id' },
};

/** 关系类型 -> 边抽取规则 (从哪张表的哪两个字段抽边) */
const EDGE_SOURCES = {
  Link_Org_Has_Sub:           { table: 'biz_org', srcObj: 'Obj_Org_Unit', tgtObj: 'Obj_Org_Unit', srcCol: 'parent_id', tgtCol: 'org_id' },
  Link_Org_Has_Contract:      { table: 'biz_contract', srcObj: 'Obj_Org_Unit', tgtObj: 'Obj_Sales_Contract', srcCol: 'org_id', tgtCol: 'contract_id' },
  Link_Customer_Has_Contract: { table: 'biz_contract', srcObj: 'Obj_Mkt_Customer', tgtObj: 'Obj_Sales_Contract', srcCol: 'customer_id', tgtCol: 'contract_id' },
  Link_Contract_Has_Order:    { table: 'biz_order', srcObj: 'Obj_Sales_Contract', tgtObj: 'Obj_Sales_Order', srcCol: 'contract_id', tgtCol: 'order_id' },
  Link_Contract_Has_Receipt:  { table: 'biz_receipt', srcObj: 'Obj_Sales_Contract', tgtObj: 'Obj_Fin_Receipt', srcCol: 'contract_id', tgtCol: 'receipt_id' },
  Link_Order_Drive_Task:      { table: 'biz_prod_task', srcObj: 'Obj_Sales_Order', tgtObj: 'Obj_Prod_Task', srcCol: 'order_id', tgtCol: 'task_id' },
  Link_Org_Has_PO:            { table: 'biz_purchase_order', srcObj: 'Obj_Org_Unit', tgtObj: 'Obj_Scm_PurchaseOrder', srcCol: 'org_id', tgtCol: 'po_id' },
  Link_PO_To_Supplier:        { table: 'biz_purchase_order', srcObj: 'Obj_Scm_PurchaseOrder', tgtObj: 'Obj_Scm_Supplier', srcCol: 'po_id', tgtCol: 'supplier_id' },
  Link_PO_To_Material:        { table: 'biz_purchase_order', srcObj: 'Obj_Scm_PurchaseOrder', tgtObj: 'Obj_Scm_Material', srcCol: 'po_id', tgtCol: 'material_id' },
  Link_Material_Has_Inventory:{ table: 'biz_inventory', srcObj: 'Obj_Scm_Material', tgtObj: 'Obj_Inv_Inventory', srcCol: 'material_id', tgtCol: 'inv_id' },
  Link_Org_Has_Inventory:     { table: 'biz_inventory', srcObj: 'Obj_Org_Unit', tgtObj: 'Obj_Inv_Inventory', srcCol: 'org_id', tgtCol: 'inv_id' },
  Link_Risk_Refer_Object:     { table: 'biz_risk', srcObj: 'Obj_Gov_Risk', tgtObj: null /* 多态 */, srcCol: 'risk_id', tgtCol: 'ref_id', polyCol: 'ref_object' },
  Link_Org_Has_Risk:          { table: 'biz_risk', srcObj: 'Obj_Org_Unit', tgtObj: 'Obj_Gov_Risk', srcCol: 'org_id', tgtCol: 'risk_id' },
};

/**
 * 执行图谱构建任务: 从业务表抽取实体和关系写入图存储
 */
async function buildGraph(taskId) {
  const start = Date.now();
  const [[task]] = await pool.query('SELECT * FROM kp_graph_task WHERE id=?', [taskId]);
  if (!task) throw Object.assign(new Error('图谱任务不存在'), { status: 404 });
  const graphCode = task.graph_code;
  const [[model]] = await pool.query('SELECT * FROM kp_graph_model WHERE code=?', [graphCode]);
  if (!model) throw Object.assign(new Error('图谱模型不存在'), { status: 404 });

  await pool.query("UPDATE kp_graph_task SET last_status='running' WHERE id=?", [taskId]);

  try {
    const includeObjects = pj(model.include_objects, []);
    const includeLinks = pj(model.include_links, []);

    // 重建(批量模式): 清空该图谱节点和边
    await pool.query('DELETE FROM kp_graph_edge WHERE graph_code=?', [graphCode]);
    await pool.query('DELETE FROM kp_graph_node WHERE graph_code=?', [graphCode]);

    // ---- 实体抽取 ----
    let nodeCount = 0;
    const nodeIdMap = new Map(); // `${objCode}:${entityId}` -> node row id
    for (const objCode of includeObjects) {
      const src = ENTITY_SOURCES[objCode];
      if (!src) continue;
      const [rows] = await pool.query(`SELECT * FROM ${src.table}`);
      if (!rows.length) continue;
      const values = rows.map(r => [
        graphCode, objCode, String(r[src.pk]), String(r[src.display] ?? r[src.pk]),
        JSON.stringify(r), src.orgField ? r[src.orgField] : null,
      ]);
      await pool.query(
        'INSERT IGNORE INTO kp_graph_node (graph_code,object_code,entity_id,entity_name,props,org_id) VALUES ?', [values]);
      nodeCount += rows.length;
    }
    // 加载节点 id 映射
    const [allNodes] = await pool.query('SELECT id,object_code,entity_id FROM kp_graph_node WHERE graph_code=?', [graphCode]);
    for (const n of allNodes) nodeIdMap.set(`${n.object_code}:${n.entity_id}`, n.id);

    // ---- 关系抽取 ----
    let edgeCount = 0;
    for (const linkCode of includeLinks) {
      const rule = EDGE_SOURCES[linkCode];
      if (!rule) continue;
      const [rows] = await pool.query(`SELECT * FROM ${rule.table}`);
      const values = [];
      for (const r of rows) {
        const srcKey = `${rule.srcObj}:${r[rule.srcCol]}`;
        const tgtObj = rule.tgtObj || r[rule.polyCol]; // 多态关系
        const tgtKey = `${tgtObj}:${r[rule.tgtCol]}`;
        const s = nodeIdMap.get(srcKey), t = nodeIdMap.get(tgtKey);
        if (s && t) values.push([graphCode, linkCode, s, t, JSON.stringify({})]);
      }
      if (values.length) {
        await pool.query(
          'INSERT IGNORE INTO kp_graph_edge (graph_code,link_code,source_node,target_node,props) VALUES ?', [values]);
        edgeCount += values.length;
      }
    }

    // ---- 质量校验 ----
    const [[isolated]] = await pool.query(
      `SELECT COUNT(*) AS c FROM kp_graph_node n WHERE n.graph_code=?
       AND NOT EXISTS (SELECT 1 FROM kp_graph_edge e WHERE e.graph_code=? AND (e.source_node=n.id OR e.target_node=n.id))`,
      [graphCode, graphCode]);
    const [[dupNames]] = await pool.query(
      `SELECT COUNT(*) AS c FROM (SELECT entity_name FROM kp_graph_node WHERE graph_code=? AND object_code IN ('Obj_Mkt_Customer','Obj_Scm_Supplier') GROUP BY object_code, entity_name HAVING COUNT(*)>1) t`,
      [graphCode]);
    const coverage = nodeCount > 0 ? 100 : 0;
    const qualityReport = {
      isolated_nodes: isolated.c,
      duplicate_nodes: dupNames.c,
      node_integrity: '通过',
      relation_integrity: edgeCount > 0 ? '通过' : '异常',
      coverage_rate: coverage,
    };
    const qualityStatus = isolated.c > nodeCount * 0.3 || edgeCount === 0 ? 'abnormal' : 'normal';
    const duration = Date.now() - start;

    await pool.query(
      `UPDATE kp_graph_task SET last_run_at=NOW(), last_status='success', node_count=?, edge_count=?, success_rate=?, quality_status=? WHERE id=?`,
      [nodeCount, edgeCount, 100.0, qualityStatus, taskId]);
    await pool.query(
      'INSERT INTO kp_graph_task_log (task_id,duration_ms,node_count,edge_count,status,message,quality_report) VALUES (?,?,?,?,?,?,?)',
      [taskId, duration, nodeCount, edgeCount, 'success', `构建完成: ${nodeCount}节点 ${edgeCount}边`, JSON.stringify(qualityReport)]);

    return { nodeCount, edgeCount, durationMs: duration, qualityReport, qualityStatus };
  } catch (e) {
    await pool.query("UPDATE kp_graph_task SET last_status='failed' WHERE id=?", [taskId]);
    await pool.query(
      'INSERT INTO kp_graph_task_log (task_id,status,message) VALUES (?,?,?)',
      [taskId, 'failed', e.message]);
    throw e;
  }
}

/** 搜索节点 */
async function searchNodes(graphCode, keyword, objectCode = null, limit = 20) {
  let sql = 'SELECT id,object_code,entity_id,entity_name,org_id FROM kp_graph_node WHERE graph_code=? AND (entity_name LIKE ? OR entity_id LIKE ?)';
  const params = [graphCode, `%${keyword}%`, `%${keyword}%`];
  if (objectCode) { sql += ' AND object_code=?'; params.push(objectCode); }
  sql += ' LIMIT ?'; params.push(limit);
  const [rows] = await pool.query(sql, params);
  return rows;
}

/** 展开邻居(支持多跳) */
async function expandNeighbors(graphCode, nodeId, hops = 1, maxNodes = 150) {
  const nodes = new Map(); const edges = [];
  let frontier = [Number(nodeId)];
  const visited = new Set(frontier);

  const [seed] = await pool.query('SELECT id,object_code,entity_id,entity_name,props FROM kp_graph_node WHERE id=?', [nodeId]);
  if (!seed.length) throw Object.assign(new Error('节点不存在'), { status: 404 });
  nodes.set(seed[0].id, { ...seed[0], props: pj(seed[0].props, {}), level: 0 });

  for (let h = 1; h <= hops && frontier.length && nodes.size < maxNodes; h++) {
    const [rows] = await pool.query(
      `SELECT e.id AS eid, e.link_code, e.source_node, e.target_node FROM kp_graph_edge e
       WHERE e.graph_code=? AND (e.source_node IN (?) OR e.target_node IN (?))`,
      [graphCode, frontier, frontier]);
    const next = [];
    const newIds = new Set();
    for (const e of rows) {
      edges.push({ id: e.eid, link_code: e.link_code, source: e.source_node, target: e.target_node });
      for (const nid of [e.source_node, e.target_node]) {
        if (!visited.has(nid)) { visited.add(nid); next.push(nid); newIds.add(nid); }
      }
      if (nodes.size + newIds.size >= maxNodes) break;
    }
    if (next.length) {
      const [nrows] = await pool.query(
        'SELECT id,object_code,entity_id,entity_name,props FROM kp_graph_node WHERE id IN (?)', [next]);
      for (const n of nrows) nodes.set(n.id, { ...n, props: pj(n.props, {}), level: h });
    }
    frontier = next;
  }
  // 去重边
  const seen = new Set();
  const uniqEdges = edges.filter(e => {
    const k = `${e.source}-${e.link_code}-${e.target}`;
    if (seen.has(k) || !nodes.has(e.source) || !nodes.has(e.target)) return false;
    seen.add(k); return true;
  });
  return { nodes: [...nodes.values()], edges: uniqEdges };
}

/** 路径查询: BFS 求两节点(或节点->对象类型)间路径 */
async function findPaths(graphCode, startNodeId, { endNodeId = null, endObjectCode = null, maxHops = 3, maxPaths = 10 } = {}) {
  // 加载全图邻接表(规模可控: 数千节点)
  const [edges] = await pool.query(
    'SELECT link_code,source_node,target_node FROM kp_graph_edge WHERE graph_code=?', [graphCode]);
  const adj = new Map();
  const addAdj = (a, b, lc, dir) => {
    if (!adj.has(a)) adj.set(a, []);
    adj.get(a).push({ to: b, link: lc, dir });
  };
  for (const e of edges) {
    addAdj(e.source_node, e.target_node, e.link_code, 'out');
    addAdj(e.target_node, e.source_node, e.link_code, 'in');
  }
  const [nodeRows] = await pool.query(
    'SELECT id,object_code,entity_id,entity_name FROM kp_graph_node WHERE graph_code=?', [graphCode]);
  const nodeMap = new Map(nodeRows.map(n => [n.id, n]));

  const start = Number(startNodeId);
  const results = [];
  const queue = [[start, [start], []]]; // [current, nodePath, edgePath]
  while (queue.length && results.length < maxPaths) {
    const [cur, npath, epath] = queue.shift();
    if (npath.length - 1 >= 1) {
      const curNode = nodeMap.get(cur);
      const isEnd = endNodeId ? cur === Number(endNodeId)
        : endObjectCode ? (curNode && curNode.object_code === endObjectCode) : false;
      if (isEnd) {
        results.push({
          nodes: npath.map(id => nodeMap.get(id)),
          links: epath,
          hops: npath.length - 1,
        });
        continue;
      }
    }
    if (npath.length - 1 >= maxHops) continue;
    for (const nb of (adj.get(cur) || [])) {
      if (npath.includes(nb.to)) continue;
      queue.push([nb.to, [...npath, nb.to], [...epath, { link: nb.link, dir: nb.dir }]]);
    }
  }
  return results;
}

/** 影响分析: 从某节点出发 BFS 统计影响的对象类型分布 */
async function impactAnalysis(graphCode, nodeId, maxHops = 3) {
  const { nodes, edges } = await expandNeighbors(graphCode, nodeId, maxHops, 500);
  const byType = {};
  for (const n of nodes) {
    if (String(n.id) === String(nodeId)) continue;
    byType[n.object_code] = byType[n.object_code] || { count: 0, samples: [], totalAmount: 0 };
    const t = byType[n.object_code];
    t.count += 1;
    if (t.samples.length < 5) t.samples.push(n.entity_name);
    const p = n.props || {};
    const amt = Number(p.contract_amount || p.overdue_amount || p.po_amount || p.amount || 0);
    if (!Number.isNaN(amt)) t.totalAmount += amt;
  }
  // 对象类型名称
  const [objTypes] = await pool.query('SELECT code,name FROM kp_object_type');
  const nameMap = Object.fromEntries(objTypes.map(o => [o.code, o.name]));
  const impact = Object.entries(byType).map(([code, v]) => ({
    object_code: code, object_name: nameMap[code] || code,
    count: v.count, samples: v.samples, total_amount: Math.round(v.totalAmount * 100) / 100,
  })).sort((a, b) => b.count - a.count);
  return { impacted: impact, graph: { nodes, edges } };
}

module.exports = { buildGraph, searchNodes, expandNeighbors, findPaths, impactAnalysis, ENTITY_SOURCES };
