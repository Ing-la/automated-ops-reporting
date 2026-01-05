# visualization 模块说明

## 功能概述

visualization模块负责生成运营分析报告所需的图表，采用蓝色简约科技风格。

## 模块结构

- `generate_charts.py`: 图表生成主模块
- `__init__.py`: 模块导出

## 生成的图表

### 核心图表（6个）

1. **转化漏斗图** (`overview_conversion_funnel`)
   - 展示：总测试记录 → 已完成测试 → 接入意向 → 开通 → 调用
   - 位置：第一部分 - 总体运营盘点

2. **测试周期分布直方图** (`process_test_cycle_distribution`)
   - 展示：测试周期分布、平均值、中位数、超长测试标记
   - 位置：第二部分 - 流程与进度分析

3. **转化率对比柱状图** (`conversion_rate_comparison`)
   - 展示：整体调用率、开通→调用转化率、接入意向→调用转化率
   - 位置：第三部分 - 转化与收益分析

4. **产品调用率TOP 10柱状图** (`conversion_product_top10`)
   - 展示：调用率最高的10个产品
   - 位置：第三部分 - 转化与收益分析

5. **客户调用率TOP 10柱状图** (`conversion_customer_top10`)
   - 展示：调用率最高的10个客户
   - 位置：第三部分 - 转化与收益分析

6. **滞后场景分布饼图** (`risk_lag_scenarios`)
   - 展示：各滞后场景的数量和占比
   - 位置：第四部分 - 滞后与风险识别

## 图表风格

- **配色方案**：蓝色科技风格
  - 主蓝色：#1E88E5
  - 浅蓝色：#42A5F5
  - 深蓝色：#0D47A1
- **字体**：支持中文显示（SimHei、Microsoft YaHei）
- **样式**：简约、专业、科技感

## 使用方法

### 基本使用

```python
from src.visualization import generate_all_charts

# 生成所有图表
chart_paths = generate_all_charts('2025-12')
```

### 单独生成某个图表

```python
from src.visualization.generate_charts import (
    generate_conversion_funnel,
    generate_test_cycle_distribution,
    # ... 其他图表函数
)
from src.report.generate_report import load_metrics_result

metrics_result = load_metrics_result('2025-12')

# 生成转化漏斗图
funnel_path = generate_conversion_funnel(metrics_result, '2025-12')
```

## 输出文件

所有图表保存在 `output/figures/` 目录下，文件命名格式：
- `{chart_name}_{YYYY_MM}.png`
- 例如：`overview_conversion_funnel_2025_12.png`

## 依赖要求

- `matplotlib>=3.7.0`
- `numpy>=1.24.0`
- `pandas>=2.0.0`

安装：
```bash
pip install matplotlib numpy pandas
```

## 注意事项

1. **中文字体**：确保系统安装了中文字体（SimHei、Microsoft YaHei等）
2. **图表大小**：默认DPI为300，适合打印和展示
3. **文件格式**：所有图表保存为PNG格式
4. **错误处理**：如果数据不足，会生成空图表提示




