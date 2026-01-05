"""
可视化模块

生成运营分析报告所需的图表
"""

from .generate_charts import (
    generate_conversion_funnel,
    generate_conversion_rate_comparison,
    generate_product_top10,
    generate_customer_top10,
    generate_all_charts,
)

__all__ = [
    "generate_conversion_funnel",
    "generate_conversion_rate_comparison",
    "generate_product_top10",
    "generate_customer_top10",
    "generate_all_charts",
]


