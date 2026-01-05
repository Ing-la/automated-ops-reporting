# metrics 模块说明

## 功能概述

metrics模块负责计算所有运营分析指标，支持产品/客户/部门/销售多维度分析。

**核心设计原则**：
- **聚焦新增和新改动**：重点关注本月新进展和近3个月的变化，而非全量历史统计
- **全量统计作为汇总**：必要的全量统计量作为汇总信息，但不作为主要分析内容
- **近3个月数据**：流程分析、转化分析、风险识别都基于近3个月数据，避免被旧数据稀释

## 模块结构

- `status_changes.py`: 状态变化识别（对比本月和上月snapshot）
- `overview_metrics.py`: 总体运营盘点指标
- `process_metrics.py`: 流程与进度分析指标
- `conversion_metrics.py`: 转化与收益分析指标（核心）
- `risk_metrics.py`: 滞后与风险识别指标
- `calculate_all.py`: 指标计算主入口

## 使用方法

### 基本使用

```python
from metrics.calculate_all import calculate_all_metrics

# 计算2025年12月的所有指标
result = calculate_all_metrics('2025-12')

# 访问各项指标
overview = result['overview']  # 总体运营盘点
process = result['process']  # 流程与进度分析
conversion = result['conversion']  # 转化与收益分析
risk = result['risk']  # 滞后与风险识别
```

### 指标结构

#### 1. 总体运营盘点 (`overview`)

包含以下字段：
- `scale_and_structure`: 规模与结构概览（本月新增）
  - `new_test_count`: 本月新增测试量
  - `new_customer_count`: 新增客户数
  - `new_product_count`: 新增子产品数
  - `sample_size_distribution`: 样本量分布统计
- `overall_progress`: 截至本月的整体进展（全量汇总）
  - `date_range`: 数据起止日期
  - `total_records`: 总测试记录数
  - `completed_test_count`: 已完成测试数量
  - `has_access_intent_count`: 已明确接入意向数量
  - `opened_count`: 已开通数量
  - `called_count`: 已调用数量（核心收益指标）
- `monthly_new_progress`: 本月新增进展
  - `new_completed_test`: 本月新完成测试（新增+状态更新）
  - `new_opened`: 本月新开通（新增+状态更新）
  - `new_called`: 本月新调用（新增+状态更新，核心收益指标）
  - `new_opened_list`: 本月新开通详细列表（前50条）
  - `new_called_list`: 本月新调用详细列表（前50条）

#### 2. 流程与进度分析 (`process`) - 近3个月数据

基于**申请日期**筛选近3个月的数据（从当前月份往前推90天）：
- `test_progress`: 测试流程进度分析
  - `period`: 数据范围说明（"近3个月"）
  - `total_count`: 近3个月总记录数
  - `has_test_return_date_count`: 有测试返回日期的记录数
  - `test_completion_rate`: 测试完成率
  - `status_distribution`: 测试状态分布
- `test_cycle`: 测试周期与效率
  - `period`: 数据范围说明
  - `mean`: 平均测试周期（天）
  - `median`: 中位数测试周期
  - `long_test_count`: 超长测试数量（>30天）
  - `long_test_records`: 超长测试记录列表（前30条）

#### 3. 转化与收益分析 (`conversion`) - 核心，近3个月数据

基于**申请日期**筛选近3个月的数据：
- `core_conversion`: 收益转化核心指标
  - `period`: 数据范围说明
  - `overall_call_rate`: 整体调用率
  - `opened_to_call_rate`: 开通→调用转化率
  - `intent_to_call_rate`: 接入意向→调用转化率
- `product_analysis`: 产品维度收益分析
  - `top_products`: 调用率Top 10产品
  - `zero_call_products`: 长期无调用产品
- `customer_analysis`: 客户维度收益分析
  - `high_call_customers`: 高调用客户
  - `intent_not_called_customers`: 有意向但未调用客户清单
- `intent_not_opened_list`: 有意向但未开通列表（近3个月）

#### 4. 滞后与风险识别 (`risk`) - 近3个月数据

基于**申请日期**筛选近3个月的数据：
- `completed_no_intent`: 测试完成但长期无意向
- `intent_not_opened`: 明确有意向但未开通
- `opened_not_called`: 已开通但长期未调用（重点风险）
- `not_called_reasons`: 不调用原因结构分析

## 核心设计原则

### 1. 聚焦新增和新改动

- **总体运营盘点**：重点关注本月新进展，全量统计作为汇总（需注明起止日期）
- **流程与进度分析**：基于近3个月数据，列出超长测试周期记录
- **转化与收益分析**：基于近3个月数据，列出有意向未开通记录
- **风险识别**：基于近3个月数据，列出关键风险点（超长测试、有意向未开通、开通未调用）

### 2. 状态变化识别

metrics模块会对比本月和上月的snapshot，识别：
- **新增记录**：主键在上月snapshot中不存在
- **状态更新**：主键存在，但状态字段发生了变化（如：未开通→已开通，未调用→已调用）

这样可以准确反映真实的业务转化和收益，避免低估。

### 2. 多维度分析

支持以下维度的分析：
- 产品维度：各子产品调用率、调用贡献分布
- 客户维度：客户调用率分布、高调用客户识别
- 销售维度：可按销售人员维度分析（待扩展）

### 3. 收益判断标准

**是否调用 = 是否产生收益（唯一标准）**

所有价值、转化、高价值判断，最终应锚定在"已调用"字段。

## 注意事项

1. **首次运行**：如果上月的snapshot不存在，会使用None作为previous_snapshot，所有记录都会被识别为新增记录
2. **主键定义**：使用"客户简称 + 子产品名称 + 申请日期"作为主键，用于匹配和对比
3. **状态更新**：会识别状态变化（0→1），包括新完成测试、新开通、新调用等
4. **数据范围**：
   - **总体运营盘点**：本月新进展（重点）+ 全量汇总（注明起止日期）
   - **流程与进度分析**：近3个月数据（基于申请日期筛选）
   - **转化与收益分析**：近3个月数据（基于申请日期筛选）
   - **风险识别**：近3个月数据（基于申请日期筛选）
5. **近3个月定义**：从当前月份往前推90天（约3个月）

