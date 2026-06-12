<template>
  <div class="kp-page">
    <div class="kp-page-title">图谱模型</div>
    <div class="kp-page-desc">配置图谱名称、入图对象、入图关系、权限和同步方式</div>
    <div class="kp-card">
      <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
        <el-button type="primary" @click="openEdit()">新建图谱模型</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="code" label="图谱编码" width="180"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
        <el-table-column prop="name" label="图谱名称" width="160" />
        <el-table-column prop="scene" label="所属场景" width="110" />
        <el-table-column label="入图对象" min-width="200">
          <template #default="{row}">
            <el-tooltip :content="pj(row.include_objects,[]).join(', ')">
              <span>{{ pj(row.include_objects,[]).length }} 个对象</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="入图关系" width="100"><template #default="{row}">{{ pj(row.include_links,[]).length }} 个关系</template></el-table-column>
        <el-table-column label="同步" width="110"><template #default="{row}">{{ {batch:'批量',incremental:'增量',cdc:'CDC'}[row.sync_mode] }}/{{ {daily:'每日',hourly:'每小时',realtime:'实时'}[row.sync_cycle] }}</template></el-table-column>
        <el-table-column label="状态" width="90"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{row}">
            <el-button size="small" plain @click="openEdit(row)">编辑</el-button>
            <LifecycleActions :status="row.status" :api="api.graphModels" :id="row.id" @done="load" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="editVisible" :title="form.id?'编辑图谱模型':'新建图谱模型'" width="640px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="图谱编码" required><el-input v-model="form.code" :disabled="!!form.id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="图谱名称" required><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="所属场景"><el-input v-model="form.scene" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="权限策略">
            <el-select v-model="form.perm_policy" style="width:100%">
              <el-option label="继承本体对象权限" value="inherit_object" /><el-option label="独立配置" value="independent" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="入图对象" required>
            <el-select v-model="form.include_objects" multiple style="width:100%" filterable>
              <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="入图关系" required>
            <el-select v-model="form.include_links" multiple style="width:100%" filterable>
              <el-option v-for="l in links" :key="l.code" :label="l.name" :value="l.code" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="同步方式">
            <el-select v-model="form.sync_mode" style="width:100%">
              <el-option label="批量" value="batch" /><el-option label="增量" value="incremental" /><el-option label="CDC" value="cdc" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="同步周期">
            <el-select v-model="form.sync_cycle" style="width:100%">
              <el-option label="每日" value="daily" /><el-option label="每小时" value="hourly" /><el-option label="实时" value="realtime" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="图谱说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editVisible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { api, pj } from '../../api';
import StatusTag from '../../components/StatusTag.vue';
import LifecycleActions from '../../components/LifecycleActions.vue';

const rows = ref([]); const loading = ref(false);
const objects = ref([]); const links = ref([]);
const editVisible = ref(false); const form = ref({});

async function load() {
  loading.value = true;
  try {
    const d = await api.graphModels.list({ size: 50 });
    rows.value = d.list;
  } finally { loading.value = false; }
}
function openEdit(row) {
  form.value = row
    ? { ...row, include_objects: pj(row.include_objects, []), include_links: pj(row.include_links, []) }
    : { code: '', name: '', scene: '经营分析', include_objects: [], include_links: [], sync_mode: 'batch', sync_cycle: 'daily', perm_policy: 'inherit_object', description: '' };
  editVisible.value = true;
}
async function save() {
  const f = form.value;
  if (!f.code || !f.name || !f.include_objects.length) return ElMessage.warning('请填写必填项并选择入图对象');
  if (f.id) await api.graphModels.update(f.id, f); else await api.graphModels.create(f);
  ElMessage.success('保存成功'); editVisible.value = false; load();
}
onMounted(async () => {
  const [o, l] = await Promise.all([api.objects.list({ size: 100 }), api.links.list({ size: 100 })]);
  objects.value = o.list; links.value = l.list;
  load();
});
</script>
