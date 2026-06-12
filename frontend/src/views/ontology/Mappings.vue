<template>
  <div class="kp-page">
    <div class="kp-page-title">数据映射</div>
    <div class="kp-page-desc">将本体对象和属性映射到底层数据表，并执行映射校验</div>
    <el-row :gutter="14">
      <el-col :span="6">
        <div class="kp-card">
          <div style="font-weight:600;margin-bottom:10px">对象列表</div>
          <el-menu :default-active="currentObj" @select="selectObj">
            <el-menu-item v-for="o in objects" :key="o.code" :index="o.code">
              <span>{{ o.name }}</span><span class="mono" style="margin-left:6px;font-size:11px">{{ o.code }}</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-col>
      <el-col :span="18">
        <div class="kp-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:12px">
            <span style="font-weight:600">{{ currentObjName }} — 数据源字段映射</span>
            <div>
              <el-button size="small" type="primary" plain @click="openEdit()">新增映射</el-button>
              <el-button size="small" type="success" @click="validate" :loading="validating">执行映射校验</el-button>
            </div>
          </div>
          <el-table :data="rows" v-loading="loading" size="small" stripe>
            <el-table-column prop="property_code" label="属性" width="140"><template #default="{row}"><span class="mono">{{ row.property_code }}</span></template></el-table-column>
            <el-table-column prop="data_source" label="数据源" width="110" />
            <el-table-column prop="table_name" label="数据表" width="160"><template #default="{row}"><span class="mono">{{ row.table_name }}</span></template></el-table-column>
            <el-table-column prop="source_field" label="源字段" width="130"><template #default="{row}"><span class="mono">{{ row.source_field }}</span></template></el-table-column>
            <el-table-column prop="transform_rule" label="转换规则" min-width="130" show-overflow-tooltip />
            <el-table-column label="必填" width="56" align="center"><template #default="{row}"><el-tag size="small" :type="row.is_required?'warning':'info'">{{ row.is_required?'是':'否' }}</el-tag></template></el-table-column>
            <el-table-column label="校验状态" width="86">
              <template #default="{row}">
                <el-tag size="small" :type="row.check_status==='passed'?'success':row.check_status==='failed'?'danger':'info'">
                  {{ {passed:'通过',failed:'失败',pending:'待校验'}[row.check_status] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="checked_at" label="最近校验" width="150"><template #default="{row}">{{ fmt(row.checked_at) }}</template></el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{row}">
                <el-button size="small" link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="remove(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 校验结果 -->
          <div v-if="validateResult" style="margin-top:14px;border-top:1px dashed #e6ecf5;padding-top:12px">
            <el-alert :type="validateResult.passed?'success':'error'" :closable="false"
              :title="validateResult.passed ? '映射校验全部通过' : '映射校验存在问题'" style="margin-bottom:10px" />
            <el-table :data="validateResult.results.filter(r=>!r.passed)" size="small" v-if="!validateResult.passed">
              <el-table-column prop="property" label="属性" width="150" />
              <el-table-column prop="property_name" label="名称" width="110" />
              <el-table-column label="问题"><template #default="{row}">{{ row.errors.join('；') }}</template></el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="editVisible" :title="form.id?'编辑映射':'新增映射'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="属性" required>
          <el-select v-model="form.property_code" style="width:100%" filterable :disabled="!!form.id">
            <el-option v-for="p in properties" :key="p.code" :label="`${p.name}(${p.code})`" :value="p.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据源"><el-input v-model="form.data_source" placeholder="经营数据中台" /></el-form-item>
        <el-form-item label="数据表" required><el-input v-model="form.table_name" placeholder="dwd_sales_contract" /></el-form-item>
        <el-form-item label="源字段" required><el-input v-model="form.source_field" /></el-form-item>
        <el-form-item label="转换规则"><el-input v-model="form.transform_rule" placeholder="金额单位转换(元→万元)" /></el-form-item>
        <el-form-item label="是否必填"><el-switch v-model="form.is_required" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api } from '../../api';

const objects = ref([]); const currentObj = ref('');
const rows = ref([]); const loading = ref(false);
const properties = ref([]);
const validating = ref(false); const validateResult = ref(null);
const editVisible = ref(false); const form = ref({});

const currentObjName = computed(() => objects.value.find(o => o.code === currentObj.value)?.name || '');
const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-';

async function selectObj(code) {
  currentObj.value = code;
  validateResult.value = null;
  loading.value = true;
  try {
    const [m, p] = await Promise.all([
      api.mappings.list({ object_code: code, size: 100 }),
      api.properties.list({ object_code: code, size: 100 }),
    ]);
    rows.value = m.list; properties.value = p.list;
  } finally { loading.value = false; }
}
async function validate() {
  validating.value = true;
  try {
    validateResult.value = await api.mappings.validate(currentObj.value);
    selectObj(currentObj.value);
    if (validateResult.value.passed) ElMessage.success('校验全部通过');
  } finally { validating.value = false; }
}
function openEdit(row) {
  form.value = row ? { ...row } : { object_code: currentObj.value, property_code: '', data_source: '经营数据中台', table_name: '', source_field: '', transform_rule: '', is_required: 0 };
  editVisible.value = true;
}
async function save() {
  const f = form.value;
  if (!f.property_code || !f.table_name || !f.source_field) return ElMessage.warning('请填写必填项');
  if (f.id) await api.mappings.update(f.id, f); else await api.mappings.create(f);
  ElMessage.success('保存成功'); editVisible.value = false; selectObj(currentObj.value);
}
async function remove(row) {
  try {
    await ElMessageBox.confirm('确认删除该映射?', '提示', { type: 'warning' });
    await api.mappings.remove(row.id);
    ElMessage.success('已删除'); selectObj(currentObj.value);
  } catch { /* */ }
}
onMounted(async () => {
  const d = await api.objects.list({ size: 100 });
  objects.value = d.list;
  if (objects.value.length) selectObj(objects.value[0].code);
});
</script>
