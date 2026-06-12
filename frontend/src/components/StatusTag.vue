<template>
  <el-tag :type="info.type" size="small" effect="light">{{ info.label }}</el-tag>
</template>
<script setup>
import { computed } from 'vue';
import { STATUS_MAP } from '../api';
const props = defineProps({ status: String });
const info = computed(() => STATUS_MAP[props.status] || { label: props.status || '-', type: 'info' });
</script>
