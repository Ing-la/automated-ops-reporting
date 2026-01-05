"""
Excel文件结构验证模块

用于验证raw数据文件是否符合预期的数据结构
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Optional


# 必需的列名（中文）
REQUIRED_COLUMNS = [
    '客户简称',
    '子产品名称',
    '申请时间',
    '测试返回时间',
    '销售',
    '客户类型',
    '客户综合级别',
    '售前主产品名称',
    '系统主产品名称',
    '接入意向',
    '是否开通',
    '是否调用',
    '样本量'
]

# 可选的列名（如果存在也会处理）
OPTIONAL_COLUMNS = [
    '不接入原因'
]


def validate_excel_structure(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    验证Excel文件结构是否符合要求
    
    Args:
        file_path: Excel文件路径
    
    Returns:
        (是否有效, 错误信息)
        如果有效，返回 (True, None)
        如果无效，返回 (False, 错误描述)
    """
    if not file_path.exists():
        return False, f"文件不存在: {file_path}"
    
    if not file_path.suffix.lower() in ['.xlsx', '.xls']:
        return False, f"文件格式不正确，应为Excel文件(.xlsx或.xls): {file_path.suffix}"
    
    try:
        # 尝试读取Excel文件
        df = pd.read_excel(file_path, nrows=0)  # 只读取列名，不读取数据
        actual_columns = set(df.columns.tolist())
        required_columns_set = set(REQUIRED_COLUMNS)
        
        # 检查必需的列是否存在
        missing_columns = required_columns_set - actual_columns
        if missing_columns:
            return False, f"缺少必需的列: {', '.join(sorted(missing_columns))}"
        
        # 检查是否有数据行
        df_full = pd.read_excel(file_path)
        if len(df_full) == 0:
            return False, "Excel文件为空，没有数据行"
        
        return True, None
        
    except Exception as e:
        return False, f"读取Excel文件失败: {str(e)}"


def detect_latest_application_date(file_path: Path) -> Optional[str]:
    """
    从Excel文件中检测最新的申请日期
    
    Args:
        file_path: Excel文件路径
    
    Returns:
        最新的申请日期，格式YYYY-MM-DD，如果无法检测则返回None
    """
    try:
        df = pd.read_excel(file_path)
        
        if '申请时间' not in df.columns:
            return None
        
        # 转换申请时间为日期格式
        df['申请时间_parsed'] = pd.to_datetime(df['申请时间'], errors='coerce')
        
        # 过滤掉无效日期
        valid_dates = df['申请时间_parsed'].dropna()
        
        if len(valid_dates) == 0:
            return None
        
        # 找到最新的日期
        latest_date = valid_dates.max()
        
        return latest_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        return None


def detect_month_from_file(file_path: Path) -> Optional[str]:
    """
    从Excel文件中检测月份（基于最新的申请日期）
    如果申请日期为空，使用文件修改时间作为备选
    
    Args:
        file_path: Excel文件路径
    
    Returns:
        月份，格式YYYY-MM，如果无法检测则返回None
    """
    # 首先尝试从申请日期检测
    latest_date_str = detect_latest_application_date(file_path)
    
    if latest_date_str:
        # 从日期字符串提取年月
        try:
            from datetime import datetime
            date_obj = datetime.strptime(latest_date_str, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m')
        except:
            pass
    
    # 如果申请日期检测失败，使用文件修改时间
    try:
        from datetime import datetime
        mtime = file_path.stat().st_mtime
        date_obj = datetime.fromtimestamp(mtime)
        return date_obj.strftime('%Y-%m')
    except:
        return None


def find_raw_files(raw_dir: Path) -> list:
    """
    查找raw目录中的所有Excel文件
    
    Args:
        raw_dir: raw目录路径
    
    Returns:
        Excel文件列表
    """
    if not raw_dir.exists():
        return []
    
    excel_files = []
    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.xlsx', '.xls']:
            excel_files.append(file_path)
    
    return sorted(excel_files)

