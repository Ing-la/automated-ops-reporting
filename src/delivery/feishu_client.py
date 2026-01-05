"""
飞书推送客户端

使用飞书机器人Webhook API推送消息
支持签名验证（如果启用了签名校验）
"""

import json
import os
import time
import hmac
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from src.utils.config import get_feishu_config


class FeishuClient:
    """飞书机器人客户端"""
    
    def __init__(self, webhook_url: Optional[str] = None, secret: Optional[str] = None):
        """
        初始化飞书客户端
        
        Args:
            webhook_url: 飞书Webhook URL，如果不提供则从环境变量读取
            secret: 签名密钥（如果启用了签名校验），如果不提供则从环境变量读取
        """
        config = get_feishu_config()
        self.webhook_url = webhook_url or config["webhook_url"]
        self.secret = secret or config.get("secret")
        if not self.webhook_url:
            raise ValueError("未配置飞书Webhook URL，请设置环境变量 FEISHU_WEBHOOK_URL")
    
    def _generate_signature(self, timestamp: str, body: str = "") -> str:
        """
        生成签名（如果配置了密钥）
        
        根据飞书官方文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
        
        Args:
            timestamp: 时间戳（字符串）
            body: 请求体JSON字符串（可选，某些版本可能需要）
        
        Returns:
            签名字符串
        """
        if not self.secret:
            return ""
        
        # 飞书Webhook v2签名算法：timestamp + "\n" + secret
        # 注意：根据官方文档，Webhook v2只需要timestamp和secret，不需要请求体
        string_to_sign = f"{timestamp}\n{self.secret}"
        
        # 使用HMAC-SHA256计算签名
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        # Base64编码
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    def send_text(self, text: str) -> bool:
        """
        发送文本消息
        
        Args:
            text: 消息文本（支持Markdown格式）
        
        Returns:
            是否发送成功
        """
        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        return self._send(payload)
    
    def send_card(self, title: str, content: str, link_url: Optional[str] = None) -> bool:
        """
        发送卡片消息（旧版格式，保留兼容性）
        
        Args:
            title: 卡片标题
            content: 卡片内容（支持Markdown）
            link_url: 跳转链接（可选）
        
        Returns:
            是否发送成功
        """
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content
                }
            }
        ]
        
        if link_url:
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "查看完整报告"
                        },
                        "type": "primary",
                        "url": link_url
                    }
                ]
            })
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": elements
            }
        }
        return self._send(payload)
    
    def send_report_card(
        self,
        title: str,
        report_meta: str,
        key_metrics: Optional[str] = None,
        conclusions: List[str] = None,
        actions: List[Dict[str, str]] = None,
        report_url: Optional[str] = None,
        table_urls: List[Dict[str, str]] = None
    ) -> bool:
        """
        发送报告卡片（新版格式）
        
        Args:
            title: 卡片标题（例如："📊 风控运营分析报告｜2025-12"）
            report_meta: 报告元信息（时间/范围）
            key_metrics: 关键指标摘要（可选）
            conclusions: 核心结论列表（3-5条，可选）
            actions: 行动建议列表，每个元素包含 priority, target, action, purpose（可选）
            report_url: 完整报告链接（可选）
            table_urls: 表格附件链接列表，每个元素包含 name 和 url（可选）
        
        Returns:
            是否发送成功
        """
        if conclusions is None:
            conclusions = []
        if actions is None:
            actions = []
        if table_urls is None:
            table_urls = []
            
        elements = []
        
        # 1. 报告元信息
        if report_meta:
            elements.append({
                "tag": "markdown",
                "content": report_meta
            })
        
        # 2. 关键指标摘要
        if key_metrics:
            elements.append({
                "tag": "markdown",
                "content": key_metrics
            })
        
        # 3. 分隔线
        elements.append({"tag": "hr"})
        
        # 4. 核心结论
        if conclusions:
            conclusions_text = "**🔍 核心结论**\n" + "\n".join([f"- {c}" for c in conclusions])
            elements.append({
                "tag": "markdown",
                "content": conclusions_text
            })
        else:
            # 如果没有结论，显示提示信息
            elements.append({
                "tag": "markdown",
                "content": "**🔍 核心结论**\n- 暂无LLM分析结论（请使用 --include-llm 参数生成）"
            })
        
        # 5. 重点行动
        if actions:
            from .parse_llm_insights import format_actions_table
            actions_table = format_actions_table(actions)
            if actions_table:
                actions_text = "**👉 重点行动（本月）**\n" + actions_table
                elements.append({
                    "tag": "markdown",
                    "content": actions_text
                })
        elif conclusions:
            # 如果有结论但没有行动建议，显示提示信息
            elements.append({
                "tag": "markdown",
                "content": "**👉 重点行动（本月）**\n- 暂无行动建议"
            })
        
        # 6. 数据附件（如果有）
        if table_urls:
            table_links = []
            # 表格名称映射（中文显示名称）
            table_name_map = {
                'new_opened_list': '本月新开通列表',
                'new_called_list': '本月新调用列表',
                'long_test_records': '超长测试周期记录',
                'intent_not_opened': '有意向但未开通列表',
                'completed_no_intent': '长期无意向记录',
                'opened_not_called': '长期未调用记录'
            }
            
            for table_info in table_urls:
                table_name = table_info.get('name', '')
                table_url = table_info.get('url', '')
                display_name = table_name_map.get(table_name, table_name)
                if table_url:
                    table_links.append(f"- [{display_name}]({table_url})")
            
            if table_links:
                elements.append({"tag": "hr"})
                attachments_text = "**📎 数据附件**\n" + "\n".join(table_links)
                elements.append({
                    "tag": "markdown",
                    "content": attachments_text
                })
        
        # 7. 分隔线
        elements.append({"tag": "hr"})
        
        # 8. 操作按钮
        if report_url:
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📄 查看完整报告"
                        },
                        "url": report_url,
                        "type": "primary"
                    }
                ]
            })
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": elements
            }
        }
        return self._send(payload)
    
    def _send(self, payload: Dict[str, Any]) -> bool:
        """
        发送请求到飞书Webhook
        
        Args:
            payload: 请求负载
        
        Returns:
            是否发送成功
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # 如果配置了签名密钥，添加签名验证
            # 根据飞书官方文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
            # Webhook v2使用请求头方式：X-Lark-Signature 和 X-Lark-Request-Timestamp
            # 签名算法：timestamp + "\n" + secret，然后HMAC-SHA256，最后Base64编码
            if self.secret:
                timestamp = str(int(time.time()))
                sign = self._generate_signature(timestamp)
                headers["X-Lark-Signature"] = sign
                headers["X-Lark-Request-Timestamp"] = timestamp
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # 飞书API返回code=0表示成功
            if result.get("code") == 0:
                return True
            else:
                error_msg = result.get('msg', '未知错误')
                error_code = result.get('code', '未知')
                print(f"⚠️  飞书推送失败: {error_msg} (code: {error_code})")
                
                # 如果是签名错误，提示检查密钥配置
                if error_code == 19021:
                    print("   提示：签名验证失败")
                    print("   请检查：")
                    print("   1. FEISHU_WEBHOOK_SECRET 是否正确")
                    print("   2. 机器人是否启用了签名校验")
                    print("   3. 如果机器人未启用签名校验，可以不设置 FEISHU_WEBHOOK_SECRET")
                
                return False
        except Exception as e:
            print(f"⚠️  飞书推送异常: {e}")
            import traceback
            traceback.print_exc()
            return False


def push_to_feishu(
    title: str,
    summary: str,
    report_url: Optional[str] = None,
    webhook_url: Optional[str] = None,
    secret: Optional[str] = None,
    use_card: bool = True
) -> bool:
    """
    推送报告摘要到飞书
    
    Args:
        title: 消息标题
        summary: 报告摘要（Markdown格式）
        report_url: 完整报告链接（可选）
        webhook_url: 飞书Webhook URL（可选，默认从环境变量读取）
        secret: 签名密钥（可选，默认从环境变量读取）
        use_card: 是否使用卡片格式（默认True，支持Markdown渲染）
    
    Returns:
        是否推送成功
    """
    client = FeishuClient(webhook_url=webhook_url, secret=secret)
    
    # 始终使用卡片格式以支持Markdown渲染
    if use_card:
        return client.send_card(title=title, content=summary, link_url=report_url)
    else:
        # 如果明确不使用卡片，使用文本格式（不推荐，Markdown可能无法正确渲染）
        return client.send_text(f"## {title}\n\n{summary}")

