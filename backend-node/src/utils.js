/**
 * 通用工具: 响应封装 / 分页 / JSON 解析 / 审计
 */
const pool = require('./config/db');

const ok = (res, data, extra = {}) => res.json({ code: 0, message: 'success', data, ...extra });
const fail = (res, message, code = 1, status = 400) => res.status(status).json({ code, message, data: null });

/** 包装 async 路由，统一异常处理 */
const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

/** 解析分页参数 */
function pageParams(req) {
  const page = Math.max(1, parseInt(req.query.page || '1', 10));
  const size = Math.min(200, Math.max(1, parseInt(req.query.size || '20', 10)));
  return { page, size, offset: (page - 1) * size };
}

/** 安全解析 JSON 字段(mysql2 已自动解析 JSON 列，做兜底) */
function pj(v, dft = null) {
  if (v === null || v === undefined) return dft;
  if (typeof v === 'object') return v;
  try { return JSON.parse(v); } catch { return dft; }
}

/** 记录审计日志 */
async function audit(module, action, { type = null, code = null, name = null, operator = 'admin', detail = {} } = {}) {
  try {
    await pool.query(
      'INSERT INTO kp_audit_log (module,action,knowledge_type,knowledge_code,knowledge_name,operator,detail) VALUES (?,?,?,?,?,?,?)',
      [module, action, type, code, name, operator, JSON.stringify(detail)]
    );
  } catch (e) {
    console.error('audit log failed:', e.message);
  }
}

/** 记录版本快照 */
async function saveVersion(knowledgeType, knowledgeId, knowledgeCode, version, snapshot, changeNote, operator = 'admin') {
  await pool.query(
    'INSERT INTO kp_version (knowledge_type,knowledge_id,knowledge_code,version,snapshot,change_note,operator) VALUES (?,?,?,?,?,?,?)',
    [knowledgeType, knowledgeId, knowledgeCode, version, JSON.stringify(snapshot), changeNote, operator]
  );
}

/** 生成审核单号 */
async function nextReviewNo() {
  const [[row]] = await pool.query("SELECT COUNT(*) AS c FROM kp_review");
  return `REVIEW-${String(row.c + 1).padStart(4, '0')}`;
}

/** 版本号自增: v1.0 -> v1.1 */
function bumpVersion(v) {
  const m = /^v(\d+)\.(\d+)$/.exec(v || 'v1.0');
  if (!m) return 'v1.1';
  return `v${m[1]}.${Number(m[2]) + 1}`;
}

module.exports = { ok, fail, wrap, pageParams, pj, audit, saveVersion, nextReviewNo, bumpVersion };
