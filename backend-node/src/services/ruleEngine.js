/**
 * 规则引擎: 规则试运行/正式运行，扫描监控对象生成预警明细
 * 支持 PRD 中定义的规则类型: threshold / yoy / mom / composite
 */
const pool = require('../config/db');
const { pj } = require('../utils');

const LEVEL_NAMES = { red: '红色', orange: '橙色', yellow: '黄色', blue: '蓝色' };

/** 回款逾期规则: 扫描 biz_receipt */
async function runReceiptOverdue(rule) {
  const [rows] = await pool.query(
    `SELECT r.receipt_id, r.contract_id, r.overdue_days, r.overdue_amount, c.org_id, o.org_name, c.contract_name, cu.customer_name
     FROM biz_receipt r
     JOIN biz_contract c ON r.contract_id=c.contract_id
     JOIN biz_org o ON c.org_id=o.org_id
     JOIN biz_customer cu ON c.customer_id=cu.customer_id
     WHERE r.receipt_status='overdue' AND r.overdue_days > 30
     ORDER BY r.overdue_amount DESC`);
  return rows.map(r => {
    const od = r.overdue_days, amt = Number(r.overdue_amount);
    const level = (od > 180 || amt > 1000) ? 'red' : (od > 90 || amt > 500) ? 'orange'
      : (od > 30 || amt > 100) ? 'yellow' : 'blue';
    return {
      target_id: r.receipt_id, target_name: `${r.contract_name}`,
      org: r.org_name, customer: r.customer_name,
      level, level_name: LEVEL_NAMES[level],
      detail: `逾期${od}天，逾期金额${amt.toFixed(2)}万元`,
      value: amt,
    };
  });
}

/** 利润下降规则: 基于指标事实同比/环比 */
async function runProfitDecline(rule) {
  const [[latest]] = await pool.query(
    "SELECT MAX(period) AS p FROM biz_metric_fact WHERE metric_code='profit_total' AND period_type='month'");
  const period = latest.p;
  const [y, m] = period.split('-').map(Number);
  const momP = m === 1 ? `${y - 1}-12` : `${y}-${String(m - 1).padStart(2, '0')}`;
  const yoyP = `${y - 1}-${String(m).padStart(2, '0')}`;
  const [rows] = await pool.query(
    `SELECT f.org_id, o.org_name, f.value AS cur,
       (SELECT value FROM biz_metric_fact WHERE metric_code='profit_total' AND org_id=f.org_id AND period=?) AS mom,
       (SELECT value FROM biz_metric_fact WHERE metric_code='profit_total' AND org_id=f.org_id AND period=?) AS yoy
     FROM biz_metric_fact f JOIN biz_org o ON f.org_id=o.org_id
     WHERE f.metric_code='profit_total' AND f.period=? AND o.org_level=3`,
    [momP, yoyP, period]);
  const alerts = [];
  for (const r of rows) {
    const yoyChg = r.yoy ? ((r.cur - r.yoy) / Math.abs(r.yoy)) * 100 : null;
    const momChg = r.mom ? ((r.cur - r.mom) / Math.abs(r.mom)) * 100 : null;
    if ((yoyChg !== null && yoyChg < -20) || (momChg !== null && momChg < -15)) {
      const level = yoyChg !== null && yoyChg < -30 ? 'red' : yoyChg !== null && yoyChg < -20 ? 'orange' : 'yellow';
      alerts.push({
        target_id: r.org_id, target_name: r.org_name, org: r.org_name,
        level, level_name: LEVEL_NAMES[level],
        detail: `${period}利润${Number(r.cur).toFixed(0)}万元，同比${yoyChg === null ? 'N/A' : yoyChg.toFixed(1) + '%'}，环比${momChg === null ? 'N/A' : momChg.toFixed(1) + '%'}`,
        value: Number(r.cur),
      });
    }
  }
  return alerts;
}

/** 合同延期规则 */
async function runContractDelay(rule) {
  const [rows] = await pool.query(
    `SELECT c.contract_id, c.contract_name, c.contract_amount, o.org_name, cu.customer_name
     FROM biz_contract c JOIN biz_org o ON c.org_id=o.org_id JOIN biz_customer cu ON c.customer_id=cu.customer_id
     WHERE c.contract_status='delayed' AND c.contract_amount > 100
     ORDER BY c.contract_amount DESC`);
  return rows.map(r => {
    const amt = Number(r.contract_amount);
    const level = amt > 2000 ? 'red' : amt > 800 ? 'orange' : 'yellow';
    return {
      target_id: r.contract_id, target_name: r.contract_name, org: r.org_name, customer: r.customer_name,
      level, level_name: LEVEL_NAMES[level],
      detail: `合同延期，金额${amt.toFixed(2)}万元`, value: amt,
    };
  });
}

/** 库存积压规则 */
async function runInventoryAge(rule) {
  const [rows] = await pool.query(
    `SELECT i.inv_id, m.material_name, i.amount, i.age_days, o.org_name
     FROM biz_inventory i JOIN biz_material m ON i.material_id=m.material_id JOIN biz_org o ON i.org_id=o.org_id
     WHERE i.age_days > 300 ORDER BY i.amount DESC`);
  return rows.map(r => ({
    target_id: r.inv_id, target_name: `${r.material_name}库存`, org: r.org_name,
    level: r.age_days > 500 ? 'orange' : 'yellow',
    level_name: r.age_days > 500 ? '橙色' : '黄色',
    detail: `库龄${r.age_days}天，金额${Number(r.amount).toFixed(2)}万元`, value: Number(r.amount),
  }));
}

/** 采购价格异常规则 */
async function runPOPriceAbnormal(rule) {
  const [rows] = await pool.query(
    `SELECT p.po_id, s.supplier_name, m.material_name, m.std_price, p.unit_price, p.po_amount, o.org_name,
       ROUND((p.unit_price - m.std_price) / m.std_price * 100, 1) AS pct
     FROM biz_purchase_order p
     JOIN biz_supplier s ON p.supplier_id=s.supplier_id
     JOIN biz_material m ON p.material_id=m.material_id
     JOIN biz_org o ON p.org_id=o.org_id
     WHERE (p.unit_price - m.std_price) / m.std_price > 0.10
     ORDER BY pct DESC`);
  return rows.map(r => ({
    target_id: r.po_id, target_name: `${r.supplier_name}-${r.material_name}`, org: r.org_name,
    level: r.pct > 20 ? 'orange' : 'yellow',
    level_name: r.pct > 20 ? '橙色' : '黄色',
    detail: `采购价${r.unit_price}元高于标准价${r.std_price}元 ${r.pct}%`, value: Number(r.po_amount),
  }));
}

const EXECUTORS = {
  Rule_Receipt_Overdue: runReceiptOverdue,
  Rule_Profit_Decline: runProfitDecline,
  Rule_Contract_Delay: runContractDelay,
  Rule_Inventory_Age: runInventoryAge,
  Rule_PO_Price_Abnormal: runPOPriceAbnormal,
};

/**
 * 运行规则 (试运行 dry-run 或正式运行)
 */
async function runRule(ruleCode, { dryRun = true } = {}) {
  const [[rule]] = await pool.query('SELECT * FROM kp_rule WHERE code=?', [ruleCode]);
  if (!rule) throw Object.assign(new Error('规则不存在'), { status: 404 });
  const exec = EXECUTORS[ruleCode];
  if (!exec) {
    return { rule_code: ruleCode, matched: 0, alerts: [], message: '该规则暂无内置执行器(自定义表达式规则需在二期接入表达式引擎)' };
  }
  const alerts = await exec(rule);
  await pool.query(
    'INSERT INTO kp_rule_run_log (rule_code,run_type,matched,alerts,status,message) VALUES (?,?,?,?,?,?)',
    [ruleCode, dryRun ? 'test' : 'auto', alerts.length,
     JSON.stringify(alerts.slice(0, 50)), 'success', dryRun ? '试运行完成' : '运行完成']);
  const byLevel = {};
  alerts.forEach(a => { byLevel[a.level] = (byLevel[a.level] || 0) + 1; });
  return { rule_code: ruleCode, rule_name: rule.name, matched: alerts.length, by_level: byLevel, alerts };
}

module.exports = { runRule };
