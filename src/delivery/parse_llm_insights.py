"""
解析LLM生成的结论和行动建议

从Markdown格式的LLM输出中提取结论和行动建议
"""

import re
from typing import Dict, List, Optional, Tuple


def parse_llm_insights(llm_text: str, debug: bool = False) -> Dict[str, any]:
    """
    解析LLM生成的结论和行动建议
    
    Args:
        llm_text: LLM生成的Markdown格式文本
        debug: 是否输出调试信息
    
    Returns:
        包含结论和行动建议的字典
        {
            "conclusions": ["结论1", "结论2", ...],
            "actions": [
                {"priority": "高", "target": "对象", "action": "行动", "purpose": "目的"},
                ...
            ]
        }
    """
    result = {
        "conclusions": [],
        "actions": []
    }
    
    if not llm_text:
        if debug:
            print("⚠️  LLM文本为空")
        return result
    
    # 跳过文件头部分（如果存在）
    # 文件头格式：以 # 开头，包含"生成时间"等，然后是 --- 分隔符
    lines = llm_text.split('\n')
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' or (line.strip().startswith('---') and i > 0):
            content_start = i + 1
            if debug:
                print(f"找到分隔符，跳过前 {content_start} 行")
            break
        # 如果找到结论标题，说明已经跳过文件头
        if re.search(r'###\s*结论', line, re.IGNORECASE):
            content_start = i
            if debug:
                print(f"找到结论标题，跳过前 {content_start} 行")
            break
    
    # 重新组合文本（跳过文件头）
    content_text = '\n'.join(lines[content_start:])
    
    if debug:
        print(f"处理后的文本长度: {len(content_text)} 字符")
        print(f"文本前200字符: {content_text[:200]}")
    
    # 提取结论部分（支持多种格式）
    # 格式1: ### 结论
    # 格式2: ## 一、提炼【结论】
    # 格式3: 结论（不带###）
    conclusion_patterns = [
        r'###\s*结论\s*\n(.*?)(?=###\s*行动建议|###\s*[^#]|##\s*|$)',
        r'##\s*[一二三四五六七八九十\d、．.]*\s*提炼.*?结论.*?\n(.*?)(?=###|##|$)',
        r'结论\s*\n(.*?)(?=行动建议|###|##|$)',
        r'###\s*结论\s*\n(.*?)(?=\n###|\n##|$)',  # 更宽松的匹配
    ]
    
    conclusion_text = None
    matched_pattern = None
    for i, pattern in enumerate(conclusion_patterns):
        conclusion_match = re.search(pattern, content_text, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            matched_pattern = i
            if debug:
                print(f"✅ 使用模式 {i} 匹配到结论部分，长度: {len(conclusion_text)} 字符")
            break
    
    if not conclusion_text and debug:
        print("⚠️  未找到结论部分")
        # 尝试查找所有包含"结论"的行
        for i, line in enumerate(content_text.split('\n')[:20]):
            if '结论' in line:
                print(f"   第{i}行包含'结论': {line[:100]}")
    
    if conclusion_text:
        # 提取列表项（以 - 或 * 开头，支持多行）
        # 改进正则：匹配完整的列表项，包括多行内容
        conclusion_items = re.findall(r'[-*]\s*(.+?)(?=\n[-*]|\n###|\n##|\n\n\n|$)', conclusion_text, re.DOTALL)
        
        # 如果正则匹配失败，尝试逐行解析
        if not conclusion_items:
            for line in conclusion_text.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    item = line[1:].strip()
                    if item and len(item) > 3:
                        conclusion_items.append(item)
        
        result["conclusions"] = [
            line.strip().replace('\n', ' ').replace('  ', ' ').replace('  ', ' ')
            for line in conclusion_items 
            if line.strip() and len(line.strip()) > 3  # 过滤太短的内容
        ]
        
        if debug:
            print(f"✅ 提取到 {len(result['conclusions'])} 条结论")
            for i, c in enumerate(result['conclusions'], 1):
                print(f"   结论{i}: {c[:50]}...")
    
    # 提取行动建议表格（支持多种格式）
    action_patterns = [
        r'###\s*行动建议\s*\n(.*?)(?=###|##|$)',
        r'##\s*[一二三四五六七八九十\d、．.]*\s*给出.*?行动建议.*?\n(.*?)(?=###|##|$)',
        r'行动建议\s*\n(.*?)(?=###|##|$)',
    ]
    
    action_text = None
    for i, pattern in enumerate(action_patterns):
        action_match = re.search(pattern, content_text, re.DOTALL | re.IGNORECASE)
        if action_match:
            action_text = action_match.group(1).strip()
            if debug:
                print(f"✅ 使用模式 {i} 匹配到行动建议部分，长度: {len(action_text)} 字符")
            break
    
    if action_text:
        # 查找表格（匹配包含多行的表格）
        table_lines = action_text.split('\n')
        # 找到表格开始位置（包含 | 的行）
        table_start = -1
        for i, line in enumerate(table_lines):
            if '|' in line and ('优先级' in line or 'priority' in line.lower() or '行动对象' in line):
                table_start = i
                if debug:
                    print(f"✅ 找到表格开始位置: 第{i}行")
                break
        
        if table_start >= 0:
            # 跳过表头（标题行和分隔行）
            for line in table_lines[table_start + 2:]:
                if '|' in line and not line.strip().startswith('|---'):
                    parts = [p.strip() for p in line.split('|')]
                    # 移除空字符串
                    parts = [p for p in parts if p]
                    if len(parts) >= 3:
                        action_item = {
                            "priority": parts[0] if len(parts) > 0 else "",
                            "target": parts[1] if len(parts) > 1 else "",
                            "action": parts[2] if len(parts) > 2 else "",
                            "purpose": parts[3] if len(parts) > 3 else ""
                        }
                        # 只添加非空行
                        if action_item["priority"] and action_item["action"]:
                            result["actions"].append(action_item)
            
            if debug:
                print(f"✅ 提取到 {len(result['actions'])} 条行动建议")
    
    return result


def format_priority_emoji(priority: str) -> str:
    """将优先级转换为emoji"""
    priority_lower = priority.lower().strip()
    if '高' in priority_lower or 'high' in priority_lower or 'urgent' in priority_lower:
        return "🔴"
    elif '中' in priority_lower or 'medium' in priority_lower or 'normal' in priority_lower:
        return "🟠"
    elif '低' in priority_lower or 'low' in priority_lower:
        return "🟢"
    else:
        return "⚪"


def format_actions_table(actions: List[Dict]) -> str:
    """
    格式化行动建议为Markdown表格
    
    Args:
        actions: 行动建议列表
    
    Returns:
        Markdown格式的表格字符串
    """
    if not actions:
        return ""
    
    lines = ["| 优先级 | 行动对象 | 建议行动 |", "| --- | --- | --- |"]
    
    for action in actions:
        priority_emoji = format_priority_emoji(action.get("priority", ""))
        priority_display = f"{priority_emoji} {action.get('priority', '')}"
        target = action.get("target", "")
        action_text = action.get("action", "")
        lines.append(f"| {priority_display} | {target} | {action_text} |")
    
    return "\n".join(lines)

