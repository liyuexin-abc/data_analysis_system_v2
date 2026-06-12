/**
 * 通用 CRUD 路由工厂
 * 为各知识对象提供 列表/详情/新建/更新/删除 + 生命周期转换 的标准接口
 */
const express = require('express');
const pool = require('../config/db');
const { ok, fail, wrap, pageParams, audit } = require('../utils');
const { transition } = require('../services/lifecycle');

/**
 * @param {object} cfg
 *  table: 表名
 *  type: 生命周期知识类型(可空则无生命周期)
 *  codeField/nameField: 编码与名称字段
 *  searchFields: 关键词搜索字段
 *  filters: 允许的精确过滤字段
 *  jsonFields: JSON 字段(写入时序列化)
 *  module: 审计模块名
 *  hooks: { afterList(rows), beforeCreate(body), beforeUpdate(body) }
 */
function crudRouter(cfg) {
  const r = express.Router();
  const {
    table, type = null, codeField = 'code', nameField = 'name',
    searchFields = [], filters = [], jsonFields = [], module: mod = table, hooks = {},
  } = cfg;

  // 列表
  r.get('/', wrap(async (req, res) => {
    const { page, size, offset } = pageParams(req);
    const where = []; const params = [];
    if (req.query.keyword && searchFields.length) {
      where.push('(' + searchFields.map(f => `${f} LIKE ?`).join(' OR ') + ')');
      searchFields.forEach(() => params.push(`%${req.query.keyword}%`));
    }
    for (const f of filters) {
      if (req.query[f] !== undefined && req.query[f] !== '') {
        where.push(`${f}=?`); params.push(req.query[f]);
      }
    }
    const whereSql = where.length ? 'WHERE ' + where.join(' AND ') : '';
    const [[{ total }]] = await pool.query(`SELECT COUNT(*) AS total FROM ${table} ${whereSql}`, params);
    const [rows] = await pool.query(
      `SELECT * FROM ${table} ${whereSql} ORDER BY id DESC LIMIT ? OFFSET ?`, [...params, size, offset]);
    const list = hooks.afterList ? await hooks.afterList(rows) : rows;
    ok(res, { list, total, page, size });
  }));

  // 详情
  r.get('/:id(\\d+)', wrap(async (req, res) => {
    const [[row]] = await pool.query(`SELECT * FROM ${table} WHERE id=?`, [req.params.id]);
    if (!row) return fail(res, '记录不存在', 1, 404);
    const data = hooks.afterDetail ? await hooks.afterDetail(row) : row;
    ok(res, data);
  }));

  const serialize = (body) => {
    const data = { ...body };
    delete data.id; delete data.created_at; delete data.updated_at;
    for (const f of jsonFields) {
      if (data[f] !== undefined && data[f] !== null && typeof data[f] === 'object') {
        data[f] = JSON.stringify(data[f]);
      }
    }
    return data;
  };

  // 新建
  r.post('/', wrap(async (req, res) => {
    let body = req.body;
    if (hooks.beforeCreate) body = await hooks.beforeCreate(body);
    const data = serialize(body);
    if (type && !data.status) data.status = 'draft';
    const fields = Object.keys(data);
    if (!fields.length) return fail(res, '请求体为空');
    const [result] = await pool.query(
      `INSERT INTO ${table} (${fields.join(',')}) VALUES (${fields.map(() => '?').join(',')})`,
      fields.map(f => data[f]));
    await audit(mod, 'create', { type, code: String(data[codeField] ?? result.insertId), name: data[nameField], detail: {} });
    const [[row]] = await pool.query(`SELECT * FROM ${table} WHERE id=?`, [result.insertId]);
    ok(res, row);
  }));

  // 更新
  r.put('/:id(\\d+)', wrap(async (req, res) => {
    const [[exist]] = await pool.query(`SELECT * FROM ${table} WHERE id=?`, [req.params.id]);
    if (!exist) return fail(res, '记录不存在', 1, 404);
    let body = req.body;
    if (hooks.beforeUpdate) body = await hooks.beforeUpdate(body, exist);
    const data = serialize(body);
    delete data.status; delete data.version; // 状态和版本只能走生命周期接口
    const fields = Object.keys(data);
    if (!fields.length) return fail(res, '无可更新字段');
    await pool.query(
      `UPDATE ${table} SET ${fields.map(f => `${f}=?`).join(',')} WHERE id=?`,
      [...fields.map(f => data[f]), req.params.id]);
    // 已发布对象修改后自动进入"变更中"
    if (type && exist.status === 'published') {
      await pool.query(`UPDATE ${table} SET status='changing' WHERE id=?`, [req.params.id]);
    }
    await audit(mod, 'update', { type, code: String(exist[codeField]), name: exist[nameField], detail: { fields } });
    const [[row]] = await pool.query(`SELECT * FROM ${table} WHERE id=?`, [req.params.id]);
    ok(res, row);
  }));

  // 删除
  r.delete('/:id(\\d+)', wrap(async (req, res) => {
    const [[exist]] = await pool.query(`SELECT * FROM ${table} WHERE id=?`, [req.params.id]);
    if (!exist) return fail(res, '记录不存在', 1, 404);
    if (type && exist.status === 'published') {
      return fail(res, '已发布的知识不允许直接删除，请先停用');
    }
    await pool.query(`DELETE FROM ${table} WHERE id=?`, [req.params.id]);
    await audit(mod, 'delete', { type, code: String(exist[codeField]), name: exist[nameField], detail: {} });
    ok(res, null);
  }));

  // 生命周期转换
  if (type) {
    r.post('/:id(\\d+)/lifecycle/:action', wrap(async (req, res) => {
      const result = await transition(type, req.params.id, req.params.action, {
        operator: req.body.operator || 'admin', comment: req.body.comment || '',
      });
      ok(res, result);
    }));
  }

  return r;
}

module.exports = crudRouter;
