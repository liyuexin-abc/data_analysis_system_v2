#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识平台元数据假数据:
业务域 / 本体对象 / 属性 / 关系 / 接口 / 动作 / 函数 / 数据映射
术语词典 / 指标语义 / 规则语义 / 方法论 / 图谱模型与任务 / RAG文档 / Skill / 治理数据
"""
import pymysql
import json
import datetime

DB = dict(host='127.0.0.1', user='kp_user', password='kp_pass_2026',
          database='knowledge_platform', charset='utf8mb4')

J = lambda x: json.dumps(x, ensure_ascii=False)


def main():
    db = pymysql.connect(**DB)
    cur = db.cursor()
    tables = ['kp_domain', 'kp_object_type', 'kp_property', 'kp_link_type', 'kp_interface',
              'kp_object_interface', 'kp_action', 'kp_function', 'kp_mapping', 'kp_term',
              'kp_metric_semantic', 'kp_rule', 'kp_method', 'kp_graph_model', 'kp_graph_task',
              'kp_document', 'kp_skill', 'kp_review', 'kp_version', 'kp_audit_log', 'kp_rule_run_log']
    for t in tables:
        cur.execute(f'TRUNCATE TABLE {t}')

    # ============ 业务域 ============
    domains = [
        ('org', '组织域', '集团、板块、二级单位、三级单位的组织架构管理', '王建国', 'published'),
        ('market', '市场域', '客户、区域、行业等市场对象管理', '李市场', 'published'),
        ('sales', '销售域', '合同、订单、履约等销售业务对象', '张销售', 'published'),
        ('finance', '财务域', '收入、成本、利润、回款等财务对象', '刘财务', 'published'),
        ('scm', '供应链域', '采购、供应商、物料管理', '陈供应', 'published'),
        ('inventory', '库存域', '库存、库龄、周转管理', '杨库存', 'published'),
        ('production', '生产域', '生产任务、交付管理', '周生产', 'published'),
        ('investment', '投资域', '投资项目、资产管理(二期规划)', '吴投资', 'draft'),
        ('governance', '治理域', '预警、风险、整改任务管理', '郑风控', 'published'),
    ]
    cur.executemany(
        "INSERT INTO kp_domain (code,name,description,owner,status) VALUES (%s,%s,%s,%s,%s)", domains)

    # ============ 本体对象 ============
    # code,name,domain,desc,pk,display,in_graph,searchable,monitorable,perm_field,sec,owner,status
    objects = [
        ('Obj_Org_Unit', '组织单位', 'org', '集团组织架构中的单位实体，包括集团、板块、二级单位、三级单位', 'org_id', 'org_name', 1, 1, 0, 'org_id', 'normal', '王建国', 'published'),
        ('Obj_Mkt_Customer', '客户', 'market', '与际华发生业务往来的客户，含政府、军队、企业、外贸客户', 'customer_id', 'customer_name', 1, 1, 1, None, 'sensitive', '李市场', 'published'),
        ('Obj_Sales_Contract', '合同', 'sales', '与客户签订的销售合同，是经营分析的核心对象', 'contract_id', 'contract_name', 1, 1, 1, 'org_id', 'sensitive', '张销售', 'published'),
        ('Obj_Sales_Order', '订单', 'sales', '合同下的执行订单，驱动生产任务', 'order_id', 'order_id', 1, 1, 1, None, 'normal', '张销售', 'published'),
        ('Obj_Fin_Receipt', '回款记录', 'finance', '合同回款计划与实际回款记录，支撑回款风险分析', 'receipt_id', 'receipt_id', 1, 1, 1, None, 'confidential', '刘财务', 'published'),
        ('Obj_Scm_Supplier', '供应商', 'scm', '原材料和设备供应商', 'supplier_id', 'supplier_name', 1, 1, 1, None, 'normal', '陈供应', 'published'),
        ('Obj_Scm_PurchaseOrder', '采购单', 'scm', '向供应商发出的采购订单', 'po_id', 'po_id', 1, 1, 1, 'org_id', 'normal', '陈供应', 'published'),
        ('Obj_Scm_Material', '物料', 'scm', '生产所需的原材料、辅料', 'material_id', 'material_name', 1, 1, 0, None, 'normal', '陈供应', 'published'),
        ('Obj_Inv_Inventory', '库存', 'inventory', '各单位物料库存，含库龄和周转信息', 'inv_id', 'inv_id', 1, 0, 1, 'org_id', 'normal', '杨库存', 'published'),
        ('Obj_Prod_Task', '生产任务', 'production', '订单驱动的生产任务', 'task_id', 'task_id', 1, 0, 1, 'org_id', 'normal', '周生产', 'published'),
        ('Obj_Gov_Risk', '风险事项', 'governance', '预警规则触发或人工上报的风险事项', 'risk_id', 'risk_name', 1, 1, 1, 'org_id', 'sensitive', '郑风控', 'published'),
        ('Obj_Gov_RectifyTask', '整改任务', 'governance', '针对风险事项派发的整改闭环任务', 'task_id', 'task_id', 0, 1, 1, 'org_id', 'normal', '郑风控', 'published'),
        ('Obj_Inv_Project', '投资项目', 'investment', '投资项目对象(二期规划，演示接口扩展机制)', 'project_id', 'project_name', 0, 1, 0, 'org_id', 'confidential', '吴投资', 'draft'),
    ]
    cur.executemany(
        "INSERT INTO kp_object_type (code,name,domain_code,description,primary_key,display_field,in_graph,searchable,monitorable,data_perm_field,security_level,owner,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)

    # ============ 属性 ============
    # obj,code,name,type,pk,req,sens,search,filter,agg,disp,src,qrules,perm
    P = []
    def prop(obj, code, name, dt, pk=0, req=0, sens=0, sea=0, fil=0, agg=0, disp=0, src=None, qr=None, perm='normal', desc=''):
        P.append((obj, code, name, dt, pk, req, sens, sea, fil, agg, disp, src, J(qr or []), perm, desc))

    prop('Obj_Org_Unit', 'org_id', '组织编码', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_org.org_id', ['not_null', 'unique'])
    prop('Obj_Org_Unit', 'org_name', '组织名称', 'string', 0, 1, 0, 1, 1, 0, 1, 'biz_org.org_name', ['not_null'])
    prop('Obj_Org_Unit', 'org_level', '组织层级', 'int', 0, 1, 0, 0, 1, 0, 1, 'biz_org.org_level', ['enum'])
    prop('Obj_Org_Unit', 'parent_id', '上级组织', 'string', 0, 0, 0, 0, 1, 0, 0, 'biz_org.parent_id', ['ref_check'])
    prop('Obj_Org_Unit', 'region', '所在区域', 'string', 0, 0, 0, 1, 1, 0, 1, 'biz_org.region')
    prop('Obj_Org_Unit', 'leader', '负责人', 'string', 0, 0, 1, 0, 0, 0, 0, 'biz_org.leader', perm='sensitive')

    prop('Obj_Mkt_Customer', 'customer_id', '客户编码', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_customer.customer_id', ['not_null', 'unique'])
    prop('Obj_Mkt_Customer', 'customer_name', '客户名称', 'string', 0, 1, 0, 1, 1, 0, 1, 'biz_customer.customer_name', ['not_null'])
    prop('Obj_Mkt_Customer', 'industry', '所属行业', 'string', 0, 0, 0, 1, 1, 0, 1, 'biz_customer.industry')
    prop('Obj_Mkt_Customer', 'credit_level', '信用等级', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_customer.credit_level', ['enum'])
    prop('Obj_Mkt_Customer', 'customer_type', '客户类型', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_customer.customer_type', ['enum'])
    prop('Obj_Mkt_Customer', 'contact', '联系人', 'string', 0, 0, 1, 0, 0, 0, 0, 'biz_customer.contact', perm='sensitive')

    prop('Obj_Sales_Contract', 'contract_id', '合同编号', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_contract.contract_id', ['not_null', 'unique'])
    prop('Obj_Sales_Contract', 'contract_name', '合同名称', 'string', 0, 1, 0, 1, 0, 0, 1, 'biz_contract.contract_name', ['not_null'])
    prop('Obj_Sales_Contract', 'org_id', '签约单位', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_contract.org_id', ['ref_check'])
    prop('Obj_Sales_Contract', 'customer_id', '客户', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_contract.customer_id', ['ref_check'])
    prop('Obj_Sales_Contract', 'contract_amount', '合同金额', 'decimal', 0, 1, 1, 0, 1, 1, 1, 'biz_contract.contract_amount', ['not_null', 'non_negative'], 'sensitive', '合同总金额，单位万元')
    prop('Obj_Sales_Contract', 'sign_date', '签约日期', 'date', 0, 1, 0, 0, 1, 0, 1, 'biz_contract.sign_date', ['not_null'])
    prop('Obj_Sales_Contract', 'delivery_date', '约定交付日期', 'date', 0, 0, 0, 0, 1, 0, 1, 'biz_contract.delivery_date', ['time_check'])
    prop('Obj_Sales_Contract', 'contract_status', '合同状态', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_contract.contract_status', ['enum'])
    prop('Obj_Sales_Contract', 'product_line', '产品线', 'string', 0, 0, 0, 1, 1, 0, 1, 'biz_contract.product_line')
    prop('Obj_Sales_Contract', 'fulfill_rate', '履约率', 'decimal', 0, 0, 0, 0, 1, 1, 1, 'biz_contract.fulfill_rate', ['range_0_100'])

    prop('Obj_Sales_Order', 'order_id', '订单编号', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_order.order_id', ['not_null', 'unique'])
    prop('Obj_Sales_Order', 'contract_id', '所属合同', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_order.contract_id', ['ref_check'])
    prop('Obj_Sales_Order', 'order_amount', '订单金额', 'decimal', 0, 1, 1, 0, 1, 1, 1, 'biz_order.order_amount', ['non_negative'], 'sensitive')
    prop('Obj_Sales_Order', 'order_date', '下单日期', 'date', 0, 1, 0, 0, 1, 0, 1, 'biz_order.order_date')
    prop('Obj_Sales_Order', 'product_name', '产品名称', 'string', 0, 0, 0, 1, 1, 0, 1, 'biz_order.product_name')
    prop('Obj_Sales_Order', 'order_status', '订单状态', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_order.order_status', ['enum'])

    prop('Obj_Fin_Receipt', 'receipt_id', '回款编号', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_receipt.receipt_id', ['not_null', 'unique'])
    prop('Obj_Fin_Receipt', 'contract_id', '所属合同', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_receipt.contract_id', ['ref_check'])
    prop('Obj_Fin_Receipt', 'plan_amount', '应收金额', 'decimal', 0, 1, 1, 0, 1, 1, 1, 'biz_receipt.plan_amount', ['non_negative'], 'confidential')
    prop('Obj_Fin_Receipt', 'actual_amount', '实收金额', 'decimal', 0, 0, 1, 0, 1, 1, 1, 'biz_receipt.actual_amount', ['non_negative'], 'confidential')
    prop('Obj_Fin_Receipt', 'due_date', '应收日期', 'date', 0, 1, 0, 0, 1, 0, 1, 'biz_receipt.due_date', ['time_check'])
    prop('Obj_Fin_Receipt', 'overdue_days', '逾期天数', 'int', 0, 0, 0, 0, 1, 1, 1, 'biz_receipt.overdue_days', ['non_negative'])
    prop('Obj_Fin_Receipt', 'overdue_amount', '逾期金额', 'decimal', 0, 0, 1, 0, 1, 1, 1, 'biz_receipt.overdue_amount', ['non_negative'], 'confidential')
    prop('Obj_Fin_Receipt', 'receipt_status', '回款状态', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_receipt.receipt_status', ['enum'])

    prop('Obj_Scm_Supplier', 'supplier_id', '供应商编码', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_supplier.supplier_id', ['not_null', 'unique'])
    prop('Obj_Scm_Supplier', 'supplier_name', '供应商名称', 'string', 0, 1, 0, 1, 1, 0, 1, 'biz_supplier.supplier_name', ['not_null'])
    prop('Obj_Scm_Supplier', 'category', '供应品类', 'string', 0, 0, 0, 1, 1, 0, 1, 'biz_supplier.category')
    prop('Obj_Scm_Supplier', 'rating', '供应商评级', 'string', 0, 0, 0, 0, 1, 0, 1, 'biz_supplier.rating', ['enum'])

    prop('Obj_Scm_PurchaseOrder', 'po_id', '采购单号', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_purchase_order.po_id', ['not_null', 'unique'])
    prop('Obj_Scm_PurchaseOrder', 'org_id', '采购单位', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_purchase_order.org_id', ['ref_check'])
    prop('Obj_Scm_PurchaseOrder', 'supplier_id', '供应商', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_purchase_order.supplier_id', ['ref_check'])
    prop('Obj_Scm_PurchaseOrder', 'material_id', '物料', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_purchase_order.material_id', ['ref_check'])
    prop('Obj_Scm_PurchaseOrder', 'po_amount', '采购金额', 'decimal', 0, 1, 0, 0, 1, 1, 1, 'biz_purchase_order.po_amount', ['non_negative'])
    prop('Obj_Scm_PurchaseOrder', 'unit_price', '采购单价', 'decimal', 0, 1, 0, 0, 1, 1, 1, 'biz_purchase_order.unit_price', ['non_negative'])

    prop('Obj_Scm_Material', 'material_id', '物料编码', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_material.material_id', ['not_null', 'unique'])
    prop('Obj_Scm_Material', 'material_name', '物料名称', 'string', 0, 1, 0, 1, 1, 0, 1, 'biz_material.material_name', ['not_null'])
    prop('Obj_Scm_Material', 'category', '物料类别', 'string', 0, 0, 0, 1, 1, 0, 1, 'biz_material.category')
    prop('Obj_Scm_Material', 'std_price', '标准单价', 'decimal', 0, 0, 0, 0, 1, 1, 1, 'biz_material.std_price', ['non_negative'])

    prop('Obj_Inv_Inventory', 'inv_id', '库存编号', 'string', 1, 1, 0, 0, 1, 0, 1, 'biz_inventory.inv_id', ['not_null', 'unique'])
    prop('Obj_Inv_Inventory', 'org_id', '所属单位', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_inventory.org_id', ['ref_check'])
    prop('Obj_Inv_Inventory', 'material_id', '物料', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_inventory.material_id', ['ref_check'])
    prop('Obj_Inv_Inventory', 'amount', '库存金额', 'decimal', 0, 0, 0, 0, 1, 1, 1, 'biz_inventory.amount', ['non_negative'])
    prop('Obj_Inv_Inventory', 'age_days', '库龄天数', 'int', 0, 0, 0, 0, 1, 1, 1, 'biz_inventory.age_days', ['non_negative'])
    prop('Obj_Inv_Inventory', 'turnover_rate', '周转率', 'decimal', 0, 0, 0, 0, 1, 1, 1, 'biz_inventory.turnover_rate')

    prop('Obj_Prod_Task', 'task_id', '任务编号', 'string', 1, 1, 0, 0, 1, 0, 1, 'biz_prod_task.task_id', ['not_null', 'unique'])
    prop('Obj_Prod_Task', 'order_id', '所属订单', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_prod_task.order_id', ['ref_check'])
    prop('Obj_Prod_Task', 'org_id', '生产单位', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_prod_task.org_id', ['ref_check'])
    prop('Obj_Prod_Task', 'plan_qty', '计划数量', 'int', 0, 1, 0, 0, 0, 1, 1, 'biz_prod_task.plan_qty', ['non_negative'])
    prop('Obj_Prod_Task', 'done_qty', '完成数量', 'int', 0, 0, 0, 0, 0, 1, 1, 'biz_prod_task.done_qty', ['non_negative'])
    prop('Obj_Prod_Task', 'task_status', '任务状态', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_prod_task.task_status', ['enum'])

    prop('Obj_Gov_Risk', 'risk_id', '风险编号', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_risk.risk_id', ['not_null', 'unique'])
    prop('Obj_Gov_Risk', 'risk_name', '风险名称', 'string', 0, 1, 0, 1, 0, 0, 1, 'biz_risk.risk_name', ['not_null'])
    prop('Obj_Gov_Risk', 'risk_type', '风险类型', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_risk.risk_type', ['enum'])
    prop('Obj_Gov_Risk', 'risk_level', '风险等级', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_risk.risk_level', ['enum'])
    prop('Obj_Gov_Risk', 'amount', '涉及金额', 'decimal', 0, 0, 1, 0, 1, 1, 1, 'biz_risk.amount', ['non_negative'], 'sensitive')
    prop('Obj_Gov_Risk', 'risk_status', '处置状态', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_risk.risk_status', ['enum'])

    prop('Obj_Gov_RectifyTask', 'task_id', '整改单号', 'string', 1, 1, 0, 1, 1, 0, 1, 'biz_rectify_task.task_id', ['not_null', 'unique'])
    prop('Obj_Gov_RectifyTask', 'risk_id', '关联风险', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_rectify_task.risk_id', ['ref_check'])
    prop('Obj_Gov_RectifyTask', 'assignee', '责任人', 'string', 0, 1, 1, 0, 1, 0, 1, 'biz_rectify_task.assignee', perm='sensitive')
    prop('Obj_Gov_RectifyTask', 'deadline', '整改期限', 'date', 0, 1, 0, 0, 1, 0, 1, 'biz_rectify_task.deadline')
    prop('Obj_Gov_RectifyTask', 'task_status', '任务状态', 'string', 0, 1, 0, 0, 1, 0, 1, 'biz_rectify_task.task_status', ['enum'])

    cur.executemany(
        "INSERT INTO kp_property (object_code,code,name,data_type,is_primary,is_required,is_sensitive,searchable,filterable,aggregatable,default_display,source_field,quality_rules,perm_label,description) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", P)

    # ============ 关系 ============
    links = [
        # code,name,src,tgt,dir,card,sf,tf,drill,graph,weight,perm,desc,status
        ('Link_Org_Has_Sub', '组织包含下级', 'Obj_Org_Unit', 'Obj_Org_Unit', 'directed', '1:N', 'org_id', 'parent_id', 1, 1, 1.0, 'source', '组织层级树关系，支撑组织穿透', 'published'),
        ('Link_Org_Has_Contract', '组织拥有合同', 'Obj_Org_Unit', 'Obj_Sales_Contract', 'directed', '1:N', 'org_id', 'org_id', 1, 1, 1.0, 'source', '单位合同分析的核心关系', 'published'),
        ('Link_Customer_Has_Contract', '客户关联合同', 'Obj_Mkt_Customer', 'Obj_Sales_Contract', 'directed', '1:N', 'customer_id', 'customer_id', 1, 1, 1.0, 'target', '客户贡献分析', 'published'),
        ('Link_Contract_Has_Order', '合同包含订单', 'Obj_Sales_Contract', 'Obj_Sales_Order', 'directed', '1:N', 'contract_id', 'contract_id', 1, 1, 1.0, 'source', '合同转订单分析', 'published'),
        ('Link_Contract_Has_Receipt', '合同包含回款', 'Obj_Sales_Contract', 'Obj_Fin_Receipt', 'directed', '1:N', 'contract_id', 'contract_id', 1, 1, 1.0, 'source', '回款风险分析的核心关系', 'published'),
        ('Link_Order_Drive_Task', '订单驱动生产任务', 'Obj_Sales_Order', 'Obj_Prod_Task', 'directed', '1:N', 'order_id', 'order_id', 1, 1, 1.0, 'source', '产销协同分析', 'published'),
        ('Link_Org_Has_PO', '组织发起采购', 'Obj_Org_Unit', 'Obj_Scm_PurchaseOrder', 'directed', '1:N', 'org_id', 'org_id', 1, 1, 1.0, 'source', '采购成本分析', 'published'),
        ('Link_PO_To_Supplier', '采购单对应供应商', 'Obj_Scm_PurchaseOrder', 'Obj_Scm_Supplier', 'directed', 'N:1', 'supplier_id', 'supplier_id', 1, 1, 1.0, 'source', '供应商分析', 'published'),
        ('Link_PO_To_Material', '采购单对应物料', 'Obj_Scm_PurchaseOrder', 'Obj_Scm_Material', 'directed', 'N:1', 'material_id', 'material_id', 1, 1, 1.0, 'source', '采购价格分析', 'published'),
        ('Link_Material_Has_Inventory', '物料形成库存', 'Obj_Scm_Material', 'Obj_Inv_Inventory', 'directed', '1:N', 'material_id', 'material_id', 1, 1, 1.0, 'source', '库存分析', 'published'),
        ('Link_Org_Has_Inventory', '组织持有库存', 'Obj_Org_Unit', 'Obj_Inv_Inventory', 'directed', '1:N', 'org_id', 'org_id', 1, 1, 1.0, 'source', '单位库存分析', 'published'),
        ('Link_Risk_Refer_Object', '风险关联业务对象', 'Obj_Gov_Risk', 'Obj_Sales_Contract', 'directed', 'N:1', 'ref_id', 'contract_id', 1, 1, 1.5, 'source', '风险溯源(多态关联，按 ref_object 区分目标类型)', 'published'),
        ('Link_Risk_Has_Rectify', '风险派发整改', 'Obj_Gov_Risk', 'Obj_Gov_RectifyTask', 'directed', '1:N', 'risk_id', 'risk_id', 1, 0, 1.0, 'source', '风险闭环管理', 'published'),
        ('Link_Org_Has_Risk', '组织存在风险', 'Obj_Org_Unit', 'Obj_Gov_Risk', 'directed', '1:N', 'org_id', 'org_id', 1, 1, 1.2, 'source', '单位风险全景', 'published'),
    ]
    cur.executemany(
        "INSERT INTO kp_link_type (code,name,source_object,target_object,direction,cardinality,source_field,target_field,drillable,in_graph,weight,perm_inherit,description,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", links)

    # ============ 接口 ============
    interfaces = [
        ('If_Searchable', '可搜索对象', '可被全局搜索、智能问数识别', ['display_field'], [], [], []),
        ('If_Drillable', '可穿透对象', '可被下钻分析和图谱路径调用', ['primary_key'], [], [], []),
        ('If_Monitorable', '可监控对象', '可被预警规则引擎监控', ['primary_key'], ['Fn_Calc_Overdue_Days'], ['Act_Confirm_Alert'], []),
        ('If_Attributable', '可归因对象', '可参与根因分析', ['primary_key'], [], [], []),
        ('If_Reportable', '可报告对象', '可进入报告模板', [], [], [], []),
        ('If_Riskable', '可风险评估对象', '可计算风险等级', ['risk_level'], ['Fn_Risk_Score'], [], []),
        ('If_Closable', '可闭环对象', '可执行确认、派单、关闭等动作', [], [], ['Act_Dispatch_Task', 'Act_Close_Risk'], []),
        ('If_GraphNode', '可入图对象', '可写入知识图谱', ['primary_key', 'display_field'], [], [], []),
    ]
    cur.executemany(
        "INSERT INTO kp_interface (code,name,description,required_props,support_funcs,support_actions,perm_required) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        [(c, n, d, J(rp), J(sf), J(sa), J(pr)) for c, n, d, rp, sf, sa, pr in interfaces])

    oi = []
    impl = {
        'Obj_Org_Unit': ['If_Searchable', 'If_Drillable', 'If_GraphNode', 'If_Reportable'],
        'Obj_Mkt_Customer': ['If_Searchable', 'If_Drillable', 'If_GraphNode', 'If_Riskable', 'If_Reportable'],
        'Obj_Sales_Contract': ['If_Searchable', 'If_Drillable', 'If_Monitorable', 'If_Attributable', 'If_Reportable', 'If_Riskable', 'If_GraphNode'],
        'Obj_Sales_Order': ['If_Searchable', 'If_Drillable', 'If_Monitorable', 'If_GraphNode'],
        'Obj_Fin_Receipt': ['If_Drillable', 'If_Monitorable', 'If_Attributable', 'If_Riskable', 'If_GraphNode'],
        'Obj_Scm_Supplier': ['If_Searchable', 'If_Drillable', 'If_Riskable', 'If_GraphNode'],
        'Obj_Scm_PurchaseOrder': ['If_Drillable', 'If_Monitorable', 'If_Attributable', 'If_GraphNode'],
        'Obj_Scm_Material': ['If_Searchable', 'If_Drillable', 'If_GraphNode'],
        'Obj_Inv_Inventory': ['If_Drillable', 'If_Monitorable', 'If_GraphNode'],
        'Obj_Prod_Task': ['If_Drillable', 'If_Monitorable', 'If_GraphNode'],
        'Obj_Gov_Risk': ['If_Searchable', 'If_Drillable', 'If_Closable', 'If_Reportable', 'If_GraphNode'],
        'Obj_Gov_RectifyTask': ['If_Searchable', 'If_Closable'],
    }
    for o, ifs in impl.items():
        for i in ifs:
            oi.append((o, i))
    cur.executemany("INSERT INTO kp_object_interface (object_code,interface_code) VALUES (%s,%s)", oi)

    # ============ 动作 / 函数 ============
    actions = [
        ('Act_Confirm_Alert', '确认预警', 'Obj_Gov_Risk', 'business', {'params': ['risk_id', 'comment']}, '确认预警事件真实有效'),
        ('Act_Dispatch_Task', '派发整改任务', 'Obj_Gov_Risk', 'business', {'params': ['risk_id', 'assignee', 'deadline']}, '针对风险派发整改任务'),
        ('Act_Close_Risk', '关闭风险', 'Obj_Gov_Risk', 'business', {'params': ['risk_id', 'close_reason']}, '风险处置完成后关闭'),
        ('Act_Notify_Org', '通知责任单位', 'Obj_Org_Unit', 'notify', {'params': ['org_id', 'message']}, '向责任单位发送通知'),
        ('Act_Gen_Report', '生成分析报告', None, 'system', {'params': ['template', 'org_id', 'period']}, '调用报告生成Skill'),
        ('Act_Urge_Receipt', '发起催收', 'Obj_Fin_Receipt', 'business', {'params': ['receipt_id', 'urge_level']}, '对逾期回款发起催收流程'),
    ]
    cur.executemany(
        "INSERT INTO kp_action (code,name,object_code,action_type,params,description) VALUES (%s,%s,%s,%s,%s,%s)",
        [(c, n, o, t, J(p), d) for c, n, o, t, p, d in actions])

    functions = [
        ('Fn_Calc_Overdue_Days', '计算逾期天数', 'Obj_Fin_Receipt', 'int', 'DATEDIFF(CURRENT_DATE, due_date) WHERE actual_amount < plan_amount', '计算回款逾期天数'),
        ('Fn_Calc_Receipt_Rate', '计算回款率', 'Obj_Sales_Contract', 'decimal', 'SUM(actual_amount) / SUM(plan_amount) * 100', '计算合同回款率'),
        ('Fn_Risk_Score', '计算风险评分', 'Obj_Gov_Risk', 'decimal', 'CASE risk_level WHEN red THEN 90+ WHEN orange THEN 70-90 ...', '综合风险评分'),
        ('Fn_Calc_Fulfill_Rate', '计算履约率', 'Obj_Sales_Contract', 'decimal', 'SUM(done_qty) / SUM(plan_qty) * 100', '基于生产任务计算履约率'),
        ('Fn_Inventory_Age', '计算库龄', 'Obj_Inv_Inventory', 'int', 'DATEDIFF(CURRENT_DATE, in_stock_date)', '计算库存库龄'),
    ]
    cur.executemany(
        "INSERT INTO kp_function (code,name,object_code,return_type,expression,description) VALUES (%s,%s,%s,%s,%s,%s)", functions)

    # ============ 数据映射 (基于属性 source_field 自动生成) ============
    cur.execute("SELECT object_code, code, source_field, is_required FROM kp_property WHERE source_field IS NOT NULL")
    maps = []
    for oc, pc, sf, req in cur.fetchall():
        tbl, fld = sf.split('.')
        maps.append((oc, pc, '经营数据中台', tbl, fld, '金额单位转换(元→万元)' if 'amount' in fld else None,
                     req, 'passed', '映射校验通过', datetime.datetime(2026, 6, 10, 2, 0)))
    cur.executemany(
        "INSERT INTO kp_mapping (object_code,property_code,data_source,table_name,source_field,transform_rule,is_required,check_status,check_message,checked_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", maps)

    # ============ 指标语义 ============
    metrics = [
        dict(code='profit_total', name='利润总额', cat='财务指标',
             bdef='反映企业一定期间经营成果的核心财务指标，体现盈利能力。',
             formula='利润总额 = 营业收入 - 营业成本 - 销售费用 - 管理费用 - 财务费用 + 其他收益',
             syn=['利润', '盈利', '挣钱', '赚了多少', '盈利情况'],
             periods=['month', 'quarter', 'year'], dims=['org', 'time', 'customer', 'product'],
             objs=['Obj_Org_Unit'], charts=['line', 'bar', 'waterfall'],
             cmp=['yoy', 'mom', 'budget'], ap='MTH_Profit_Attribution', sec='confidential',
             tpl='{org}{period}利润总额为{value}万元，{compare_desc}。主要影响因素：{factors}。'),
        dict(code='revenue_total', name='营业收入', cat='财务指标',
             bdef='企业在销售商品、提供劳务等日常活动中形成的经济利益总流入。',
             formula='营业收入 = Σ(各单位主营业务收入 + 其他业务收入)',
             syn=['收入', '营收', '销售收入', '进账'],
             periods=['month', 'quarter', 'year'], dims=['org', 'time', 'customer', 'product'],
             objs=['Obj_Org_Unit'], charts=['line', 'bar'], cmp=['yoy', 'mom', 'budget'],
             ap='MTH_Revenue_Attribution', sec='sensitive',
             tpl='{org}{period}营业收入为{value}万元，{compare_desc}。'),
        dict(code='cost_total', name='营业成本', cat='财务指标',
             bdef='企业为生产产品、提供劳务而发生的直接成本。',
             formula='营业成本 = 直接材料 + 直接人工 + 制造费用',
             syn=['成本', '花了多少', '成本开支'],
             periods=['month', 'quarter', 'year'], dims=['org', 'time', 'product'],
             objs=['Obj_Org_Unit'], charts=['line', 'bar'], cmp=['yoy', 'mom'],
             ap='MTH_Cost_Attribution', sec='sensitive',
             tpl='{org}{period}营业成本为{value}万元，{compare_desc}。'),
        dict(code='receipt_rate', name='回款率', cat='经营指标',
             bdef='衡量合同回款执行情况的指标，反映资金回笼能力。',
             formula='回款率 = 实际回款金额 / 应回款金额 × 100%',
             syn=['回款情况', '钱回来多少', '收款率', '回款比例'],
             periods=['month', 'quarter', 'year'], dims=['org', 'time', 'customer'],
             objs=['Obj_Org_Unit', 'Obj_Sales_Contract'], charts=['line', 'gauge'],
             cmp=['yoy', 'mom', 'budget'], ap='MTH_Receipt_Risk', sec='sensitive', unit='%',
             tpl='{org}{period}回款率为{value}%，{compare_desc}。'),
        dict(code='overdue_amount', name='逾期金额', cat='风险指标',
             bdef='超过约定回款日期仍未收回的款项总额，是回款风险的核心度量。',
             formula='逾期金额 = Σ(应收金额 - 实收金额) WHERE 当前日期 > 应收日期',
             syn=['逾期款', '钱没回来', '欠款', '拖欠金额', '逾期回款'],
             periods=['month', 'quarter'], dims=['org', 'time', 'customer'],
             objs=['Obj_Org_Unit', 'Obj_Fin_Receipt'], charts=['bar', 'rank'],
             cmp=['mom'], ap='MTH_Receipt_Risk', sec='confidential',
             tpl='{org}{period}逾期金额为{value}万元，{compare_desc}。建议关注高风险客户。'),
        dict(code='contract_amount_sum', name='合同签约额', cat='经营指标',
             bdef='统计期内新签合同的金额总和，反映市场开拓能力。',
             formula='合同签约额 = Σ(统计期内签约合同金额)',
             syn=['签约额', '合同额', '签了多少合同', '新签合同'],
             periods=['month', 'quarter', 'year'], dims=['org', 'time', 'customer', 'product'],
             objs=['Obj_Org_Unit', 'Obj_Sales_Contract'], charts=['line', 'bar', 'rank'],
             cmp=['yoy', 'mom'], ap=None, sec='sensitive',
             tpl='{org}{period}合同签约额为{value}万元，{compare_desc}。'),
        dict(code='fulfill_rate', name='履约率', cat='经营指标',
             bdef='衡量合同按约定交付执行的比率，反映履约能力和交付质量。',
             formula='履约率 = 按期交付订单数 / 应交付订单总数 × 100%',
             syn=['履约情况', '交付率', '按期交付'],
             periods=['month', 'quarter'], dims=['org', 'time', 'product'],
             objs=['Obj_Org_Unit', 'Obj_Sales_Contract'], charts=['line', 'gauge'],
             cmp=['yoy', 'mom'], ap=None, sec='normal', unit='%',
             tpl='{org}{period}履约率为{value}%，{compare_desc}。'),
        dict(code='expense_sell', name='销售费用', cat='财务指标',
             bdef='企业销售商品过程中发生的费用。', formula='销售费用 = Σ销售环节各项费用',
             syn=['销售开支'], periods=['month', 'quarter', 'year'], dims=['org', 'time'],
             objs=['Obj_Org_Unit'], charts=['line'], cmp=['yoy', 'mom'], ap=None, sec='sensitive', tpl=None),
        dict(code='expense_admin', name='管理费用', cat='财务指标',
             bdef='企业行政管理部门为组织和管理生产经营活动发生的各项费用。',
             formula='管理费用 = Σ管理环节各项费用',
             syn=['管理开支'], periods=['month', 'quarter', 'year'], dims=['org', 'time'],
             objs=['Obj_Org_Unit'], charts=['line'], cmp=['yoy', 'mom'], ap=None, sec='sensitive', tpl=None),
        dict(code='expense_fin', name='财务费用', cat='财务指标',
             bdef='企业为筹集生产经营所需资金而发生的费用。', formula='财务费用 = 利息支出 - 利息收入 + 汇兑损失等',
             syn=['财务开支', '利息'], periods=['month', 'quarter', 'year'], dims=['org', 'time'],
             objs=['Obj_Org_Unit'], charts=['line'], cmp=['yoy', 'mom'], ap=None, sec='sensitive', tpl=None),
        dict(code='income_other', name='其他收益', cat='财务指标',
             bdef='与企业日常活动相关的政府补助等其他收益。', formula='其他收益 = 政府补助 + 其他',
             syn=['补贴', '其他收入'], periods=['month', 'quarter', 'year'], dims=['org', 'time'],
             objs=['Obj_Org_Unit'], charts=['line'], cmp=['yoy'], ap=None, sec='sensitive', tpl=None),
    ]
    cur.executemany(
        "INSERT INTO kp_metric_semantic (metric_code,metric_name,category,business_def,formula_desc,synonyms,stat_periods,dimensions,bind_objects,charts,default_compare,attribution_path,unit,security_level,answer_template,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published')",
        [(m['code'], m['name'], m['cat'], m['bdef'], m['formula'], J(m['syn']), J(m['periods']),
          J(m['dims']), J(m['objs']), J(m['charts']), J(m['cmp']), m['ap'],
          m.get('unit', '万元'), m['sec'], m.get('tpl')) for m in metrics])

    # ============ 术语词典 ============
    terms = [
        # term, ttype, mtype, target, tname, conf, examples, disamb
        ('利润', 'metric_alias', 'metric', 'profit_total', '利润总额', 0.85, '今年利润怎么样', '默认利润总额；财务深度分析场景可推荐净利润等多选'),
        ('盈利', 'metric_alias', 'metric', 'profit_total', '利润总额', 0.9, '哪个单位最盈利', None),
        ('挣钱', 'metric_alias', 'metric', 'profit_total', '利润总额', 0.85, '今年挣了多少钱', None),
        ('收入', 'metric_alias', 'metric', 'revenue_total', '营业收入', 0.85, '本月收入多少', '默认营业收入'),
        ('营收', 'metric_alias', 'metric', 'revenue_total', '营业收入', 0.95, '各板块营收对比', None),
        ('成本', 'metric_alias', 'metric', 'cost_total', '营业成本', 0.9, '成本为什么上升', None),
        ('回款', 'metric_alias', 'metric', 'receipt_rate', '回款率', 0.8, '回款情况如何', '问"率"映射回款率，问"金额"映射回款金额'),
        ('钱没回来', 'phrase', 'metric', 'overdue_amount', '逾期金额', 0.85, '哪些合同钱没回来', '出现"逾期"优先映射逾期金额'),
        ('欠款', 'phrase', 'metric', 'overdue_amount', '逾期金额', 0.85, '客户欠款排名', None),
        ('逾期', 'phrase', 'metric', 'overdue_amount', '逾期金额', 0.9, '逾期最多的单位', None),
        ('签约额', 'metric_alias', 'metric', 'contract_amount_sum', '合同签约额', 0.9, '本季度签约额', None),
        ('合同额', 'property_alias', 'metric', 'contract_amount_sum', '合同签约额', 0.85, '合同额最大的客户', '指合同维度时映射 contract_amount 属性'),
        ('履约', 'metric_alias', 'metric', 'fulfill_rate', '履约率', 0.85, '履约情况怎么样', None),
        ('单位', 'object_alias', 'object', 'Obj_Org_Unit', '组织单位', 0.8, '哪个单位利润最高', '根据用户组织权限和上下文判断二级/三级单位'),
        ('子公司', 'object_alias', 'object', 'Obj_Org_Unit', '组织单位', 0.85, '各子公司排名', None),
        ('公司', 'object_alias', 'object', 'Obj_Org_Unit', '组织单位', 0.7, '哪些公司有风险', None),
        ('板块', 'object_alias', 'object', 'Obj_Org_Unit', '组织单位', 0.85, '各板块经营情况', '限定 org_level=2'),
        ('客户', 'object_alias', 'object', 'Obj_Mkt_Customer', '客户', 0.95, '最大的客户是谁', None),
        ('甲方', 'object_alias', 'object', 'Obj_Mkt_Customer', '客户', 0.8, '甲方付款情况', None),
        ('合同', 'object_alias', 'object', 'Obj_Sales_Contract', '合同', 0.95, '有多少在执行的合同', None),
        ('订单', 'object_alias', 'object', 'Obj_Sales_Order', '订单', 0.95, '订单交付情况', None),
        ('供应商', 'object_alias', 'object', 'Obj_Scm_Supplier', '供应商', 0.95, '哪家供应商涨价了', None),
        ('库存', 'object_alias', 'object', 'Obj_Inv_Inventory', '库存', 0.9, '库存积压情况', None),
        ('风险', 'risk_expr', 'object', 'Obj_Gov_Risk', '风险事项', 0.8, '有哪些风险', '问"有哪些风险"映射风险事项；问指标风险映射预警规则'),
        ('有问题', 'risk_expr', 'object', 'Obj_Gov_Risk', '风险事项', 0.7, '哪些合同有问题', '结合上下文判断风险类型'),
        ('异常', 'risk_expr', 'object', 'Obj_Gov_Risk', '风险事项', 0.75, '本月有什么异常', None),
        ('今年', 'time_expr', 'time', 'year_current', '本年', 0.95, '今年收入', None),
        ('本月', 'time_expr', 'time', 'month_current', '本月', 0.95, '本月利润', None),
        ('上个月', 'time_expr', 'time', 'month_last', '上月', 0.95, '上个月回款率', None),
        ('最近三个月', 'time_expr', 'time', 'month_recent_3', '近3个月', 0.95, '最近三个月趋势', None),
        ('去年', 'time_expr', 'time', 'year_last', '去年', 0.95, '去年同期', None),
        ('生成报告', 'action_expr', 'action', 'Act_Gen_Report', '生成分析报告', 0.9, '生成月度经营报告', None),
        ('派给', 'action_expr', 'action', 'Act_Dispatch_Task', '派发整改任务', 0.85, '把这个问题派给财务部', None),
        ('催收', 'action_expr', 'action', 'Act_Urge_Receipt', '发起催收', 0.9, '对逾期款发起催收', None),
        ('合同问题', 'phrase', 'object', 'Obj_Gov_Risk', '风险事项', 0.6, '最近合同有什么问题', '可能指合同延期/履约异常/回款异常，需结合上下文或发起澄清'),
    ]
    import random as _r
    _r.seed(7)
    cur.executemany(
        "INSERT INTO kp_term (term,term_type,map_type,map_target,map_target_name,scenes,priority,confidence,examples,disambiguation,hit_count,correct_count,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published')",
        [(t, tt, mt, tg, tn, J(['经营分析']), 5, c, ex, dis, _r.randint(20, 500), _r.randint(0, 8))
         for t, tt, mt, tg, tn, c, ex, dis in terms])

    # ============ 规则语义 ============
    rules = [
        dict(code='Rule_Receipt_Overdue', name='回款逾期预警', rtype='threshold',
             obj='Obj_Fin_Receipt', metric='overdue_amount',
             cond={'logic': 'AND', 'conditions': [{'field': 'overdue_days', 'op': '>', 'value': 30}]},
             levels=[
                 {'level': 'red', 'color': '#f56c6c', 'condition': '逾期>180天 或 金额>1000万', 'suggestion': '立即专项督办，启动法务程序评估'},
                 {'level': 'orange', 'color': '#e6a23c', 'condition': '逾期>90天 或 金额>500万', 'suggestion': '纳入重点催收清单，每周跟进'},
                 {'level': 'yellow', 'color': '#f7ba2a', 'condition': '逾期>30天 或 金额>100万', 'suggestion': '责任单位说明原因并制定回款计划'},
                 {'level': 'blue', 'color': '#409eff', 'condition': '轻微异常', 'suggestion': '持续关注'}],
             cycle='daily', notify=['经营管理部', '责任单位财务负责人'],
             sug='建议根据逾期等级启动分级催收：红色专项督办、橙色重点催收、黄色单位说明。',
             acts=['Act_Confirm_Alert', 'Act_Dispatch_Task', 'Act_Urge_Receipt'],
             skills=['SKILL_RECEIPT_RISK']),
        dict(code='Rule_Profit_Decline', name='利润异常下降预警', rtype='composite',
             obj='Obj_Org_Unit', metric='profit_total',
             cond={'logic': 'OR', 'conditions': [
                 {'field': 'yoy_change', 'op': '<', 'value': -20, 'desc': '同比下降>20%'},
                 {'field': 'mom_change', 'op': '<', 'value': -15, 'desc': '环比下降>15%'}]},
             levels=[
                 {'level': 'red', 'color': '#f56c6c', 'condition': '同比下降>30%', 'suggestion': '集团约谈，启动专项利润归因'},
                 {'level': 'orange', 'color': '#e6a23c', 'condition': '同比下降>20%', 'suggestion': '调用利润归因Skill，单位提交说明'},
                 {'level': 'yellow', 'color': '#f7ba2a', 'condition': '同比下降>10%', 'suggestion': '纳入月度经营关注清单'}],
             cycle='monthly', notify=['经营管理部', '集团领导'],
             sug='触发后自动调用利润归因Skill分析下降原因，生成预警事件并通知经营管理部。',
             acts=['Act_Confirm_Alert', 'Act_Gen_Report'], skills=['SKILL_PROFIT_ATTR']),
        dict(code='Rule_Contract_Delay', name='合同履约延期预警', rtype='threshold',
             obj='Obj_Sales_Contract', metric='fulfill_rate',
             cond={'logic': 'AND', 'conditions': [
                 {'field': 'contract_status', 'op': '=', 'value': 'delayed'},
                 {'field': 'contract_amount', 'op': '>', 'value': 100}]},
             levels=[
                 {'level': 'red', 'color': '#f56c6c', 'condition': '金额>2000万且延期', 'suggestion': '集团督办，评估违约风险'},
                 {'level': 'orange', 'color': '#e6a23c', 'condition': '金额>800万且延期', 'suggestion': '板块协调产能，制定赶工计划'},
                 {'level': 'yellow', 'color': '#f7ba2a', 'condition': '延期合同', 'suggestion': '单位说明延期原因'}],
             cycle='daily', notify=['生产管理部', '责任单位'],
             sug='对延期合同穿透订单和生产任务，定位延期环节。',
             acts=['Act_Confirm_Alert', 'Act_Dispatch_Task'], skills=['SKILL_CONTRACT_FULFILL']),
        dict(code='Rule_Inventory_Age', name='库存积压预警', rtype='threshold',
             obj='Obj_Inv_Inventory', metric='overdue_amount',
             cond={'logic': 'AND', 'conditions': [{'field': 'age_days', 'op': '>', 'value': 300}]},
             levels=[
                 {'level': 'orange', 'color': '#e6a23c', 'condition': '库龄>500天', 'suggestion': '制定清理处置方案'},
                 {'level': 'yellow', 'color': '#f7ba2a', 'condition': '库龄>300天', 'suggestion': '分析积压原因，控制采购'}],
             cycle='daily', notify=['供应链管理部'],
             sug='对积压库存分析关联物料采购计划，建议暂停同类物料采购。',
             acts=['Act_Dispatch_Task'], skills=[]),
        dict(code='Rule_PO_Price_Abnormal', name='采购价格异常预警', rtype='yoy',
             obj='Obj_Scm_PurchaseOrder', metric='cost_total',
             cond={'logic': 'AND', 'conditions': [{'field': 'price_vs_std', 'op': '>', 'value': 10, 'desc': '采购价高于标准价10%'}]},
             levels=[
                 {'level': 'orange', 'color': '#e6a23c', 'condition': '高于标准价>20%', 'suggestion': '暂停该供应商下单，启动比价'},
                 {'level': 'yellow', 'color': '#f7ba2a', 'condition': '高于标准价>10%', 'suggestion': '供应商约谈，分析涨价原因'}],
             cycle='daily', notify=['供应链管理部', '采购单位'],
             sug='穿透分析该供应商所有在途采购单，评估对成本和利润的影响。',
             acts=['Act_Confirm_Alert'], skills=['SKILL_COST_ATTR']),
    ]
    cur.executemany(
        "INSERT INTO kp_rule (code,name,rule_type,monitor_object,monitor_metric,trigger_cond,risk_levels,apply_orgs,run_cycle,notify_targets,suggestion,actions,skills,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published')",
        [(r['code'], r['name'], r['rtype'], r['obj'], r['metric'], J(r['cond']), J(r['levels']),
          J(['ORG_GROUP']), r['cycle'], J(r['notify']), r['sug'], J(r['acts']), J(r['skills'])) for r in rules])

    # 规则运行记录
    runlogs = []
    for r in rules:
        for d in range(5):
            runlogs.append((r['code'],
                            datetime.datetime(2026, 6, 12 - d, 2, 0),
                            'auto', _r.randint(0, 25), J([]), 'success', '运行完成'))
    cur.executemany(
        "INSERT INTO kp_rule_run_log (rule_code,run_time,run_type,matched,alerts,status,message) VALUES (%s,%s,%s,%s,%s,%s,%s)", runlogs)

    # ============ 方法论 ============
    methods = [
        dict(code='MTH_Profit_Attribution', name='利润归因分析方法',
             metrics=['profit_total'], objs=['Obj_Org_Unit'],
             steps=[
                 {'seq': 1, 'name': '差异计算', 'desc': '计算本期利润与对比期利润差异'},
                 {'seq': 2, 'name': '因素拆解', 'desc': '拆解收入、成本、销售费用、管理费用、财务费用、其他收益影响'},
                 {'seq': 3, 'name': '贡献度计算', 'desc': '计算各因素贡献度 = 因素变化额 / 总变化额'},
                 {'seq': 4, 'name': '收入穿透', 'desc': '对收入下降穿透合同、订单、客户'},
                 {'seq': 5, 'name': '成本穿透', 'desc': '对成本上升穿透采购单、物料、供应商'},
                 {'seq': 6, 'name': '费用穿透', 'desc': '对费用上升穿透费用科目和责任单位'},
                 {'seq': 7, 'name': '结论生成', 'desc': '生成Top原因和管理建议'},
                 {'seq': 8, 'name': '闭环动作', 'desc': '支持生成利润归因报告或派发整改任务'}],
             tree={'code': 'profit_total', 'name': '利润总额', 'op': None, 'children': [
                 {'code': 'revenue_total', 'name': '营业收入', 'op': '+'},
                 {'code': 'cost_total', 'name': '营业成本', 'op': '-'},
                 {'code': 'expense_sell', 'name': '销售费用', 'op': '-'},
                 {'code': 'expense_admin', 'name': '管理费用', 'op': '-'},
                 {'code': 'expense_fin', 'name': '财务费用', 'op': '-'},
                 {'code': 'income_other', 'name': '其他收益', 'op': '+'}]},
             paths=[
                 {'name': '收入下降路径', 'path': ['Obj_Org_Unit', 'Obj_Sales_Contract', 'Obj_Sales_Order', 'Obj_Mkt_Customer']},
                 {'name': '成本上升路径', 'path': ['Obj_Org_Unit', 'Obj_Scm_PurchaseOrder', 'Obj_Scm_Material', 'Obj_Scm_Supplier']}],
             algo='贡献度 = 因素变化额 / 总变化额 × 100%',
             charts=['waterfall', 'attribution_tree'],
             tpl='本期{org}利润总额{value}万元，较{compare_period}{direction}{diff}万元({pct}%)。主要原因：{top_factors}。建议：{suggestions}',
             skills=['SKILL_PROFIT_ATTR']),
        dict(code='MTH_Receipt_Risk', name='回款风险分析方法',
             metrics=['receipt_rate', 'overdue_amount'], objs=['Obj_Org_Unit', 'Obj_Sales_Contract'],
             steps=[
                 {'seq': 1, 'name': '逾期识别', 'desc': '识别所有逾期回款记录及账龄分布'},
                 {'seq': 2, 'name': '风险分级', 'desc': '按逾期天数和金额划分红橙黄蓝等级'},
                 {'seq': 3, 'name': '客户穿透', 'desc': '沿组织→合同→回款→客户路径定位高风险客户'},
                 {'seq': 4, 'name': '账龄分析', 'desc': '分析30/90/180天账龄结构'},
                 {'seq': 5, 'name': '催收建议', 'desc': '生成分级催收建议和重点客户清单'}],
             tree=None,
             paths=[{'name': '回款风险路径', 'path': ['Obj_Org_Unit', 'Obj_Sales_Contract', 'Obj_Fin_Receipt', 'Obj_Mkt_Customer']}],
             algo='风险评分 = 0.5×逾期金额占比 + 0.3×逾期天数分 + 0.2×客户信用分',
             charts=['rank', 'aging_chart'],
             tpl='{org}逾期金额{value}万元，涉及{contract_count}个合同、{customer_count}个客户。高风险客户：{top_customers}。建议：{suggestions}',
             skills=['SKILL_RECEIPT_RISK']),
        dict(code='MTH_Revenue_Attribution', name='收入归因分析方法',
             metrics=['revenue_total'], objs=['Obj_Org_Unit'],
             steps=[
                 {'seq': 1, 'name': '差异计算', 'desc': '计算本期与对比期收入差异'},
                 {'seq': 2, 'name': '维度拆解', 'desc': '按单位、产品线、客户拆解收入变化'},
                 {'seq': 3, 'name': '合同穿透', 'desc': '定位收入变化的主要合同'},
                 {'seq': 4, 'name': '结论生成', 'desc': '生成收入变化原因和建议'}],
             tree=None,
             paths=[{'name': '收入分析路径', 'path': ['Obj_Org_Unit', 'Obj_Sales_Contract', 'Obj_Mkt_Customer']}],
             algo='贡献度 = 维度成员变化额 / 总变化额', charts=['bar', 'rank'],
             tpl='{org}{period}收入{value}万元，{compare_desc}。', skills=['SKILL_QA']),
        dict(code='MTH_Cost_Attribution', name='成本归因分析方法',
             metrics=['cost_total'], objs=['Obj_Org_Unit'],
             steps=[
                 {'seq': 1, 'name': '差异计算', 'desc': '计算成本变化'},
                 {'seq': 2, 'name': '采购穿透', 'desc': '穿透采购单分析价格和数量因素'},
                 {'seq': 3, 'name': '供应商定位', 'desc': '定位涨价供应商和物料'},
                 {'seq': 4, 'name': '建议生成', 'desc': '生成比价、换源等降本建议'}],
             tree=None,
             paths=[{'name': '成本上升路径', 'path': ['Obj_Org_Unit', 'Obj_Scm_PurchaseOrder', 'Obj_Scm_Material', 'Obj_Scm_Supplier']}],
             algo='价格因素 = (本期价-基期价)×本期量; 数量因素 = (本期量-基期量)×基期价',
             charts=['waterfall', 'rank'],
             tpl='{org}成本{value}万元，{compare_desc}。主要涨价供应商：{top_suppliers}。', skills=['SKILL_COST_ATTR']),
        dict(code='MTH_Contract_Fulfill', name='合同履约分析方法',
             metrics=['fulfill_rate'], objs=['Obj_Sales_Contract'],
             steps=[
                 {'seq': 1, 'name': '履约盘点', 'desc': '统计合同履约状态分布'},
                 {'seq': 2, 'name': '延期定位', 'desc': '穿透订单和生产任务定位延期环节'},
                 {'seq': 3, 'name': '产能分析', 'desc': '分析生产单位产能负荷'},
                 {'seq': 4, 'name': '建议生成', 'desc': '生成赶工、调配产能建议'}],
             tree=None,
             paths=[{'name': '履约穿透路径', 'path': ['Obj_Sales_Contract', 'Obj_Sales_Order', 'Obj_Prod_Task']}],
             algo=None, charts=['gantt', 'rank'],
             tpl='合同{contract}履约率{value}%，延期环节：{delay_points}。', skills=['SKILL_CONTRACT_FULFILL']),
    ]
    cur.executemany(
        "INSERT INTO kp_method (code,name,scenes,apply_metrics,apply_objects,steps,decompose_tree,graph_paths,contribution_algo,output_charts,output_template,bind_skills,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published')",
        [(m['code'], m['name'], J(['经营分析']), J(m['metrics']), J(m['objs']), J(m['steps']),
          J(m['tree']) if m['tree'] else None, J(m['paths']), m['algo'], J(m['charts']),
          m['tpl'], J(m['skills'])) for m in methods])

    # ============ 图谱模型 / 任务 ============
    cur.execute(
        "INSERT INTO kp_graph_model (code,name,scene,description,include_objects,include_links,sync_mode,sync_cycle,perm_policy,status) "
        "VALUES ('graph_business_core','经营核心关系图谱','经营数据分析','支撑经营穿透、回款风险、利润归因的核心业务关系图谱',%s,%s,'batch','daily','inherit_object','published')",
        (J(['Obj_Org_Unit', 'Obj_Mkt_Customer', 'Obj_Sales_Contract', 'Obj_Sales_Order', 'Obj_Fin_Receipt',
            'Obj_Scm_Supplier', 'Obj_Scm_PurchaseOrder', 'Obj_Scm_Material', 'Obj_Inv_Inventory',
            'Obj_Prod_Task', 'Obj_Gov_Risk']),
         J(['Link_Org_Has_Sub', 'Link_Org_Has_Contract', 'Link_Customer_Has_Contract', 'Link_Contract_Has_Order',
            'Link_Contract_Has_Receipt', 'Link_Order_Drive_Task', 'Link_Org_Has_PO', 'Link_PO_To_Supplier',
            'Link_PO_To_Material', 'Link_Material_Has_Inventory', 'Link_Org_Has_Inventory',
            'Link_Risk_Refer_Object', 'Link_Org_Has_Risk'])))
    cur.execute(
        "INSERT INTO kp_graph_task (name,graph_code,data_sources,entity_rules,relation_rules,dedup_rules,disambig_rules,incr_field,run_cycle,retry_times,quality_rules,perm_policy,status) "
        "VALUES ('经营核心图谱每日构建','graph_business_core',%s,%s,%s,%s,%s,'update_time','daily',3,%s,'inherit_object','published')",
        (J(['biz_org', 'biz_customer', 'biz_contract', 'biz_order', 'biz_receipt', 'biz_supplier',
            'biz_purchase_order', 'biz_material', 'biz_inventory', 'biz_prod_task', 'biz_risk']),
         J({'rule': '按对象主键生成节点，显示字段作为节点名称'}),
         J({'rule': '按关系类型源/目标关联字段生成边'}),
         J({'rule': '主键去重'}), J({'rule': '客户名称、供应商名称统一编码合并'}),
         J(['isolated_node', 'relation_integrity', 'duplicate_node'])))

    # ============ RAG 文档 ============
    docs = [
        dict(name='际华集团经营分析管理办法(2026版)', dtype='regulation', tags=['经营分析', '管理制度'],
             sec='sensitive', roles=['经营管理部', '集团领导', '二级单位负责人'],
             content="""第一章 总则
第一条 为规范际华集团经营分析工作，提升经营决策科学化水平，依据集团管理制度制定本办法。
第二条 本办法适用于集团总部、各板块及二级单位的经营分析工作。
第二章 经营分析体系
第三条 经营分析体系包括月度经营分析、季度经营分析会、年度经营总结三个层级。
第四条 月度经营分析重点关注：营业收入、利润总额、回款率、合同签约额、履约率五项核心指标。
第五条 各二级单位应于每月5日前报送经营数据，经营管理部于每月10日前完成集团月度经营分析报告。
第三章 指标管理
第六条 利润总额为集团考核核心指标，口径为：营业收入-营业成本-期间费用+其他收益。
第七条 回款率考核目标为90%，低于85%的单位需提交专项说明。
第八条 逾期金额超过500万元的单位，纳入集团重点督办范围。
第四章 异常处置
第九条 利润同比下降超过20%的单位，须在5个工作日内提交利润归因分析报告。
第十条 经营预警事件实行分级管理：红色预警由集团领导督办，橙色预警由经营管理部跟踪，黄色预警由责任单位自行处置并备案。"""),
        dict(name='应收账款与回款管理制度', dtype='regulation', tags=['回款', '应收账款', '风险'],
             sec='sensitive', roles=['财务部', '经营管理部', '二级单位负责人'],
             content="""第一条 为加强应收账款管理，加速资金回笼，防范回款风险，制定本制度。
第二条 合同签订时必须明确回款节点和账期，原则上账期不超过90天，政府和军队客户可放宽至180天。
第三条 回款风险分级标准：
（一）红色风险：逾期超过180天或逾期金额超过1000万元，立即启动专项督办，必要时启动法务程序；
（二）橙色风险：逾期超过90天或逾期金额超过500万元，纳入重点催收清单，每周跟进；
（三）黄色风险：逾期超过30天或逾期金额超过100万元，责任单位提交说明并制定回款计划；
（四）蓝色风险：轻微逾期，持续关注。
第四条 各单位应于每月末核对应收账款账龄，30天、90天、180天账龄结构纳入月度经营分析。
第五条 对信用等级为B级及以下客户，新签合同须收取不低于30%预付款。
第六条 催收责任：合同经办人为第一责任人，单位财务负责人为监督责任人。"""),
        dict(name='2026年5月集团月度经营分析报告(摘要)', dtype='report', tags=['月度报告', '经营分析'],
             sec='confidential', roles=['集团领导', '经营管理部'],
             content="""一、总体经营情况
2026年5月集团实现营业收入4.9亿元，同比增长6.2%；利润总额3,860万元，同比下降8.5%；回款率86.3%，低于90%考核目标。
二、重点问题
1. 际华3521特种装备公司利润同比下降31%，主要因凯夫拉纤维布等原材料采购价格上涨18%，叠加两个大额防护装备合同延期交付；
2. 际华3543针织公司回款率降至74%，某煤炭集团客户逾期金额达820万元，已触发橙色预警；
3. 库存方面，3514面料公司迷彩印染布库龄超过400天，积压金额约600万元。
三、管理建议
1. 对3521公司启动成本专项归因，评估供应商比价换源方案；
2. 对3543公司逾期客户启动重点催收，必要时调整合作策略；
3. 督促3514公司制定库存清理处置方案。"""),
        dict(name='利润归因分析操作指引', dtype='faq', tags=['利润', '归因分析', '操作指引'],
             sec='normal', roles=['全体业务用户'],
             content="""Q1：什么是利润归因分析？
A：利润归因分析是将利润变化拆解为收入、成本、费用等因素的影响，并计算各因素贡献度，定位变化主因的分析方法。
Q2：如何发起利润归因分析？
A：在智能问数中输入"XX单位利润为什么下降"，或在预警中心利润预警事件上点击"归因分析"。
Q3：贡献度怎么计算？
A：贡献度 = 因素变化额 / 利润总变化额 × 100%。例如利润下降1000万，其中成本上升贡献600万，则成本因素贡献度60%。
Q4：归因结果能下钻吗？
A：可以。收入下降可穿透到合同、订单、客户；成本上升可穿透到采购单、物料、供应商。
Q5：如何生成归因报告？
A：归因结果页面点击"生成报告"，系统将按报告模板自动生成并引用知识库制度依据。"""),
        dict(name='典型案例：某公司回款风险化解实践', dtype='case', tags=['回款', '案例', '催收'],
             sec='normal', roles=['全体业务用户'],
             content="""案例背景：2025年三季度，际华3502公司某行政执法制服合同（金额2,300万元）出现回款逾期，逾期金额920万元，逾期天数最高达160天，触发橙色预警。
处置过程：
1. 预警触发后，系统自动派发整改任务至3502公司财务负责人；
2. 通过知识图谱穿透发现该客户在3503公司另有一个合同也存在45天逾期，合并评估客户整体风险；
3. 公司层面启动重点催收：高层对接客户主管部门、调整后续批次发货节奏、协商分期回款计划；
4. 两个月内回款680万元，剩余240万元按分期计划于次季度收回，风险闭环。
经验总结：
1. 跨单位客户风险需要图谱穿透合并评估，避免信息孤岛；
2. 催收要"先保合作再保回款"，分期方案优于强硬停货；
3. 预警-派单-跟踪-闭环的数字化流程将处置周期缩短约40%。"""),
        dict(name='智能问数常见问题FAQ', dtype='faq', tags=['智能问数', 'FAQ'],
             sec='normal', roles=['全体业务用户'],
             content="""Q1：智能问数支持哪些问题？
A：支持指标查询（如"本月集团利润多少"）、排名对比（如"哪个单位收入最高"）、趋势分析（如"最近6个月回款率趋势"）、原因分析（如"3521公司利润为什么下降"）、风险查询（如"有哪些红色预警"）。
Q2：为什么有些数据我看不到？
A：系统按照您的组织权限和数据密级控制可见范围，机密指标仅限授权角色查看。
Q3：问数答案的口径是什么？
A：答案统一使用指标语义中心发布的口径，点击答案中的指标名称可查看业务定义和公式说明。
Q4：如何纠正错误的理解？
A：答案下方点"踩"并填写说明，知识管理员将根据反馈优化术语映射。"""),
    ]
    for d in docs:
        cur.execute(
            "INSERT INTO kp_document (name,doc_type,scenes,domains,security_level,visible_roles,effective_date,tags,content,uploader,parse_status,chunk_status,vector_status,status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'知识管理员','parsed','pending','pending','draft')",
            (d['name'], d['dtype'], J(['经营分析']), J(['finance', 'sales']), d['sec'],
             J(d['roles']), datetime.date(2026, 1, 1), J(d['tags']), d['content']))

    # ============ Skill ============
    skills = [
        ('SKILL_QA', '智能问数 Skill', '将自然语言问题转化为指标查询并组织回答',
         {'terms': '术语词典', 'metrics': '指标语义', 'ontology': '本体对象与关系', 'perm': '权限语义'}),
        ('SKILL_PROFIT_ATTR', '利润归因 Skill', '执行利润归因方法论，生成归因树和管理建议',
         {'metric': 'profit_total 指标语义', 'method': 'MTH_Profit_Attribution 方法论', 'graph': '图谱归因路径'}),
        ('SKILL_RECEIPT_RISK', '回款风险 Skill', '执行回款风险分析方法论，输出风险客户清单',
         {'metric': 'receipt_rate/overdue_amount 指标语义', 'rule': 'Rule_Receipt_Overdue 账龄规则', 'graph': '合同-回款图谱'}),
        ('SKILL_COST_ATTR', '成本归因 Skill', '穿透采购定位涨价供应商和物料',
         {'metric': 'cost_total 指标语义', 'method': 'MTH_Cost_Attribution 方法论', 'graph': '采购-供应商图谱'}),
        ('SKILL_CONTRACT_FULFILL', '合同履约分析 Skill', '分析合同履约和延期环节',
         {'metric': 'fulfill_rate 指标语义', 'method': 'MTH_Contract_Fulfill 方法论'}),
        ('SKILL_REPORT_GEN', '报告生成 Skill', '按模板生成经营分析报告并引用RAG知识',
         {'metrics': '指标解释', 'method': '分析方法论', 'rag': '报告模板与制度文档'}),
        ('SKILL_ALERT_DETECT', '预警检测 Skill', '按规则语义扫描监控对象生成预警事件',
         {'rules': '规则语义', 'metrics': '指标语义', 'objects': '可监控对象'}),
    ]
    cur.executemany(
        "INSERT INTO kp_skill (code,name,description,depend_knowledge,call_count) VALUES (%s,%s,%s,%s,%s)",
        [(c, n, d, J(dk), _r.randint(50, 1200)) for c, n, d, dk in skills])

    # ============ 治理数据: 审核单 / 版本 / 审计 ============
    reviews = [
        ('REVIEW-0001', 'object', 13, 'Obj_Inv_Project', '投资项目', '吴投资', 'create',
         {'desc': '新增投资项目对象，实现If_Searchable等5个接口'}, ['投资分析页面(规划)'], 'pending', None, None, None),
        ('REVIEW-0002', 'metric', 1, 'profit_total', '利润总额', '刘财务', 'update',
         {'field': 'formula_desc', 'old': '收入-成本-费用', 'new': '营业收入-营业成本-期间费用+其他收益'},
         ['智能问数', '月度经营报告', 'SKILL_PROFIT_ATTR'], 'approved', '王指标', '口径调整符合财务准则', datetime.datetime(2026, 6, 10, 14, 30)),
        ('REVIEW-0003', 'term', 35, '合同问题', '合同问题', '李术语', 'create',
         {'desc': '新增多义术语"合同问题"及消歧规则'}, ['智能问数'], 'pending', None, None, None),
        ('REVIEW-0004', 'rule', 5, 'Rule_PO_Price_Abnormal', '采购价格异常预警', '郑风控', 'update',
         {'field': 'trigger_cond', 'old': '>15%', 'new': '>10%'}, ['预警中心', 'SKILL_COST_ATTR'],
         'rejected', '陈供应', '阈值过低会产生大量噪音预警，建议保持15%', datetime.datetime(2026, 6, 11, 9, 0)),
        ('REVIEW-0005', 'document', 3, None, '2026年5月集团月度经营分析报告(摘要)', '知识管理员', 'create',
         {'desc': '上传5月经营分析报告'}, ['RAG问答', 'SKILL_REPORT_GEN'], 'pending', None, None, None),
    ]
    cur.executemany(
        "INSERT INTO kp_review (review_no,knowledge_type,knowledge_id,knowledge_code,knowledge_name,applicant,change_type,change_detail,impact_scope,review_status,reviewer,review_comment,reviewed_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [(a, b, c, d, e, f, g, J(h), J(i), j, k, l, m) for a, b, c, d, e, f, g, h, i, j, k, l, m in reviews])

    versions = [
        ('object', 3, 'Obj_Sales_Contract', 'v1.0', {'name': '合同', 'property_count': 10}, '初版发布', '张销售'),
        ('metric', 1, 'profit_total', 'v1.0', {'formula': '收入-成本-费用'}, '初版发布', '刘财务'),
        ('metric', 1, 'profit_total', 'v1.1', {'formula': '营业收入-营业成本-期间费用+其他收益'}, '口径调整：明确期间费用和其他收益', '刘财务'),
        ('rule', 1, 'Rule_Receipt_Overdue', 'v1.0', {'threshold': '逾期>30天'}, '初版发布', '郑风控'),
        ('method', 1, 'MTH_Profit_Attribution', 'v1.0', {'steps': 8}, '初版发布', '经营分析组'),
    ]
    cur.executemany(
        "INSERT INTO kp_version (knowledge_type,knowledge_id,knowledge_code,version,snapshot,change_note,operator) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        [(a, b, c, d, J(e), f, g) for a, b, c, d, e, f, g in versions])

    audits = [
        ('ontology', 'publish', 'object', 'Obj_Sales_Contract', '合同', '张销售', {'version': 'v1.0'}),
        ('metric', 'update', 'metric', 'profit_total', '利润总额', '刘财务', {'field': 'formula_desc'}),
        ('metric', 'approve', 'metric', 'profit_total', '利润总额', '王指标', {'review_no': 'REVIEW-0002'}),
        ('rule', 'publish', 'rule', 'Rule_Receipt_Overdue', '回款逾期预警', '郑风控', {'version': 'v1.0'}),
        ('graph', 'run', 'graph_task', 'graph_business_core', '经营核心图谱每日构建', 'system', {'result': 'success'}),
        ('term', 'create', 'term', '合同问题', '合同问题', '李术语', {'status': 'draft'}),
        ('rag', 'create', 'document', None, '2026年5月集团月度经营分析报告(摘要)', '知识管理员', {'doc_type': 'report'}),
        ('qa', 'call', 'skill', 'SKILL_QA', '智能问数 Skill', 'AI-Agent', {'question': '哪个单位回款风险最高'}),
    ]
    cur.executemany(
        "INSERT INTO kp_audit_log (module,action,knowledge_type,knowledge_code,knowledge_name,operator,detail) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        [(a, b, c, d, e, f, J(g)) for a, b, c, d, e, f, g in audits])

    db.commit()
    for t in tables:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t}: {cur.fetchone()[0]}')
    db.close()


if __name__ == '__main__':
    main()
