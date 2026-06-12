/**
 * 知识对象统一生命周期服务
 * 状态机: draft -> pending_check -> (check_failed | pending_review) -> published -> changing/disabled/deprecated
 * 所有知识类型(对象/关系/指标/术语/规则/方法论/图谱/文档/业务域)共用
 */
const pool = require('../config/db');
const { audit, saveVersion, nextReviewNo, bumpVersion } = require('../utils');

/** 知识类型注册表: 类型 -> {table, codeField, nameField} */
const REGISTRY = {
  domain:   { table: 'kp_domain',          codeField: 'code',        nameField: 'name' },
  object:   { table: 'kp_object_type',     codeField: 'code',        nameField: 'name' },
  link:     { table: 'kp_link_type',       codeField: 'code',        nameField: 'name' },
  term:     { table: 'kp_term',            codeField: 'term',        nameField: 'term' },
  metric:   { table: 'kp_metric_semantic', codeField: 'metric_code', nameField: 'metric_name' },
  rule:     { table: 'kp_rule',            codeField: 'code',        nameField: 'name' },
  method:   { table: 'kp_method',          codeField: 'code',        nameField: 'name' },
  graph:    { table: 'kp_graph_model',     codeField: 'code',        nameField: 'name' },
  document: { table: 'kp_document',        codeField: 'id',          nameField: 'name' },
};

const TRANSITIONS = {
  submit_check:  { from: ['draft', 'check_failed', 'changing'], to: 'pending_check' },
  check_pass:    { from: ['pending_check'], to: 'pending_review' },
  check_fail:    { from: ['pending_check'], to: 'check_failed' },
  approve:       { from: ['pending_review'], to: 'published' },
  reject:        { from: ['pending_review'], to: 'draft' },
  start_change:  { from: ['published'], to: 'changing' },
  disable:       { from: ['published', 'changing'], to: 'disabled' },
  enable:        { from: ['disabled'], to: 'published' },
  deprecate:     { from: ['disabled'], to: 'deprecated' },
};

const STATUS_NAMES = {
  draft: '草稿', pending_check: '待校验', check_failed: '校验不通过',
  pending_review: '待审核', published: '已发布', changing: '变更中',
  disabled: '已停用', deprecated: '已废弃',
};

/** 系统校验规则: 各知识类型提交校验时执行 */
async function runChecks(type, row) {
  const errors = [];
  if (type === 'object') {
    if (!row.primary_key) errors.push('对象缺少主键字段');
    if (!row.display_field) errors.push('对象缺少展示字段');
    const [props] = await pool.query('SELECT COUNT(*) AS c FROM kp_property WHERE object_code=?', [row.code]);
    if (props[0].c === 0) errors.push('对象未配置任何属性');
    const [pk] = await pool.query('SELECT COUNT(*) AS c FROM kp_property WHERE object_code=? AND is_primary=1', [row.code]);
    if (pk[0].c === 0) errors.push('对象属性中未标记主键属性');
    const [[d]] = await pool.query('SELECT COUNT(*) AS c FROM kp_domain WHERE code=?', [row.domain_code]);
    if (d.c === 0) errors.push(`所属业务域 ${row.domain_code} 不存在`);
    // 敏感属性必须有权限标签
    const [sens] = await pool.query(
      "SELECT code FROM kp_property WHERE object_code=? AND is_sensitive=1 AND (perm_label IS NULL OR perm_label='normal')", [row.code]);
    if (sens.length) errors.push(`敏感属性未配置权限标签: ${sens.map(s => s.code).join(', ')}`);
  }
  if (type === 'link') {
    for (const f of ['source_object', 'target_object']) {
      const [[o]] = await pool.query('SELECT COUNT(*) AS c FROM kp_object_type WHERE code=?', [row[f]]);
      if (o.c === 0) errors.push(`${f === 'source_object' ? '源' : '目标'}对象 ${row[f]} 不存在`);
    }
    if (!row.source_field || !row.target_field) errors.push('关系缺少关联字段');
  }
  if (type === 'metric') {
    if (!row.business_def) errors.push('指标缺少业务定义');
    if (!row.formula_desc) errors.push('指标缺少公式说明');
    const binds = typeof row.bind_objects === 'string' ? JSON.parse(row.bind_objects || '[]') : (row.bind_objects || []);
    if (!binds.length) errors.push('指标未绑定本体对象');
    for (const b of binds) {
      const [[o]] = await pool.query('SELECT COUNT(*) AS c FROM kp_object_type WHERE code=?', [b]);
      if (o.c === 0) errors.push(`绑定对象 ${b} 不存在`);
    }
  }
  if (type === 'term') {
    if (!row.map_target) errors.push('术语缺少标准映射');
  }
  if (type === 'rule') {
    const [[o]] = await pool.query('SELECT COUNT(*) AS c FROM kp_object_type WHERE code=?', [row.monitor_object]);
    if (o.c === 0) errors.push(`监控对象 ${row.monitor_object} 不存在`);
    const cond = typeof row.trigger_cond === 'string' ? JSON.parse(row.trigger_cond || '{}') : (row.trigger_cond || {});
    if (!cond.conditions || !cond.conditions.length) errors.push('规则缺少触发条件');
  }
  if (type === 'method') {
    const steps = typeof row.steps === 'string' ? JSON.parse(row.steps || '[]') : (row.steps || []);
    if (!steps.length) errors.push('方法论缺少分析步骤');
  }
  if (type === 'graph') {
    const objs = typeof row.include_objects === 'string' ? JSON.parse(row.include_objects || '[]') : (row.include_objects || []);
    if (!objs.length) errors.push('图谱模型未选择入图对象');
  }
  if (type === 'document') {
    if (!row.content) errors.push('文档内容为空');
    if (!row.security_level) errors.push('文档未配置密级');
  }
  return errors;
}

/**
 * 执行生命周期转换
 * @returns {object} { status, checkErrors? }
 */
async function transition(type, id, action, { operator = 'admin', comment = '' } = {}) {
  const reg = REGISTRY[type];
  if (!reg) throw Object.assign(new Error(`未知知识类型: ${type}`), { status: 400 });
  const tr = TRANSITIONS[action];
  if (!tr) throw Object.assign(new Error(`未知生命周期动作: ${action}`), { status: 400 });

  const [[row]] = await pool.query(`SELECT * FROM ${reg.table} WHERE id=?`, [id]);
  if (!row) throw Object.assign(new Error('知识对象不存在'), { status: 404 });
  if (!tr.from.includes(row.status)) {
    throw Object.assign(
      new Error(`当前状态[${STATUS_NAMES[row.status] || row.status}]不允许执行[${action}]`), { status: 400 });
  }

  let newStatus = tr.to;
  let checkErrors = [];

  // 提交校验时自动执行系统校验
  if (action === 'submit_check') {
    checkErrors = await runChecks(type, row);
    newStatus = checkErrors.length ? 'check_failed' : 'pending_review';
    // 校验通过自动创建审核单
    if (!checkErrors.length) {
      const reviewNo = await nextReviewNo();
      await pool.query(
        'INSERT INTO kp_review (review_no,knowledge_type,knowledge_id,knowledge_code,knowledge_name,applicant,change_type,change_detail,impact_scope,review_status) VALUES (?,?,?,?,?,?,?,?,?,?)',
        [reviewNo, type, id, String(row[reg.codeField] ?? id), row[reg.nameField], operator,
         row.status === 'changing' ? 'update' : 'create',
         JSON.stringify({ comment }), JSON.stringify([]), 'pending']);
    }
  }

  // 审核通过 -> 发布 + 版本快照
  if (action === 'approve') {
    const newVer = row.status === 'changing' ? bumpVersion(row.version) : (row.version || 'v1.0');
    await pool.query(`UPDATE ${reg.table} SET version=? WHERE id=?`, [newVer, id]);
    await saveVersion(type, id, String(row[reg.codeField] ?? id), newVer, row, comment || '审核通过发布', operator);
    await pool.query(
      "UPDATE kp_review SET review_status='approved', reviewer=?, review_comment=?, reviewed_at=NOW() WHERE knowledge_type=? AND knowledge_id=? AND review_status='pending'",
      [operator, comment, type, id]);
  }
  if (action === 'reject') {
    await pool.query(
      "UPDATE kp_review SET review_status='rejected', reviewer=?, review_comment=?, reviewed_at=NOW() WHERE knowledge_type=? AND knowledge_id=? AND review_status='pending'",
      [operator, comment, type, id]);
  }

  await pool.query(`UPDATE ${reg.table} SET status=? WHERE id=?`, [newStatus, id]);
  await audit(type, action, {
    type, code: String(row[reg.codeField] ?? id), name: row[reg.nameField], operator,
    detail: { from: row.status, to: newStatus, comment, checkErrors },
  });
  return { status: newStatus, statusName: STATUS_NAMES[newStatus], checkErrors };
}

module.exports = { transition, runChecks, REGISTRY, STATUS_NAMES };
