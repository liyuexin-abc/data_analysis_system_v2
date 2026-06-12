<template>
  <div class="kp-page">
    <div class="kp-page-title">关系管理</div>
    <div class="kp-page-desc">配置对象之间的业务关系，支撑图谱、下钻、问数路径规划</div>
    <div class="kp-card">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <el-select v-model="filter.source_object" placeholder="源对象" clearable style="width:160px" @change="load">
          <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
        </el-select>
        <el-select v-model="filter.status" placeholder="状态" clearable style="width:110px" @change="load">
          <el-option v-for="(v,k) in STATUS_MAP" :key="k" :label="v.label" :value="k" />
        </el-select>
        <el-input v-model="filter.keyword" placeholder="关键词" clearable style="width:160px" @change="load" />
        <div style="flex:1"></div>
        <el-button type="primary" @click="openEdit()">新建关系</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" stripe @row-click="selectRow">
        <el-table-column prop="code" label="关系编码" min-width="200"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
        <el-table-column prop="name" label="关系名称" width="140" />
        <el-table-column label="源→目标" min-width="190">
          <template #default="{row}">
            {{ row.source_name }} <el-icon style="vertical-align:-2px;color:#2563eb"><Right /></el-icon> {{ row.target_name }}
          </template>
        </el-table-column>
        <el-table-column prop="cardinality" label="基数" width="60" align="center" />
        <el-table-column label="方向" width="60" align="center"><template #default="{row}">{{ row.direction==='directed'?'单向':'双向' }}</template></el-table-column>
        <el-table-column label="下钻" width="56" align="center"><template #default="{row}"><el-tag size="small" :type="row.drillable?'success':'info'">{{ row.drillable?'是':'否' }}</el-tag></template></el-table-column>
        <el-table-column label="入图" width="56" align="center"><template #default="{row}"><el-tag size="small" :type="row.in_graph?'success':'info'">{{ row.in_graph?'是':'否' }}</el-tag></template></el-table-column>
        <el-table-column label="权限策略" width="90"><template #default="{row}">{{ {source:'继承源',target:'继承目标',independent:'独立'}[row.perm_inherit] }}</template></el-table-column>
        <el-table-column label="状态" width="90"><template #default="{row}"><StatusTag :status="row.status" /></template></el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{row}">
            <el-button size="small" plain @click.stop="openEdit(row)">编辑</el-button>
            <LifecycleActions :status="row.status" :api="api.links" :id="row.id" @done="load" />
          </template>
        </el-table-column>
      </el-table>

      <!-- 关系路径预览 -->
      <div style="margin-top:16px;border-top:1px dashed #e6ecf5;padding-top:12px">
        <div style="font-weight:600;margin-bottom:8px">关系路径预览
          <el-select v-model="previewObj" placeholder="选择起点对象" size="small" style="width:170px;margin-left:10px" @change="loadPaths">
            <el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" />
          </el-select>
        </div>
        <div v-if="paths.length" style="display:flex;flex-direction:column;gap:6px;max-height:220px;overflow:auto">
          <div v-for="(p,i) in paths" :key="i" style="display:flex;align-items:center;gap:4px;font-size:13px">
            <template v-for="(n,j) in p.nodes" :key="j">
              <el-tag size="small" :effect="j===0?'dark':'plain'">{{ n.name }}</el-tag>
              <el-icon v-if="j<p.nodes.length-1" color="#94a3b8"><Right /></el-icon>
            </template>
            <span style="color:#94a3b8;margin-left:8px">({{ p.links.join(' / ') }})</span>
          </div>
        </div>
        <el-empty v-else description="选择起点对象查看可达路径" :image-size="50" />
      </div>
    </div>

    <el-dialog v-model="editVisible" :title="form.id?'编辑关系':'新建关系'" width="640px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="关系编码" required><el-input v-model="form.code" :disabled="!!form.id" placeholder="Link_X_Has_Y" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关系名称" required><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="源对象" required>
            <el-select v-model="form.source_object" style="width:100%" filterable><el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" /></el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="目标对象" required>
            <el-select v-model="form.target_object" style="width:100%" filterable><el-option v-for="o in objects" :key="o.code" :label="o.name" :value="o.code" /></el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="源关联字段" required><el-input v-model="form.source_field" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="目标关联字段" required><el-input v-model="form.target_field" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="关系方向">
            <el-select v-model="form.direction" style="width:100%"><el-option label="单向" value="directed" /><el-option label="双向" value="bidirectional" /></el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="关系基数">
            <el-select v-model="form.cardinality" style="width:100%"><el-option v-for="c in ['1:1','1:N','N:1','N:N']" :key="c" :label="c" :value="c" /></el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="关系权重"><el-input-number v-model="form.weight" :min="0" :step="0.1" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="支持下钻"><el-switch v-model="form.drillable" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="进入图谱"><el-switch v-model="form.in_graph" :active-value="1" :inactive-value="0" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="权限继承">
            <el-select v-model="form.perm_inherit" style="width:100%">
              <el-option label="继承源对象" value="source" /><el-option label="继承目标对象" value="target" /><el-option label="独立配置" value="independent" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="关系说明" required><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
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
import { api, STATUS_MAP } from '../../api';
import StatusTag from '../../components/StatusTag.vue';
import LifecycleActions from '../../components/LifecycleActions.vue';

const rows = ref([]); const loading = ref(false);
const objects = ref([]);
const filter = ref({ source_object: '', status: '', keyword: '' });
const editVisible = ref(false); const form = ref({});
const previewObj = ref(''); const paths = ref([]);

async function load() {
  loading.value = true;
  try {
    const data = await api.links.list({ ...filter.value, size: 100 });
    rows.value = data.list;
  } finally { loading.value = false; }
}
function openEdit(row) {
  form.value = row ? { ...row } : {
    code: '', name: '', source_object: '', target_object: '', source_field: '', target_field: '',
    direction: 'directed', cardinality: '1:N', weight: 1.0, drillable: 1, in_graph: 1,
    perm_inherit: 'source', description: '',
  };
  editVisible.value = true;
}
async function save() {
  const f = form.value;
  if (!f.code || !f.name || !f.source_object || !f.target_object || !f.source_field || !f.target_field || !f.description) {
    return ElMessage.warning('请填写所有必填字段');
  }
  const payload = { ...f };
  delete payload.source_name; delete payload.target_name;
  if (f.id) await api.links.update(f.id, payload); else await api.links.create(payload);
  ElMessage.success('保存成功'); editVisible.value = false; load();
}
function selectRow(row) { previewObj.value = row.source_object; loadPaths(); }
async function loadPaths() {
  if (!previewObj.value) return;
  paths.value = await api.links.pathPreview(previewObj.value);
}
onMounted(async () => {
  const d = await api.objects.list({ size: 100 });
  objects.value = d.list;
  load();
});
</script>
