"""
LLM分析文本生成模块

基于metrics计算结果，调用大模型生成运营分析解读文本
支持多种LLM API（OpenAI、Dify等）
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .prepare_context import prepare_llm_context, estimate_token_count


# 默认提示词模板
DEFAULT_PROMPT_TEMPLATE = """你是一个【运营分析结论生成器】，不是报告撰写者。

你的输入已经包含：
- 已整理好的指标数据
- 已生成的表格与图表
- 已限定分析范围与时间窗口

你的任务【仅限以下内容】：

## 一、提炼【结论】
- 只输出"判断性结论"，不复述任何具体数值
- 关注：变化、异常、结构性问题、瓶颈
- 每条结论必须是"可判断对错"的陈述
- 最多输出5条结论

## 二、给出【行动建议】
- 每条建议必须对应至少一条结论
- 建议必须可执行（明确对象 + 行为）
- 不允许泛泛而谈（如"持续关注""进一步优化"）

## 【严格禁止】
- ❌ 复述表格或图表中的数值
- ❌ 重复描述"新增多少、占比多少"等已给出的事实
- ❌ 输出完整报告结构或章节标题
- ❌ 使用"本报告认为 / 本文分析 / 综上所述"等报告语言
- ❌ 输出超过 15 行的自然语言

## 【输出格式（必须严格遵守）】

### 结论

- 结论 1
- 结论 2
- 结论 3（最多 5 条）

### 行动建议

| 优先级 | 行动对象 | 建议行动 | 目的 |
|------|--------|--------|----|
| 高 |  |  |  |
| 中 |  |  |  |

## 【风格要求】
- 使用要点式表达
- 每条不超过 2 行
- 面向"业务负责人 / 运营负责人"阅读

## 数据说明
- 当前分析月份：{current_month}
- 对比基准月份：{previous_month}（如果存在）

## 核心业务逻辑
1. **收益判断标准**：只有"已调用"才代表真实业务收益，测试状态、接入意向、是否开通仅用于流程分析
2. **关键转化指标**：
   - 整体调用率 = 已调用数量 / 总测试记录数
   - 开通→调用转化率 = 已调用数量 / 已开通数量
   - 接入意向→调用转化率 = 已调用数量 / 已明确接入意向数量

## 需要分析的数据

```json
{metrics_data}
```

请基于以上数据，生成结论和行动建议："""


class LLMClient:
    """LLM客户端基类"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
        
        Returns:
            生成的文本
        """
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量OPENAI_API_KEY读取
            model: 模型名称，默认gpt-4
        """
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """调用OpenAI API生成文本"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一位资深的运营数据分析专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        return response.choices[0].message.content


class AliyunBailianClient(LLMClient):
    """阿里云百炼（通义千问）API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-turbo", base_url: Optional[str] = None):
        """
        初始化阿里云百炼客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量ALIYUN_BAILIAN_API_KEY读取
            model: 模型名称，默认qwen-turbo，可选：qwen-turbo, qwen-plus, qwen-max等
            base_url: API基础URL，如果不提供则从环境变量ALIYUN_BAILIAN_BASE_URL读取，默认使用官方API地址
        """
        import requests
        self.requests = requests
        self.api_key = api_key or os.getenv("ALIYUN_BAILIAN_API_KEY")
        self.model = model
        # 阿里云百炼API的正确端点
        # 使用OpenAI兼容格式的端点（推荐）
        default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        # 如果环境变量中设置了URL，优先使用环境变量的值
        env_url = os.getenv("ALIYUN_BAILIAN_BASE_URL")
        self.base_url = base_url or env_url or default_base_url
        
        if not self.api_key:
            raise ValueError("需要提供ALIYUN_BAILIAN_API_KEY环境变量或api_key参数")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """调用阿里云百炼API生成文本"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 判断使用哪种API格式
        # 如果base_url包含compatible-mode，使用OpenAI兼容格式
        # 否则使用阿里云原生格式
        if "/compatible-mode/" in self.base_url:
            # OpenAI兼容格式
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一位资深的运营数据分析专家，擅长风控服务运营数据分析。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
            }
        else:
            # 阿里云原生格式
            data = {
                "model": self.model,
                "input": {
                    "messages": [
                        {"role": "system", "content": "你是一位资深的运营数据分析专家，擅长风控服务运营数据分析。"},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                }
            }
        
        response = self.requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=kwargs.get("timeout", 60)
        )
        response.raise_for_status()
        result = response.json()
        
        # 提取生成的文本（兼容两种格式）
        if "/compatible-mode/" in self.base_url:
            # OpenAI兼容格式的返回
            if result.get("choices") and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"API返回格式异常: {result}")
        else:
            # 阿里云原生格式的返回
            if result.get("output") and result["output"].get("choices"):
                return result["output"]["choices"][0]["message"]["content"]
            elif result.get("output") and result["output"].get("text"):
                return result["output"]["text"]
            else:
                raise ValueError(f"API返回格式异常: {result}")


class DifyClient(LLMClient):
    """Dify API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化Dify客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量DIFY_API_KEY读取
            base_url: API基础URL，如果不提供则从环境变量DIFY_BASE_URL读取
        """
        import requests
        self.requests = requests
        self.api_key = api_key or os.getenv("DIFY_API_KEY")
        self.base_url = base_url or os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
        
        if not self.api_key:
            raise ValueError("需要提供DIFY_API_KEY环境变量或api_key参数")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """调用Dify API生成文本"""
        # Dify API调用示例（需要根据实际API调整）
        # 这里提供一个通用的实现框架
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 注意：这里需要根据Dify的实际API格式调整
        # 以下是示例格式，实际使用时需要查看Dify API文档
        data = {
            "inputs": {"query": prompt},
            "query": prompt,
            "response_mode": "blocking",
            "user": "ops-analytics"
        }
        
        # 这里假设使用Dify的chat API
        # 实际使用时需要根据Dify的API文档调整endpoint和参数格式
        response = self.requests.post(
            f"{self.base_url}/chat-messages",
            headers=headers,
            json=data,
            timeout=kwargs.get("timeout", 60)
        )
        response.raise_for_status()
        result = response.json()
        
        # 根据Dify API的实际返回格式提取文本
        # 这里需要根据实际情况调整
        return result.get("answer", "") or result.get("message", "")


def generate_llm_insights(
    month: str,
    llm_client: Optional[LLMClient] = None,
    prompt_template: Optional[str] = None,
    max_list_items: int = 10,
    **llm_kwargs
) -> str:
    """
    生成LLM分析解读文本
    
    Args:
        month: 月份，格式YYYY-MM
        llm_client: LLM客户端实例，如果不提供则尝试自动创建
        prompt_template: 提示词模板，如果不提供则使用默认模板
        max_list_items: 列表数据保留的最大条数
        **llm_kwargs: 传递给LLM客户端的其他参数
    
    Returns:
        生成的Markdown格式分析文本
    """
    # 准备上下文数据（按月份组织）
    output_dir = Path("output") / month.replace('-', '_')
    metrics_file = output_dir / f"metrics_result_{month.replace('-', '_')}.json"
    
    context = prepare_llm_context(metrics_file, max_list_items=max_list_items)
    
    # 估算token数
    token_count = estimate_token_count(context)
    print(f"准备LLM上下文完成，预估token数: {token_count:,}")
    
    # 创建LLM客户端（如果未提供）
    if llm_client is None:
        # 优先尝试阿里云百炼
        if os.getenv("ALIYUN_BAILIAN_API_KEY"):
            print("使用阿里云百炼API")
            llm_client = AliyunBailianClient()
        # 其次尝试OpenAI
        elif os.getenv("OPENAI_API_KEY"):
            print("使用OpenAI API")
            llm_client = OpenAIClient()
        # 最后尝试Dify
        elif os.getenv("DIFY_API_KEY"):
            print("使用Dify API")
            llm_client = DifyClient()
        else:
            raise ValueError(
                "未找到LLM API配置。请设置环境变量：\n"
                "- ALIYUN_BAILIAN_API_KEY (使用阿里云百炼)\n"
                "- 或 OPENAI_API_KEY (使用OpenAI)\n"
                "- 或 DIFY_API_KEY 和 DIFY_BASE_URL (使用Dify)"
            )
    
    # 准备提示词
    if prompt_template is None:
        prompt_template = DEFAULT_PROMPT_TEMPLATE
    
    metrics_json_str = json.dumps(context, ensure_ascii=False, indent=2)
    
    prompt = prompt_template.format(
        current_month=context["current_month"],
        previous_month=context.get("previous_month", "无"),
        metrics_data=metrics_json_str
    )
    
    # 调用LLM生成文本
    print("正在调用LLM生成分析文本...")
    insights = llm_client.generate(prompt, **llm_kwargs)
    
    return insights


def save_llm_insights(month: str, insights: str) -> Path:
    """
    保存LLM生成的解读文本
    
    Args:
        month: 月份，格式YYYY-MM
        insights: LLM生成的文本
    
    Returns:
        保存的文件路径
    """
    output_dir = Path("output") / month.replace('-', '_') / "llm_insights"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    insights_file = output_dir / f"insights_{month.replace('-', '_')}.md"
    
    with open(insights_file, 'w', encoding='utf-8') as f:
        f.write(f"# LLM生成的分析解读 - {month}\n\n")
        f.write(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(insights)
    
    print(f"LLM解读文本已保存至: {insights_file}")
    return insights_file


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python -m src.llm.generate_insights YYYY-MM")
        sys.exit(1)
    
    month = sys.argv[1]
    
    try:
        insights = generate_llm_insights(month)
        save_llm_insights(month, insights)
        print("\n生成完成！")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

