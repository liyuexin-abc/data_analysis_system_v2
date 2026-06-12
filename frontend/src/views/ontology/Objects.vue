<template>
  <div class="kp-page">
    <div class="kp-page-title">对象类型管理</div>
    <div class="kp-page-desc">管理本体对象类型 — Object / Property / Link / Interface / Action / Function / Mapping</div>
    <el-row :gutter="14">
      <!-- 左侧对象列表 -->
      <el-col :span="9">
        <div class="kp-card">
          <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
            <el-select v-model="filter.domain_code" placeholder="业务域" clearable style="width:110px" @change="load">
              <el-option v-for="d in domains" :key="d.code" :label="d.name" :value="d.code" />
            </el-select>
            <el-select v-model="filter.status" placeholder="状态" clearable style="width:100px" @change="load">
              <el-option v-for="(v,k) in STATUS_MAP" :key="k" :label="v.label" :value="k" />
            </el-select>
            <el-input v-model="filter.keyword" placeholder="关键词" clearable style="width:130px" @change="load" />
            <el-button type="primary" @click="openEdit()">新建对象</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" highlight-current-row @current-change="select" size="small" max-height="640">
            <el-table-column prop="name" label="对象" width="90" />
            <el-table-column prop="code" label="编码" min-width="150"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
            <el-table-column prop="domain_code" label="域" width="70" />
            <el-table-column prop="property_count" label="属性" width="55" align="center" />
            <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <!-- 右侧详情 Tabs -->
      <el-col :span="15">
        <div class="kp-card" v-if="detail" v-loading="detailLoading">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <div>
              <span style="font-size:16px;font-weight:600">{{ detail.name }}</span>
              <span class="mono" style="margin-left:8px">{{ detail.code }}</span>
              <StatusTag :status="detail.status" style="margin-left:8px" />
              <SecurityTag :level="detail.security_level" style="margin-left:4px" />
              <el-tag size="small" effect="plain" style="margin-left:4px">{{ detail.version }}</el-tag>
            </div>
            <div>
              <el-button size="small" plain @click="openEdit(detail)">编辑</el-button>
              <el-button size="small" plain @click="copyObject">复制</el-button>
              <el-button size="small" plain @click="showImpact">查看影响</el-button>
              <LifecycleActions :status="detail.status" :api="api.objects" :id="detail.id" @done="reloadAll" />
            </div>
          </div>
          <el-tabs v-model="tab">
            <el-tab-pane label="基本信息" name="basic">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="对象编码">{{ detail.code }}</el-descriptions-item>
                <el-descriptions-item label="对象名称">{{ detail.name }}</el-descriptions-item>
                <el-descriptions-item label="所属业务域">{{ detail.domain_code }}</el-descriptions-item>
                <el-descriptions-item label="主键字段">{{ detail.primary_key }}</el-descriptions-item>
                <el-descriptions-item label="展示字段">{{ detail.display_field }}</el-descriptions-item>
                <el-descriptions-item label="数据权限字段">{{ detail.data_perm_field || '-' }}</el-descriptions-item>
                <el-descriptions-item label="是否入图"><el-tag size="small" :type="detail.in_graph?'success':'info'">{{ detail.in_graph?'是':'否' }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="是否可搜索"><el-tag size="small" :type="detail.searchable?'success':'info'">{{ detail.searchable?'是':'否' }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="是否可监控"><el-tag size="small" :type="detail.monitorable?'success':'info'">{{ detail.monitorable?'是':'否' }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="负责人">{{ detail.owner }}</el-descriptions-item>
                <el-descriptions-item label="对象说明" :span="2">{{ detail.description }}</el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>
            <el-tab-pane :label="`属性(${detail.properties?.length||0})`" name="props">
              <div style="margin-bottom:8px"><el-button size="small" type="primary" plain @click="openPropEdit()">新增属性</el-button></div>
              <el-table :data="detail.properties" size="small" max-height="480">
                <el-table-column prop="code" label="编码" width="130"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
                <el-table-column prop="name" label="名称" width="100" />
                <el-table-column prop="data_type" label="类型" width="70" />
                <el-table-column label="主键" width="50" align="center"><template #default="{row}"><el-icon v-if="row.is_primary" color="#2563eb"><Key /></el-icon></template></el-table-column>
                <el-table-column label="敏感" width="50" align="center"><template #default="{row}"><el-icon v-if="row.is_sensitive" color="#e6a23c"><Lock /></el-icon></template></el-table-column>
                <el-table-column label="聚合" width="50" align="center"><template #default="{row}"><el-icon v-if="row.aggregatable" color="#10b981"><Histogram /></el-icon></template></el-table-column>
                <el-table-column prop="source_field" label="来源字段" min-width="150"><template #default="{row}"><span class="mono">{{ row.source_field || '-' }}</span></template></el-table-column>
                <el-table-column label="操作" width="140" fixed="right">
                  <template #default="{row}">
                    <el-button size="small" link type="primary" @click="openPropEdit(row)">编辑</el-button>
                    <el-button size="small" link type="danger" @click="deleteProp(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="`关系(${detail.links?.length||0})`" name="links">
              <el-table :data="detail.links" size="small">
                <el-table-column prop="name" label="关系名称" min-width="120" />
                <el-table-column label="方向" min-width="180">
                  <template #default="{row}">
                    <span>{{ row.source_name }} <el-icon style="vertical-align:-2px"><Right /></el-icon> {{ row.target_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="cardinality" label="基数" width="60" />
                <el-table-column label="入图" width="60" align="center"><template #default="{row}"><el-tag size="small" :type="row.in_graph?'success':'info'">{{ row.in_graph?'是':'否' }}</el-tag></template></el-table-column>
                <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="`接口(${detail.interfaces?.length||0})`" name="ifs">
              <el-table :data="detail.interfaces" size="small">
                <el-table-column prop="code" label="接口编码" width="150"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
                <el-table-column prop="name" label="接口名称" width="130" />
                <el-table-column prop="description" label="说明" />
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="`动作(${detail.actions?.length||0})`" name="acts">
              <el-table :data="detail.actions" size="small">
                <el-table-column prop="code" label="编码" width="160"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
                <el-table-column prop="name" label="名称" width="120" />
                <el-table-column prop="action_type" label="类型" width="90" />
                <el-table-column prop="description" label="说明" />
              </el-table>
              <el-empty v-if="!detail.actions?.length" description="无关联动作" :image-size="60" />
            </el-tab-pane>
            <el-tab-pane :label="`函数(${detail.functions?.length||0})`" name="fns">
              <el-table :data="detail.functions" size="small">
                <el-table-column prop="code" label="编码" width="180"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
                <el-table-column prop="name" label="名称" width="110" />
                <el-table-column prop="expression" label="表达式" show-overflow-tooltip />
              </el-table>
              <el-empty v-if="!detail.functions?.length" description="无关联函数" :image-size="60" />
            </el-tab-pane>
            <el-tab-pane :label="`数据映射(${detail.mappings?.length||0})`" name="maps">
              <el-table :data="detail.mappings" size="small" max-height="460">
                <el-table-column prop="property_code" label="属性" width="130"><template #default="{row}"><span class="mono">{{ row.property_code }}</span></template></el-table-column>
                <el-table-column prop="table_name" label="数据表" width="150"><template #default="{row}"><span class="mono">{{ row.table_name }}</span></template></el-table-column>
                <el-table-column prop="source_field" label="源字段" width="130"><template #default="{row}"><span class="mono">{{ row.source_field }}</span></template></el-table-column>
                <el-table-column label="校验" width="70">
                  <template #default="{row}">
                    <el-tag size="small" :type="row.check_status==='passed'?'success':row.check_status==='failed'?'danger':'info'">
                      {{ {passed:'通过',failed:'失败',pending:'待校验'}[row.check_status] }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="`指标绑定(${detail.metrics?.length||0})`" name="metrics">
              <el-table :data="detail.metrics" size="small">
                <el-table-column prop="metric_code" label="指标编码" width="180"><template #default="{row}"><span class="mono">{{ row.metric_code }}</span></template></el-table-column>
                <el-table-column prop="metric_name" label="指标名称" width="130" />
                <el-table-column label="状态"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
              </el-table>
              <el-empty v-if="!detail.metrics?.length" description="无绑定指标" :image-size="60" />
            </el-tab-pane>
            <el-tab-pane :label="`版本(${detail.versions?.length||0})`" name="vers">
              <el-timeline>
                <el-timeline-item v-for="v in detail.versions" :key="v.id" :timestamp="fmt(v.created_at)">
                  <el-tag size="small">{{ v.version }}</el-tag> {{ v.change_note }} <span style="color:#94a3b8">by {{ v.operator }}</span>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-if="!detail.versions?.length" description="无版本记录" :image-size="60" />
            </el-tab-pane>
          </el-tabs>
        </div>
        <el-empty v-else description="请选择左侧对象查看详情" />
      </el-col>
    </el-row>

    <!-- 对象编辑弹窗 -->
    <el-dialog v-model="editVisible" :title="form.id?'编辑对象':'新建对象'" width="640px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="对象编码" required><el-input v-model="form.code" :disabled="!!form.id" placeholder="Obj_Sales_Contract" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="对象名称" required><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="所属业务域" required>
            <el-select v-model="form.domain_code" style="width:100%"><el-option v-for="d in domains" :key="d.code" :label="d.name" :value="d.code" /></el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="主键字段" required><el-input v-model="form.primary_key" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="展示字段" required><el-input v-model="form.display_field" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="数据权限字段"><el-input v-model="form.data_perm_field" placeholder="org_id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="安全等级" required>
            <el-select v-model="form.security_level" style="width:100%">
              <el-option label="普通" value="normal" /><el-option label="敏感" value="sensitive" /><el-option label="机密" value="confidential" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="负责人"><el-input v-model="form.owner" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="是否入图"><el-switch v-model="form.in_graph" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="可搜索"><el-switch v-model="form.searchable" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="可监控"><el-switch v-model="form.monitorable" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="对象说明" required><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editVisible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 属性编辑弹窗 -->
    <el-dialog v-model="propVisible" :title="propForm.id?'编辑属性':'新增属性'" width="620px">
      <el-form :model="propForm" label-width="100px">
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="属性编码" required><el-input v-model="propForm.code" :disabled="!!propForm.id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="属性名称" required><el-input v-model="propForm.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="数据类型">
            <el-select v-model="propForm.data_type" style="width:100%">
              <el-option v-for="t in ['string','decimal','int','date','datetime','boolean']" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="来源字段"><el-input v-model="propForm.source_field" placeholder="表名.字段名" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="主键"><el-switch v-model="propForm.is_primary" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="必填"><el-switch v-model="propForm.is_required" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="敏感"><el-switch v-model="propForm.is_sensitive" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="可聚合"><el-switch v-model="propForm.aggregatable" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="可搜索"><el-switch v-model="propForm.searchable" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="可筛选"><el-switch v-model="propForm.filterable" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="默认展示"><el-switch v-model="propForm.default_display" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="权限标签">
            <el-select v-model="propForm.perm_label" style="width:100%">
              <el-option label="普通" value="normal" /><el-option label="敏感" value="sensitive" /><el-option label="机密" value="confidential" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="propVisible=false">取消</el-button>
        <el-button type="primary" @click="saveProp">保存</el-button>
      </template>
    </el-dialog>

    <!-- 影响分析抽屉 -->
    <el-drawer v-model="impactVisible" title="对象影响分析" size="500px">
      <el-alert type="info" :closable="false" style="margin-bottom:12px"
        title="变更或停用该对象前，请确认以下引用方不受影响" />
      <el-table :data="impacts" size="small">
        <el-table-column prop="type" label="类型" width="90" />
        <el-table-column prop="name" label="名称" width="130" />
        <el-table-column prop="detail" label="影响说明" />
      </el-table>
      <el-empty v-if="!impacts.length" description="无引用方" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api, STATUS_MAP } from '../../api';
import StatusTag from '../../components/StatusTag.vue';
import SecurityTag from '../../components/SecurityTag.vue';
import LifecycleActions from '../../components/LifecycleActions.vue';

const route = useRoute();
const rows = ref([]); const loading = ref(false);
const domains = ref([]);
const filter = ref({ domain_code: route.query.domain || '', status: '', keyword: '' });
const detail = ref(null); const detailLoading = ref(false);
const tab = ref('basic');
const editVisible = ref(false); const form = ref({});
const propVisible = ref(false); const propForm = ref({});
const impactVisible = ref(false); const impacts = ref([]);

const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '';

async function load() {
  loading.value = true;
  try {
    const data = await api.objects.list({ ...filter.value, size: 100 });
    rows.value = data.list;
  } finally { loading.value = false; }
}
async function select(row) {
  if (!row) return;
  detailLoading.value = true;
  try { detail.value = await api.objects.full(row.id); } finally { detailLoading.value = false; }
}
async function reloadAll() { await load(); if (detail.value) select({ id: detail.value.id }); }

function openEdit(row) {
  form.value = row ? { ...row } : {
    code: '', name: '', domain_code: filter.value.domain_code || '', description: '',
    primary_key: '', display_field: '', in_graph: 0, searchable: 1, monitorable: 0,
    security_level: 'normal', owner: '',
  };
  editVisible.value = true;
}
async function save() {
  const f = form.value;
  if (!f.code || !f.name || !f.domain_code || !f.primary_key || !f.display_field || !f.description) {
    return ElMessage.warning('请填写所有必填字段');
  }
  const payload = { code: f.code, name: f.name, domain_code: f.domain_code, description: f.description,
    primary_key: f.primary_key, display_field: f.display_field, in_graph: f.in_graph, searchable: f.searchable,
    monitorable: f.monitorable, data_perm_field: f.data_perm_field, security_level: f.security_level, owner: f.owner };
  if (f.id) await api.objects.update(f.id, payload); else await api.objects.create(payload);
  ElMessage.success('保存成功'); editVisible.value = false; reloadAll();
}
async function copyObject() {
  const d = detail.value;
  await api.objects.create({
    code: d.code + '_Copy', name: d.name + '(副本)', domain_code: d.domain_code, description: d.description,
    primary_key: d.primary_key, display_field: d.display_field, in_graph: d.in_graph,
    searchable: d.searchable, monitorable: d.monitorable, security_level: d.security_level, owner: d.owner,
  });
  ElMessage.success('复制成功'); load();
}
function openPropEdit(row) {
  propForm.value = row ? { ...row } : {
    object_code: detail.value.code, code: '', name: '', data_type: 'string',
    is_primary: 0, is_required: 0, is_sensitive: 0, searchable: 0, filterable: 0,
    aggregatable: 0, default_display: 0, perm_label: 'normal', source_field: '',
  };
  propVisible.value = true;
}
async function saveProp() {
  const f = propForm.value;
  if (!f.code || !f.name) return ElMessage.warning('请填写编码和名称');
  if (f.id) await api.properties.update(f.id, f); else await api.properties.create(f);
  ElMessage.success('保存成功'); propVisible.value = false; select({ id: detail.value.id });
}
async function deleteProp(row) {
  // 删除前必须做影响分析 (PRD 13.3)
  const { impacts: imp } = await api.properties.impact(row.id);
  const msg = imp.length
    ? `该属性被 ${imp.length} 处引用:\n` + imp.map(i => `· [${i.type}] ${i.name}`).join('\n') + '\n\n确认删除?'
    : '该属性无引用，确认删除?';
  try {
    await ElMessageBox.confirm(msg, '删除前影响分析', { type: 'warning', confirmButtonText: '确认删除' });
    await api.properties.remove(row.id);
    ElMessage.success('已删除'); select({ id: detail.value.id });
  } catch { /* cancel */ }
}
async function showImpact() {
  impacts.value = await api.ontologyImpact('object', detail.value.code);
  impactVisible.value = true;
}
onMounted(async () => {
  const d = await api.domains.list({ size: 50 });
  domains.value = d.list;
  await load();
  if (rows.value.length) select(rows.value[0]);
});
</script>
