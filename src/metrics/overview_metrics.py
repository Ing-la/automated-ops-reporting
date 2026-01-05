"""
总体运营盘点指标计算模块

第一部分：总体运营盘点
- 规模与结构概览（本月新增）
- 截至本月的整体进展（全量汇总，需注明起止日期）
- 本月新进展详细列表
"""

import pandas as pd
from typing import Dict
from datetime import datetime, timedelta
from .status_changes import identify_status_changes


def calculate_overview_metrics(current_snapshot: pd.DataFrame,
                               previous_snapshot: pd.DataFrame,
                               current_month: str) -> Dict:
    """
    计算总体运营盘点指标
    
    Args:
        current_snapshot: 本月snapshot（全量）
        previous_snapshot: 上月snapshot（全量），可以为None
        current_month: 当前月份，格式YYYY-MM
    
    Returns:
        包含总体运营盘点指标的字典
    """
    result = {}
    
    # 识别状态变化
    status_changes = identify_status_changes(current_snapshot, previous_snapshot, current_month)
    
    # 一、规模与结构概览
    new_records = status_changes['new_records']
    
    result['scale_and_structure'] = {
        'new_test_count': len(new_records),  # 本月新增测试量
        'new_customer_count': new_records['客户简称'].nunique() if len(new_records) > 0 else 0,  # 新增客户数
        'new_product_count': new_records['子产品名称'].nunique() if len(new_records) > 0 else 0,  # 新增子产品数
        'sample_size_distribution': {
            'total': float(new_records['样本量'].sum()) if len(new_records) > 0 else 0.0,
            'mean': float(new_records['样本量'].mean()) if len(new_records) > 0 else 0.0,
            'median': float(new_records['样本量'].median()) if len(new_records) > 0 else 0.0,
            'max': float(new_records['样本量'].max()) if len(new_records) > 0 else 0.0,
            'min': float(new_records['样本量'].min()) if len(new_records) > 0 else 0.0,
        }
    }
    
    # 二、截至本月的整体进展（基于全量snapshot，需注明起止日期）
    # 计算起止日期：从最早的申请日期到当前月份
    apply_dates = current_snapshot[current_snapshot['申请日期'] != '']['申请日期']
    if len(apply_dates) > 0:
        try:
            earliest_date = min(apply_dates)
            # 计算当前月份的实际最后一天（避免2月31日等无效日期）
            year, month = current_month.split('-')
            from calendar import monthrange
            last_day = monthrange(int(year), int(month))[1]
            latest_date = f"{current_month}-{last_day:02d}"
            date_range = f"{earliest_date} 至 {latest_date}"
        except Exception as e:
            # 如果计算失败，使用当前月份作为结束日期
            date_range = f"历史数据 至 {current_month}"
    else:
        date_range = f"历史数据 至 {current_month}"
    
    result['overall_progress'] = {
        'date_range': date_range,  # 数据起止日期
        'total_records': len(current_snapshot),  # 总测试记录数
        'completed_test_count': int(current_snapshot['完成测试'].sum()),  # 已完成测试数量
        'has_access_intent_count': int((current_snapshot['可接入'] == 1).sum()),  # 已明确接入意向数量
        'opened_count': int(current_snapshot['已开通'].sum()),  # 已开通数量
        'called_count': int(current_snapshot['已调用'].sum()),  # 已调用数量（核心）
    }
    
    # 三、本月新增进展（包含新增记录和状态更新）
    new_completed_test_count = len(status_changes['status_changes']['new_completed_test'])
    new_opened_count = len(status_changes['status_changes']['new_opened'])
    new_called_count = len(status_changes['status_changes']['new_called'])
    
    # 新增记录中的进展
    if len(new_records) > 0:
        new_completed_test_count += int(new_records['完成测试'].sum())
        new_opened_count += int(new_records['已开通'].sum())
        new_called_count += int(new_records['已调用'].sum())
    
    result['monthly_new_progress'] = {
        'new_completed_test': new_completed_test_count,  # 本月新完成测试（新增+状态更新）
        'new_opened': new_opened_count,  # 本月新开通（新增+状态更新）
        'new_called': new_called_count,  # 本月新调用（新增+状态更新，核心收益指标）
    }
    
    # 四、本月新开通和新调用的详细列表
    # 新开通列表（包含新增记录和状态更新）
    new_opened_list = []
    if len(new_records) > 0:
        new_opened_from_new = new_records[new_records['已开通'] == 1]
        for idx, row in new_opened_from_new.iterrows():
            new_opened_list.append({
                'customer': row['客户简称'],
                'product': row['子产品名称'],
                'apply_date': row['申请日期'],
                'type': '新增记录'
            })
    
    # 状态更新中的新开通
    for key in status_changes['status_changes']['new_opened']:
        # 从current_snapshot中查找
        current_key = current_snapshot['客户简称'] + '|' + current_snapshot['子产品名称'] + '|' + current_snapshot['申请日期'].fillna('').astype(str)
        matched = current_snapshot[current_key == key]
        if len(matched) > 0:
            row = matched.iloc[0]
            new_opened_list.append({
                'customer': row['客户简称'],
                'product': row['子产品名称'],
                'apply_date': row['申请日期'],
                'type': '状态更新'
            })
    
    # 新调用列表（包含新增记录和状态更新）
    new_called_list = []
    if len(new_records) > 0:
        new_called_from_new = new_records[new_records['已调用'] == 1]
        for idx, row in new_called_from_new.iterrows():
            new_called_list.append({
                'customer': row['客户简称'],
                'product': row['子产品名称'],
                'apply_date': row['申请日期'],
                'type': '新增记录'
            })
    
    # 状态更新中的新调用
    for key in status_changes['status_changes']['new_called']:
        # 从current_snapshot中查找
        current_key = current_snapshot['客户简称'] + '|' + current_snapshot['子产品名称'] + '|' + current_snapshot['申请日期'].fillna('').astype(str)
        matched = current_snapshot[current_key == key]
        if len(matched) > 0:
            row = matched.iloc[0]
            new_called_list.append({
                'customer': row['客户简称'],
                'product': row['子产品名称'],
                'apply_date': row['申请日期'],
                'type': '状态更新'
            })
    
    result['monthly_new_progress']['new_opened_list'] = new_opened_list  # 保存全部数据
    result['monthly_new_progress']['new_called_list'] = new_called_list  # 保存全部数据
    
    return result

