"""报告生成模块"""

from .generate_report import generate_monthly_report, load_metrics_result
from .generate_tables import generate_all_tables

__all__ = ['generate_monthly_report', 'load_metrics_result', 'generate_all_tables']

