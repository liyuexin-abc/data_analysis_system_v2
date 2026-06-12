-- ============================================================
-- 际华国际数据分析平台 - 知识平台数据库 Schema
-- MySQL/MariaDB utf8mb4
-- ============================================================
SET NAMES utf8mb4;
USE knowledge_platform;

-- ----------------------------------------------------------------
-- 通用说明:
-- 生命周期状态 status:
--   draft 草稿 | pending_check 待校验 | check_failed 校验不通过
--   pending_review 待审核 | published 已发布 | changing 变更中
--   disabled 已停用 | deprecated 已废弃
-- 安全等级 security_level: normal 普通 | sensitive 敏感 | confidential 机密
-- ----------------------------------------------------------------

-- ===================== 本体中心 =====================

DROP TABLE IF EXISTS kp_domain;
CREATE TABLE kp_domain (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  code          VARCHAR(64) NOT NULL UNIQUE COMMENT '业务域编码',
  name          VARCHAR(128) NOT NULL COMMENT '业务域名称',
  description   TEXT COMMENT '业务域说明',
  owner         VARCHAR(64) COMMENT '负责人',
  status        VARCHAR(32) NOT NULL DEFAULT 'draft',
  version       VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='业务域';

DROP TABLE IF EXISTS kp_object_type;
CREATE TABLE kp_object_type (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(64) NOT NULL UNIQUE COMMENT '对象编码 Obj_Sales_Contract',
  name            VARCHAR(128) NOT NULL COMMENT '对象名称',
  domain_code     VARCHAR(64) NOT NULL COMMENT '所属业务域',
  description     TEXT COMMENT '对象说明',
  primary_key     VARCHAR(64) NOT NULL COMMENT '主键字段',
  display_field   VARCHAR(64) NOT NULL COMMENT '展示字段',
  in_graph        TINYINT NOT NULL DEFAULT 0 COMMENT '是否入图',
  searchable      TINYINT NOT NULL DEFAULT 1 COMMENT '是否可搜索',
  monitorable     TINYINT NOT NULL DEFAULT 0 COMMENT '是否可监控',
  data_perm_field VARCHAR(64) COMMENT '数据权限字段',
  security_level  VARCHAR(32) NOT NULL DEFAULT 'normal' COMMENT '安全等级',
  owner           VARCHAR(64) COMMENT '负责人',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_obj_domain (domain_code),
  INDEX idx_obj_status (status)
) ENGINE=InnoDB COMMENT='本体对象类型';

DROP TABLE IF EXISTS kp_property;
CREATE TABLE kp_property (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  object_code     VARCHAR(64) NOT NULL COMMENT '所属对象编码',
  code            VARCHAR(64) NOT NULL COMMENT '属性编码',
  name            VARCHAR(128) NOT NULL COMMENT '属性名称',
  data_type       VARCHAR(32) NOT NULL DEFAULT 'string' COMMENT 'string/decimal/int/date/datetime/boolean',
  is_primary      TINYINT NOT NULL DEFAULT 0,
  is_required     TINYINT NOT NULL DEFAULT 0,
  is_sensitive    TINYINT NOT NULL DEFAULT 0,
  searchable      TINYINT NOT NULL DEFAULT 0,
  filterable      TINYINT NOT NULL DEFAULT 0,
  aggregatable    TINYINT NOT NULL DEFAULT 0,
  default_display TINYINT NOT NULL DEFAULT 0,
  source_field    VARCHAR(128) COMMENT '数据来源字段',
  quality_rules   JSON COMMENT '质量规则 ["not_null","unique"]',
  perm_label      VARCHAR(32) DEFAULT 'normal' COMMENT '权限标签',
  description     TEXT,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_prop (object_code, code),
  INDEX idx_prop_obj (object_code)
) ENGINE=InnoDB COMMENT='对象属性';

DROP TABLE IF EXISTS kp_link_type;
CREATE TABLE kp_link_type (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(96) NOT NULL UNIQUE COMMENT '关系编码 Link_Contract_Has_Receipt',
  name            VARCHAR(128) NOT NULL COMMENT '关系名称',
  source_object   VARCHAR(64) NOT NULL COMMENT '源对象编码',
  target_object   VARCHAR(64) NOT NULL COMMENT '目标对象编码',
  direction       VARCHAR(16) NOT NULL DEFAULT 'directed' COMMENT 'directed单向 bidirectional双向',
  cardinality     VARCHAR(8) NOT NULL DEFAULT '1:N' COMMENT '1:1/1:N/N:1/N:N',
  source_field    VARCHAR(64) NOT NULL COMMENT '源关联字段',
  target_field    VARCHAR(64) NOT NULL COMMENT '目标关联字段',
  drillable       TINYINT NOT NULL DEFAULT 1 COMMENT '是否支持下钻',
  in_graph        TINYINT NOT NULL DEFAULT 1 COMMENT '是否进入图谱',
  weight          DECIMAL(6,2) DEFAULT 1.0 COMMENT '关系权重',
  perm_inherit    VARCHAR(32) DEFAULT 'source' COMMENT 'source/target/independent',
  description     TEXT COMMENT '关系说明',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_link_src (source_object),
  INDEX idx_link_tgt (target_object)
) ENGINE=InnoDB COMMENT='对象关系类型';

DROP TABLE IF EXISTS kp_interface;
CREATE TABLE kp_interface (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(64) NOT NULL UNIQUE COMMENT '接口编码 If_Searchable',
  name            VARCHAR(128) NOT NULL,
  description     TEXT,
  required_props  JSON COMMENT '必需属性',
  support_funcs   JSON COMMENT '支持函数',
  support_actions JSON COMMENT '支持动作',
  perm_required   JSON COMMENT '权限要求',
  status          VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='本体接口';

DROP TABLE IF EXISTS kp_object_interface;
CREATE TABLE kp_object_interface (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  object_code    VARCHAR(64) NOT NULL,
  interface_code VARCHAR(64) NOT NULL,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_oi (object_code, interface_code)
) ENGINE=InnoDB COMMENT='对象实现接口';

DROP TABLE IF EXISTS kp_action;
CREATE TABLE kp_action (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  code         VARCHAR(64) NOT NULL UNIQUE COMMENT '动作编码 Act_Confirm_Alert',
  name         VARCHAR(128) NOT NULL,
  object_code  VARCHAR(64) COMMENT '适用对象',
  action_type  VARCHAR(32) DEFAULT 'business' COMMENT 'business/system/notify',
  params       JSON COMMENT '动作参数定义',
  description  TEXT,
  status       VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='本体动作';

DROP TABLE IF EXISTS kp_function;
CREATE TABLE kp_function (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  code         VARCHAR(64) NOT NULL UNIQUE COMMENT '函数编码 Fn_Calc_Overdue_Days',
  name         VARCHAR(128) NOT NULL,
  object_code  VARCHAR(64) COMMENT '适用对象',
  return_type  VARCHAR(32) DEFAULT 'decimal',
  expression   TEXT COMMENT '函数表达式说明',
  description  TEXT,
  status       VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='本体函数';

DROP TABLE IF EXISTS kp_mapping;
CREATE TABLE kp_mapping (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  object_code     VARCHAR(64) NOT NULL,
  property_code   VARCHAR(64) NOT NULL,
  data_source     VARCHAR(128) COMMENT '数据源系统',
  table_name      VARCHAR(128) COMMENT '数据表',
  source_field    VARCHAR(128) COMMENT '源字段',
  transform_rule  VARCHAR(255) COMMENT '转换规则',
  is_required     TINYINT DEFAULT 0,
  check_status    VARCHAR(16) DEFAULT 'pending' COMMENT 'pending/passed/failed',
  check_message   VARCHAR(512),
  checked_at      DATETIME,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_map (object_code, property_code),
  INDEX idx_map_obj (object_code)
) ENGINE=InnoDB COMMENT='数据映射';

-- ===================== 术语词典 =====================

DROP TABLE IF EXISTS kp_term;
CREATE TABLE kp_term (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  term            VARCHAR(128) NOT NULL COMMENT '术语(用户说法)',
  term_type       VARCHAR(32) NOT NULL COMMENT 'metric_alias/object_alias/property_alias/phrase/time_expr/action_expr/risk_expr',
  map_type        VARCHAR(32) NOT NULL COMMENT '映射类型 metric/object/property/action/rule/time',
  map_target      VARCHAR(128) NOT NULL COMMENT '标准映射目标编码',
  map_target_name VARCHAR(128) COMMENT '标准映射目标名称',
  scenes          JSON COMMENT '适用场景',
  priority        INT DEFAULT 5,
  confidence      DECIMAL(4,2) DEFAULT 0.8,
  examples        TEXT COMMENT '示例问法',
  disambiguation  TEXT COMMENT '消歧规则',
  hit_count       INT DEFAULT 0 COMMENT '命中次数',
  correct_count   INT DEFAULT 0 COMMENT '纠错次数',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_term (term),
  INDEX idx_term_type (term_type)
) ENGINE=InnoDB COMMENT='术语词典';

-- ===================== 指标语义中心 =====================

DROP TABLE IF EXISTS kp_metric_semantic;
CREATE TABLE kp_metric_semantic (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  metric_code     VARCHAR(64) NOT NULL UNIQUE COMMENT '指标编码 profit_total',
  metric_name     VARCHAR(128) NOT NULL COMMENT '指标名称',
  category        VARCHAR(64) DEFAULT '经营指标' COMMENT '指标分类',
  business_def    TEXT COMMENT '业务定义',
  formula_desc    TEXT COMMENT '公式说明',
  synonyms        JSON COMMENT '同义词',
  stat_periods    JSON COMMENT '统计周期 ["month","quarter","year"]',
  dimensions      JSON COMMENT '适用维度 ["org","customer","time"]',
  bind_objects    JSON COMMENT '绑定对象编码',
  charts          JSON COMMENT '推荐图表',
  default_compare JSON COMMENT '默认对比 ["yoy","mom","budget"]',
  attribution_path VARCHAR(64) COMMENT '归因路径(方法论编码)',
  unit            VARCHAR(32) DEFAULT '万元',
  security_level  VARCHAR(32) NOT NULL DEFAULT 'normal',
  answer_template TEXT COMMENT '解释模板',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='指标语义';

-- ===================== 规则语义中心 =====================

DROP TABLE IF EXISTS kp_rule;
CREATE TABLE kp_rule (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(64) NOT NULL UNIQUE COMMENT '规则编码 Rule_Receipt_Overdue',
  name            VARCHAR(128) NOT NULL,
  rule_type       VARCHAR(32) NOT NULL DEFAULT 'threshold' COMMENT 'threshold/yoy/mom/composite/forecast',
  monitor_object  VARCHAR(64) NOT NULL COMMENT '监控对象编码',
  monitor_metric  VARCHAR(64) NOT NULL COMMENT '监控指标编码',
  trigger_cond    JSON COMMENT '触发条件 {logic:"OR",conditions:[...]}',
  risk_levels     JSON COMMENT '风险等级配置 [{level,color,condition,suggestion}]',
  apply_orgs      JSON COMMENT '适用组织',
  run_cycle       VARCHAR(32) DEFAULT 'daily' COMMENT 'realtime/daily/monthly',
  notify_targets  JSON COMMENT '通知对象',
  suggestion      TEXT COMMENT '处置建议',
  actions         JSON COMMENT '关联动作',
  skills          JSON COMMENT '推荐Skill',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='规则语义';

DROP TABLE IF EXISTS kp_rule_run_log;
CREATE TABLE kp_rule_run_log (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  rule_code    VARCHAR(64) NOT NULL,
  run_time     DATETIME DEFAULT CURRENT_TIMESTAMP,
  run_type     VARCHAR(16) DEFAULT 'auto' COMMENT 'auto/test',
  matched      INT DEFAULT 0 COMMENT '命中数量',
  alerts       JSON COMMENT '生成预警明细',
  status       VARCHAR(16) DEFAULT 'success',
  message      VARCHAR(512),
  INDEX idx_rrl_rule (rule_code)
) ENGINE=InnoDB COMMENT='规则运行记录';

-- ===================== 分析方法论中心 =====================

DROP TABLE IF EXISTS kp_method;
CREATE TABLE kp_method (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(64) NOT NULL UNIQUE COMMENT '方法编码 MTH_Profit_Attribution',
  name            VARCHAR(128) NOT NULL,
  scenes          JSON COMMENT '适用场景',
  apply_metrics   JSON COMMENT '适用指标',
  apply_objects   JSON COMMENT '适用对象',
  steps           JSON COMMENT '分析步骤 [{seq,name,desc}]',
  decompose_tree  JSON COMMENT '指标拆解树',
  graph_paths     JSON COMMENT '图谱穿透路径',
  contribution_algo VARCHAR(255) COMMENT '贡献度算法',
  output_charts   JSON COMMENT '输出图表',
  output_template TEXT COMMENT 'AI解释模板',
  bind_skills     JSON COMMENT '绑定Skill',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='分析方法论';

-- ===================== 图谱中心 =====================

DROP TABLE IF EXISTS kp_graph_model;
CREATE TABLE kp_graph_model (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(64) NOT NULL UNIQUE COMMENT '图谱编码 graph_business_core',
  name            VARCHAR(128) NOT NULL,
  scene           VARCHAR(64) COMMENT '所属场景',
  description     TEXT,
  include_objects JSON COMMENT '入图对象编码',
  include_links   JSON COMMENT '入图关系编码',
  sync_mode       VARCHAR(32) DEFAULT 'batch' COMMENT 'batch/incremental/cdc',
  sync_cycle      VARCHAR(32) DEFAULT 'daily' COMMENT 'daily/hourly/realtime',
  perm_policy     VARCHAR(64) DEFAULT 'inherit_object' COMMENT '权限策略',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='图谱模型';

DROP TABLE IF EXISTS kp_graph_task;
CREATE TABLE kp_graph_task (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(128) NOT NULL COMMENT '任务名称',
  graph_code      VARCHAR(64) NOT NULL,
  data_sources    JSON COMMENT '数据来源表',
  entity_rules    JSON COMMENT '实体抽取规则',
  relation_rules  JSON COMMENT '关系抽取规则',
  dedup_rules     JSON COMMENT '去重规则',
  disambig_rules  JSON COMMENT '消歧规则',
  incr_field      VARCHAR(64) DEFAULT 'update_time',
  run_cycle       VARCHAR(32) DEFAULT 'daily',
  retry_times     INT DEFAULT 3,
  quality_rules   JSON,
  perm_policy     VARCHAR(64) DEFAULT 'inherit_object',
  last_run_at     DATETIME,
  last_status     VARCHAR(16) COMMENT 'success/failed/running',
  node_count      INT DEFAULT 0,
  edge_count      INT DEFAULT 0,
  success_rate    DECIMAL(5,2) DEFAULT 0,
  quality_status  VARCHAR(16) DEFAULT 'normal',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='图谱构建任务';

DROP TABLE IF EXISTS kp_graph_task_log;
CREATE TABLE kp_graph_task_log (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  task_id      INT NOT NULL,
  run_time     DATETIME DEFAULT CURRENT_TIMESTAMP,
  duration_ms  INT,
  node_count   INT DEFAULT 0,
  edge_count   INT DEFAULT 0,
  status       VARCHAR(16) DEFAULT 'success',
  message      TEXT,
  quality_report JSON COMMENT '质量报告: 孤立节点、重复节点等',
  INDEX idx_gtl_task (task_id)
) ENGINE=InnoDB COMMENT='图谱构建日志';

DROP TABLE IF EXISTS kp_graph_node;
CREATE TABLE kp_graph_node (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  graph_code   VARCHAR(64) NOT NULL,
  object_code  VARCHAR(64) NOT NULL COMMENT '对象类型编码',
  entity_id    VARCHAR(64) NOT NULL COMMENT '业务主键',
  entity_name  VARCHAR(255) NOT NULL COMMENT '显示名称',
  props        JSON COMMENT '节点属性快照',
  org_id       VARCHAR(64) COMMENT '数据权限',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_node (graph_code, object_code, entity_id),
  INDEX idx_node_name (entity_name),
  INDEX idx_node_obj (object_code)
) ENGINE=InnoDB COMMENT='图谱节点实例';

DROP TABLE IF EXISTS kp_graph_edge;
CREATE TABLE kp_graph_edge (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  graph_code    VARCHAR(64) NOT NULL,
  link_code     VARCHAR(96) NOT NULL COMMENT '关系类型编码',
  source_node   BIGINT NOT NULL,
  target_node   BIGINT NOT NULL,
  props         JSON,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_edge (graph_code, link_code, source_node, target_node),
  INDEX idx_edge_src (source_node),
  INDEX idx_edge_tgt (target_node)
) ENGINE=InnoDB COMMENT='图谱边实例';

-- ===================== RAG 知识库 =====================

DROP TABLE IF EXISTS kp_document;
CREATE TABLE kp_document (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(255) NOT NULL COMMENT '文档名称',
  doc_type        VARCHAR(32) NOT NULL DEFAULT 'regulation' COMMENT 'regulation制度/report报告/faq/case案例',
  scenes          JSON COMMENT '所属场景',
  domains         JSON COMMENT '所属业务域',
  security_level  VARCHAR(32) NOT NULL DEFAULT 'normal',
  visible_roles   JSON COMMENT '可见角色',
  effective_date  DATE,
  expire_date     DATE,
  tags            JSON,
  content         LONGTEXT COMMENT '文档内容',
  file_name       VARCHAR(255),
  uploader        VARCHAR(64),
  parse_status    VARCHAR(16) DEFAULT 'pending' COMMENT 'pending/parsing/parsed/failed',
  chunk_status    VARCHAR(16) DEFAULT 'pending' COMMENT 'pending/chunking/chunked/failed',
  vector_status   VARCHAR(16) DEFAULT 'pending' COMMENT 'pending/vectorizing/vectorized/failed',
  chunk_count     INT DEFAULT 0,
  ref_count       INT DEFAULT 0 COMMENT '引用次数',
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  version         VARCHAR(16) NOT NULL DEFAULT 'v1.0',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='RAG文档';

DROP TABLE IF EXISTS kp_doc_chunk;
CREATE TABLE kp_doc_chunk (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  doc_id       INT NOT NULL,
  chunk_index  INT NOT NULL,
  content      TEXT NOT NULL,
  token_count  INT DEFAULT 0,
  vector_id    VARCHAR(64) COMMENT 'ChromaDB向量ID',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_chunk_doc (doc_id)
) ENGINE=InnoDB COMMENT='文档切片';

-- ===================== 知识治理 =====================

DROP TABLE IF EXISTS kp_review;
CREATE TABLE kp_review (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  review_no     VARCHAR(32) NOT NULL UNIQUE COMMENT '审核单号 REVIEW-001',
  knowledge_type VARCHAR(32) NOT NULL COMMENT 'object/link/metric/term/rule/method/graph/document/domain',
  knowledge_id  INT NOT NULL,
  knowledge_code VARCHAR(96),
  knowledge_name VARCHAR(128),
  applicant     VARCHAR(64) COMMENT '申请人',
  change_type   VARCHAR(16) NOT NULL DEFAULT 'create' COMMENT 'create/update/disable',
  change_detail JSON COMMENT '变更内容',
  impact_scope  JSON COMMENT '影响范围',
  review_status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT 'pending/approved/rejected',
  reviewer      VARCHAR(64),
  review_comment VARCHAR(512),
  reviewed_at   DATETIME,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_review_status (review_status),
  INDEX idx_review_type (knowledge_type)
) ENGINE=InnoDB COMMENT='审核单';

DROP TABLE IF EXISTS kp_version;
CREATE TABLE kp_version (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  knowledge_type VARCHAR(32) NOT NULL,
  knowledge_id   INT NOT NULL,
  knowledge_code VARCHAR(96),
  version        VARCHAR(16) NOT NULL,
  snapshot       JSON COMMENT '版本快照',
  change_note    VARCHAR(512),
  operator       VARCHAR(64),
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ver_kt (knowledge_type, knowledge_id)
) ENGINE=InnoDB COMMENT='知识版本记录';

DROP TABLE IF EXISTS kp_audit_log;
CREATE TABLE kp_audit_log (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY,
  module         VARCHAR(32) NOT NULL COMMENT '模块',
  action         VARCHAR(32) NOT NULL COMMENT 'create/update/delete/submit/approve/reject/publish/disable/run/call',
  knowledge_type VARCHAR(32),
  knowledge_code VARCHAR(96),
  knowledge_name VARCHAR(128),
  operator       VARCHAR(64) DEFAULT 'admin',
  detail         JSON,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_module (module),
  INDEX idx_audit_time (created_at)
) ENGINE=InnoDB COMMENT='审计日志';

DROP TABLE IF EXISTS kp_quality_check;
CREATE TABLE kp_quality_check (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  check_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
  check_items  JSON COMMENT '各检查项结果',
  total_score  DECIMAL(5,2),
  operator     VARCHAR(64) DEFAULT 'system'
) ENGINE=InnoDB COMMENT='知识质量检查';

-- ===================== Skill 注册 =====================

DROP TABLE IF EXISTS kp_skill;
CREATE TABLE kp_skill (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  code            VARCHAR(64) NOT NULL UNIQUE,
  name            VARCHAR(128) NOT NULL,
  description     TEXT,
  depend_knowledge JSON COMMENT '依赖知识清单',
  call_count      INT DEFAULT 0,
  status          VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Skill注册';

DROP TABLE IF EXISTS kp_qa_log;
CREATE TABLE kp_qa_log (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  question      TEXT NOT NULL,
  matched_terms JSON COMMENT '命中术语',
  matched_metrics JSON COMMENT '识别指标',
  matched_objects JSON COMMENT '识别对象',
  plan          JSON COMMENT '执行计划',
  answer        LONGTEXT,
  knowledge_refs JSON COMMENT '知识引用',
  duration_ms   INT,
  feedback      VARCHAR(16) COMMENT 'good/bad',
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='智能问数调用记录';

-- ============================================================
-- 经营业务假数据表 (biz_*) — 际华国际经营分析场景
-- ============================================================

DROP TABLE IF EXISTS biz_org;
CREATE TABLE biz_org (
  org_id      VARCHAR(64) PRIMARY KEY,
  org_name    VARCHAR(128) NOT NULL,
  org_level   INT NOT NULL COMMENT '1集团 2板块 3二级单位 4三级单位',
  parent_id   VARCHAR(64),
  org_type    VARCHAR(32) COMMENT 'group/segment/company/factory',
  region      VARCHAR(64),
  leader      VARCHAR(64),
  status      VARCHAR(16) DEFAULT 'active',
  INDEX idx_org_parent (parent_id)
) ENGINE=InnoDB COMMENT='组织单位';

DROP TABLE IF EXISTS biz_customer;
CREATE TABLE biz_customer (
  customer_id   VARCHAR(64) PRIMARY KEY,
  customer_name VARCHAR(128) NOT NULL,
  industry      VARCHAR(64),
  region        VARCHAR(64),
  credit_level  VARCHAR(8) COMMENT 'AAA/AA/A/B/C',
  customer_type VARCHAR(32) COMMENT 'gov政府/military军队/enterprise企业/export外贸',
  contact       VARCHAR(64),
  created_year  INT
) ENGINE=InnoDB COMMENT='客户';

DROP TABLE IF EXISTS biz_contract;
CREATE TABLE biz_contract (
  contract_id     VARCHAR(64) PRIMARY KEY,
  contract_name   VARCHAR(255) NOT NULL,
  org_id          VARCHAR(64) NOT NULL COMMENT '签约单位',
  customer_id     VARCHAR(64) NOT NULL,
  contract_amount DECIMAL(16,2) NOT NULL COMMENT '合同金额(万元)',
  sign_date       DATE,
  delivery_date   DATE COMMENT '约定交付日期',
  contract_status VARCHAR(32) COMMENT 'executing履约中/completed已完成/delayed延期/terminated终止',
  product_line    VARCHAR(64) COMMENT '职业装/职业鞋靴/防护装备/纺织面料/其他',
  fulfill_rate    DECIMAL(5,2) COMMENT '履约率%',
  INDEX idx_ct_org (org_id),
  INDEX idx_ct_cust (customer_id)
) ENGINE=InnoDB COMMENT='合同';

DROP TABLE IF EXISTS biz_order;
CREATE TABLE biz_order (
  order_id     VARCHAR(64) PRIMARY KEY,
  contract_id  VARCHAR(64) NOT NULL,
  order_amount DECIMAL(16,2) COMMENT '订单金额(万元)',
  order_date   DATE,
  quantity     INT COMMENT '数量(件/双)',
  product_name VARCHAR(128),
  order_status VARCHAR(32) COMMENT 'producing生产中/delivered已交付/delayed延期',
  INDEX idx_od_ct (contract_id)
) ENGINE=InnoDB COMMENT='订单';

DROP TABLE IF EXISTS biz_receipt;
CREATE TABLE biz_receipt (
  receipt_id     VARCHAR(64) PRIMARY KEY,
  contract_id    VARCHAR(64) NOT NULL,
  plan_amount    DECIMAL(16,2) COMMENT '应收金额(万元)',
  actual_amount  DECIMAL(16,2) COMMENT '实收金额(万元)',
  due_date       DATE COMMENT '应收日期',
  receipt_date   DATE COMMENT '实收日期',
  overdue_days   INT DEFAULT 0 COMMENT '逾期天数',
  overdue_amount DECIMAL(16,2) DEFAULT 0 COMMENT '逾期金额(万元)',
  receipt_status VARCHAR(32) COMMENT 'received已回款/partial部分回款/overdue逾期',
  INDEX idx_rc_ct (contract_id)
) ENGINE=InnoDB COMMENT='回款记录';

DROP TABLE IF EXISTS biz_supplier;
CREATE TABLE biz_supplier (
  supplier_id   VARCHAR(64) PRIMARY KEY,
  supplier_name VARCHAR(128) NOT NULL,
  category      VARCHAR(64) COMMENT '面料/辅料/皮革/橡胶/设备',
  region        VARCHAR(64),
  rating        VARCHAR(8) COMMENT 'A/B/C/D',
  coop_years    INT COMMENT '合作年限'
) ENGINE=InnoDB COMMENT='供应商';

DROP TABLE IF EXISTS biz_material;
CREATE TABLE biz_material (
  material_id   VARCHAR(64) PRIMARY KEY,
  material_name VARCHAR(128) NOT NULL,
  category      VARCHAR(64),
  unit          VARCHAR(16),
  std_price     DECIMAL(12,2) COMMENT '标准单价(元)'
) ENGINE=InnoDB COMMENT='物料';

DROP TABLE IF EXISTS biz_purchase_order;
CREATE TABLE biz_purchase_order (
  po_id        VARCHAR(64) PRIMARY KEY,
  org_id       VARCHAR(64) NOT NULL COMMENT '采购单位',
  supplier_id  VARCHAR(64) NOT NULL,
  material_id  VARCHAR(64) NOT NULL,
  po_amount    DECIMAL(16,2) COMMENT '采购金额(万元)',
  unit_price   DECIMAL(12,2) COMMENT '采购单价(元)',
  quantity     DECIMAL(14,2),
  po_date      DATE,
  po_status    VARCHAR(32) COMMENT 'ordered已下单/received已到货/closed已关闭',
  INDEX idx_po_org (org_id),
  INDEX idx_po_sup (supplier_id),
  INDEX idx_po_mat (material_id)
) ENGINE=InnoDB COMMENT='采购单';

DROP TABLE IF EXISTS biz_inventory;
CREATE TABLE biz_inventory (
  inv_id        VARCHAR(64) PRIMARY KEY,
  org_id        VARCHAR(64) NOT NULL,
  material_id   VARCHAR(64) NOT NULL,
  warehouse     VARCHAR(64),
  qty           DECIMAL(14,2),
  amount        DECIMAL(16,2) COMMENT '库存金额(万元)',
  age_days      INT COMMENT '库龄(天)',
  turnover_rate DECIMAL(6,2) COMMENT '周转率',
  INDEX idx_inv_org (org_id),
  INDEX idx_inv_mat (material_id)
) ENGINE=InnoDB COMMENT='库存';

DROP TABLE IF EXISTS biz_prod_task;
CREATE TABLE biz_prod_task (
  task_id     VARCHAR(64) PRIMARY KEY,
  order_id    VARCHAR(64) NOT NULL,
  org_id      VARCHAR(64) NOT NULL COMMENT '生产单位',
  plan_qty    INT,
  done_qty    INT,
  start_date  DATE,
  plan_finish DATE,
  task_status VARCHAR(32) COMMENT 'producing/finished/delayed',
  INDEX idx_pt_order (order_id),
  INDEX idx_pt_org (org_id)
) ENGINE=InnoDB COMMENT='生产任务';

DROP TABLE IF EXISTS biz_risk;
CREATE TABLE biz_risk (
  risk_id      VARCHAR(64) PRIMARY KEY,
  risk_name    VARCHAR(255) NOT NULL,
  risk_type    VARCHAR(64) COMMENT '回款风险/履约风险/利润风险/供应链风险/库存风险',
  risk_level   VARCHAR(8) COMMENT 'red/orange/yellow/blue',
  ref_object   VARCHAR(64) COMMENT '关联对象类型编码',
  ref_id       VARCHAR(64) COMMENT '关联对象实例ID',
  org_id       VARCHAR(64),
  rule_code    VARCHAR(64) COMMENT '触发规则',
  description  TEXT,
  amount       DECIMAL(16,2) COMMENT '涉及金额(万元)',
  found_date   DATE,
  risk_status  VARCHAR(32) COMMENT 'open待处置/processing处置中/closed已闭环',
  INDEX idx_risk_org (org_id)
) ENGINE=InnoDB COMMENT='风险事项';

DROP TABLE IF EXISTS biz_rectify_task;
CREATE TABLE biz_rectify_task (
  task_id     VARCHAR(64) PRIMARY KEY,
  risk_id     VARCHAR(64) NOT NULL,
  org_id      VARCHAR(64),
  assignee    VARCHAR(64) COMMENT '责任人',
  content     TEXT,
  deadline    DATE,
  task_status VARCHAR(32) COMMENT 'pending/processing/done',
  INDEX idx_rt_risk (risk_id)
) ENGINE=InnoDB COMMENT='整改任务';

DROP TABLE IF EXISTS biz_metric_fact;
CREATE TABLE biz_metric_fact (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  metric_code VARCHAR(64) NOT NULL,
  org_id      VARCHAR(64) NOT NULL,
  period      VARCHAR(16) NOT NULL COMMENT '期间 2026-05 / 2026-Q1 / 2025',
  period_type VARCHAR(8) NOT NULL DEFAULT 'month' COMMENT 'month/quarter/year',
  value       DECIMAL(18,4) NOT NULL,
  budget      DECIMAL(18,4) COMMENT '预算值',
  UNIQUE KEY uk_fact (metric_code, org_id, period),
  INDEX idx_fact_metric (metric_code),
  INDEX idx_fact_org (org_id),
  INDEX idx_fact_period (period)
) ENGINE=InnoDB COMMENT='指标事实表';
