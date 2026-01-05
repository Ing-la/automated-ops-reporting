"""
指标计算主入口

整合所有metrics模块，提供统一的指标计算接口
"""

import pandas as pd
import json
from typing import Dict, Optional
from pathlib import Path

from .overview_metrics import calculate_overview_metrics
from .process_metrics import calculate_process_metrics
from .conversion_metrics import calculate_conversion_metrics
from .risk_metrics import calculate_risk_metrics


def load_snapshot(month: str, snapshot_dir: Path) -> Optional[pd.DataFrame]:
    """
    加载snapshot文件
    
    Args:
        month: 月份，格式YYYY-MM
        snapshot_dir: snapshot目录路径
    
    Returns:
        snapshot DataFrame，如果文件不存在返回None
    """
    # 优先尝试CSV格式
    csv_file = snapshot_dir / f"snapshot_{month.replace('-', '_')}.csv"
    if csv_file.exists():
        return pd.read_csv(csv_file)
    
    # 尝试parquet格式
    parquet_file = snapshot_dir / f"snapshot_{month.replace('-', '_')}.parquet"
    if parquet_file.exists():
        try:
            return pd.read_parquet(parquet_file)
        except:
            pass
    
    return None


def calculate_all_metrics(current_month: str, 
                         snapshot_dir: Optional[Path] = None) -> Dict:
    """
    计算所有指标
    
    Args:
        current_month: 当前月份，格式YYYY-MM
        snapshot_dir: snapshot目录路径，如果为None则使用默认路径
    
    Returns:
        包含所有指标的字典
    """
    if snapshot_dir is None:
        snapshot_dir = Path(__file__).parent.parent.parent / 'data' / 'snapshot'
    
    # 加载本月snapshot
    current_snapshot = load_snapshot(current_month, snapshot_dir)
    if current_snapshot is None:
        raise FileNotFoundError(f"未找到{current_month}的snapshot文件")
    
    # 计算上个月份
    year, month = current_month.split('-')
    prev_year = int(year)
    prev_month = int(month) - 1
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    prev_month_str = f"{prev_year:04d}-{prev_month:02d}"
    
    # 加载上月snapshot（可能不存在，首次运行）
    previous_snapshot = load_snapshot(prev_month_str, snapshot_dir)
    
    # 计算各项指标
    result = {
        'current_month': current_month,
        'previous_month': prev_month_str if previous_snapshot is not None else None,
        'overview': calculate_overview_metrics(current_snapshot, previous_snapshot, current_month),
        'process': calculate_process_metrics(current_snapshot, current_month),
        'conversion': calculate_conversion_metrics(current_snapshot, current_month),
        'risk': calculate_risk_metrics(current_snapshot, current_month),
    }
    
    # 保存结果到JSON文件（按月份组织）
    output_dir = Path(__file__).parent.parent.parent / 'output' / current_month.replace('-', '_')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"metrics_result_{current_month.replace('-', '_')}.json"
    
    # 将结果转换为可序列化的格式
    def convert_to_serializable(obj):
        """递归转换对象为可序列化格式"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, (dict, list)):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            else:
                return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    serializable_result = convert_to_serializable(result)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_result, f, ensure_ascii=False, indent=2)
    
    print(f"详细结果已保存到: {output_file}")
    
    return result

