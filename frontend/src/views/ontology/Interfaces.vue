<template>
  <div class="kp-page">
    <div class="kp-page-title">接口管理</div>
    <div class="kp-page-desc">对象实现接口即可被平台通用能力识别 — 本体业务可扩展性的核心机制</div>
    <el-row :gutter="14">
      <el-col :span="14">
        <div class="kp-card">
          <el-table :data="rows" v-loading="loading" highlight-current-row @current-change="select">
            <el-table-column prop="code" label="接口编码" width="150"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
            <el-table-column prop="name" label="接口名称" width="130" />
            <el-table-column prop="description" label="说明" min-width="200" />
            <el-table-column label="实现对象数" width="100" align="center">
              <template #default="{row}"><el-badge :value="row.implemented_by?.length||0" type="primary" /></template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="kp-card" v-if="current">
          <div style="font-weight:600;margin-bottom:10px">{{ current.name }} <span class="mono">{{ current.code }}</span></div>
          <el-descriptions :column="1" border size="small" style="margin-bottom:12px">
            <el-descriptions-item label="必需属性">
              <el-tag v-for="p in pj(current.required_props,[])" :key="p" size="small" style="margin-right:4px">{{ p }}</el-tag>
              <span v-if="!pj(current.required_props,[]).length">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="支持函数">
              <el-tag v-for="p in pj(current.support_funcs,[])" :key="p" size="small" type="success" style="margin-right:4px">{{ p }}</el-tag>
              <span v-if="!pj(current.support_funcs,[]).length">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="支持动作">
              <el-tag v-for="p in pj(current.support_actions,[])" :key="p" size="small" type="warning" style="margin-right:4px">{{ p }}</el-tag>
              <span v-if="!pj(current.support_actions,[]).length">-</span>
            </el-descriptions-item>
          </el-descriptions>
          <div style="font-weight:600;margin-bottom:8px;font-size:13px">已实现该接口的对象</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">
            <el-tag v-for="o in current.implemented_by" :key="o.code" closable @close="unimplement(o)" effect="plain">{{ o.name }}</el-tag>
          </div>
          <div style="display:flex;gap:8px">
            <el-select v-model="newImpl" placeholder="选择对象实现该接口" size="small" style="flex:1" filterable>
              <el-option v-for="o in availableObjects" :key="o.code" :label="o.name" :value="o.code" />
            </el-select>
            <el-button size="small" type="primary" @click="implement">实现接口</el-button>
          </div>
        </div>
        <el-empty v-else description="选择左侧接口查看详情" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { api, pj } from '../../api';

const rows = ref([]); const loading = ref(false);
const current = ref(null); const objects = ref([]); const newImpl = ref('');

const availableObjects = computed(() => {
  if (!current.value) return [];
  const implemented = new Set((current.value.implemented_by || []).map(o => o.code));
  return objects.value.filter(o => !implemented.has(o.code));
});

async function load() {
  loading.value = true;
  try {
    const data = await api.interfaces.list({ size: 50 });
    rows.value = data.list;
    if (current.value) current.value = rows.value.find(r => r.id === current.value.id) || null;
  } finally { loading.value = false; }
}
function select(row) { current.value = row; newImpl.value = ''; }
async function implement() {
  if (!newImpl.value) return;
  await api.interfaces.implement({ object_code: newImpl.value, interface_code: current.value.code });
  ElMessage.success('已实现接口'); newImpl.value = ''; load();
}
async function unimplement(o) {
  await api.interfaces.unimplement({ object_code: o.code, interface_code: current.value.code });
  ElMessage.success('已取消实现'); load();
}
onMounted(async () => {
  const d = await api.objects.list({ size: 100 });
  objects.value = d.list;
  load();
});
</script>
