"""
文件管理工具模块

用于管理raw数据的移动和历史记录
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional


def move_raw_to_history(raw_file: Path, month: str) -> Path:
    """
    将raw数据文件移动到history目录（根据数据月份组织）
    
    Args:
        raw_file: raw数据文件路径
        month: 月份，格式YYYY-MM（根据数据中的申请日期确定）
    
    Returns:
        移动后的文件路径
    """
    # 创建history目录结构：data/history/YYYY_MM/
    history_dir = Path("data") / "history" / month.replace('-', '_')
    history_dir.mkdir(parents=True, exist_ok=True)
    
    # 目标文件路径（保留原文件名，不做任何改动）
    target_file = history_dir / raw_file.name
    
    # 如果目标文件已存在，添加时间戳后缀
    if target_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = target_file.stem
        suffix = target_file.suffix
        target_file = history_dir / f"{stem}_{timestamp}{suffix}"
    
    # 移动文件
    shutil.move(str(raw_file), str(target_file))
    
    return target_file


def clear_raw_directory(month: str, raw_dir: Path = None) -> List[Path]:
    """
    清空raw目录（将所有文件移动到history）
    
    Args:
        month: 月份，格式YYYY-MM，用于组织history目录
        raw_dir: raw目录路径，默认为data/raw
    
    Returns:
        移动的文件列表
    """
    if raw_dir is None:
        raw_dir = Path("data") / "raw"
    
    if not raw_dir.exists():
        return []
    
    moved_files = []
    
    # 遍历raw目录中的所有文件
    for file_path in raw_dir.iterdir():
        if file_path.is_file():
            try:
                # 移动到history（使用传入的月份）
                target_path = move_raw_to_history(file_path, month)
                moved_files.append(target_path)
            except Exception as e:
                print(f"警告：移动文件失败 {file_path.name}: {e}")
    
    return moved_files

