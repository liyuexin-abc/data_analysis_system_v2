<template>
  <div class="kp-page">
    <div class="kp-page-title">审核中心</div>
    <div class="kp-page-desc">集中处理本体、指标语义、规则、方法论、文档的审核事项</div>
    <div class="kp-card">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <el-select v-model="filter.review_status" placeholder="审核状态" clearable style="width:120px" @change="load">
          <el-option label="待审核" value="pending" /><el-option label="已通过" value="approved" /><el-option label="已驳回" value="rejected" />
        </el-select>
      </div>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="review_no" label="审核单号" width="120"><template #default="{row}"><span class="mono">{{ row.review_no }}</span></template></el-table-column>
        <el-table-column label="知识类型" width="90"><template #default="{row}"><el-tag size="small" effect="plain">{{ TYPE_NAMES[row.knowledge_type]||row.knowledge_type }}</el-tag></template></el-table-column>
        <el-table-column prop="knowledge_name" label="知识名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="applicant" label="申请人" width="100" />
        <el-table-column label="变更类型" width="90"><template #default="{row}">{{ {create:'新增',update:'修改',disable:'停用'}[row.change_type] }}</template></el-table-column>
        <el-table-column label="审核状态" width="90">
          <template #default="{row}"><el-tag size="small" :type="{pending:'warning',approved:'success',rejected:'danger'}[row.review_status]">{{ {pending:'待审核',approved:'通过',rejected:'驳回'}[row.review_status] }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="reviewer" label="审核人" width="90" />
        <el-table-column prop="created_at" label="提交时间" width="160"><template #default="{row}">{{ fmt(row.created_at) }}</template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{row}">
            <el-button size="small" plain @click="detail(row)">查看详情</el-button>
            <el-button v-if="row.review_status==='pending'" size="small" type="success" plain @click="approve(row)">通过</el-button>
            <el-button v-if="row.review_status==='pending'" size="small" type="danger" plain @click="reject(row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px;justify-content:flex-end" layout="total, prev, pager, next"
        :total="total" :page-size="filter.size" v-model:current-page="filter.page" @current-change="load" />
    </div>

    <el-drawer v-model="detailVisible" title="审核详情" size="560px">
      <template v-if="detailData">
        <el-descriptions :column="1" border size="small" style="margin-bottom:14px">
          <el-descriptions-item label="单号">{{ detailData.review.review_no }}</el-descriptions-item>
          <el-descriptions-item label="知识">{{ detailData.review.knowledge_name }}</el-descriptions-item>
          <el-descriptions-item label="变更内容"><pre class="mono" style="margin:0;white-space:pre-wrap">{{ JSON.stringify(pj(detailData.review.change_detail,{}), null, 1) }}</pre></el-descriptions-item>
          <el-descriptions-item label="审核意见">{{ detailData.review.review_comment || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div style="font-weight:600;margin-bottom:8px;font-size:13px">影响范围分析</div>
        <el-table :data="detailData.impacts" size="small" style="margin-bottom:14px">
          <el-table-column prop="type" label="类型" width="90" /><el-table-column prop="name" label="名称" width="120" /><el-table-column prop="detail" label="说明" />
        </el-table>
        <div style="font-weight:600;margin-bottom:8px;font-size:13px">历史版本</div>
        <el-timeline>
          <el-timeline-item v-for="v in detailData.versions" :key="v.id" :timestamp="fmt(v.created_at)">
            <el-tag size="small">{{ v.version }}</el-tag> {{ v.change_note }}
          </el-timeline-item>
        </el-timeline>
      </template>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api, pj } from '../../api';
const TYPE_NAMES = { object: '本体对象', link: '关系', metric: '指标语义', term: '术语', rule: '规则', method: '方法论', graph: '图谱', document: '文档', domain: '业务域' };
const rows = ref([]); const total = ref(0); const loading = ref(false);
const filter = ref({ review_status: '', page: 1, size: 20 });
const detailVisible = ref(false); const detailData = ref(null);
const fmt = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-';
async function load() {
  loading.value = true;
  try { const d = await api.governance.reviews(filter.value); rows.value = d.list; total.value = d.total; }
  finally { loading.value = false; }
}
async function detail(row) { detailData.value = await api.governance.reviewDetail(row.id); detailVisible.value = true; }
async function approve(row) {
  try {
    const { value } = await ElMessageBox.prompt('审核意见(可选)', '审核通过', { confirmButtonText: '通过并发布' });
    await api.governance.approve(row.id, { comment: value || '' });
    ElMessage.success('已通过并发布'); load();
  } catch { /* */ }
}
async function reject(row) {
  try {
    const { value } = await ElMessageBox.prompt('驳回原因', '驳回', { confirmButtonText: '驳回', inputValidator: v => !!v || '请填写原因' });
    await api.governance.reject(row.id, { comment: value });
    ElMessage.success('已驳回'); load();
  } catch { /* */ }
}
onMounted(load);
</script>
