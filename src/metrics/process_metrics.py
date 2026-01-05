"""
流程与进度分析指标计算模块

第二部分：流程与进度分析（近3个月数据）
- 测试流程进度分析
- 测试周期与效率
- 超长测试周期识别
"""

import pandas as pd
from typing import Dict
from datetime import datetime, timedelta


def filter_recent_3_months(df: pd.DataFrame, current_month: str) -> pd.DataFrame:
    """
    筛选近3个月的数据（基于申请日期）
    
    Args:
        df: snapshot DataFrame
        current_month: 当前月份，格式YYYY-MM
    
    Returns:
        近3个月的DataFrame
    """
    # 计算3个月前的日期
    year, month = current_month.split('-')
    current_date = datetime(int(year), int(month), 1)
    three_months_ago = current_date - timedelta(days=90)  # 约3个月
    
    # 筛选申请日期在近3个月内的记录
    def is_recent(date_str):
        if date_str == '' or pd.isna(date_str):
            return False
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj >= three_months_ago
        except:
            return False
    
    recent_mask = df['申请日期'].apply(is_recent)
    return df[recent_mask].copy()


def calculate_process_metrics(current_snapshot: pd.DataFrame, current_month: str) -> Dict:
    """
    计算流程与进度分析指标（基于近3个月数据）
    
    Args:
        current_snapshot: 本月snapshot（全量）
        current_month: 当前月份，格式YYYY-MM
    
    Returns:
        包含流程与进度分析指标的字典
    """
    result = {}
    
    # 筛选近3个月的数据
    recent_data = filter_recent_3_months(current_snapshot, current_month)
    
    # 一、测试流程进度分析（近3个月）
    total_count = len(recent_data)
    
    # 处理空DataFrame的情况
    if total_count == 0:
        result['test_progress'] = {
            'period': '近3个月',
            'total_count': 0,
            'has_test_return_date_count': 0,
            'test_completion_rate': 0.0,
            'status_distribution': {
                'applied_test': 0,
                'completed_test': 0,
                'accessible': 0,
                'not_accessible': 0,
            }
        }
        return result
    
    # 申请测试数量（申请测试=1）
    # 向后兼容：如果snapshot中没有"申请测试"列，则基于申请日期计算
    if '申请测试' in recent_data.columns:
        applied_test_count = int(recent_data['申请测试'].sum())
    elif '申请日期' in recent_data.columns:
        # 旧schema兼容：基于申请日期判断
        applied_test_count = int((recent_data['申请日期'] != '').sum())
    else:
        # 如果既没有申请测试列也没有申请日期列，使用总记录数
        applied_test_count = total_count
    
    # 完成测试数量（完成测试=1）
    completed_test_count = int(recent_data['完成测试'].sum()) if '完成测试' in recent_data.columns else 0
    has_test_return_date = (recent_data['测试返回日期'] != '').sum() if '测试返回日期' in recent_data.columns else 0
    # 测试完成率 = 完成测试数量 / 申请测试数量
    test_completion_rate = completed_test_count / applied_test_count if applied_test_count > 0 else 0.0
    
    # 测试状态分布
    # 向后兼容：如果snapshot中没有"申请测试"列，则基于申请日期计算
    if '申请测试' in recent_data.columns:
        applied_test_count_for_dist = int(recent_data['申请测试'].sum())
    elif '申请日期' in recent_data.columns:
        applied_test_count_for_dist = int((recent_data['申请日期'] != '').sum())
    else:
        applied_test_count_for_dist = total_count
    
    status_distribution = {
        'applied_test': applied_test_count_for_dist,
        'completed_test': int(recent_data['完成测试'].sum()) if '完成测试' in recent_data.columns else 0,
        'accessible': int(recent_data['可接入'].sum()) if '可接入' in recent_data.columns else 0,
        'not_accessible': int(recent_data['不接入'].sum()) if '不接入' in recent_data.columns else 0,
    }
    
    result['test_progress'] = {
        'period': '近3个月',  # 说明数据范围
        'total_count': total_count,
        'has_test_return_date_count': int(has_test_return_date),
        'test_completion_rate': float(test_completion_rate),
        'status_distribution': status_distribution
    }
    
    # 二、测试周期与效率（近3个月）
    # 计算申请→测试返回时间（天数）
    test_cycles = []
    long_test_records = []  # 超长测试记录
    for idx, row in recent_data.iterrows():
        apply_date_str = row['申请日期']
        return_date_str = row['测试返回日期']
        
        if apply_date_str != '' and return_date_str != '':
            try:
                apply_date = datetime.strptime(apply_date_str, '%Y-%m-%d')
                return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
                days = (return_date - apply_date).days
                if days >= 0:  # 只保留合理的正数天数
                    test_cycles.append(days)
                    # 记录超长测试（>30天）
                    if days > 30:
                        long_test_records.append({
                            'customer': row['客户简称'],
                            'product': row['子产品名称'],
                            'apply_date': apply_date_str,
                            'return_date': return_date_str,
                            'days': days
                        })
            except:
                pass
    
    if test_cycles:
        result['test_cycle'] = {
            'period': '近3个月',
            'count': len(test_cycles),
            'mean': float(sum(test_cycles) / len(test_cycles)),
            'median': float(sorted(test_cycles)[len(test_cycles) // 2]),
            'min': int(min(test_cycles)),
            'max': int(max(test_cycles)),
            'long_test_threshold': 30,  # 超长测试阈值（30天）
            'long_test_count': len(long_test_records),
            'long_test_records': sorted(long_test_records, key=lambda x: x['days'], reverse=True)[:30],  # 前30条超长测试
        }
    else:
        result['test_cycle'] = {
            'period': '近3个月',
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'min': 0,
            'max': 0,
            'long_test_threshold': 30,
            'long_test_count': 0,
            'long_test_records': [],
        }
    
    return result

