<template>
  <div class="kp-page">
    <div class="kp-page-title">知识质量检查</div>
    <div class="kp-page-desc">本体完整率、指标语义覆盖率、术语覆盖率、图谱覆盖率等八项质量指标</div>
    <div class="kp-card" style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
        <div style="font-weight:600">质量指标
          <el-tag size="small" style="margin-left:8px" :type="quality.quality_score>=80?'success':'warning'">综合评分 {{ quality.quality_score }}</el-tag>
        </div>
        <el-button type="primary" :loading="running" @click="run">执行质量检查</el-button>
      </div>
      <el-row :gutter="14">
        <el-col :span="6" v-for="q in items" :key="q.label" style="margin-bottom:14px">
          <div class="stat-card">
            <div class="num" :style="{color:q.value>=80?'#10b981':q.value>=50?'#f59e0b':'#ef4444'}">{{ q.value }}%</div>
            <div class="label">{{ q.label }}</div>
            <el-progress :percentage="q.value" :show-text="false" :stroke-width="6" style="margin-top:8px"
              :color="q.value>=80?'#10b981':q.value>=50?'#f59e0b':'#ef4444'" />
          </div>
        </el-col>
      </el-row>
    </div>
    <div class="kp-card">
      <div style="font-weight:600;margin-bottom:10px">检查历史</div>
      <el-table :data="history" size="small">
        <el-table-column prop="check_time" label="检查时间" width="180"><template #default="{row}">{{ fmt(row.check_time) }}</template></el-table-column>
        <el-table-column prop="total_score" label="综合评分" width="100" align="center" />
        <el-table-column prop="operator" label="执行人" width="100" />
        <el-table-column label="明细"><template #default="{row}"><span class="mono" style="font-size:11px">{{ JSON.stringify(pj(row.check_items,{})) }}</span></template></el-table-column>
      </el-table>
      <el-empty v-if="!history.length" description="暂无检查记录" :image-size="60" />
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { api, pj } from '../../api';
const quality = ref({}); const history = ref([]); const running = ref(false);
const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-';
const items = computed(() => [
  { label: '本体完整率', value: quality.value.ontology_rate ?? 0 },
  { label: '关系完整率', value: quality.value.link_rate ?? 0 },
  { label: '指标语义覆盖率', value: quality.value.metric_rate ?? 0 },
  { label: '术语覆盖率', value: quality.value.term_rate ?? 0 },
  { label: '图谱覆盖率', value: quality.value.graph_rate ?? 0 },
  { label: '规则可执行率', value: quality.value.rule_rate ?? 0 },
  { label: '方法论可用率', value: quality.value.method_rate ?? 0 },
  { label: 'RAG可检索率', value: quality.value.rag_rate ?? 0 },
]);
async function load() {
  quality.value = await api.governance.quality();
  history.value = await api.governance.qualityHistory();
}
async function run() {
  running.value = true;
  try { quality.value = await api.governance.qualityRun(); ElMessage.success('质量检查完成'); history.value = await api.governance.qualityHistory(); }
  finally { running.value = false; }
}
onMounted(load);
</script>
