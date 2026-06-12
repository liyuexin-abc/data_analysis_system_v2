<template>
  <div class="kp-page">
    <div class="kp-page-title">动作与函数管理</div>
    <div class="kp-page-desc">本体动作(Action)支撑业务闭环操作；函数(Function)提供可计算能力</div>
    <el-row :gutter="14">
      <el-col :span="13">
        <div class="kp-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:10px">
            <span style="font-weight:600">动作 Action</span>
            <el-button size="small" type="primary" plain @click="openActionEdit()">新建动作</el-button>
          </div>
          <el-table :data="actions" size="small" v-loading="loadingA">
            <el-table-column prop="code" label="编码" width="160"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
            <el-table-column prop="name" label="名称" width="110" />
            <el-table-column prop="object_code" label="适用对象" width="140"><template #default="{row}"><span class="mono">{{ row.object_code || '通用' }}</span></template></el-table-column>
            <el-table-column prop="action_type" label="类型" width="80">
              <template #default="{row}"><el-tag size="small" effect="plain">{{ {business:'业务',system:'系统',notify:'通知'}[row.action_type] }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="description" label="说明" show-overflow-tooltip />
            <el-table-column label="操作" width="110">
              <template #default="{row}">
                <el-button size="small" link type="primary" @click="openActionEdit(row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="removeAction(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="11">
        <div class="kp-card">
          <div style="font-weight:600;margin-bottom:10px">函数 Function</div>
          <el-table :data="functions" size="small" v-loading="loadingF">
            <el-table-column prop="code" label="编码" width="180"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
            <el-table-column prop="name" label="名称" width="110" />
            <el-table-column prop="return_type" label="返回" width="70" />
            <el-table-column prop="expression" label="表达式" show-overflow-tooltip />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="actionVisible" :title="actionForm.id?'编辑动作':'新建动作'" width="520px">
      <el-form :model="actionForm" label-width="90px">
        <el-form-item label="动作编码" required><el-input v-model="actionForm.code" :disabled="!!actionForm.id" placeholder="Act_Xxx" /></el-form-item>
        <el-form-item label="动作名称" required><el-input v-model="actionForm.name" /></el-form-item>
        <el-form-item label="适用对象">
          <el-select v-model="actionForm.object_code" clearable style="width:100%" filterable>
            <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="动作类型">
          <el-select v-model="actionForm.action_type" style="width:100%">
            <el-option label="业务动作" value="business" /><el-option label="系统动作" value="system" /><el-option label="通知动作" value="notify" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明"><el-input v-model="actionForm.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionVisible=false">取消</el-button>
        <el-button type="primary" @click="saveAction">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api } from '../../api';

const actions = ref([]); const functions = ref([]); const objects = ref([]);
const loadingA = ref(false); const loadingF = ref(false);
const actionVisible = ref(false); const actionForm = ref({});

async function load() {
  loadingA.value = loadingF.value = true;
  try {
    const [a, f] = await Promise.all([api.actions.list({ size: 100 }), api.functions.list({ size: 100 })]);
    actions.value = a.list; functions.value = f.list;
  } finally { loadingA.value = loadingF.value = false; }
}
function openActionEdit(row) {
  actionForm.value = row ? { ...row } : { code: '', name: '', object_code: '', action_type: 'business', description: '' };
  actionVisible.value = true;
}
async function saveAction() {
  const f = actionForm.value;
  if (!f.code || !f.name) return ElMessage.warning('请填写编码和名称');
  if (f.id) await api.actions.update(f.id, f); else await api.actions.create(f);
  ElMessage.success('保存成功'); actionVisible.value = false; load();
}
async function removeAction(row) {
  try {
    await ElMessageBox.confirm(`确认删除动作 ${row.name}?`, '提示', { type: 'warning' });
    await api.actions.remove(row.id);
    ElMessage.success('已删除'); load();
  } catch { /* */ }
}
onMounted(async () => {
  const d = await api.objects.list({ size: 100 });
  objects.value = d.list;
  load();
});
</script>
