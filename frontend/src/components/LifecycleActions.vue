<template>
  <span>
    <el-button v-if="['draft','check_failed','changing'].includes(status)" size="small" type="primary" plain
      @click="run('submit_check')">提交校验</el-button>
    <el-button v-if="status==='pending_review'" size="small" type="success" plain
      @click="run('approve')">审核发布</el-button>
    <el-button v-if="status==='pending_review'" size="small" type="danger" plain
      @click="run('reject')">驳回</el-button>
    <el-button v-if="status==='published'" size="small" type="warning" plain
      @click="run('start_change')">发起变更</el-button>
    <el-button v-if="['published','changing'].includes(status)" size="small" type="info" plain
      @click="run('disable')">停用</el-button>
    <el-button v-if="status==='disabled'" size="small" type="success" plain
      @click="run('enable')">启用</el-button>
  </span>
</template>
<script setup>
import { ElMessage, ElMessageBox } from 'element-plus';
const props = defineProps({ status: String, api: Object, id: [Number, String] });
const emit = defineEmits(['done']);

async function run(action) {
  let comment = '';
  if (['approve', 'reject', 'disable'].includes(action)) {
    try {
      const { value } = await ElMessageBox.prompt('请填写处理意见(可选)', '确认操作', {
        confirmButtonText: '确定', cancelButtonText: '取消', inputPlaceholder: '意见说明',
      });
      comment = value || '';
    } catch { return; }
  }
  try {
    const res = await props.api.lifecycle(props.id, action, { comment });
    if (res.checkErrors && res.checkErrors.length) {
      ElMessage.warning('校验不通过: ' + res.checkErrors.join('；'));
    } else {
      ElMessage.success(`操作成功，当前状态: ${res.statusName}`);
    }
    emit('done');
  } catch { /* handled */ }
}
</script>
