<template>
  <div class="kp-page">
    <div class="kp-page-title">审计日志</div>
    <div class="kp-page-desc">知识对象的创建、修改、审批、发布、调用等全量操作记录</div>
    <div class="kp-card">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <el-select v-model="filter.module" placeholder="模块" clearable style="width:120px" @change="load">
          <el-option v-for="m in ['ontology','graph','term','metric','rule','method','rag','governance','qa','skill']" :key="m" :label="m" :value="m" />
        </el-select>
        <el-select v-model="filter.action" placeholder="动作" clearable style="width:130px" @change="load">
          <el-option v-for="(v,k) in ACTIONS" :key="k" :label="v" :value="k" />
        </el-select>
        <el-input v-model="filter.keyword" placeholder="编码/名称/操作人" clearable style="width:200px" @change="load" />
      </div>
      <el-table :data="rows" v-loading="loading" stripe size="small">
        <el-table-column prop="created_at" label="时间" width="160"><template #default="{row}">{{ fmt(row.created_at) }}</template></el-table-column>
        <el-table-column prop="module" label="模块" width="90"><template #default="{row}"><el-tag size="small" effect="plain">{{ row.module }}</el-tag></template></el-table-column>
        <el-table-column label="动作" width="90"><template #default="{row}">{{ ACTIONS[row.action]||row.action }}</template></el-table-column>
        <el-table-column prop="knowledge_code" label="知识编码" width="200"><template #default="{row}"><span class="mono">{{ row.knowledge_code || '-' }}</span></template></el-table-column>
        <el-table-column prop="knowledge_name" label="知识名称" width="170" show-overflow-tooltip />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column label="明细"><template #default="{row}"><span class="mono" style="font-size:11px">{{ JSON.stringify(pj(row.detail,{})) }}</span></template></el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px;justify-content:flex-end" layout="total, prev, pager, next"
        :total="total" :page-size="filter.size" v-model:current-page="filter.page" @current-change="load" />
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { api, pj } from '../../api';
const ACTIONS = { create: '新建', update: '修改', delete: '删除', submit_check: '提交校验', approve: '审核通过', reject: '驳回', publish: '发布', disable: '停用', run: '执行', call: '调用', enable: '启用', start_change: '发起变更' };
const rows = ref([]); const total = ref(0); const loading = ref(false);
const filter = ref({ module: '', action: '', keyword: '', page: 1, size: 20 });
const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-';
async function load() {
  loading.value = true;
  try { const d = await api.governance.auditLogs(filter.value); rows.value = d.list; total.value = d.total; }
  finally { loading.value = false; }
}
onMounted(load);
</script>
