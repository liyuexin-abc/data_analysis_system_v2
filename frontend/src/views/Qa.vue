<template>
  <div class="kp-page" style="display:flex;flex-direction:column;height:calc(100vh - 56px);box-sizing:border-box">
    <div class="kp-page-title">智能问数</div>
    <div class="kp-page-desc">术语匹配 → 语义解析 → 路径规划 → 数据查询 → 方法论分析 → AI 回答(可追溯知识引用)</div>
    <div class="kp-card" style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <el-scrollbar style="flex:1" ref="scrollRef">
        <div style="display:flex;flex-direction:column;gap:14px;padding:6px">
          <div v-if="!messages.length" style="text-align:center;padding:30px 0">
            <div style="color:#64748b;margin-bottom:14px">试试这些问题:</div>
            <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
              <el-tag v-for="q in samples" :key="q" style="cursor:pointer" effect="plain" @click="ask(q)">{{ q }}</el-tag>
            </div>
          </div>
          <template v-for="(m,i) in messages" :key="i">
            <div v-if="m.role==='user'" class="chat-bubble-user">{{ m.content }}</div>
            <div v-else class="chat-bubble-ai">
              <div v-if="m.loading"><el-icon class="is-loading"><Loading /></el-icon> 正在调用知识平台分析...</div>
              <template v-else>
                <div style="white-space:pre-wrap;font-size:13px;line-height:1.75">{{ m.content }}</div>
                <div v-if="m.refs?.length" style="margin-top:10px;border-top:1px dashed #eef2f7;padding-top:8px">
                  <span style="font-size:12px;color:#94a3b8">知识引用: </span>
                  <el-tag v-for="(r,j) in m.refs" :key="j" size="small" effect="plain" style="margin:0 4px 4px 0">[{{ r.type }}] {{ r.name }}</el-tag>
                </div>
                <div style="margin-top:6px;font-size:12px;color:#94a3b8">
                  意图: {{ m.intent }} · 耗时 {{ m.duration }}ms
                  <el-button size="small" link @click="m.showPlan=!m.showPlan">{{ m.showPlan?'收起':'查看' }}执行计划</el-button>
                </div>
                <pre v-if="m.showPlan" style="background:#f8fafc;padding:8px;border-radius:6px;font-size:11px;max-height:240px;overflow:auto">{{ JSON.stringify(m.parse, null, 2) }}</pre>
              </template>
            </div>
          </template>
        </div>
      </el-scrollbar>
      <div style="display:flex;gap:10px;padding-top:12px;border-top:1px solid #eef2f7">
        <el-input v-model="input" placeholder="输入经营分析问题，如: 哪个单位回款风险最高，为什么？" size="large"
          @keyup.enter="ask()" :disabled="asking" />
        <el-button type="primary" size="large" :loading="asking" @click="ask()">提问</el-button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, nextTick } from 'vue';
import { api } from '../api';

const samples = [
  '今年集团利润怎么样', '3521公司利润为什么下降', '哪个单位回款风险最高，为什么',
  '逾期金额最多的客户有哪些', '最近六个月集团收入趋势', '回款逾期超过90天应该怎么处置',
];
const messages = ref([]); const input = ref(''); const asking = ref(false);
const scrollRef = ref();

async function ask(q) {
  const question = q || input.value.trim();
  if (!question || asking.value) return;
  input.value = '';
  messages.value.push({ role: 'user', content: question });
  const aiMsg = { role: 'ai', loading: true };
  messages.value.push(aiMsg);
  asking.value = true;
  scrollBottom();
  try {
    const r = await api.ai.qa(question);
    Object.assign(aiMsg, {
      loading: false, content: r.answer, refs: r.knowledge_refs,
      intent: r.intent, duration: r.duration_ms, parse: r.parse, showPlan: false,
    });
  } catch (e) {
    Object.assign(aiMsg, { loading: false, content: '抱歉，分析失败: ' + e.message, refs: [] });
  } finally { asking.value = false; scrollBottom(); }
}
async function scrollBottom() {
  await nextTick();
  const wrap = scrollRef.value?.wrapRef;
  if (wrap) wrap.scrollTop = wrap.scrollHeight;
}
</script>
