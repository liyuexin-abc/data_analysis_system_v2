<template>
  <div class="kp-page">
    <div class="kp-page-title">影响分析(知识)</div>
    <div class="kp-page-desc">变更知识对象前，分析其被指标、规则、页面、Skill 引用情况</div>
    <div class="kp-card">
      <el-form inline style="margin-bottom:8px">
        <el-form-item label="知识类型">
          <el-select v-model="type" style="width:140px" @change="code=''">
            <el-option label="本体对象" value="object" /><el-option label="对象属性" value="property" />
            <el-option label="对象关系" value="link" /><el-option label="指标语义" value="metric" />
            <el-option label="规则语义" value="rule" /><el-option label="分析方法论" value="method" />
            <el-option label="业务域" value="domain" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识编码">
          <el-input v-model="code" style="width:280px" placeholder="如 Obj_Sales_Contract 或 Obj_Sales_Contract.contract_amount" />
        </el-form-item>
        <el-form-item><el-button type="primary" :loading="loading" @click="analyze">分析影响</el-button></el-form-item>
      </el-form>
      <el-alert v-if="analyzed" :type="impacts.length?'warning':'success'" :closable="false" style="margin-bottom:12px"
        :title="impacts.length ? `该知识对象被 ${impacts.length} 处引用，变更前请评估影响` : '该知识对象无引用，可安全变更'" />
      <el-table :data="impacts" v-loading="loading" stripe>
        <el-table-column prop="type" label="影响对象类型" width="130" />
        <el-table-column prop="code" label="编码" width="220"><template #default="{row}"><span class="mono">{{ row.code }}</span></template></el-table-column>
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="detail" label="影响内容" min-width="220" />
      </el-table>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { api } from '../../api';
const type = ref('object'); const code = ref('Obj_Sales_Contract');
const impacts = ref([]); const loading = ref(false); const analyzed = ref(false);
async function analyze() {
  if (!code.value) return ElMessage.warning('请输入知识编码');
  loading.value = true;
  try { impacts.value = await api.governance.impact(type.value, code.value); analyzed.value = true; }
  finally { loading.value = false; }
}
</script>
