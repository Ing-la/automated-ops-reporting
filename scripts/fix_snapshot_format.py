"""
修复snapshot格式：将旧格式转换为新格式
- 删除"测试中"列
- 添加"申请测试"列（基于申请日期）
"""
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshot"

def fix_snapshot_format(month: str):
    """
    修复指定月份的snapshot格式
    
    Args:
        month: 月份，格式YYYY-MM或YYYY_MM
    """
    # 统一格式为YYYY_MM
    month_str = month.replace('-', '_')
    snapshot_file = SNAPSHOT_DIR / f"snapshot_{month_str}.csv"
    
    if not snapshot_file.exists():
        print(f"错误：未找到文件 {snapshot_file}")
        return False
    
    print(f"正在读取snapshot: {snapshot_file}")
    df = pd.read_csv(snapshot_file, encoding='utf-8-sig')
    
    print(f"原始数据:")
    print(f"  总记录数: {len(df)}")
    print(f"  列数: {len(df.columns)}")
    print(f"  有'测试中'列: {'测试中' in df.columns}")
    print(f"  有'申请测试'列: {'申请测试' in df.columns}")
    
    # 备份原文件
    backup_file = snapshot_file.with_suffix('.csv.backup')
    df.to_csv(backup_file, index=False, encoding='utf-8-sig')
    print(f"✓ 已备份原文件到: {backup_file}")
    
    # 修复格式
    modified = False
    
    # 1. 删除"测试中"列（如果存在）
    if '测试中' in df.columns:
        df = df.drop(columns=['测试中'])
        modified = True
        print("✓ 已删除'测试中'列")
    
    # 2. 添加"申请测试"列（如果不存在）
    if '申请测试' not in df.columns:
        # 基于申请日期判断：只要有申请日期就赋值1
        df['申请测试'] = (df['申请日期'] != '').astype(int)
        modified = True
        print("✓ 已添加'申请测试'列")
        print(f"  申请测试数量: {df['申请测试'].sum()}/{len(df)}")
    
    # 3. 验证"完成测试"列的逻辑（基于测试返回日期）
    if '完成测试' in df.columns and '测试返回日期' in df.columns:
        # 检查完成测试列是否与测试返回日期一致
        expected_completed = (df['测试返回日期'] != '').sum()
        actual_completed = df['完成测试'].sum()
        if expected_completed != actual_completed:
            print(f"⚠️  完成测试列可能需要修正:")
            print(f"    基于测试返回日期: {expected_completed}条")
            print(f"    当前完成测试列: {actual_completed}条")
            # 修正完成测试列
            df['完成测试'] = (df['测试返回日期'] != '').astype(int)
            modified = True
            print(f"✓ 已修正'完成测试'列: {df['完成测试'].sum()}条")
    
    if modified:
        # 保存修复后的文件
        df.to_csv(snapshot_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ 已保存修复后的snapshot: {snapshot_file}")
        print(f"  总记录数: {len(df)}")
        print(f"  列数: {len(df.columns)}")
        
        # 验证最终格式
        print(f"\n最终格式验证:")
        print(f"  有'测试中'列: {'测试中' in df.columns} (应为False)")
        print(f"  有'申请测试'列: {'申请测试' in df.columns} (应为True)")
        print(f"  申请测试数量: {df['申请测试'].sum()}")
        print(f"  完成测试数量: {df['完成测试'].sum()}")
        
        return True
    else:
        print("\n✓ snapshot格式已正确，无需修改")
        # 删除备份文件
        backup_file.unlink()
        return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='修复snapshot格式')
    parser.add_argument('month', help='月份，格式YYYY-MM或YYYY_MM')
    
    args = parser.parse_args()
    
    success = fix_snapshot_format(args.month)
    sys.exit(0 if success else 1)



