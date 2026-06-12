<template>
  <el-tag :type="info.type" size="small" effect="plain">{{ info.label }}</el-tag>
</template>
<script setup>
import { computed } from 'vue';
import { SECURITY_MAP } from '../api';
const props = defineProps({ level: String });
const info = computed(() => SECURITY_MAP[props.level] || { label: props.level || '-', type: 'info' });
</script>
