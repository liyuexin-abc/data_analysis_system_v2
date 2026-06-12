<template>
  <div class="kp-page">
    <div class="kp-page-title">指标语义</div>
    <div class="kp-page-desc">管理指标业务含义、公式解释、对象绑定、维度、解释模板与权限标签</div>
    <el-row :gutter="14">
      <el-col :span="10">
        <div class="kp-card">
          <div style="display:flex;gap:8px;margin-bottom:10px">
            <el-input v-model="filter.keyword" placeholder="搜索指标" clearable style="flex:1" @change="load" />
            <el-button type="primary" @click="openEdit()">新建</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" size="small" highlight-current-row @current-change="r=>current=r" max-height="620">
            <el-table-column prop="metric_name" label="指标" width="100" />
            <el-table-column prop="metric_code" label="编码" min-width="140"><template #default="{row}"><span class="mono">{{ row.metric_code }}</span></template></el-table-column>
            <el-table-column prop="category" label="分类" width="80" />
            <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="kp-card" v-if="current">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <div><span style="font-size:16px;font-weight:600">{{ current.metric_name }}</span>
              <span class="mono" style="margin-left:8px">{{ current.metric_code }}</span>
              <SecurityTag :level="current.security_level" style="margin-left:6px" />
              <el-tag size="small" effect="plain" style="margin-left:4px">{{ current.version }}</el-tag>
            </div>
            <div>
              <el-button size="small" plain @click="openEdit(current)">编辑</el-button>
              <el-button size="small" plain @click="showRefs">查看引用</el-button>
              <LifecycleActions :status="current.status" :api="api.metrics" :id="current.id" @done="load" />
            </div>
          </div>
          <el-tabs>
            <el-tab-pane label="口径与公式">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="业务定义">{{ current.business_def }}</el-descriptions-item>
                <el-descriptions-item label="公式说明">{{ current.formula_desc }}</el-descriptions-item>
                <el-descriptions-item label="同义词"><el-tag v-for="s in pj(current.synonyms,[])" :key="s" size="small" style="margin-right:4px">{{ s }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="统计周期">{{ pj(current.stat_periods,[]).join('、') }}</el-descriptions-item>
                <el-descriptions-item label="单位">{{ current.unit }}</el-descriptions-item>
                <el-descriptions-item label="解释模板">{{ current.answer_template || '-' }}</el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>
            <el-tab-pane label="对象与维度">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="绑定对象"><el-tag v-for="o in pj(current.bind_objects,[])" :key="o" size="small" type="success" style="margin-right:4px">{{ o }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="适用维度"><el-tag v-for="d in pj(current.dimensions,[])" :key="d" size="small" effect="plain" style="margin-right:4px">{{ d }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="推荐图表">{{ pj(current.charts,[]).join('、') }}</el-descriptions-item>
                <el-descriptions-item label="默认对比">{{ pj(current.default_compare,[]).join('、') }}</el-descriptions-item>
                <el-descriptions-item label="归因路径"><span class="mono">{{ current.attribution_path || '-' }}</span></el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>
            <el-tab-pane label="数据预览">
              <div ref="dataChart" style="height:280px"></div>
              <el-button size="small" plain @click="loadData">加载集团数据</el-button>
            </el-tab-pane>
            <el-tab-pane label="测试问数">
              <el-input v-model="testQ" placeholder="输入示例问题，如: 今年利润怎么样" style="margin-bottom:10px">
                <template #append><el-button @click="testParse">解析</el-button></template>
              </el-input>
              <pre v-if="parseResult" style="background:#f8fafc;padding:10px;border-radius:6px;font-size:12px;max-height:340px;overflow:auto">{{ JSON.stringify(parseResult, null, 2) }}</pre>
            </el-tab-pane>
          </el-tabs>
        </div>
        <el-empty v-else description="选择左侧指标查看语义详情" />
      </el-col>
    </el-row>

    <el-dialog v-model="editVisible" :title="form.id?'编辑指标语义':'新建指标语义'" width="640px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="指标编码" required><el-input v-model="form.metric_code" :disabled="!!form.id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="指标名称" required><el-input v-model="form.metric_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="分类"><el-input v-model="form.category" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="安全等级">
            <el-select v-model="form.security_level" style="width:100%"><el-option label="普通" value="normal" /><el-option label="敏感" value="sensitive" /><el-option label="机密" value="confidential" /></el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="业务定义" required><el-input v-model="form.business_def" type="textarea" :rows="2" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="公式说明" required><el-input v-model="form.formula_desc" type="textarea" :rows="2" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="同义词"><el-select v-model="form.synonyms" multiple filterable allow-create style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="绑定对象" required>
            <el-select v-model="form.bind_objects" multiple style="width:100%"><el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" /></el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用维度">
            <el-select v-model="form.dimensions" multiple style="width:100%"><el-option v-for="d in ['org','time','customer','product']" :key="d" :label="d" :value="d" /></el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="解释模板"><el-input v-model="form.answer_template" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>

    <el-drawer v-model="refsVisible" title="指标引用分析" size="460px">
      <el-table :data="refs" size="small">
        <el-table-column prop="type" label="类型" width="100" /><el-table-column prop="name" label="名称" width="120" /><el-table-column prop="detail" label="说明" />
      </el-table>
      <el-empty v-if="!refs.length" description="无引用" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { api, pj } from '../api';
import StatusTag from '../components/StatusTag.vue';
import SecurityTag from '../components/SecurityTag.vue';
import LifecycleActions from '../components/LifecycleActions.vue';

const rows = ref([]); const loading = ref(false); const current = ref(null);
const filter = ref({ keyword: '', size: 100 });
const editVisible = ref(false); const form = ref({}); const objects = ref([]);
const refsVisible = ref(false); const refs = ref([]);
const dataChart = ref(); const testQ = ref(''); const parseResult = ref(null);

async function load() {
  loading.value = true;
  try { rows.value = (await api.metrics.list(filter.value)).list; }
  finally { loading.value = false; }
}
function openEdit(row) {
  form.value = row ? { ...row, synonyms: pj(row.synonyms, []), bind_objects: pj(row.bind_objects, []), dimensions: pj(row.dimensions, []) }
    : { metric_code: '', metric_name: '', category: '经营指标', business_def: '', formula_desc: '', synonyms: [], bind_objects: [], dimensions: ['org', 'time'], security_level: 'normal', answer_template: '' };
  editVisible.value = true;
}
async function save() {
  const f = form.value;
  if (!f.metric_code || !f.metric_name || !f.business_def) return ElMessage.warning('请填写必填项');
  const payload = { ...f };
  ['stat_periods', 'charts', 'default_compare'].forEach(k => { if (typeof payload[k] === 'string') payload[k] = pj(payload[k], []); });
  if (f.id) await api.metrics.update(f.id, payload); else await api.metrics.create(payload);
  ElMessage.success('保存成功'); editVisible.value = false; load();
}
async function showRefs() { refs.value = await api.metrics.references(current.value.id); refsVisible.value = true; }
async function loadData() {
  const data = await api.metrics.data(current.value.metric_code, { org_id: 'ORG_GROUP', periods: 12 });
  await nextTick();
  echarts.init(dataChart.value).setOption({
    tooltip: { trigger: 'axis' }, grid: { left: 70, right: 20, top: 30, bottom: 30 },
    legend: { data: ['实际', '预算'] },
    xAxis: { type: 'category', data: data.map(d => d.period) },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef2f7' } } },
    series: [
      { name: '实际', type: 'line', smooth: true, data: data.map(d => d.value), itemStyle: { color: '#2563eb' }, areaStyle: { opacity: 0.08 } },
      { name: '预算', type: 'line', smooth: true, data: data.map(d => d.budget), itemStyle: { color: '#94a3b8' }, lineStyle: { type: 'dashed' } },
    ],
  });
}
async function testParse() { if (testQ.value) parseResult.value = await api.ai.parse(testQ.value); }
onMounted(async () => { objects.value = (await api.objects.list({ size: 100 })).list; load(); });
</script>
