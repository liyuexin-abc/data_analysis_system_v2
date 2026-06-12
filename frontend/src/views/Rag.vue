<template>
  <div class="kp-page">
    <div class="kp-page-title">RAG知识库</div>
    <div class="kp-page-desc">管理制度、报告、FAQ、案例文档，支持解析、切片、向量化与检索测试</div>
    <div class="kp-card" style="margin-bottom:14px">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <el-select v-model="filter.doc_type" placeholder="文档类型" clearable style="width:120px" @change="load">
          <el-option label="制度" value="regulation" /><el-option label="报告" value="report" /><el-option label="FAQ" value="faq" /><el-option label="案例" value="case" />
        </el-select>
        <el-input v-model="filter.keyword" placeholder="搜索文档" clearable style="width:200px" @change="load" />
        <div style="flex:1"></div>
        <el-input v-model="ragQ" placeholder="RAG 检索测试: 输入问题" style="width:300px" @keyup.enter="ragTest" />
        <el-button plain :loading="ragLoading" @click="ragTest">检索问答</el-button>
        <el-button type="primary" @click="openEdit()">上传文档</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="name" label="文档名称" min-width="220" show-overflow-tooltip />
        <el-table-column label="类型" width="70"><template #default="{row}"><el-tag size="small" effect="plain">{{ {regulation:'制度',report:'报告',faq:'FAQ',case:'案例'}[row.doc_type] }}</el-tag></template></el-table-column>
        <el-table-column label="密级" width="70"><template #default="{row}"><SecurityTag :level="row.security_level" /></template></el-table-column>
        <el-table-column prop="uploader" label="上传人" width="90" />
        <el-table-column label="解析" width="70"><template #default="{row}"><el-tag size="small" :type="row.parse_status==='parsed'?'success':row.parse_status==='failed'?'danger':'info'">{{ {parsed:'成功',failed:'失败',pending:'未解析',parsing:'解析中'}[row.parse_status] }}</el-tag></template></el-table-column>
        <el-table-column label="切片" width="64" align="center"><template #default="{row}">{{ row.chunk_count }}</template></el-table-column>
        <el-table-column label="向量化" width="76"><template #default="{row}"><el-tag size="small" :type="row.vector_status==='vectorized'?'success':row.vector_status==='failed'?'danger':'info'">{{ {vectorized:'成功',failed:'失败',pending:'未向量化',vectorizing:'进行中'}[row.vector_status] }}</el-tag></template></el-table-column>
        <el-table-column prop="ref_count" label="引用" width="60" align="center" />
        <el-table-column label="状态" width="86"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="{row}">
            <el-button size="small" type="primary" plain :loading="processingId===row.id" @click="processAll(row)">解析+向量化</el-button>
            <el-button size="small" plain @click="showChunks(row)">切片</el-button>
            <LifecycleActions :status="row.status" :api="api.documents" :id="row.id" @done="load" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="kp-card" v-if="ragResult">
      <div style="font-weight:600;margin-bottom:8px">RAG 问答结果</div>
      <div style="white-space:pre-wrap;font-size:13px;line-height:1.7;background:#fbfdff;padding:14px;border-radius:8px;border:1px solid #eef2f7">{{ ragResult.answer }}</div>
      <div style="margin-top:10px">
        <span style="font-size:13px;color:#64748b">引用来源: </span>
        <el-tag v-for="r in ragResult.references" :key="r.chunk_index+'-'+r.doc_id" size="small" style="margin-right:6px">{{ r.doc_name }} ({{ r.score }})</el-tag>
      </div>
    </div>

    <el-dialog v-model="editVisible" title="上传文档" width="640px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="文档名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="文档类型">
          <el-select v-model="form.doc_type" style="width:100%"><el-option label="制度" value="regulation" /><el-option label="报告" value="report" /><el-option label="FAQ" value="faq" /><el-option label="案例" value="case" /></el-select>
        </el-form-item>
        <el-form-item label="密级">
          <el-select v-model="form.security_level" style="width:100%"><el-option label="普通" value="normal" /><el-option label="敏感" value="sensitive" /><el-option label="机密" value="confidential" /></el-select>
        </el-form-item>
        <el-form-item label="文档内容" required><el-input v-model="form.content" type="textarea" :rows="10" placeholder="粘贴文档文本内容" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>

    <el-drawer v-model="chunksVisible" title="文档切片" size="540px">
      <div v-for="c in chunks" :key="c.id" style="border:1px solid #eef2f7;border-radius:8px;padding:10px;margin-bottom:10px;font-size:13px">
        <div style="color:#94a3b8;font-size:11px;margin-bottom:4px">切片 #{{ c.chunk_index }} · {{ c.token_count }} tokens · <span class="mono">{{ c.vector_id || '未向量化' }}</span></div>
        <div style="white-space:pre-wrap">{{ c.content }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { api } from '../api';
import StatusTag from '../components/StatusTag.vue';
import SecurityTag from '../components/SecurityTag.vue';
import LifecycleActions from '../components/LifecycleActions.vue';

const rows = ref([]); const loading = ref(false);
const filter = ref({ doc_type: '', keyword: '', size: 50 });
const editVisible = ref(false); const form = ref({});
const chunksVisible = ref(false); const chunks = ref([]);
const processingId = ref(null);
const ragQ = ref(''); const ragResult = ref(null); const ragLoading = ref(false);

async function load() {
  loading.value = true;
  try { rows.value = (await api.documents.list(filter.value)).list; }
  finally { loading.value = false; }
}
function openEdit() {
  form.value = { name: '', doc_type: 'regulation', security_level: 'normal', content: '', uploader: '知识管理员', scenes: ['经营分析'], visible_roles: ['全体业务用户'] };
  editVisible.value = true;
}
async function save() {
  if (!form.value.name || !form.value.content) return ElMessage.warning('请填写名称和内容');
  await api.documents.create(form.value);
  ElMessage.success('上传成功，请执行解析+向量化'); editVisible.value = false; load();
}
async function processAll(row) {
  processingId.value = row.id;
  try {
    const r = await api.documents.processAll(row.id);
    ElMessage.success(`处理完成: ${r.chunks} 切片，${r.vectorized} 向量`);
    load();
  } finally { processingId.value = null; }
}
async function showChunks(row) { chunks.value = await api.documents.chunks(row.id); chunksVisible.value = true; }
async function ragTest() {
  if (!ragQ.value) return;
  ragLoading.value = true;
  try { ragResult.value = await api.ai.ragAnswer({ question: ragQ.value }); }
  finally { ragLoading.value = false; }
}
onMounted(load);
</script>
