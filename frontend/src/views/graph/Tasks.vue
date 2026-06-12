<template>
  <div class="kp-page">
    <div class="kp-page-title">图谱构建任务</div>
    <div class="kp-page-desc">管理图谱构建、同步、失败重试和质量校验</div>
    <div class="kp-card">
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="name" label="任务名称" min-width="170" />
        <el-table-column prop="graph_code" label="图谱" width="170"><template #default="{row}"><span class="mono">{{ row.graph_code }}</span></template></el-table-column>
        <el-table-column label="执行周期" width="80"><template #default="{row}">{{ {daily:'每日',hourly:'每小时',realtime:'实时'}[row.run_cycle] }}</template></el-table-column>
        <el-table-column prop="last_run_at" label="上次执行" width="160"><template #default="{row}">{{ fmt(row.last_run_at) }}</template></el-table-column>
        <el-table-column prop="node_count" label="节点数" width="90" align="right"><template #default="{row}">{{ (row.node_count||0).toLocaleString() }}</template></el-table-column>
        <el-table-column prop="edge_count" label="边数" width="90" align="right"><template #default="{row}">{{ (row.edge_count||0).toLocaleString() }}</template></el-table-column>
        <el-table-column prop="success_rate" label="成功率" width="80" align="center"><template #default="{row}">{{ row.success_rate }}%</template></el-table-column>
        <el-table-column label="质量" width="70" align="center">
          <template #default="{row}"><el-tag size="small" :type="row.quality_status==='normal'?'success':'danger'">{{ row.quality_status==='normal'?'正常':'异常' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="运行状态" width="86" align="center">
          <template #default="{row}">
            <el-tag size="small" :type="{success:'success',failed:'danger',running:'warning'}[row.last_status]||'info'">
              {{ {success:'成功',failed:'失败',running:'运行中'}[row.last_status]||'未运行' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{row}">
            <el-button size="small" type="primary" plain :loading="runningId===row.id" @click="run(row)">立即执行</el-button>
            <el-button size="small" plain @click="showLogs(row)">查看日志</el-button>
            <el-button size="small" plain @click="showQuality(row)">质量报告</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer v-model="logsVisible" title="构建日志" size="560px">
      <el-timeline>
        <el-timeline-item v-for="l in logs" :key="l.id" :timestamp="fmt(l.run_time)"
          :type="l.status==='success'?'success':'danger'">
          <div style="font-size:13px">
            <el-tag size="small" :type="l.status==='success'?'success':'danger'">{{ l.status }}</el-tag>
            {{ l.message }}
            <span v-if="l.duration_ms" style="color:#94a3b8">({{ l.duration_ms }}ms, {{ l.node_count }}节点/{{ l.edge_count }}边)</span>
          </div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!logs.length" description="无日志" />
    </el-drawer>

    <el-dialog v-model="qualityVisible" title="图谱质量报告" width="480px">
      <el-descriptions :column="1" border v-if="qualityReport">
        <el-descriptions-item label="孤立节点">{{ qualityReport.isolated_nodes }}</el-descriptions-item>
        <el-descriptions-item label="重复节点">{{ qualityReport.duplicate_nodes }}</el-descriptions-item>
        <el-descriptions-item label="节点完整性">{{ qualityReport.node_integrity }}</el-descriptions-item>
        <el-descriptions-item label="关系完整性">{{ qualityReport.relation_integrity }}</el-descriptions-item>
        <el-descriptions-item label="图谱覆盖率">{{ qualityReport.coverage_rate }}%</el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="暂无质量报告，请先执行构建" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { api } from '../../api';

const rows = ref([]); const loading = ref(false);
const runningId = ref(null);
const logsVisible = ref(false); const logs = ref([]);
const qualityVisible = ref(false); const qualityReport = ref(null);

const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-';

async function load() {
  loading.value = true;
  try { rows.value = (await api.graphTasks.list({ size: 50 })).list; }
  finally { loading.value = false; }
}
async function run(row) {
  runningId.value = row.id;
  try {
    const r = await api.graphTasks.run(row.id);
    ElMessage.success(`构建完成: ${r.nodeCount} 节点 / ${r.edgeCount} 边`);
    load();
  } finally { runningId.value = null; }
}
async function showLogs(row) { logs.value = await api.graphTasks.logs(row.id); logsVisible.value = true; }
async function showQuality(row) {
  const ls = await api.graphTasks.logs(row.id);
  const latest = ls.find(l => l.quality_report);
  qualityReport.value = latest ? (typeof latest.quality_report === 'string' ? JSON.parse(latest.quality_report) : latest.quality_report) : null;
  qualityVisible.value = true;
}
onMounted(load);
</script>
