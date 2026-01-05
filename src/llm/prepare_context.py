"""
LLM上下文准备模块

从完整的metrics JSON中提取关键指标，减少token消耗
策略：保留所有数值型汇总指标，列表数据只保留TOP N条
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def prepare_llm_context(
    metrics_json_path: str | Path,
    max_list_items: int = 10
) -> Dict[str, Any]:
    """
    从JSON中提取关键指标，减少token消耗
    
    Args:
        metrics_json_path: metrics结果JSON文件路径
        max_list_items: 列表数据保留的最大条数，默认10条
    
    Returns:
        精简后的指标字典，用于LLM分析
    
    策略：
    1. 保留所有数值型汇总指标
    2. 列表数据只保留TOP N条（通常是已经排序好的TOP列表）
    3. 移除不必要的详细记录
    """
    metrics_json_path = Path(metrics_json_path)
    
    if not metrics_json_path.exists():
        raise FileNotFoundError(f"未找到metrics结果文件：{metrics_json_path}")
    
    with open(metrics_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取关键指标
    context = {
        "current_month": data["current_month"],
        "previous_month": data.get("previous_month"),
        
        # Overview: 保留所有汇总指标
        "overview": {
            "scale_and_structure": data["overview"]["scale_and_structure"],
            "overall_progress": data["overview"]["overall_progress"],
            "monthly_new_progress": {
                **{k: v for k, v in data["overview"]["monthly_new_progress"].items() 
                   if not isinstance(v, list)},
                # 列表只保留前N条
                "new_opened_list": data["overview"]["monthly_new_progress"].get("new_opened_list", [])[:max_list_items],
                "new_called_list": data["overview"]["monthly_new_progress"].get("new_called_list", [])[:max_list_items],
            }
        },
        
        # Process: 保留统计指标，列表限制数量
        "process": {
            "test_progress": data["process"]["test_progress"],
            "test_cycle": {
                **{k: v for k, v in data["process"]["test_cycle"].items() 
                   if not isinstance(v, list)},
                "long_test_records": data["process"]["test_cycle"].get("long_test_records", [])[:max_list_items],
            }
        },
        
        # Conversion: 保留转化率和TOP N列表
        "conversion": {
            "core_conversion": data["conversion"]["core_conversion"],
            "product_analysis": {
                **{k: v for k, v in data["conversion"]["product_analysis"].items() 
                   if not isinstance(v, list)},
                "top_products": data["conversion"]["product_analysis"].get("top_products", []),
                "products": data["conversion"]["product_analysis"].get("products", [])[:max_list_items],
                "zero_call_products": data["conversion"]["product_analysis"].get("zero_call_products", [])[:max_list_items],
            },
            "customer_analysis": {
                **{k: v for k, v in data["conversion"]["customer_analysis"].items() 
                   if not isinstance(v, list)},
                "high_call_customers": data["conversion"]["customer_analysis"].get("high_call_customers", []),
                "customers": data["conversion"]["customer_analysis"].get("customers", [])[:max_list_items],
                "intent_not_called_customers": data["conversion"]["customer_analysis"].get("intent_not_called_customers", [])[:max_list_items],
            },
            "intent_not_opened_list": {
                **{k: v for k, v in data["conversion"]["intent_not_opened_list"].items() 
                   if not isinstance(v, list)},
                "records": data["conversion"]["intent_not_opened_list"].get("records", [])[:max_list_items],
            }
        },
        
        # Risk: 保留风险指标和TOP N列表
        "risk": {
            "completed_no_intent": {
                **{k: v for k, v in data["risk"]["completed_no_intent"].items() 
                   if not isinstance(v, list)},
                "long_term_records": data["risk"]["completed_no_intent"].get("long_term_records", [])[:max_list_items],
            },
            "intent_not_opened": {
                **{k: v for k, v in data["risk"]["intent_not_opened"].items() 
                   if not isinstance(v, list)},
                "records": data["risk"]["intent_not_opened"].get("records", [])[:max_list_items],
            },
            "opened_not_called": {
                **{k: v for k, v in data["risk"]["opened_not_called"].items() 
                   if not isinstance(v, list)},
                "long_term_records": data["risk"]["opened_not_called"].get("long_term_records", [])[:max_list_items],
            },
            "not_called_reasons": data["risk"].get("not_called_reasons", {}),
        }
    }
    
    return context


def estimate_token_count(context: Dict[str, Any]) -> int:
    """
    粗略估算token数量
    
    Args:
        context: 上下文字典
    
    Returns:
        预估的token数量
    """
    json_str = json.dumps(context, ensure_ascii=False)
    # 粗略估算：1 token ≈ 4 字符（中文和英文混合）
    return len(json_str) // 4


if __name__ == "__main__":
    # 测试
    context = prepare_llm_context("output/metrics_result_2025_12.json", max_list_items=10)
    token_count = estimate_token_count(context)
    
    print(f"提取的关键指标结构:")
    print(f"  - 当前月份: {context['current_month']}")
    print(f"  - 上月月份: {context.get('previous_month')}")
    print(f"  - 预估token数: {token_count:,}")
    print(f"\n各部分的keys:")
    print(f"  - Overview: {list(context['overview'].keys())}")
    print(f"  - Process: {list(context['process'].keys())}")
    print(f"  - Conversion: {list(context['conversion'].keys())}")
    print(f"  - Risk: {list(context['risk'].keys())}")




