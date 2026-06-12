import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  { path: '/', redirect: '/overview' },
  { path: '/overview', component: () => import('./views/Overview.vue'), meta: { title: '知识总览' } },
  // 本体中心
  { path: '/ontology/domains', component: () => import('./views/ontology/Domains.vue'), meta: { title: '业务域管理' } },
  { path: '/ontology/objects', component: () => import('./views/ontology/Objects.vue'), meta: { title: '对象类型管理' } },
  { path: '/ontology/links', component: () => import('./views/ontology/Links.vue'), meta: { title: '关系管理' } },
  { path: '/ontology/interfaces', component: () => import('./views/ontology/Interfaces.vue'), meta: { title: '接口管理' } },
  { path: '/ontology/actions', component: () => import('./views/ontology/Actions.vue'), meta: { title: '动作管理' } },
  { path: '/ontology/mappings', component: () => import('./views/ontology/Mappings.vue'), meta: { title: '数据映射' } },
  // 图谱中心
  { path: '/graph/models', component: () => import('./views/graph/Models.vue'), meta: { title: '图谱模型' } },
  { path: '/graph/tasks', component: () => import('./views/graph/Tasks.vue'), meta: { title: '图谱构建任务' } },
  { path: '/graph/explore', component: () => import('./views/graph/Explore.vue'), meta: { title: '图谱浏览' } },
  { path: '/graph/path', component: () => import('./views/graph/PathQuery.vue'), meta: { title: '路径查询' } },
  { path: '/graph/impact', component: () => import('./views/graph/Impact.vue'), meta: { title: '影响分析' } },
  // 语义中心
  { path: '/terms', component: () => import('./views/Terms.vue'), meta: { title: '术语词典' } },
  { path: '/metrics', component: () => import('./views/Metrics.vue'), meta: { title: '指标语义' } },
  { path: '/rules', component: () => import('./views/Rules.vue'), meta: { title: '规则语义' } },
  { path: '/methods', component: () => import('./views/Methods.vue'), meta: { title: '分析方法论' } },
  { path: '/rag', component: () => import('./views/Rag.vue'), meta: { title: 'RAG知识库' } },
  { path: '/skills', component: () => import('./views/Skills.vue'), meta: { title: 'Skill注册' } },
  // 治理
  { path: '/governance/reviews', component: () => import('./views/governance/Reviews.vue'), meta: { title: '审核中心' } },
  { path: '/governance/versions', component: () => import('./views/governance/Versions.vue'), meta: { title: '版本管理' } },
  { path: '/governance/impact', component: () => import('./views/governance/ImpactAnalysis.vue'), meta: { title: '影响分析' } },
  { path: '/governance/quality', component: () => import('./views/governance/Quality.vue'), meta: { title: '质量检查' } },
  { path: '/governance/audit', component: () => import('./views/governance/Audit.vue'), meta: { title: '审计日志' } },
  // 智能问数
  { path: '/qa', component: () => import('./views/Qa.vue'), meta: { title: '智能问数' } },
];

const router = createRouter({ history: createWebHistory(), routes });
router.afterEach((to) => { document.title = `${to.meta.title || ''} · 际华知识平台`; });
export default router;
