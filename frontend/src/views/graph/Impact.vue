<template>
  <div class="kp-page">
    <div class="kp-page-title">影响分析(图谱)</div>
    <div class="kp-page-desc">分析某个客户、合同、供应商等对象对其他业务对象的影响范围</div>
    <div class="kp-card" style="margin-bottom:14px">
      <el-form inline>
        <el-form-item label="分析对象">
          <el-autocomplete v-model="keyword" :fetch-suggestions="suggest" style="width:300px"
            placeholder="搜索供应商、客户、合同..." @select="(i)=>node=i" />
        </el-form-item>
        <el-form-item label="影响范围(跳数)">
          <el-select v-model="hops" style="width:80px"><el-option v-for="h in [2,3,4]" :key="h" :label="h" :value="h" /></el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" :loading="loading" @click="analyze">影响分析</el-button></el-form-item>
      </el-form>
    </div>
    <el-row :gutter="14" v-if="result">
      <el-col :span="9">
        <div class="kp-card">
          <div style="font-weight:600;margin-bottom:10px">影响对象分布</div>
          <el-table :data="result.impacted" size="small">
            <el-table-column prop="object_name" label="对象类型" width="100" />
            <el-table-column prop="count" label="数量" width="70" align="center" />
            <el-table-column label="涉及金额(万)" width="110" align="right"><template #default="{row}">{{ row.total_amount?.toLocaleString() }}</template></el-table-column>
            <el-table-column label="示例"><template #default="{row}"><span style="font-size:12px;color:#64748b">{{ row.samples.slice(0,2).join('、') }}</span></template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="15">
        <div class="kp-card"><div ref="chartEl" style="height:540px"></div></div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { useRoute } from 'vue-router';
import { api } from '../../api';

const route = useRoute();
const keyword = ref(''); const node = ref(null); const hops = ref(3);
const result = ref(null); const loading = ref(false);
const chartEl = ref(); let chart = null;

async function suggest(q, cb) {
  if (!q) return cb([]);
  const rows = await api.graphExplore.search({ keyword: q });
  cb(rows.map(r => ({ ...r, value: r.entity_name })));
}
async function analyze() {
  if (!node.value) return ElMessage.warning('请选择分析对象');
  loading.value = true;
  try {
    result.value = await api.impactAnalysis({ node_id: node.value.id, max_hops: hops.value });
    await nextTick(); render();
  } finally { loading.value = false; }
}
function render() {
  if (!chart) chart = echarts.init(chartEl.value);
  const { nodes, edges } = result.value.graph;
  const cats = [...new Set(nodes.map(n => n.object_code))];
  chart.setOption({
    tooltip: {},
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'graph', layout: 'force', roam: true,
      force: { repulsion: 180, edgeLength: 70 },
      categories: cats.map(c => ({ name: c })),
      label: { show: true, fontSize: 9, formatter: p => p.data.name.slice(0, 10) },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 5,
      lineStyle: { color: '#cbd5e1' },
      data: nodes.map(n => ({ id: String(n.id), name: n.entity_name, category: cats.indexOf(n.object_code), symbolSize: n.level === 0 ? 34 : Math.max(10, 22 - n.level * 5) })),
      links: edges.map(e => ({ source: String(e.source), target: String(e.target) })),
    }],
  }, true);
}
onMounted(async () => {
  if (route.query.node) {
    const n = await api.graphExplore.node(route.query.node);
    node.value = n; keyword.value = n.entity_name;
    analyze();
  }
});
</script>
