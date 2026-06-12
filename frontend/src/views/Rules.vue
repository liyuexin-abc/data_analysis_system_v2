<template>
  <div class="kp-page">
    <div class="kp-page-title">规则语义</div>
    <div class="kp-page-desc">配置预警规则、风险分级、触发逻辑、处置建议，支持规则试运行</div>
    <el-row :gutter="14">
      <el-col :span="10">
        <div class="kp-card">
          <el-table :data="rows" v-loading="loading" size="small" highlight-current-row @current-change="r=>{current=r;testResult=null}" max-height="640">
            <el-table-column prop="name" label="规则名称" min-width="130" />
            <el-table-column label="类型" width="70"><template #default="{row}"><el-tag size="small" effect="plain">{{ {threshold:'阈值',yoy:'同比',mom:'环比',composite:'组合',forecast:'预测'}[row.rule_type] }}</el-tag></template></el-table-column>
            <el-table-column label="周期" width="66"><template #default="{row}">{{ {realtime:'实时',daily:'每日',monthly:'每月'}[row.run_cycle] }}</template></el-table-column>
            <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="kp-card" v-if="current">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <div><span style="font-size:16px;font-weight:600">{{ current.name }}</span><span class="mono" style="margin-left:8px">{{ current.code }}</span></div>
            <div>
              <el-button size="small" type="primary" plain :loading="testing" @click="testRun">试运行</el-button>
              <LifecycleActions :status="current.status" :api="api.rules" :id="current.id" @done="load" />
            </div>
          </div>
          <el-descriptions :column="2" border size="small" style="margin-bottom:12px">
            <el-descriptions-item label="监控对象"><span class="mono">{{ current.monitor_object }}</span></el-descriptions-item>
            <el-descriptions-item label="监控指标"><span class="mono">{{ current.monitor_metric }}</span></el-descriptions-item>
            <el-descriptions-item label="触发条件" :span="2">
              <span class="mono" style="font-size:12px">{{ condDesc }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="处置建议" :span="2">{{ current.suggestion }}</el-descriptions-item>
            <el-descriptions-item label="通知对象">{{ pj(current.notify_targets,[]).join('、') }}</el-descriptions-item>
            <el-descriptions-item label="推荐Skill">{{ pj(current.skills,[]).join('、') || '-' }}</el-descriptions-item>
          </el-descriptions>
          <div style="font-weight:600;font-size:13px;margin-bottom:8px">风险等级配置</div>
          <el-table :data="pj(current.risk_levels,[])" size="small" style="margin-bottom:12px">
            <el-table-column label="等级" width="80"><template #default="{row}"><el-tag size="small" :color="row.color" style="color:#fff;border:none">{{ {red:'红色',orange:'橙色',yellow:'黄色',blue:'蓝色'}[row.level] }}</el-tag></template></el-table-column>
            <el-table-column prop="condition" label="条件" width="200" />
            <el-table-column prop="suggestion" label="处置建议" />
          </el-table>
          <div v-if="testResult">
            <el-alert type="success" :closable="false" style="margin-bottom:10px"
              :title="`试运行完成: 命中 ${testResult.matched} 条 ` + Object.entries(testResult.by_level||{}).map(([k,v])=>`${ {red:'红',orange:'橙',yellow:'黄',blue:'蓝'}[k]}${v}条`).join(' / ')" />
            <el-table :data="testResult.alerts.slice(0,10)" size="small" max-height="260">
              <el-table-column label="等级" width="60"><template #default="{row}"><el-tag size="small" :color="RISK_COLOR[row.level]" style="color:#fff;border:none">{{ row.level_name }}</el-tag></template></el-table-column>
              <el-table-column prop="target_name" label="对象" min-width="140" show-overflow-tooltip />
              <el-table-column prop="org" label="单位" width="150" show-overflow-tooltip />
              <el-table-column prop="detail" label="明细" min-width="170" show-overflow-tooltip />
            </el-table>
          </div>
        </div>
        <el-empty v-else description="选择左侧规则查看详情" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { api, pj, RISK_COLOR } from '../api';
import StatusTag from '../components/StatusTag.vue';
import LifecycleActions from '../components/LifecycleActions.vue';

const rows = ref([]); const loading = ref(false); const current = ref(null);
const testing = ref(false); const testResult = ref(null);

const condDesc = computed(() => {
  const c = pj(current.value?.trigger_cond, {});
  if (!c.conditions) return '-';
  return (c.logic || 'AND') + ': ' + c.conditions.map(x => x.desc || `${x.field} ${x.op} ${x.value}`).join(' | ');
});
async function load() {
  loading.value = true;
  try { rows.value = (await api.rules.list({ size: 50 })).list; }
  finally { loading.value = false; }
}
async function testRun() {
  testing.value = true;
  try { testResult.value = await api.rules.testRun(current.value.id); }
  finally { testing.value = false; }
}
onMounted(load);
</script>
