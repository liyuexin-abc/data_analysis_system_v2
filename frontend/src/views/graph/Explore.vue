<template>
  <div class="kp-page">
    <div class="kp-page-title">图谱浏览</div>
    <div class="kp-page-desc">可视化查看业务对象实例之间的关系 — 支持搜索、多跳展开、节点详情</div>
    <el-row :gutter="14">
      <el-col :span="18">
        <div class="kp-card" style="padding:12px">
          <div style="display:flex;gap:8px;margin-bottom:10px">
            <el-select v-model="searchType" placeholder="对象类型" clearable style="width:130px" size="default">
              <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
            </el-select>
            <el-autocomplete v-model="keyword" :fetch-suggestions="suggest" placeholder="搜索客户、合同、单位、供应商..."
              style="flex:1" clearable @select="onSelect">
              <template #default="{item}">
                <span><el-tag size="small" effect="plain">{{ objName(item.object_code) }}</el-tag> {{ item.entity_name }}</span>
              </template>
            </el-autocomplete>
            <el-select v-model="hops" style="width:96px">
              <el-option v-for="h in [1,2,3,4,5]" :key="h" :label="`${h} 跳`" :value="h" />
            </el-select>
            <el-button type="primary" @click="expandSelected">展开</el-button>
          </div>
          <div ref="chartEl" style="height:600px;background:#fbfdff;border:1px solid #eef2f7;border-radius:8px" v-loading="loadingGraph"></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kp-card" style="margin-bottom:14px">
          <div style="font-weight:600;margin-bottom:10px">图谱统计</div>
          <div style="display:flex;gap:18px;margin-bottom:10px">
            <div><div style="font-size:22px;font-weight:700;color:#2563eb">{{ stats.node_count?.toLocaleString() }}</div><div style="font-size:12px;color:#94a3b8">节点</div></div>
            <div><div style="font-size:22px;font-weight:700;color:#38bdf8">{{ stats.edge_count?.toLocaleString() }}</div><div style="font-size:12px;color:#94a3b8">边</div></div>
          </div>
          <el-scrollbar max-height="180px">
            <div v-for="t in stats.by_type" :key="t.object_code"
              style="display:flex;justify-content:space-between;font-size:13px;padding:3px 0">
              <span>{{ t.object_name }}</span><span class="mono">{{ t.count }}</span>
            </div>
          </el-scrollbar>
        </div>
        <div class="kp-card" v-if="nodeDetail">
          <div style="font-weight:600;margin-bottom:10px">节点详情</div>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="类型">{{ nodeDetail.object_name }}</el-descriptions-item>
            <el-descriptions-item label="ID"><span class="mono">{{ nodeDetail.entity_id }}</span></el-descriptions-item>
            <el-descriptions-item label="名称">{{ nodeDetail.entity_name }}</el-descriptions-item>
            <el-descriptions-item v-for="(v,k) in displayProps" :key="k" :label="k">{{ v }}</el-descriptions-item>
          </el-descriptions>
          <el-button size="small" type="primary" plain style="margin-top:10px;width:100%"
            @click="$router.push({path:'/graph/impact', query:{node:nodeDetail.id}})">影响分析</el-button>
        </div>
        <el-empty v-else description="点击图中节点查看详情" :image-size="60" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { api } from '../../api';

const objects = ref([]); const stats = ref({});
const keyword = ref(''); const searchType = ref(''); const hops = ref(2);
const selectedNode = ref(null);
const chartEl = ref(); let chart = null;
const loadingGraph = ref(false);
const nodeDetail = ref(null);

const COLORS = {
  Obj_Org_Unit: '#2563eb', Obj_Mkt_Customer: '#10b981', Obj_Sales_Contract: '#f59e0b',
  Obj_Sales_Order: '#8b5cf6', Obj_Fin_Receipt: '#ef4444', Obj_Scm_Supplier: '#14b8a6',
  Obj_Scm_PurchaseOrder: '#f97316', Obj_Scm_Material: '#84cc16', Obj_Inv_Inventory: '#06b6d4',
  Obj_Prod_Task: '#a855f7', Obj_Gov_Risk: '#dc2626',
};
const objName = (code) => objects.value.find(o => o.code === code)?.name || code;
const displayProps = computed(() => {
  if (!nodeDetail.value?.props) return {};
  const p = nodeDetail.value.props;
  const keep = ['contract_amount', 'overdue_amount', 'overdue_days', 'po_amount', 'amount', 'risk_level',
    'contract_status', 'receipt_status', 'credit_level', 'region', 'industry', 'rating', 'age_days'];
  const out = {};
  for (const k of keep) if (p[k] !== undefined && p[k] !== null) out[k] = p[k];
  return out;
});

async function suggest(q, cb) {
  if (!q) return cb([]);
  const rows = await api.graphExplore.search({ keyword: q, object_code: searchType.value || undefined });
  cb(rows.map(r => ({ ...r, value: r.entity_name })));
}
function onSelect(item) { selectedNode.value = item; expandSelected(); }

async function expandSelected() {
  if (!selectedNode.value) return ElMessage.warning('请先搜索并选择一个节点');
  loadingGraph.value = true;
  try {
    const data = await api.graphExplore.neighbors(selectedNode.value.id, { hops: hops.value });
    render(data);
  } finally { loadingGraph.value = false; }
}

function render({ nodes, edges }) {
  const categories = [...new Set(nodes.map(n => n.object_code))];
  chart.setOption({
    tooltip: { formatter: (p) => p.dataType === 'node' ? `${objName(p.data.object_code)}<br/>${p.data.name}` : p.data.link_name || '' },
    legend: { data: categories.map(objName), bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      force: { repulsion: 220, edgeLength: [60, 140], gravity: 0.12 },
      categories: categories.map(c => ({ name: objName(c), itemStyle: { color: COLORS[c] || '#64748b' } })),
      label: { show: true, fontSize: 10, formatter: (p) => p.data.name.length > 12 ? p.data.name.slice(0, 12) + '…' : p.data.name },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 6,
      lineStyle: { color: '#cbd5e1', curveness: 0.1 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
      data: nodes.map(n => ({
        id: String(n.id), name: n.entity_name, object_code: n.object_code,
        category: categories.indexOf(n.object_code),
        symbolSize: n.level === 0 ? 38 : Math.max(14, 26 - n.level * 5),
      })),
      links: edges.map(e => ({ source: String(e.source), target: String(e.target), link_name: e.link_code })),
    }],
  }, true);
}

onMounted(async () => {
  chart = echarts.init(chartEl.value);
  chart.on('click', async (p) => {
    if (p.dataType === 'node') {
      nodeDetail.value = await api.graphExplore.node(p.data.id);
      selectedNode.value = { id: p.data.id };
    }
  });
  const [o, s] = await Promise.all([api.objects.list({ size: 100 }), api.graphExplore.stats({})]);
  objects.value = o.list; stats.value = s;
  // 默认加载集团节点
  const seed = await api.graphExplore.search({ keyword: '际华集团' });
  if (seed.length) { selectedNode.value = seed[0]; expandSelected(); }
  window.addEventListener('resize', resize);
});
function resize() { chart?.resize(); }
onBeforeUnmount(() => { window.removeEventListener('resize', resize); chart?.dispose(); });
</script>
