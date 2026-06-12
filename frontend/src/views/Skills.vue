<template>
  <div class="kp-page">
    <div class="kp-page-title">Skill注册</div>
    <div class="kp-page-desc">Skill 依赖知识声明与知识加载预览 — 知识平台与 Skill 联动机制</div>
    <el-row :gutter="14">
      <el-col :span="12">
        <div class="kp-card">
          <el-table :data="rows" v-loading="loading" highlight-current-row @current-change="select" size="small">
            <el-table-column prop="name" label="Skill" width="160" />
            <el-table-column prop="code" label="编码" min-width="150"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
            <el-table-column prop="call_count" label="调用次数" width="90" align="center" />
            <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="kp-card" v-if="detail">
          <div style="font-weight:600;margin-bottom:10px">{{ detail.skill.name }} — 知识加载预览</div>
          <div style="font-size:13px;color:#64748b;margin-bottom:10px">依赖知识声明:</div>
          <el-descriptions :column="1" border size="small" style="margin-bottom:14px">
            <el-descriptions-item v-for="(v,k) in detail.depend_knowledge" :key="k" :label="k">{{ v }}</el-descriptions-item>
          </el-descriptions>
          <div style="font-size:13px;color:#64748b;margin-bottom:8px">执行时按需加载的知识:</div>
          <div style="display:flex;flex-direction:column;gap:6px;font-size:13px">
            <div v-if="detail.loaded.metrics?.length"><b>指标语义:</b> <el-tag v-for="m in detail.loaded.metrics" :key="m.metric_code" size="small" style="margin-right:4px">{{ m.metric_name }}</el-tag></div>
            <div v-if="detail.loaded.methods?.length"><b>方法论:</b> <el-tag v-for="m in detail.loaded.methods" :key="m.code" size="small" type="success" style="margin-right:4px">{{ m.name }}</el-tag></div>
            <div v-if="detail.loaded.rules?.length"><b>规则:</b> <el-tag v-for="m in detail.loaded.rules" :key="m.code" size="small" type="warning" style="margin-right:4px">{{ m.name }}</el-tag></div>
            <div v-if="detail.loaded.term_count"><b>术语词典:</b> {{ detail.loaded.term_count }} 条已发布术语</div>
            <div v-if="detail.loaded.object_count"><b>本体对象:</b> {{ detail.loaded.object_count }} 个已发布对象</div>
          </div>
        </div>
        <el-empty v-else description="选择左侧 Skill 查看知识依赖" />
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../api';
import StatusTag from '../components/StatusTag.vue';
const rows = ref([]); const loading = ref(false); const detail = ref(null);
async function load() {
  loading.value = true;
  try { rows.value = (await api.skills.list({ size: 50 })).list; } finally { loading.value = false; }
}
async function select(row) { if (row) detail.value = await api.skills.knowledge(row.id); }
onMounted(load);
</script>
