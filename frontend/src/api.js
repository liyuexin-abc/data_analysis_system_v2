import axios from 'axios';
import { ElMessage } from 'element-plus';

const http = axios.create({ baseURL: '/api', timeout: 180000 });

http.interceptors.response.use(
  (resp) => {
    if (resp.data && resp.data.code !== 0) {
      ElMessage.error(resp.data.message || '请求失败');
      return Promise.reject(new Error(resp.data.message));
    }
    return resp.data.data;
  },
  (err) => {
    const msg = err.response?.data?.message || err.message || '网络错误';
    ElMessage.error(msg);
    return Promise.reject(err);
  }
);

export default http;

/* ============ 通用 CRUD ============ */
export const crud = (base) => ({
  list: (params) => http.get(base, { params }),
  detail: (id) => http.get(`${base}/${id}`),
  create: (data) => http.post(base, data),
  update: (id, data) => http.put(`${base}/${id}`, data),
  remove: (id) => http.delete(`${base}/${id}`),
  lifecycle: (id, action, data = {}) => http.post(`${base}/${id}/lifecycle/${action}`, data),
});

/* ============ 模块 API ============ */
export const api = {
  overview: () => http.get('/governance/overview'),

  domains: crud('/ontology/domains'),
  objects: { ...crud('/ontology/objects'), full: (id) => http.get(`/ontology/objects/${id}/full`) },
  properties: {
    ...crud('/ontology/properties'),
    impact: (id) => http.get(`/ontology/properties/${id}/impact`),
    batchImport: (data) => http.post('/ontology/properties/batch-import', data),
  },
  links: { ...crud('/ontology/links'), pathPreview: (code) => http.get(`/ontology/links/path-preview/${code}`) },
  interfaces: {
    ...crud('/ontology/interfaces'),
    implement: (d) => http.post('/ontology/interfaces/implement', d),
    unimplement: (d) => http.post('/ontology/interfaces/unimplement', d),
  },
  actions: crud('/ontology/actions'),
  functions: crud('/ontology/functions'),
  mappings: { ...crud('/ontology/mappings'), validate: (objectCode) => http.post(`/ontology/mappings/validate/${objectCode}`) },
  ontologyImpact: (type, code) => http.get(`/ontology/impact/${type}/${encodeURIComponent(code)}`),

  graphModels: crud('/graph/models'),
  graphTasks: {
    ...crud('/graph/tasks'),
    run: (id) => http.post(`/graph/tasks/${id}/run`),
    logs: (id) => http.get(`/graph/tasks/${id}/logs`),
  },
  graphExplore: {
    search: (params) => http.get('/graph/explore/search', { params }),
    neighbors: (nodeId, params) => http.get(`/graph/explore/neighbors/${nodeId}`, { params }),
    node: (nodeId) => http.get(`/graph/explore/node/${nodeId}`),
    stats: (params) => http.get('/graph/explore/stats', { params }),
  },
  pathQuery: (data) => http.post('/graph/path-query', data),
  impactAnalysis: (data) => http.post('/graph/impact-analysis', data),

  terms: {
    ...crud('/terms'),
    matchTest: (question) => http.post('/terms/match-test', { question }),
    batchImport: (terms) => http.post('/terms/batch-import', { terms }),
  },
  metrics: {
    ...crud('/metrics'),
    references: (id) => http.get(`/metrics/${id}/references`),
    data: (code, params) => http.get(`/metrics/${code}/data`, { params }),
  },
  rules: {
    ...crud('/rules'),
    testRun: (id) => http.post(`/rules/${id}/test-run`),
    runLogs: (id) => http.get(`/rules/${id}/run-logs`),
  },
  methods: crud('/methods'),
  skills: { ...crud('/skills'), knowledge: (id) => http.get(`/skills/${id}/knowledge`) },

  documents: {
    ...crud('/rag/documents'),
    parse: (id) => http.post(`/rag/documents/${id}/parse`),
    vectorize: (id) => http.post(`/rag/documents/${id}/vectorize`),
    processAll: (id) => http.post(`/rag/documents/${id}/process-all`),
    chunks: (id) => http.get(`/rag/documents/${id}/chunks`),
  },

  governance: {
    reviews: (params) => http.get('/governance/reviews', { params }),
    reviewDetail: (id) => http.get(`/governance/reviews/${id}`),
    approve: (id, data) => http.post(`/governance/reviews/${id}/approve`, data),
    reject: (id, data) => http.post(`/governance/reviews/${id}/reject`, data),
    versions: (params) => http.get('/governance/versions', { params }),
    versionCompare: (params) => http.get('/governance/versions/compare', { params }),
    impact: (type, code) => http.get(`/governance/impact/${type}/${encodeURIComponent(code)}`),
    auditLogs: (params) => http.get('/governance/audit-logs', { params }),
    quality: () => http.get('/governance/quality'),
    qualityRun: () => http.post('/governance/quality/run'),
    qualityHistory: () => http.get('/governance/quality/history'),
  },

  biz: {
    orgTree: () => http.get('/biz/orgs/tree'),
    orgs: () => http.get('/biz/orgs'),
    metricFacts: (params) => http.get('/biz/metric-facts', { params }),
    metricRank: (params) => http.get('/biz/metric-rank', { params }),
    list: (resource, params) => http.get(`/biz/${resource}`, { params }),
  },

  ai: {
    qa: (question) => http.post('/ai/qa', { question }),
    parse: (question) => http.post('/ai/qa/parse', { question }),
    qaLogs: (params) => http.get('/ai/qa/logs', { params }),
    feedback: (data) => http.post('/ai/qa/feedback', data),
    profitAttr: (data) => http.post('/ai/attribution/profit', data),
    receiptRisk: (data) => http.post('/ai/attribution/receipt-risk', data),
    methodTest: (data) => http.post('/ai/method/test', data),
    ragSearch: (data) => http.post('/ai/rag/search', data),
    ragAnswer: (data) => http.post('/ai/rag/answer', data),
  },
};

/* ============ 常量 ============ */
export const STATUS_MAP = {
  draft: { label: '草稿', type: 'info' },
  pending_check: { label: '待校验', type: 'warning' },
  check_failed: { label: '校验不通过', type: 'danger' },
  pending_review: { label: '待审核', type: 'warning' },
  published: { label: '已发布', type: 'success' },
  changing: { label: '变更中', type: 'warning' },
  disabled: { label: '已停用', type: 'info' },
  deprecated: { label: '已废弃', type: 'danger' },
};

export const SECURITY_MAP = {
  normal: { label: '普通', type: 'info' },
  sensitive: { label: '敏感', type: 'warning' },
  confidential: { label: '机密', type: 'danger' },
};

export const RISK_COLOR = { red: '#f56c6c', orange: '#e6a23c', yellow: '#f7ba2a', blue: '#409eff' };
export const RISK_NAME = { red: '红色', orange: '橙色', yellow: '黄色', blue: '蓝色' };

export const pj = (v, dft = null) => {
  if (v === null || v === undefined) return dft;
  if (typeof v === 'object') return v;
  try { return JSON.parse(v); } catch { return dft; }
};
