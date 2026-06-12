# 际华国际数据分析平台 — 知识平台

基于 PRD《知识平台配置业务逻辑及页面设计说明书 V1.0》的工程级全栈实现。

## 架构

```
前端 Vue3 + Element Plus + ECharts (浅色科技风)
   ↓ /api
Node.js 主服务 (Express, :8000)
   本体/术语/指标/规则/方法论 CRUD · 统一生命周期状态机 · 图谱构建与多跳查询
   规则引擎 · 知识治理(审核/版本/影响分析/质量/审计) · /api/ai 代理
   ↓
Python AI 服务 (FastAPI, :8100)
   智能问数管线(术语匹配→语义解析→意图识别→数据查询→方法论分析→LLM回答)
   利润归因 · 回款风险分析 · RAG向量化与检索
   ↓
MySQL(MariaDB) 34张表  +  ChromaDB(开源向量库, 持久化)
LLM: qwen3-235b-a22b-instruct-2507  |  Embedding: text-embedding-v4 (DashScope兼容)
```

## 功能覆盖(对照 PRD)

| 模块 | 实现 |
|---|---|
| 知识总览 | 8类统计卡 / 8项质量率 / 待办审核 / 最近变更 / Skill调用监控 |
| 本体中心 | 业务域、对象(9个Tab详情)、属性(批量/影响分析后删除)、关系(路径预览)、接口(实现/取消机制)、动作函数、数据映射(6条校验规则) |
| 图谱中心 | 模型配置、构建任务(执行/日志/质量报告)、图谱浏览(力导图/多跳展开)、路径查询(BFS)、影响分析 |
| 术语词典 | 7类术语、消歧规则、命中测试、命中/纠错统计 |
| 指标语义 | 口径/公式/同义词/对象绑定/维度/归因路径/解释模板/数据预览/测试问数/引用分析 |
| 规则语义 | 5类规则、红橙黄蓝分级、试运行(5个内置执行器)、运行记录 |
| 分析方法论 | 8步骤利润归因、指标拆解树、图谱穿透路径、贡献度算法、方法论测试 |
| RAG知识库 | 上传→解析→切片→向量化→发布全流程、引用来源、过期过滤、检索问答 |
| 知识治理 | 统一生命周期(草稿→校验→审核→发布→变更→停用)、审核中心、版本对比、影响分析、质量检查、审计日志 |
| 智能问数 | PRD第21章完整流程，回答含可追溯知识引用与执行计划 |
| Skill联动 | 7个Skill注册、依赖知识声明、知识加载预览 |

## 演示数据(际华经营场景)

16组织(集团/4板块/8公司/3分厂)、20客户、144合同、346订单、530回款、
12供应商、159采购单、52库存、60风险事项、1782条指标事实(18个月×11指标)。
内置剧情: 3521/3543公司利润下滑(供应商涨价+合同延期)，可用于归因演示。

## 快速启动

```bash
# 1. 数据库
sudo service mariadb start
mysql -ukp_user -pkp_pass_2026 knowledge_platform < database/schema.sql
python3 database/seed/seed_business.py && python3 database/seed/seed_knowledge.py

# 2. AI 服务
cd ai-service && pip install fastapi uvicorn chromadb openai pymysql
python3 -m uvicorn main:app --host 0.0.0.0 --port 8100 &

# 3. 主服务(含前端静态托管)
cd backend-node && npm install && node src/app.js &

# 4. 初始化图谱与RAG向量
curl -X POST localhost:8000/api/graph/tasks/1/run
for i in 1 2 3 4 5 6; do curl -X POST localhost:8000/api/rag/documents/$i/process-all; done
```

访问 http://localhost:8000

## 说明
- 鉴权/权限底层服务按要求未实现(数据模型已预留 security_level/perm_label/visible_roles 字段)
- 移动端按要求未实现
