"""
表格生成模块

将报告中的关键表格保存为CSV文件，便于后续分析和查看
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional


def ensure_tables_dir(month: str) -> Path:
    """确保tables目录存在（按月份组织）"""
    tables_dir = Path("output") / month.replace('-', '_') / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    return tables_dir


def save_table_to_csv(data: List[Dict[str, Any]], filename: str, month: str, 
                      columns: Optional[List[str]] = None) -> Path:
    """
    将数据保存为CSV文件
    
    Args:
        data: 数据列表
        filename: 文件名（不含扩展名）
        month: 月份，格式YYYY-MM
        columns: 列名列表，如果为None则从数据中推断
    
    Returns:
        保存的文件路径
    """
    tables_dir = ensure_tables_dir(month)
    
    if not data:
        # 创建空文件
        df = pd.DataFrame(columns=columns or [])
    else:
        df = pd.DataFrame(data)
        if columns:
            # 只保留指定的列
            df = df[[col for col in columns if col in df.columns]]
    
    file_path = tables_dir / f"{filename}_{month.replace('-', '_')}.csv"
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    return file_path


def generate_all_tables(metrics_result: Dict[str, Any], month: str) -> Dict[str, Path]:
    """
    生成表格文件（仅生成PDF中超过15行的表格）
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        表格文件路径字典
    """
    tables = {}
    MAX_PDF_ROWS_THRESHOLD = 15  # PDF中超过15行的表格才生成Excel
    
    print("\n正在生成表格文件...")
    
    overview = metrics_result.get('overview', {})
    monthly = overview.get('monthly_new_progress', {})
    conversion = metrics_result.get('conversion', {})
    process = metrics_result.get('process', {})
    risk = metrics_result.get('risk', {})
    
    # 1. 本月新开通详细列表（如果超过15条才生成Excel）
    new_opened_list = monthly.get('new_opened_list', [])
    if new_opened_list and len(new_opened_list) > MAX_PDF_ROWS_THRESHOLD:
        try:
            file_path = save_table_to_csv(
                new_opened_list,
                'new_opened_list',
                month,
                columns=['customer', 'product', 'apply_date', 'type']
            )
            tables['new_opened_list'] = file_path
            print(f"  ✓ 本月新开通列表: {len(new_opened_list)} 条（超过15条，已生成Excel）")
        except Exception as e:
            print(f"  ⚠️  本月新开通列表生成失败: {e}")
    elif new_opened_list:
        print(f"  - 本月新开通列表: {len(new_opened_list)} 条（不超过15条，无需Excel）")
    
    # 2. 本月新调用详细列表（如果超过15条才生成Excel）
    new_called_list = monthly.get('new_called_list', [])
    if new_called_list and len(new_called_list) > MAX_PDF_ROWS_THRESHOLD:
        try:
            file_path = save_table_to_csv(
                new_called_list,
                'new_called_list',
                month,
                columns=['customer', 'product', 'apply_date', 'type']
            )
            tables['new_called_list'] = file_path
            print(f"  ✓ 本月新调用列表: {len(new_called_list)} 条（超过15条，已生成Excel）")
        except Exception as e:
            print(f"  ⚠️  本月新调用列表生成失败: {e}")
    elif new_called_list:
        print(f"  - 本月新调用列表: {len(new_called_list)} 条（不超过15条，无需Excel）")
    
    # 3. 产品调用率TOP 10（只显示10条，不需要Excel）
    # 4. 客户调用率TOP 10（只显示10条，不需要Excel）
    # 这两个表格在PDF中只显示10条，不需要生成Excel
    
    # 5. 超长测试周期记录（如果总数超过15条才生成Excel）
    test_cycle = process.get('test_cycle', {})
    long_test_records = test_cycle.get('long_test_records', [])
    if long_test_records and len(long_test_records) > MAX_PDF_ROWS_THRESHOLD:
        try:
            long_test_data = []
            for item in long_test_records:
                long_test_data.append({
                    '客户简称': item.get('customer', ''),
                    '子产品名称': item.get('product', ''),
                    '申请日期': item.get('apply_date', ''),
                    '测试返回日期': item.get('return_date', ''),
                    '测试周期（天）': item.get('days', 0)
                })
            file_path = save_table_to_csv(
                long_test_data,
                'long_test_records',
                month
            )
            tables['long_test_records'] = file_path
            print(f"  ✓ 超长测试周期记录: {len(long_test_data)} 条（超过15条，已生成Excel）")
        except Exception as e:
            print(f"  ⚠️  超长测试周期表格生成失败: {e}")
    elif long_test_records:
        print(f"  - 超长测试周期记录: {len(long_test_records)} 条（不超过15条，无需Excel）")
    
    # 6. 有意向但未开通列表（如果超过15条才生成Excel）
    intent_not_opened = conversion.get('intent_not_opened_list', {})
    intent_not_opened_records = intent_not_opened.get('records', [])
    if intent_not_opened_records and len(intent_not_opened_records) > MAX_PDF_ROWS_THRESHOLD:
        try:
            intent_data = []
            for item in intent_not_opened_records:
                intent_data.append({
                    '客户简称': item.get('客户简称', ''),
                    '子产品名称': item.get('子产品名称', ''),
                    '申请日期': item.get('申请日期', '')
                })
            file_path = save_table_to_csv(
                intent_data,
                'intent_not_opened',
                month
            )
            tables['intent_not_opened'] = file_path
            print(f"  ✓ 有意向但未开通列表: {len(intent_data)} 条（超过15条，已生成Excel）")
        except Exception as e:
            print(f"  ⚠️  有意向但未开通表格生成失败: {e}")
    elif intent_not_opened_records:
        print(f"  - 有意向但未开通列表: {len(intent_not_opened_records)} 条（不超过15条，无需Excel）")
    
    # 7. 长期无意向记录（如果超过15条才生成Excel）
    completed_no_intent = risk.get('completed_no_intent', {})
    long_term_records = completed_no_intent.get('long_term_records', [])
    if long_term_records and len(long_term_records) > MAX_PDF_ROWS_THRESHOLD:
        try:
            no_intent_data = []
            for item in long_term_records:
                no_intent_data.append({
                    '客户简称': item.get('customer', ''),
                    '子产品名称': item.get('product', ''),
                    '距离测试返回天数': item.get('days_since_return', 0)
                })
            file_path = save_table_to_csv(
                no_intent_data,
                'completed_no_intent',
                month
            )
            tables['completed_no_intent'] = file_path
            print(f"  ✓ 长期无意向记录: {len(no_intent_data)} 条（超过15条，已生成Excel）")
        except Exception as e:
            print(f"  ⚠️  长期无意向表格生成失败: {e}")
    elif long_term_records:
        print(f"  - 长期无意向记录: {len(long_term_records)} 条（不超过15条，无需Excel）")
    
    # 8. 长期未调用记录（如果超过15条才生成Excel）
    opened_not_called = risk.get('opened_not_called', {})
    long_term_no_call = opened_not_called.get('long_term_records', [])
    if long_term_no_call and len(long_term_no_call) > MAX_PDF_ROWS_THRESHOLD:
        try:
            no_call_data = []
            for item in long_term_no_call:
                no_call_data.append({
                    '客户简称': item.get('customer', ''),
                    '子产品名称': item.get('product', ''),
                    '距离申请天数': item.get('days_since_apply', 0)
                })
            file_path = save_table_to_csv(
                no_call_data,
                'opened_not_called',
                month
            )
            tables['opened_not_called'] = file_path
            print(f"  ✓ 长期未调用记录: {len(no_call_data)} 条（超过15条，已生成Excel）")
        except Exception as e:
            print(f"  ⚠️  长期未调用表格生成失败: {e}")
    elif long_term_no_call:
        print(f"  - 长期未调用记录: {len(long_term_no_call)} 条（不超过15条，无需Excel）")
    
    print(f"\n✅ 表格生成完成: {len(tables)} 个文件（仅生成超过15行的表格）")
    
    return tables

