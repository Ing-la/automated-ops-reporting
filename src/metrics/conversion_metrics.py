"""
转化与收益分析指标计算模块（核心）

第三部分：转化与收益分析（近3个月数据）
- 收益转化核心指标
- 产品维度收益分析
- 客户维度收益分析
- 有意向未开通列表
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


def calculate_conversion_metrics(current_snapshot: pd.DataFrame, current_month: str) -> Dict:
    """
    计算转化与收益分析指标（核心部分，基于近3个月数据）
    
    Args:
        current_snapshot: 本月snapshot（全量）
        current_month: 当前月份，格式YYYY-MM
    
    Returns:
        包含转化与收益分析指标的字典
    """
    result = {}
    
    # 筛选近3个月的数据
    recent_data = filter_recent_3_months(current_snapshot, current_month)
    
    total_count = len(recent_data)
    if total_count == 0:
        return result
    
    # 一、收益转化核心指标（全部围绕"已调用"，近3个月）
    called_count = int(recent_data['已调用'].sum())
    opened_count = int(recent_data['已开通'].sum())
    has_access_intent_count = int((recent_data['可接入'] == 1).sum())
    
    result['core_conversion'] = {
        'period': '近3个月',  # 说明数据范围
        'overall_call_rate': float(called_count / total_count) if total_count > 0 else 0.0,  # 整体调用率
        'opened_to_call_rate': float(called_count / opened_count) if opened_count > 0 else 0.0,  # 开通→调用转化率
        'intent_to_call_rate': float(called_count / has_access_intent_count) if has_access_intent_count > 0 else 0.0,  # 接入意向→调用转化率
        'total_called': called_count,
        'total_opened': opened_count,
        'total_with_intent': has_access_intent_count,
    }
    
    # 二、产品维度收益分析（近3个月）
    product_metrics = []
    # 过滤掉空值和无效值
    valid_products = recent_data[recent_data['子产品名称'].notna() & (recent_data['子产品名称'] != '') & (recent_data['子产品名称'].astype(str).str.strip() != '')]['子产品名称'].unique()
    for product in valid_products:
        product_str = str(product).strip()
        if not product_str or product_str.lower() in ['nan', 'none', '']:
            continue
        product_data = recent_data[recent_data['子产品名称'] == product]
        product_total = len(product_data)
        product_called = int(product_data['已调用'].sum())
        product_call_rate = float(product_called / product_total) if product_total > 0 else 0.0
        
        product_metrics.append({
            'product_name': product_str,
            'total_count': product_total,
            'called_count': product_called,
            'call_rate': product_call_rate,
        })
    
    # 按调用率排序
    product_metrics.sort(key=lambda x: x['call_rate'], reverse=True)
    
    result['product_analysis'] = {
        'products': product_metrics,
        'top_products': product_metrics[:10] if len(product_metrics) > 10 else product_metrics,  # 前10个
        'zero_call_products': [p for p in product_metrics if p['called_count'] == 0],  # 长期无调用产品
    }
    
    # 三、客户维度收益分析（近3个月）
    customer_metrics = []
    # 过滤掉空值和无效值
    valid_customers = recent_data[recent_data['客户简称'].notna() & (recent_data['客户简称'] != '') & (recent_data['客户简称'].astype(str).str.strip() != '')]['客户简称'].unique()
    for customer in valid_customers:
        customer_str = str(customer).strip()
        if not customer_str or customer_str.lower() in ['nan', 'none', '']:
            continue
        customer_data = recent_data[recent_data['客户简称'] == customer]
        customer_total = len(customer_data)
        customer_called = int(customer_data['已调用'].sum())
        customer_call_rate = float(customer_called / customer_total) if customer_total > 0 else 0.0
        
        # 检查是否有接入意向但未调用
        has_intent_not_called = int(
            ((customer_data['可接入'] == 1) & (customer_data['已调用'] == 0)).sum()
        )
        
        customer_metrics.append({
            'customer_name': customer_str,
            'total_count': customer_total,
            'called_count': customer_called,
            'call_rate': customer_call_rate,
            'has_intent_not_called': has_intent_not_called,
        })
    
    # 按调用数排序（高调用客户）
    customer_metrics.sort(key=lambda x: x['called_count'], reverse=True)
    
    result['customer_analysis'] = {
        'period': '近3个月',
        'customers': customer_metrics,
        'high_call_customers': [c for c in customer_metrics if c['called_count'] > 0][:10],  # 前10个高调用客户
        'intent_not_called_customers': [c for c in customer_metrics if c['has_intent_not_called'] > 0],  # 有意向但未调用客户清单（风险池）
    }
    
    # 四、有意向但未开通列表（近3个月）
    intent_not_opened = recent_data[
        (recent_data['可接入'] == 1) &
        (recent_data['已开通'] == 0)
    ]
    
    result['intent_not_opened_list'] = {
        'period': '近3个月',
        'total_count': len(intent_not_opened),
        'records': intent_not_opened[['客户简称', '子产品名称', '申请日期']].to_dict('records'),  # 保存全部数据
    }
    
    return result

