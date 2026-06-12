<template>
  <el-container style="height:100%">
    <el-aside width="216px" class="kp-layout-aside">
      <div class="kp-logo">
        <div class="logo-icon">际</div>
        <div>
          <div class="logo-text">际华知识平台</div>
          <div class="logo-sub">Knowledge Platform</div>
        </div>
      </div>
      <el-scrollbar style="height:calc(100% - 56px)">
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/overview">
            <el-icon><DataBoard /></el-icon><span>知识总览</span>
          </el-menu-item>
          <el-menu-item index="/qa">
            <el-icon><ChatDotRound /></el-icon><span>智能问数</span>
          </el-menu-item>
          <el-sub-menu index="ontology">
            <template #title><el-icon><Grid /></el-icon><span>本体中心</span></template>
            <el-menu-item index="/ontology/domains">业务域管理</el-menu-item>
            <el-menu-item index="/ontology/objects">对象类型管理</el-menu-item>
            <el-menu-item index="/ontology/links">关系管理</el-menu-item>
            <el-menu-item index="/ontology/interfaces">接口管理</el-menu-item>
            <el-menu-item index="/ontology/actions">动作与函数</el-menu-item>
            <el-menu-item index="/ontology/mappings">数据映射</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="graph">
            <template #title><el-icon><Share /></el-icon><span>图谱中心</span></template>
            <el-menu-item index="/graph/models">图谱模型</el-menu-item>
            <el-menu-item index="/graph/tasks">图谱构建任务</el-menu-item>
            <el-menu-item index="/graph/explore">图谱浏览</el-menu-item>
            <el-menu-item index="/graph/path">路径查询</el-menu-item>
            <el-menu-item index="/graph/impact">影响分析</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/terms">
            <el-icon><Collection /></el-icon><span>术语词典</span>
          </el-menu-item>
          <el-menu-item index="/metrics">
            <el-icon><TrendCharts /></el-icon><span>指标语义</span>
          </el-menu-item>
          <el-menu-item index="/rules">
            <el-icon><AlarmClock /></el-icon><span>规则语义</span>
          </el-menu-item>
          <el-menu-item index="/methods">
            <el-icon><SetUp /></el-icon><span>分析方法论</span>
          </el-menu-item>
          <el-menu-item index="/rag">
            <el-icon><Document /></el-icon><span>RAG知识库</span>
          </el-menu-item>
          <el-menu-item index="/skills">
            <el-icon><MagicStick /></el-icon><span>Skill注册</span>
          </el-menu-item>
          <el-sub-menu index="governance">
            <template #title><el-icon><Stamp /></el-icon><span>知识治理</span></template>
            <el-menu-item index="/governance/reviews">审核中心</el-menu-item>
            <el-menu-item index="/governance/versions">版本管理</el-menu-item>
            <el-menu-item index="/governance/impact">影响分析</el-menu-item>
            <el-menu-item index="/governance/quality">质量检查</el-menu-item>
            <el-menu-item index="/governance/audit">审计日志</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>
    </el-aside>
    <el-container>
      <el-header class="kp-header" height="56px">
        <div style="font-weight:600;color:#334155">
          {{ $route.meta.title || '' }}
          <span style="font-weight:400;font-size:12px;color:#94a3b8;margin-left:10px">际华国际经营数据分析平台 · 语义中枢</span>
        </div>
        <div style="display:flex;align-items:center;gap:14px">
          <el-tag size="small" effect="plain" type="success">场景: 经营分析</el-tag>
          <el-avatar :size="30" style="background:var(--kp-gradient)">管</el-avatar>
          <span style="font-size:13px;color:#475569">知识管理员</span>
        </div>
      </el-header>
      <el-main style="padding:0;overflow:auto;background:var(--kp-bg)">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
