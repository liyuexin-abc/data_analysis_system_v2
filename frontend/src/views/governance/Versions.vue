<template>
  <div class="kp-page">
    <div class="kp-page-title">版本管理</div>
    <div class="kp-page-desc">知识对象版本快照与版本对比</div>
    <div class="kp-card">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <el-select v-model="filter.knowledge_type" placeholder="知识类型" clearable style="width:130px" @change="load">
          <el-option v-for="(v,k) in TYPE_NAMES" :key="k" :label="v" :value="k" />
        </el-select>
        <el-input v-model="filter.knowledge_code" placeholder="知识编码" clearable style="width:180px" @change="load" />
      </div>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column label="类型" width="100"><template #default="{row}"><el-tag size="small" effect="plain">{{ TYPE_NAMES[row.knowledge_type]||row.knowledge_type }}</el-tag></template></el-table-column>
        <el-table-column prop="knowledge_code" label="知识编码" width="200"><template #default="{row}"><span class="mono">{{ row.knowledge_code }}</span></template></el-table-column>
        <el-table-column prop="version" label="版本" width="80"><template #default="{row}"><el-tag size="small">{{ row.version }}</el-tag></template></el-table-column>
        <el-table-column prop="change_note" label="变更说明" min-width="220" show-overflow-tooltip />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="created_at" label="时间" width="160"><template #default="{row}">{{ fmt(row.created_at) }}</template></el-table-column>
        <el-table-column label="操作" width="100"><template #default="{row}"><el-button size="small" plain @click="compare(row)">版本对比</el-button></template></el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px;justify-content:flex-end" layout="total, prev, pager, next"
        :total="total" :page-size="filter.size" v-model:current-page="filter.page" @current-change="load" />
    </div>
    <el-drawer v-model="cmpVisible" title="版本对比(最近两版)" size="560px">
      <template v-if="cmp">
        <el-alert v-if="!cmp.diff.length" type="info" :closable="false" title="无差异或仅有单一版本" style="margin-bottom:10px" />
        <el-table :data="cmp.diff" size="small">
          <el-table-column prop="field" label="字段" width="130" />
          <el-table-column label="旧值"><template #default="{row}"><span class="mono" style="font-size:11px">{{ JSON.stringify(row.old_value) }}</span></template></el-table-column>
          <el-table-column label="新值"><template #default="{row}"><span class="mono" style="font-size:11px;color:#2563eb">{{ JSON.stringify(row.new_value) }}</span></template></el-table-column>
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../../api';
const TYPE_NAMES = { object: '本体对象', link: '关系', metric: '指标语义', term: '术语', rule: '规则', method: '方法论', graph: '图谱', document: '文档', domain: '业务域' };
const rows = ref([]); const total = ref(0); const loading = ref(false);
const filter = ref({ knowledge_type: '', knowledge_code: '', page: 1, size: 20 });
const cmpVisible = ref(false); const cmp = ref(null);
const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-';
async function load() {
  loading.value = true;
  try { const d = await api.governance.versions(filter.value); rows.value = d.list; total.value = d.total; }
  finally { loading.value = false; }
}
async function compare(row) {
  cmp.value = await api.governance.versionCompare({ type: row.knowledge_type, code: row.knowledge_code });
  cmpVisible.value = true;
}
onMounted(load);
</script>
