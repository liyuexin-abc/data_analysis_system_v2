/**
 * 知识影响分析服务: 变更/删除知识对象前分析其被引用情况
 */
const pool = require('../config/db');
const { pj } = require('../utils');

/** 分析某知识对象被哪些其他知识引用 */
async function analyzeImpact(knowledgeType, code) {
  const impacts = [];

  if (knowledgeType === 'domain') {
    const [objs] = await pool.query('SELECT code,name FROM kp_object_type WHERE domain_code=?', [code]);
    objs.forEach(o => impacts.push({ type: '本体对象', code: o.code, name: o.name, detail: `对象属于业务域 ${code}` }));
  }

  if (knowledgeType === 'object') {
    // 关系引用
    const [links] = await pool.query(
      'SELECT code,name FROM kp_link_type WHERE source_object=? OR target_object=?', [code, code]);
    links.forEach(l => impacts.push({ type: '对象关系', code: l.code, name: l.name, detail: '关系的源或目标对象' }));
    // 指标绑定
    const [metrics] = await pool.query('SELECT metric_code,metric_name,bind_objects FROM kp_metric_semantic');
    metrics.filter(m => pj(m.bind_objects, []).includes(code))
      .forEach(m => impacts.push({ type: '指标语义', code: m.metric_code, name: m.metric_name, detail: '指标绑定该对象' }));
    // 规则监控
    const [rules] = await pool.query('SELECT code,name FROM kp_rule WHERE monitor_object=?', [code]);
    rules.forEach(r => impacts.push({ type: '规则语义', code: r.code, name: r.name, detail: '规则监控该对象' }));
    // 方法论
    const [methods] = await pool.query('SELECT code,name,apply_objects,graph_paths FROM kp_method');
    methods.filter(m => pj(m.apply_objects, []).includes(code) ||
        JSON.stringify(pj(m.graph_paths, [])).includes(code))
      .forEach(m => impacts.push({ type: '分析方法论', code: m.code, name: m.name, detail: '方法论适用对象或图谱路径包含该对象' }));
    // 图谱
    const [graphs] = await pool.query('SELECT code,name,include_objects FROM kp_graph_model');
    graphs.filter(g => pj(g.include_objects, []).includes(code))
      .forEach(g => impacts.push({ type: '图谱模型', code: g.code, name: g.name, detail: '对象已入图' }));
    // 术语
    const [terms] = await pool.query("SELECT term FROM kp_term WHERE map_target=? AND map_type='object'", [code]);
    terms.forEach(t => impacts.push({ type: '术语词典', code: t.term, name: t.term, detail: '术语映射到该对象' }));
  }

  if (knowledgeType === 'property') {
    // code 格式: objectCode.propertyCode
    const [objCode, propCode] = code.split('.');
    const [metrics] = await pool.query('SELECT metric_code,metric_name,formula_desc FROM kp_metric_semantic');
    metrics.filter(m => (m.formula_desc || '').includes(propCode))
      .forEach(m => impacts.push({ type: '指标语义', code: m.metric_code, name: m.metric_name, detail: `公式可能使用 ${propCode}` }));
    const [links] = await pool.query(
      'SELECT code,name FROM kp_link_type WHERE (source_object=? AND source_field=?) OR (target_object=? AND target_field=?)',
      [objCode, propCode, objCode, propCode]);
    links.forEach(l => impacts.push({ type: '对象关系', code: l.code, name: l.name, detail: '关系关联字段使用该属性' }));
    const [rules] = await pool.query('SELECT code,name,trigger_cond FROM kp_rule WHERE monitor_object=?', [objCode]);
    rules.filter(r => JSON.stringify(pj(r.trigger_cond, {})).includes(propCode))
      .forEach(r => impacts.push({ type: '规则语义', code: r.code, name: r.name, detail: '触发条件使用该属性' }));
    const [maps] = await pool.query('SELECT table_name,source_field FROM kp_mapping WHERE object_code=? AND property_code=?', [objCode, propCode]);
    maps.forEach(m => impacts.push({ type: '数据映射', code: `${m.table_name}.${m.source_field}`, name: '底层数据映射', detail: '删除属性将断开数据映射' }));
    const [terms] = await pool.query("SELECT term FROM kp_term WHERE map_target=? AND map_type='property'", [propCode]);
    terms.forEach(t => impacts.push({ type: '术语词典', code: t.term, name: t.term, detail: '术语映射到该属性' }));
  }

  if (knowledgeType === 'metric') {
    const [terms] = await pool.query("SELECT term FROM kp_term WHERE map_target=? AND map_type='metric'", [code]);
    terms.forEach(t => impacts.push({ type: '术语词典', code: t.term, name: t.term, detail: '术语映射到该指标' }));
    const [rules] = await pool.query('SELECT code,name FROM kp_rule WHERE monitor_metric=?', [code]);
    rules.forEach(r => impacts.push({ type: '规则语义', code: r.code, name: r.name, detail: '规则监控该指标' }));
    const [methods] = await pool.query('SELECT code,name,apply_metrics,decompose_tree FROM kp_method');
    methods.filter(m => pj(m.apply_metrics, []).includes(code) ||
        JSON.stringify(pj(m.decompose_tree, {})).includes(code))
      .forEach(m => impacts.push({ type: '分析方法论', code: m.code, name: m.name, detail: '方法论适用指标或拆解树包含该指标' }));
    const [skills] = await pool.query('SELECT code,name,depend_knowledge FROM kp_skill');
    skills.filter(s => JSON.stringify(pj(s.depend_knowledge, {})).includes(code))
      .forEach(s => impacts.push({ type: 'Skill', code: s.code, name: s.name, detail: 'Skill 依赖该指标语义' }));
  }

  if (knowledgeType === 'link') {
    const [methods] = await pool.query('SELECT code,name,graph_paths FROM kp_method');
    const [[link]] = await pool.query('SELECT source_object,target_object FROM kp_link_type WHERE code=?', [code]);
    if (link) {
      methods.filter(m => {
        const paths = pj(m.graph_paths, []);
        return paths.some(p => {
          const seq = p.path || [];
          for (let i = 0; i < seq.length - 1; i++) {
            if (seq[i] === link.source_object && seq[i + 1] === link.target_object) return true;
          }
          return false;
        });
      }).forEach(m => impacts.push({ type: '分析方法论', code: m.code, name: m.name, detail: '方法论图谱路径经过该关系' }));
    }
    const [graphs] = await pool.query('SELECT code,name,include_links FROM kp_graph_model');
    graphs.filter(g => pj(g.include_links, []).includes(code))
      .forEach(g => impacts.push({ type: '图谱模型', code: g.code, name: g.name, detail: '关系已入图' }));
  }

  if (knowledgeType === 'rule') {
    const [skills] = await pool.query('SELECT code,name,depend_knowledge FROM kp_skill');
    skills.filter(s => JSON.stringify(pj(s.depend_knowledge, {})).includes(code))
      .forEach(s => impacts.push({ type: 'Skill', code: s.code, name: s.name, detail: 'Skill 依赖该规则' }));
    const [risks] = await pool.query('SELECT COUNT(*) AS c FROM biz_risk WHERE rule_code=?', [code]);
    if (risks[0].c > 0) impacts.push({ type: '风险事项', code: code, name: `${risks[0].c} 条风险事项`, detail: '历史风险事项由该规则触发' });
  }

  if (knowledgeType === 'method') {
    const [metrics] = await pool.query('SELECT metric_code,metric_name FROM kp_metric_semantic WHERE attribution_path=?', [code]);
    metrics.forEach(m => impacts.push({ type: '指标语义', code: m.metric_code, name: m.metric_name, detail: '指标归因路径引用该方法论' }));
    const [skills] = await pool.query('SELECT code,name,depend_knowledge FROM kp_skill');
    skills.filter(s => JSON.stringify(pj(s.depend_knowledge, {})).includes(code))
      .forEach(s => impacts.push({ type: 'Skill', code: s.code, name: s.name, detail: 'Skill 绑定该方法论' }));
  }

  return impacts;
}

module.exports = { analyzeImpact };
