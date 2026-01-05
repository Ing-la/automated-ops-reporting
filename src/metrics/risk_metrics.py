"""
滞后与风险识别指标计算模块

第四部分：滞后与风险识别（近3个月数据）
- 关键滞后场景识别
- 超长测试周期
- 有意向未开通
- 开通未调用
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


def calculate_risk_metrics(current_snapshot: pd.DataFrame, current_month: str) -> Dict:
    """
    计算滞后与风险识别指标（基于近3个月数据）
    
    Args:
        current_snapshot: 本月snapshot（全量）
        current_month: 当前月份，格式YYYY-MM
    
    Returns:
        包含滞后与风险识别指标的字典
    """
    result = {}
    
    # 筛选近3个月的数据
    recent_data = filter_recent_3_months(current_snapshot, current_month)
    
    # 一、关键滞后场景识别（近3个月）
    current_date = datetime.now()
    
    # 1. 测试完成但长期无意向（近3个月）
    # 条件：完成测试=1，可接入=0，不接入=0，且测试返回日期不为空
    completed_no_intent_mask = (
        (recent_data['完成测试'] == 1) &
        (recent_data['可接入'] == 0) &
        (recent_data['不接入'] == 0) &
        (recent_data['测试返回日期'] != '')
    )
    completed_no_intent = recent_data[completed_no_intent_mask].copy()
    
    # 计算测试返回日期距离现在的天数
    long_no_intent_records = []
    for idx, row in completed_no_intent.iterrows():
        return_date_str = row['测试返回日期']
        if return_date_str != '':
            try:
                return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
                days_since_return = (current_date - return_date).days
                if days_since_return > 30:  # 超过30天视为长期
                    long_no_intent_records.append({
                        'customer': row['客户简称'],
                        'product': row['子产品名称'],
                        'days_since_return': days_since_return,
                    })
            except:
                pass
    
    result['completed_no_intent'] = {
        'period': '近3个月',
        'total_count': len(completed_no_intent),
        'long_term_count': len(long_no_intent_records),
        'long_term_records': long_no_intent_records[:30],  # 前30条
    }
    
    # 2. 明确有意向但未开通（近3个月）
    # 条件：可接入=1，已开通=0
    intent_not_opened_mask = (recent_data['可接入'] == 1) & (recent_data['已开通'] == 0)
    intent_not_opened = recent_data[intent_not_opened_mask].copy()
    
    result['intent_not_opened'] = {
        'period': '近3个月',
        'total_count': len(intent_not_opened),
        'records': intent_not_opened[['客户简称', '子产品名称', '申请日期']].to_dict('records'),  # 保存全部数据
    }
    
    # 3. 已开通但长期未调用（重点风险，近3个月）
    # 条件：已开通=1，已调用=0
    opened_not_called_mask = (recent_data['已开通'] == 1) & (recent_data['已调用'] == 0)
    opened_not_called = recent_data[opened_not_called_mask].copy()
    
    # 计算开通时间（如果有申请日期，可以估算）
    long_not_called_records = []
    for idx, row in opened_not_called.iterrows():
        apply_date_str = row['申请日期']
        if apply_date_str != '':
            try:
                apply_date = datetime.strptime(apply_date_str, '%Y-%m-%d')
                days_since_apply = (current_date - apply_date).days
                if days_since_apply > 60:  # 超过60天视为长期
                    long_not_called_records.append({
                        'customer': row['客户简称'],
                        'product': row['子产品名称'],
                        'days_since_apply': days_since_apply,
                        'not_access_reason': row.get('不接入原因', ''),
                    })
            except:
                pass
    
    result['opened_not_called'] = {
        'period': '近3个月',
        'total_count': len(opened_not_called),
        'long_term_count': len(long_not_called_records),
        'long_term_records': long_not_called_records[:30],  # 前30条
    }
    
    # 二、不调用原因结构分析（若字段可用，近3个月）
    not_called_mask = (recent_data['已调用'] == 0) & (recent_data['不接入原因'] != '')
    not_called_reasons = recent_data[not_called_mask]['不接入原因'].value_counts().to_dict()
    
    result['not_called_reasons'] = {
        'period': '近3个月',
        'total_with_reason': len(recent_data[
            (recent_data['已调用'] == 0) &
            (recent_data['不接入原因'] != '')
        ]),
        'reason_distribution': not_called_reasons,
    }
    
    return result

