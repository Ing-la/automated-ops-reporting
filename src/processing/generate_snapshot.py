"""
生成snapshot数据脚本

【月度运行任务】处理新月份数据，结合上月snapshot生成当月snapshot（可复现的月度流程）
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import warnings
import sys

warnings.filterwarnings('ignore')

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshot"


def convert_date_to_str(date_value):
    """将日期转换为字符串格式 YYYY-MM-DD"""
    if pd.isna(date_value) or date_value == '-':
        return ''
    try:
        if isinstance(date_value, str):
            date_obj = pd.to_datetime(date_value)
        else:
            date_obj = date_value
        return date_obj.strftime('%Y-%m-%d')
    except:
        return ''


def map_test_status_to_intents(access_intent: str, test_return_date=None) -> Dict[str, int]:
    """
    将接入意向和测试返回日期映射为二值化字段
    
    业务规则：
    - 完成测试：只要有测试返回日期就赋值1（空值、-、NaN都算空值）
    - 可接入/不接入：基于接入意向字段
    
    Args:
        access_intent: 接入意向（-/可以接入/无法接入）
        test_return_date: 测试返回时间（用于判断是否完成测试）
    
    Returns:
        包含完成测试, 可接入, 不接入的字典
    """
    result = {
        '完成测试': 0,
        '可接入': 0,
        '不接入': 0
    }
    
    # 完成测试判断：只要有测试返回日期就赋值1
    # 注意：需要处理'-'、空字符串、NaN等情况
    if pd.isna(test_return_date):
        has_test_return_date = False
    else:
        test_return_str = str(test_return_date).strip()
        has_test_return_date = test_return_str != '' and test_return_str != '-' and test_return_str.lower() != 'nan'
    
    if has_test_return_date:
        result['完成测试'] = 1
    
    # 接入意向判断：'-'、空字符串、NaN都视为无接入意向
    if pd.isna(access_intent):
        has_access_intent = False
    else:
        access_intent_str = str(access_intent).strip()
        has_access_intent = access_intent_str != '' and access_intent_str != '-' and access_intent_str.lower() != 'nan'
    
    # 接入意向判断
    if has_access_intent:
        if access_intent == '可以接入':
            result['可接入'] = 1
        elif access_intent == '无法接入':
            result['不接入'] = 1
    
    return result


def convert_yes_no(value: str) -> int:
    """将是否字段转换为0/1"""
    if pd.isna(value) or value == '-':
        return 0
    return 1 if value == '是' else 0


def process_raw_data_to_snapshot(df: pd.DataFrame, snapshot_month: str) -> pd.DataFrame:
    """
    将原始数据转换为snapshot格式（中文列名）
    
    Args:
        df: 原始数据DataFrame
        snapshot_month: 快照月份，格式YYYY-MM
    
    Returns:
        转换后的snapshot DataFrame（中文列名）
    """
    # 创建snapshot数据框
    snapshot = pd.DataFrame()
    
    # 一、主键与核心维度字段
    # 处理空值和NaN，避免显示"nan"或"未知"
    snapshot['客户简称'] = df['客户简称'].fillna('').astype(str).replace('nan', '').replace('None', '')
    snapshot['子产品名称'] = df['子产品名称'].fillna('').astype(str).replace('nan', '').replace('None', '')
    snapshot['快照月份'] = snapshot_month
    
    # 添加日期字段（对时间趋势分析至关重要）
    snapshot['申请日期'] = df['申请时间'].apply(convert_date_to_str)
    snapshot['测试返回日期'] = df['测试返回时间'].apply(convert_date_to_str)
    
    # 二、组织与角色维度字段
    snapshot['销售人员'] = df['销售'].fillna('').astype(str)
    
    # 三、客户与产品属性维度
    snapshot['客户类型'] = df['客户类型'].fillna('').astype(str)
    snapshot['客户级别'] = df['客户综合级别'].fillna('').astype(str)
    snapshot['售前主产品'] = df['售前主产品名称'].fillna('').astype(str)
    snapshot['系统主产品'] = df['系统主产品名称'].fillna('').astype(str)
    
    # 四、客户意向与流程状态（二值化字段）
    # 申请测试：只要有申请日期就赋值1（基本上所有数据都要在这一列赋值1）
    snapshot['申请测试'] = (snapshot['申请日期'] != '').astype(int)
    
    # 完成测试、可接入、不接入：基于测试返回日期和接入意向
    intents = df.apply(
        lambda row: map_test_status_to_intents(
            row.get('接入意向', ''),
            row.get('测试返回时间', '')  # 传递测试返回时间用于判断
        ),
        axis=1
    )
    snapshot['完成测试'] = [x['完成测试'] for x in intents]
    snapshot['可接入'] = [x['可接入'] for x in intents]
    snapshot['不接入'] = [x['不接入'] for x in intents]
    snapshot['不接入原因'] = df['不接入原因'].fillna('').astype(str)
    
    # 五、业务结果字段
    snapshot['已开通'] = df['是否开通'].apply(convert_yes_no)
    snapshot['已调用'] = df['是否调用'].apply(convert_yes_no)
    
    # 六、补充与客观字段
    snapshot['样本量'] = pd.to_numeric(df['样本量'], errors='coerce').fillna(0).astype(float)
    
    return snapshot


def merge_with_existing_snapshot(new_data: pd.DataFrame, existing_snapshot: Optional[pd.DataFrame], 
                                 snapshot_month: str) -> pd.DataFrame:
    """
    将新数据与已有snapshot合并，生成新的snapshot（全量）
    
    合并逻辑：
    1. 新数据中的记录（基于客户简称 + 子产品名称 + 申请日期）覆盖已有记录
    2. 已有记录中不在新数据中的记录保留（历史遗留但仍有效的记录）
    3. 新数据中的新记录添加
    
    Args:
        new_data: 新数据（已转换为snapshot格式，中文列名）
        existing_snapshot: 已有的snapshot（如果存在，应该是全量的，中文列名）
        snapshot_month: 快照月份
    
    Returns:
        合并后的snapshot（全量，中文列名）
    """
    # 确保新数据的快照月份正确
    new_data['快照月份'] = snapshot_month
    
    if existing_snapshot is None or len(existing_snapshot) == 0:
        print(f"警告：没有已有snapshot，将使用新数据作为全量snapshot")
        return new_data
    
    print(f"合并已有snapshot（{len(existing_snapshot)}条，全量）与新数据（{len(new_data)}条，近3个月）")
    
    # 创建主键用于匹配（客户简称 + 子产品名称 + 申请日期）
    # 注意：申请日期可能为空，需要处理
    new_data['_key'] = (
        new_data['客户简称'] + '|' + 
        new_data['子产品名称'] + '|' + 
        new_data['申请日期'].fillna('').astype(str)
    )
    existing_snapshot['_key'] = (
        existing_snapshot['客户简称'] + '|' + 
        existing_snapshot['子产品名称'] + '|' + 
        existing_snapshot['申请日期'].fillna('').astype(str)
    )
    
    # 获取新数据中的主键集合
    new_keys = set(new_data['_key'])
    
    # 保留未被更新的已有记录（历史遗留但仍有效的记录）
    unchanged = existing_snapshot[~existing_snapshot['_key'].isin(new_keys)].copy()
    unchanged['快照月份'] = snapshot_month
    
    # 处理旧snapshot中的列：删除"测试中"列（如果存在），添加"申请测试"列（如果不存在）
    if '测试中' in unchanged.columns:
        unchanged = unchanged.drop(columns=['测试中'])
    if '申请测试' not in unchanged.columns:
        # 为旧数据添加申请测试列：只要有申请日期就赋值1
        unchanged['申请测试'] = (unchanged['申请日期'] != '').astype(int)
    
    # 新数据中的记录（更新的 + 新增的）
    updated_and_new = new_data.copy()
    
    # 合并结果：历史遗留记录 + 更新的记录 + 新增的记录 = 全量snapshot
    merged = pd.concat([unchanged, updated_and_new], ignore_index=True)
    merged = merged.drop(columns=['_key'])
    
    # 排序：按快照月份（降序）、申请日期（降序）、客户简称、子产品名称排序
    # 确保最新的数据在上面
    merged = merged.sort_values(
        by=['快照月份', '申请日期', '客户简称', '子产品名称'],
        ascending=[False, False, True, True],
        na_position='last'
    ).reset_index(drop=True)
    
    print(f"合并后共 {len(merged)} 条记录（全量）")
    print(f"  - 保留历史记录：{len(unchanged)} 条")
    print(f"  - 更新/新增记录：{len(updated_and_new)} 条")
    
    return merged


def load_existing_snapshot(month: str) -> Optional[pd.DataFrame]:
    """加载已有的snapshot文件（支持带字母后缀的文件）"""
    month_str = month.replace('-', '_')
    
    # 首先尝试基础文件名
    csv_file = SNAPSHOT_DIR / f"snapshot_{month_str}.csv"
    if csv_file.exists():
        try:
            return pd.read_csv(csv_file, encoding='utf-8-sig')
        except:
            pass
    
    # 如果基础文件不存在，尝试带字母后缀的文件
    # 找到该月份最新的snapshot文件（按字母顺序，取最后一个）
    pattern = f"snapshot_{month_str}_*.csv"
    matching_files = sorted(SNAPSHOT_DIR.glob(pattern))
    
    if matching_files:
        # 返回最新的文件（按字母顺序，最后一个）
        latest_file = matching_files[-1]
        try:
            return pd.read_csv(latest_file, encoding='utf-8-sig')
        except:
            pass
    
    return None


def generate_snapshot_filename(month: str) -> str:
    """
    生成snapshot文件名，如果同月份已存在则添加字母后缀
    
    Args:
        month: 月份，格式YYYY-MM
    
    Returns:
        文件名（不含路径），格式：snapshot_YYYY_MM.csv 或 snapshot_YYYY_MM_a.csv
    """
    month_str = month.replace('-', '_')
    base_name = f"snapshot_{month_str}.csv"
    
    # 检查基础文件名是否存在
    base_path = SNAPSHOT_DIR / base_name
    if not base_path.exists():
        return base_name
    
    # 如果存在，尝试添加字母后缀
    for suffix in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
        candidate_name = f"snapshot_{month_str}_{suffix}.csv"
        candidate_path = SNAPSHOT_DIR / candidate_name
        if not candidate_path.exists():
            return candidate_name
    
    # 如果26个字母都用完了，使用时间戳
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"snapshot_{month_str}_{timestamp}.csv"


def save_snapshot(snapshot: pd.DataFrame, month: str):
    """保存snapshot到文件"""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名（处理同月份冲突）
    filename = generate_snapshot_filename(month)
    csv_file = SNAPSHOT_DIR / filename
    snapshot.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"已保存CSV格式到: {csv_file}")


def generate_monthly_snapshot(raw_file: Path, target_month: str):
    """
    【月度运行任务】处理新月份数据，结合上月snapshot生成当月snapshot（可复现的月度流程）
    
    Args:
        raw_file: 新月份的raw数据文件路径
        target_month: 目标月份，格式YYYY-MM
    """
    if not raw_file.exists():
        print(f"错误：未找到文件 {raw_file}")
        return False
    
    print(f"正在读取新月份数据: {raw_file}")
    df_new = pd.read_excel(raw_file)
    print(f"新数据总行数: {len(df_new)}")
    
    # 转换为snapshot格式（中文列名）
    snapshot_new = process_raw_data_to_snapshot(df_new, target_month)
    
    # 计算上个月份
    year, month = target_month.split('-')
    prev_year = int(year)
    prev_month = int(month) - 1
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    prev_month_str = f"{prev_year:04d}-{prev_month:02d}"
    
    # 加载上个月的snapshot（全量）
    print(f"加载上个月snapshot: {prev_month_str}")
    existing_snapshot = load_existing_snapshot(prev_month_str)
    
    if existing_snapshot is None:
        print(f"警告：未找到上个月snapshot ({prev_month_str})，将使用新数据作为全量snapshot")
    
    # 合并生成当月的snapshot（全量）
    final_snapshot = merge_with_existing_snapshot(snapshot_new, existing_snapshot, target_month)
    
    # 保存当月的snapshot
    print(f"\n保存 {target_month} 的snapshot（全量）...")
    save_snapshot(final_snapshot, target_month)
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("生成snapshot数据（月度运行任务）")
    print("=" * 60)
    
    if len(sys.argv) < 3:
        print("用法: python generate_snapshot.py <YYYY-MM> <raw_file_name>")
        print("示例: python generate_snapshot.py 2025-12 ops_data_2025_12.xlsx")
        sys.exit(1)
    
    target_month = sys.argv[1]
    raw_file_name = sys.argv[2]
    raw_file = RAW_DATA_DIR / raw_file_name
    
    print(f"\n处理 {target_month} 的数据")
    generate_monthly_snapshot(raw_file, target_month)
    
    print("\n" + "=" * 60)
    print("snapshot生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
