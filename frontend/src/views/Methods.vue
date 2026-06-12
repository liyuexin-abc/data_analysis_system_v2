<template>
  <div class="kp-page">
    <div class="kp-page-title">分析方法论</div>
    <div class="kp-page-desc">配置归因路径、指标拆解树、分析步骤、输出模板，供 Skill 调用</div>
    <el-row :gutter="14">
      <el-col :span="9">
        <div class="kp-card">
          <el-table :data="rows" v-loading="loading" size="small" highlight-current-row @current-change="r=>{current=r;testResult=null}">
            <el-table-column prop="name" label="方法名称" min-width="140" />
            <el-table-column prop="code" label="编码" min-width="160"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
            <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="15">
        <div class="kp-card" v-if="current">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <div><span style="font-size:16px;font-weight:600">{{ current.name }}</span><span class="mono" style="margin-left:8px">{{ current.code }}</span></div>
            <LifecycleActions :status="current.status" :api="api.methods" :id="current.id" @done="load" />
          </div>
          <el-tabs>
            <el-tab-pane label="分析步骤">
              <el-steps direction="vertical" :active="99" style="max-height:380px;overflow:auto">
                <el-step v-for="s in pj(current.steps,[])" :key="s.seq" :title="`${s.seq}. ${s.name}`" :description="s.desc" status="process" />
              </el-steps>
            </el-tab-pane>
            <el-tab-pane label="指标拆解树">
              <el-tree v-if="treeData.length" :data="treeData" default-expand-all
                :props="{label:'label',children:'children'}" />
              <el-empty v-else description="该方法论无拆解树" :image-size="60" />
            </el-tab-pane>
            <el-tab-pane label="图谱路径">
              <div v-for="(p,i) in pj(current.graph_paths,[])" :key="i" style="margin-bottom:12px">
                <div style="font-size:13px;font-weight:600;margin-bottom:6px">{{ p.name }}</div>
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
                  <template v-for="(n,j) in p.path" :key="j">
                    <el-tag :effect="j===0?'dark':'plain'">{{ objName(n) }}</el-tag>
                    <el-icon v-if="j<p.path.length-1" color="#2563eb"><Right /></el-icon>
                  </template>
                </div>
              </div>
              <el-descriptions :column="1" border size="small" style="margin-top:10px">
                <el-descriptions-item label="贡献度算法">{{ current.contribution_algo || '-' }}</el-descriptions-item>
                <el-descriptions-item label="输出模板">{{ current.output_template || '-' }}</el-descriptions-item>
                <el-descriptions-item label="绑定Skill">{{ pj(current.bind_skills,[]).join('、') }}</el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>
            <el-tab-pane label="方法论测试">
              <el-form inline>
                <el-form-item label="分析对象">
                  <el-select v-model="testOrg" style="width:200px">
                    <el-option v-for="o in orgs" :key="o.org_id" :label="o.org_name" :value="o.org_id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="对比"><el-select v-model="testCompare" style="width:90px"><el-option label="环比" value="mom" /><el-option label="同比" value="yoy" /></el-select></el-form-item>
                <el-form-item><el-button type="primary" :loading="testing" @click="runTest">执行测试</el-button></el-form-item>
              </el-form>
              <div v-if="testResult">
                <el-alert :type="testResult.validation?.has_data?'success':'warning'" :closable="false" style="margin:8px 0"
                  :title="testResult.validation?.has_data ? '测试通过：方法论可正常执行' : '校验失败: ' + (testResult.validation?.missing||'')" />
                <pre style="background:#f8fafc;padding:10px;border-radius:6px;font-size:12px;max-height:320px;overflow:auto">{{ JSON.stringify(testResult.result, null, 2) }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
        <el-empty v-else description="选择左侧方法论查看详情" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { api, pj } from '../api';
import StatusTag from '../components/StatusTag.vue';
import LifecycleActions from '../components/LifecycleActions.vue';

const rows = ref([]); const loading = ref(false); const current = ref(null);
const objects = ref([]); const orgs = ref([]);
const testOrg = ref('ORG_3521'); const testCompare = ref('mom');
const testing = ref(false); const testResult = ref(null);

const objName = (c) => objects.value.find(o => o.code === c)?.name || c;
const treeData = computed(() => {
  const t = pj(current.value?.decompose_tree, null);
  if (!t) return [];
  const conv = (n) => ({ label: `${n.op ? n.op + ' ' : ''}${n.name} (${n.code})`, children: (n.children || []).map(conv) });
  return [conv(t)];
});
async function load() {
  loading.value = true;
  try { rows.value = (await api.methods.list({ size: 50 })).list; }
  finally { loading.value = false; }
}
async function runTest() {
  testing.value = true;
  try { testResult.value = await api.ai.methodTest({ method_code: current.value.code, org_id: testOrg.value, compare: testCompare.value }); }
  finally { testing.value = false; }
}
onMounted(async () => {
  const [o, g] = await Promise.all([api.objects.list({ size: 100 }), api.biz.orgs()]);
  objects.value = o.list; orgs.value = g.filter(x => x.org_level <= 3);
  load();
});
</script>
