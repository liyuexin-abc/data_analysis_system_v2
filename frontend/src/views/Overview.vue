<template>
  <div class="kp-page" v-loading="loading">
    <div class="kp-page-title">知识总览</div>
    <div class="kp-page-desc">知识平台整体建设情况、质量状态、待办审核、最近变更与调用监控</div>

    <!-- 统计卡片 -->
    <el-row :gutter="14">
      <el-col :span="3" v-for="c in statCards" :key="c.label">
        <div class="stat-card">
          <div class="num">{{ c.value }}</div>
          <div class="label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 质量概览 -->
    <el-row :gutter="14" style="margin-top:14px">
      <el-col :span="16">
        <div class="kp-card">
          <div style="font-weight:600;margin-bottom:12px">知识质量概览
            <el-tag size="small" style="margin-left:8px" :type="quality.quality_score>=80?'success':'warning'">
              综合评分 {{ quality.quality_score }}
            </el-tag>
          </div>
          <el-row :gutter="12">
            <el-col :span="6" v-for="q in qualityItems" :key="q.label" style="margin-bottom:14px">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px">
                <span style="color:#64748b">{{ q.label }}</span><span style="font-weight:600">{{ q.value }}%</span>
              </div>
              <el-progress :percentage="q.value" :show-text="false" :stroke-width="8"
                :color="q.value>=80?'#10b981':q.value>=50?'#f59e0b':'#ef4444'" />
            </el-col>
          </el-row>
        </div>
        <!-- 调用监控 -->
        <div class="kp-card" style="margin-top:14px">
          <div style="font-weight:600;margin-bottom:12px">调用监控</div>
          <div ref="callChart" style="height:240px"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="kp-card">
          <div style="font-weight:600;margin-bottom:10px">待办事项
            <el-badge :value="todos.pending_reviews?.length || 0" style="margin-left:6px" />
          </div>
          <el-scrollbar max-height="200px">
            <div v-for="r in todos.pending_reviews" :key="r.review_no"
                 style="padding:8px 0;border-bottom:1px dashed #eef2f7;font-size:13px;display:flex;justify-content:space-between">
              <span><el-tag size="small" effect="plain">{{ typeName(r.knowledge_type) }}</el-tag>
                {{ r.knowledge_name }}</span>
              <span style="color:#94a3b8">{{ r.applicant }}</span>
            </div>
            <el-empty v-if="!todos.pending_reviews?.length" description="暂无待办" :image-size="60" />
          </el-scrollbar>
          <el-button size="small" type="primary" plain style="margin-top:10px;width:100%"
            @click="$router.push('/governance/reviews')">前往审核中心</el-button>
        </div>
        <div class="kp-card" style="margin-top:14px">
          <div style="font-weight:600;margin-bottom:10px">最近变更</div>
          <el-scrollbar max-height="300px">
            <el-timeline style="padding-left:2px">
              <el-timeline-item v-for="(c,i) in recentChanges" :key="i" :timestamp="fmt(c.created_at)" size="small">
                <span style="font-size:13px">
                  <el-tag size="small" effect="plain">{{ actionName(c.action) }}</el-tag>
                  {{ c.knowledge_name || c.knowledge_code }} <span style="color:#94a3b8">by {{ c.operator }}</span>
                </span>
              </el-timeline-item>
            </el-timeline>
          </el-scrollbar>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import { api } from '../api';

const loading = ref(true);
const counts = ref({});
const quality = ref({});
const todos = ref({});
const recentChanges = ref([]);
const callMonitor = ref({});
const callChart = ref();

const statCards = computed(() => [
  { label: '业务域', value: counts.value.domain_count ?? '-' },
  { label: '本体对象', value: counts.value.object_count ?? '-' },
  { label: '对象关系', value: counts.value.link_count ?? '-' },
  { label: '指标语义', value: counts.value.metric_semantic_count ?? '-' },
  { label: '术语', value: counts.value.term_count ?? '-' },
  { label: '规则', value: counts.value.rule_count ?? '-' },
  { label: '方法论', value: counts.value.method_count ?? '-' },
  { label: 'RAG文档', value: counts.value.document_count ?? '-' },
]);

const qualityItems = computed(() => [
  { label: '本体完整率', value: quality.value.ontology_rate ?? 0 },
  { label: '关系完整率', value: quality.value.link_rate ?? 0 },
  { label: '指标语义覆盖率', value: quality.value.metric_rate ?? 0 },
  { label: '术语覆盖率', value: quality.value.term_rate ?? 0 },
  { label: '图谱覆盖率', value: quality.value.graph_rate ?? 0 },
  { label: '规则可执行率', value: quality.value.rule_rate ?? 0 },
  { label: '方法论可用率', value: quality.value.method_rate ?? 0 },
  { label: 'RAG可检索率', value: quality.value.rag_rate ?? 0 },
]);

const TYPE_NAMES = { object: '本体', link: '关系', metric: '指标', term: '术语', rule: '规则', method: '方法论', graph: '图谱', document: '文档', domain: '业务域' };
const ACTION_NAMES = { create: '新建', update: '修改', publish: '发布', approve: '审核通过', disable: '停用', run: '执行', call: '调用', submit_check: '提交校验' };
const typeName = (t) => TYPE_NAMES[t] || t;
const actionName = (a) => ACTION_NAMES[a] || a;
const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';

onMounted(async () => {
  try {
    const data = await api.overview();
    counts.value = data.counts;
    quality.value = data.quality;
    todos.value = data.todos;
    recentChanges.value = data.recent_changes;
    callMonitor.value = data.call_monitor;
    await nextTick();
    renderCallChart();
  } finally { loading.value = false; }
});

function renderCallChart() {
  const skills = callMonitor.value.skill_calls || [];
  const chart = echarts.init(callChart.value);
  chart.setOption({
    tooltip: {},
    grid: { left: 140, right: 30, top: 10, bottom: 24 },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef2f7' } } },
    yAxis: { type: 'category', data: skills.map(s => s.name).reverse(), axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar', data: skills.map(s => s.call_count).reverse(), barWidth: 14,
      itemStyle: { borderRadius: [0, 7, 7, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#2563eb' }, { offset: 1, color: '#38bdf8' }]) },
      label: { show: true, position: 'right', color: '#64748b', fontSize: 12 },
    }],
  });
}
</script>
