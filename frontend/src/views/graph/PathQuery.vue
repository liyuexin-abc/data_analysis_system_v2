<template>
  <div class="kp-page">
    <div class="kp-page-title">路径查询</div>
    <div class="kp-page-desc">查询两个对象之间的可达路径，供问数、归因、影响分析使用</div>
    <div class="kp-card" style="margin-bottom:14px">
      <el-form inline>
        <el-form-item label="起点对象类型">
          <el-select v-model="startType" style="width:140px" @change="startNode=null">
            <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="起点实例">
          <el-autocomplete v-model="startKeyword" :fetch-suggestions="suggestStart" style="width:220px"
            placeholder="搜索实例" @select="(i)=>startNode=i" />
        </el-form-item>
        <el-form-item label="终点对象类型">
          <el-select v-model="endType" style="width:140px" clearable>
            <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="终点实例(可选)">
          <el-autocomplete v-model="endKeyword" :fetch-suggestions="suggestEnd" style="width:200px"
            placeholder="留空查所有可达" clearable @select="(i)=>endNode=i" @clear="endNode=null" />
        </el-form-item>
        <el-form-item label="最大跳数">
          <el-select v-model="maxHops" style="width:80px"><el-option v-for="h in [2,3,4,5]" :key="h" :label="h" :value="h" /></el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="query">查询路径</el-button>
        </el-form-item>
      </el-form>
      <div style="color:#94a3b8;font-size:12px">
        典型场景: 回款风险路径(组织→合同→回款→客户)、利润归因路径(组织→采购单→物料→供应商)
      </div>
    </div>

    <div class="kp-card" v-if="paths.length">
      <div style="font-weight:600;margin-bottom:12px">查询结果 — 共 {{ paths.length }} 条路径</div>
      <div v-for="(p,i) in paths" :key="i"
        style="padding:12px;border:1px solid #eef2f7;border-radius:8px;margin-bottom:10px;background:#fbfdff">
        <div style="font-size:12px;color:#94a3b8;margin-bottom:6px">路径 {{ i+1 }} · {{ p.hops }} 跳</div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <template v-for="(n,j) in p.nodes" :key="j">
            <div style="text-align:center">
              <el-tag :effect="j===0||j===p.nodes.length-1?'dark':'plain'" size="default">{{ n.entity_name }}</el-tag>
              <div style="font-size:11px;color:#94a3b8;margin-top:2px">{{ objName(n.object_code) }}</div>
            </div>
            <div v-if="j<p.nodes.length-1" style="display:flex;flex-direction:column;align-items:center">
              <el-icon color="#2563eb"><Right /></el-icon>
              <span style="font-size:10px;color:#94a3b8">{{ p.links[j]?.name }}</span>
            </div>
          </template>
        </div>
      </div>
    </div>
    <el-empty v-else-if="queried" description="未找到可达路径，可尝试增大跳数" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { api } from '../../api';

const objects = ref([]);
const startType = ref('Obj_Org_Unit'); const startKeyword = ref(''); const startNode = ref(null);
const endType = ref('Obj_Fin_Receipt'); const endKeyword = ref(''); const endNode = ref(null);
const maxHops = ref(3);
const paths = ref([]); const loading = ref(false); const queried = ref(false);

const objName = (code) => objects.value.find(o => o.code === code)?.name || code;

async function suggestStart(q, cb) {
  if (!q) return cb([]);
  const rows = await api.graphExplore.search({ keyword: q, object_code: startType.value });
  cb(rows.map(r => ({ ...r, value: r.entity_name })));
}
async function suggestEnd(q, cb) {
  if (!q) return cb([]);
  const rows = await api.graphExplore.search({ keyword: q, object_code: endType.value || undefined });
  cb(rows.map(r => ({ ...r, value: r.entity_name })));
}
async function query() {
  if (!startNode.value) return ElMessage.warning('请选择起点实例');
  if (!endNode.value && !endType.value) return ElMessage.warning('请指定终点类型或实例');
  loading.value = true; queried.value = true;
  try {
    paths.value = await api.pathQuery({
      start_node_id: startNode.value.id,
      end_node_id: endNode.value?.id || null,
      end_object_code: endNode.value ? null : endType.value,
      max_hops: maxHops.value,
    });
  } finally { loading.value = false; }
}
onMounted(async () => {
  objects.value = (await api.objects.list({ size: 100 })).list;
});
</script>
