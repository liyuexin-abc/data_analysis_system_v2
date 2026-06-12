<template>
  <div class="kp-page">
    <div class="kp-page-title">术语词典</div>
    <div class="kp-page-desc">管理业务术语、同义词、问数表达，提升智能问数理解能力</div>
    <div class="kp-card">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <el-select v-model="filter.term_type" placeholder="术语类型" clearable style="width:130px" @change="load">
          <el-option v-for="(v,k) in TYPE_MAP" :key="k" :label="v" :value="k" />
        </el-select>
        <el-select v-model="filter.status" placeholder="状态" clearable style="width:110px" @change="load">
          <el-option v-for="(v,k) in STATUS_MAP" :key="k" :label="v.label" :value="k" />
        </el-select>
        <el-input v-model="filter.keyword" placeholder="搜索术语/映射" clearable style="width:170px" @change="load" />
        <el-input v-model="testQ" placeholder="术语命中测试: 输入一句话" style="width:240px" @keyup.enter="matchTest" />
        <el-button plain @click="matchTest">命中测试</el-button>
        <div style="flex:1"></div>
        <el-button type="primary" @click="openEdit()">新建术语</el-button>
      </div>
      <el-alert v-if="testResult" type="success" :closable="true" style="margin-bottom:10px" @close="testResult=null">
        <template #title>命中 {{ testResult.length }} 个术语:
          <el-tag v-for="t in testResult" :key="t.term" size="small" style="margin-left:4px">{{ t.term }} → {{ t.map_target_name }}({{ t.confidence }})</el-tag>
        </template>
      </el-alert>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="term" label="术语" width="110" />
        <el-table-column label="类型" width="100"><template #default="{row}"><el-tag size="small" effect="plain">{{ TYPE_MAP[row.term_type]||row.term_type }}</el-tag></template></el-table-column>
        <el-table-column label="标准映射" width="180"><template #default="{row}">{{ row.map_target_name }} <span class="mono">({{ row.map_target }})</span></template></el-table-column>
        <el-table-column prop="confidence" label="置信度" width="76" align="center" />
        <el-table-column prop="hit_count" label="命中" width="66" align="center" />
        <el-table-column prop="correct_count" label="纠错" width="60" align="center" />
        <el-table-column prop="examples" label="示例问法" min-width="150" show-overflow-tooltip />
        <el-table-column prop="disambiguation" label="消歧规则" min-width="150" show-overflow-tooltip />
        <el-table-column label="状态" width="88"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
        <el-table-column label="操作" width="290" fixed="right">
          <template #default="{row}">
            <el-button size="small" plain @click="openEdit(row)">编辑</el-button>
            <LifecycleActions :status="row.status" :api="api.terms" :id="row.id" @done="load" />
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px;justify-content:flex-end" layout="total, prev, pager, next"
        :total="total" :page-size="filter.size" v-model:current-page="filter.page" @current-change="load" />
    </div>

    <el-dialog v-model="editVisible" :title="form.id?'编辑术语':'新建术语'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="术语" required><el-input v-model="form.term" /></el-form-item>
        <el-form-item label="术语类型" required>
          <el-select v-model="form.term_type" style="width:100%"><el-option v-for="(v,k) in TYPE_MAP" :key="k" :label="v" :value="k" /></el-select>
        </el-form-item>
        <el-form-item label="映射类型" required>
          <el-select v-model="form.map_type" style="width:100%">
            <el-option v-for="t in ['metric','object','property','action','rule','time']" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="标准映射" required><el-input v-model="form.map_target" placeholder="目标编码 如 profit_total" /></el-form-item>
        <el-form-item label="映射名称"><el-input v-model="form.map_target_name" /></el-form-item>
        <el-form-item label="置信度"><el-input-number v-model="form.confidence" :min="0" :max="1" :step="0.05" /></el-form-item>
        <el-form-item label="示例问法"><el-input v-model="form.examples" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="消歧规则"><el-input v-model="form.disambiguation" type="textarea" :rows="2" /></el-form-item>
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
import { api, STATUS_MAP } from '../api';
import StatusTag from '../components/StatusTag.vue';
import LifecycleActions from '../components/LifecycleActions.vue';

const TYPE_MAP = { metric_alias: '指标别名', object_alias: '对象别名', property_alias: '属性别名', phrase: '业务短语', time_expr: '时间表达', action_expr: '动作表达', risk_expr: '风险表达' };
const rows = ref([]); const total = ref(0); const loading = ref(false);
const filter = ref({ term_type: '', status: '', keyword: '', page: 1, size: 20 });
const editVisible = ref(false); const form = ref({});
const testQ = ref(''); const testResult = ref(null);

async function load() {
  loading.value = true;
  try { const d = await api.terms.list(filter.value); rows.value = d.list; total.value = d.total; }
  finally { loading.value = false; }
}
function openEdit(row) {
  form.value = row ? { ...row } : { term: '', term_type: 'metric_alias', map_type: 'metric', map_target: '', map_target_name: '', confidence: 0.8, examples: '', disambiguation: '' };
  editVisible.value = true;
}
async function save() {
  const f = form.value;
  if (!f.term || !f.map_target) return ElMessage.warning('请填写术语和标准映射');
  const payload = { ...f }; delete payload.hit_count; delete payload.correct_count;
  if (f.id) await api.terms.update(f.id, payload); else await api.terms.create(payload);
  ElMessage.success('保存成功'); editVisible.value = false; load();
}
async function matchTest() {
  if (!testQ.value) return;
  testResult.value = await api.terms.matchTest(testQ.value);
}
onMounted(load);
</script>
