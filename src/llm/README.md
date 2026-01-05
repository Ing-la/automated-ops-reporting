# LLM模块说明

## 功能概述

LLM模块负责调用大模型对已计算完成的结构化指标进行运营解读，生成总体概览、趋势说明与风险提示。

**重要原则**：
- 大模型仅用于解读，不参与数据清洗、指标计算、业务规则判断
- 所有计算由Python明确实现，确保结果稳定、可复现
- LLM基于结构化的metrics结果生成文本，不直接接触原始数据

## 模块结构

- `prepare_context.py`: 从完整JSON中提取关键指标，减少token消耗
- `generate_insights.py`: 调用LLM生成分析解读文本
- `__init__.py`: 模块导出

## 使用方法

### 基本使用

```python
from src.llm import generate_llm_insights, save_llm_insights

# 生成2025年12月的LLM解读
insights = generate_llm_insights('2025-12')
save_llm_insights('2025-12', insights)
```

### 使用OpenAI API

```python
import os
from src.llm import OpenAIClient, generate_llm_insights

# 设置API密钥
os.environ['OPENAI_API_KEY'] = 'your-api-key'

# 使用OpenAI客户端
client = OpenAIClient(model='gpt-4')
insights = generate_llm_insights('2025-12', llm_client=client)
```

### 使用Dify API

```python
import os
from src.llm import DifyClient, generate_llm_insights

# 设置API密钥和基础URL
os.environ['DIFY_API_KEY'] = 'your-api-key'
os.environ['DIFY_BASE_URL'] = 'https://api.dify.ai/v1'

# 使用Dify客户端
client = DifyClient()
insights = generate_llm_insights('2025-12', llm_client=client)
```

### 自定义提示词模板

```python
from src.llm import generate_llm_insights

custom_template = """
你是一位运营数据分析专家。
请基于以下数据生成分析报告：

{metrics_data}
"""

insights = generate_llm_insights(
    '2025-12',
    prompt_template=custom_template
)
```

### 控制token消耗

```python
from src.llm import generate_llm_insights

# 限制列表数据保留条数，减少token消耗
insights = generate_llm_insights(
    '2025-12',
    max_list_items=5  # 默认10条，可以减少到5条
)
```

## 数据源

LLM模块从 `output/metrics_result_YYYY_MM.json` 读取数据。

**数据提取策略**：
1. 保留所有数值型汇总指标（完整保留）
2. 列表数据只保留TOP N条（默认10条，可配置）
3. 移除不必要的详细记录

**预期效果**：
- 原始JSON：~15,790 tokens
- 优化后：~3,000-5,000 tokens（减少70-80%）
- 保留所有关键信息，仅限制列表长度

## 输出内容

LLM生成的解读文本包含以下四个部分：

### 一、总体运营盘点解读
- 规模与结构概览解读
- 整体进展评价
- 对比上月的变化趋势

### 二、流程与进度分析解读
- 测试流程效率评价
- 测试周期分析
- 超长测试周期的风险提示

### 三、转化与收益分析解读（核心）
- 转化率指标评价
- 产品维度收益分析
- 客户维度收益分析
- 转化漏斗优化建议

### 四、滞后与风险识别解读
- 风险点说明
- 滞后场景原因分析
- 改进建议

## 输出文件

LLM解读文本保存在 `output/llm_insights/insights_YYYY_MM.md`

## 环境变量配置

### OpenAI
```bash
export OPENAI_API_KEY="your-api-key"
```

### Dify
```bash
export DIFY_API_KEY="your-api-key"
export DIFY_BASE_URL="https://api.dify.ai/v1"  # 可选，有默认值
```

## 注意事项

1. **API密钥安全**：不要将API密钥提交到代码仓库，使用环境变量管理
2. **Token消耗**：默认配置已优化token消耗，如需进一步减少可调整`max_list_items`参数
3. **API调用失败**：如果API调用失败，会抛出异常，需要检查网络连接和API密钥
4. **Dify API格式**：Dify API的具体格式可能需要根据实际API文档调整，当前实现提供了基础框架

## 集成到报告生成流程

LLM模块可以集成到报告生成流程中：

```python
from src.report.generate_report import generate_monthly_report
from src.llm import generate_llm_insights, save_llm_insights

# 生成报告
report_path = generate_monthly_report('2025-12')

# 生成LLM解读
insights = generate_llm_insights('2025-12')
insights_path = save_llm_insights('2025-12', insights)

# 可以将LLM解读合并到报告中（需要修改report模块）
```

## 依赖要求

- `openai` (可选，使用OpenAI API时需要)
- `requests` (可选，使用Dify API时需要)

安装：
```bash
pip install openai requests
```




