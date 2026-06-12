<template>
  <div class="kp-page">
    <div class="kp-page-title">业务域管理</div>
    <div class="kp-page-desc">管理知识平台中的业务域，为对象、指标、规则、方法论提供分类基础</div>
    <div class="kp-card">
      <div style="display:flex;justify-content:space-between;margin-bottom:14px">
        <el-input v-model="keyword" placeholder="搜索编码/名称" clearable style="width:240px" @change="load" />
        <el-button type="primary" @click="openEdit()">新建业务域</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="code" label="业务域编码" width="120"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
        <el-table-column prop="name" label="业务域名称" width="120" />
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="object_count" label="对象数" width="80" align="center" />
        <el-table-column prop="metric_count" label="指标数" width="80" align="center" />
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column label="状态" width="100"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="160"><template #default="{row}">{{ fmt(row.updated_at) }}</template></el-table-column>
        <el-table-column label="操作" width="380" fixed="right">
          <template #default="{row}">
            <el-button size="small" plain @click="openEdit(row)">编辑</el-button>
            <el-button size="small" plain @click="viewObjects(row)">查看对象</el-button>
            <el-button size="small" plain @click="showImpact(row)">影响分析</el-button>
            <LifecycleActions :status="row.status" :api="api.domains" :id="row.id" @done="load" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="editVisible" :title="form.id ? '编辑业务域' : '新建业务域'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="编码" required><el-input v-model="form.code" :disabled="!!form.id" placeholder="如 sales" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="form.name" placeholder="如 销售域" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.owner" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="impactVisible" title="业务域影响分析" size="480px">
      <el-table :data="impacts" size="small">
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="detail" label="影响说明" />
      </el-table>
      <el-empty v-if="!impacts.length" description="无依赖知识对象" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import { api } from '../../api';
import StatusTag from '../../components/StatusTag.vue';
import LifecycleActions from '../../components/LifecycleActions.vue';

const router = useRouter();
const rows = ref([]); const loading = ref(false); const keyword = ref('');
const editVisible = ref(false); const form = ref({});
const impactVisible = ref(false); const impacts = ref([]);

const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '';

async function load() {
  loading.value = true;
  try {
    const data = await api.domains.list({ keyword: keyword.value, size: 100 });
    rows.value = data.list;
  } finally { loading.value = false; }
}
function openEdit(row) { form.value = row ? { ...row } : { code: '', name: '', description: '', owner: '' }; editVisible.value = true; }
async function save() {
  const f = form.value;
  if (!f.code || !f.name) return ElMessage.warning('请填写编码和名称');
  if (f.id) await api.domains.update(f.id, f); else await api.domains.create(f);
  ElMessage.success('保存成功'); editVisible.value = false; load();
}
function viewObjects(row) { router.push({ path: '/ontology/objects', query: { domain: row.code } }); }
async function showImpact(row) {
  impacts.value = await api.ontologyImpact('domain', row.code);
  impactVisible.value = true;
}
onMounted(load);
</script>
