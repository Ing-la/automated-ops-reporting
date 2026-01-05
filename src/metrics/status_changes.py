"""
状态变化识别模块

对比本月和上月snapshot，识别状态变化（新增记录和状态更新）
"""

import pandas as pd
from typing import Dict, Tuple, Optional
from pathlib import Path


def create_primary_key(df: pd.DataFrame) -> pd.Series:
    """
    创建主键（客户简称 + 子产品名称 + 申请日期）
    
    Args:
        df: snapshot DataFrame
    
    Returns:
        主键Series
    """
    return (
        df['客户简称'] + '|' + 
        df['子产品名称'] + '|' + 
        df['申请日期'].fillna('').astype(str)
    )


def identify_status_changes(current_snapshot: pd.DataFrame, 
                           previous_snapshot: Optional[pd.DataFrame],
                           current_month: str) -> Dict:
    """
    识别状态变化：新增记录和状态更新
    
    Args:
        current_snapshot: 本月snapshot（全量）
        previous_snapshot: 上月snapshot（全量），如果为None表示首次运行
        current_month: 当前月份，格式YYYY-MM
    
    Returns:
        包含状态变化信息的字典
    """
    result = {
        'new_records': pd.DataFrame(),  # 新增记录（主键在上月不存在）
        'updated_records': pd.DataFrame(),  # 状态更新的记录（主键存在但状态变化）
        'unchanged_records': pd.DataFrame(),  # 未变化的记录
        'status_changes': {
            'new_completed_test': [],  # 新完成测试（测试中→完成测试）
            'new_opened': [],  # 新开通（未开通→已开通）
            'new_called': [],  # 新调用（未调用→已调用）
        }
    }
    
    if previous_snapshot is None or len(previous_snapshot) == 0:
        # 首次运行，所有记录都是新增
        result['new_records'] = current_snapshot.copy()
        return result
    
    # 创建主键
    current_key = create_primary_key(current_snapshot)
    previous_key = create_primary_key(previous_snapshot)
    
    current_snapshot['_key'] = current_key
    previous_snapshot['_key'] = previous_key
    
    # 创建上月snapshot的字典（基于主键，处理重复主键的情况）
    # 使用groupby处理重复主键，取第一条记录
    prev_grouped = previous_snapshot.groupby('_key').first()
    prev_dict = prev_grouped.to_dict('index')
    prev_keys = set(previous_key)
    current_keys = set(current_key)
    
    # 识别新增记录
    new_mask = ~current_key.isin(prev_keys)
    result['new_records'] = current_snapshot[new_mask].copy()
    
    # 识别更新的记录（主键存在但状态可能变化）
    # 对于重复主键，需要分别处理每条记录
    updated_mask = current_key.isin(prev_keys)
    updated_records = []
    new_completed_test = []
    new_opened = []
    new_called = []
    
    # 创建当前snapshot的grouped（处理重复主键）
    current_grouped = current_snapshot[updated_mask].groupby('_key')
    
    for key, current_group in current_grouped:
        prev_row = prev_dict.get(key)
        
        if prev_row is None:
            continue
        
        # 对于当前snapshot中该主键的所有记录，检查状态变化
        for idx, row in current_group.iterrows():
            # 检查状态变化
            status_changed = False
            
            # 检查测试完成状态变化
            if (prev_row.get('完成测试', 0) == 0 and row['完成测试'] == 1):
                new_completed_test.append(key)
                status_changed = True
            
            # 检查开通状态变化
            if (prev_row.get('已开通', 0) == 0 and row['已开通'] == 1):
                new_opened.append(key)
                status_changed = True
            
            # 检查调用状态变化（核心收益指标）
            if (prev_row.get('已调用', 0) == 0 and row['已调用'] == 1):
                new_called.append(key)
                status_changed = True
            
            if status_changed:
                updated_records.append(row)
    
    if updated_records:
        result['updated_records'] = pd.DataFrame(updated_records)
    
    # 识别未变化的记录（简化处理，只统计数量，不保存详细记录）
    # 注意：由于可能有重复主键，这里只做统计，不详细记录
    unchanged_count = 0
    unchanged_mask = current_key.isin(prev_keys)
    for idx, row in current_snapshot[unchanged_mask].iterrows():
        key = row['_key']
        prev_row = prev_dict.get(key)
        if prev_row is None:
            continue
        
        # 检查是否所有关键状态都未变化
        if (prev_row.get('完成测试', 0) == row['完成测试'] and
            prev_row.get('已开通', 0) == row['已开通'] and
            prev_row.get('已调用', 0) == row['已调用']):
            unchanged_count += 1
    
    # 未变化记录只保存数量统计
    result['unchanged_count'] = unchanged_count
    
    # 清理临时字段
    result['new_records'] = result['new_records'].drop(columns=['_key'], errors='ignore')
    result['updated_records'] = result['updated_records'].drop(columns=['_key'], errors='ignore')
    result['unchanged_records'] = result['unchanged_records'].drop(columns=['_key'], errors='ignore')
    
    # 保存状态变化的主键列表
    result['status_changes'] = {
        'new_completed_test': new_completed_test,
        'new_opened': new_opened,
        'new_called': new_called
    }
    
    return result

