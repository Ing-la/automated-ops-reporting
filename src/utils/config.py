"""
配置管理模块

从环境变量读取配置，避免硬编码敏感信息
支持从.env文件加载配置（如果存在）
"""

import os
from pathlib import Path
from typing import Optional

# 尝试加载.env文件（如果存在）
# 注意：主脚本会在导入模块前显式加载.env，这里作为备用
try:
    from dotenv import load_dotenv
    # 使用绝对路径计算项目根目录的.env文件
    config_file = Path(__file__).resolve()
    project_root = config_file.parent.parent.parent
    env_path = project_root / '.env'
    if env_path.exists():
        # 使用override=True确保.env文件优先于系统环境变量
        load_dotenv(env_path, override=True)
except ImportError:
    # python-dotenv未安装，跳过
    pass
except Exception:
    # 加载失败不影响程序运行
    pass


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    从环境变量读取配置值
    
    Args:
        key: 环境变量键名
        default: 默认值（如果环境变量不存在）
        required: 是否必需，如果为True且环境变量不存在则抛出异常
    
    Returns:
        环境变量值或默认值
    
    Raises:
        ValueError: 如果required=True但环境变量不存在
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"必需的环境变量 {key} 未设置")
    return value


# LLM配置
def get_llm_config() -> dict:
    """获取LLM配置"""
    return {
        "aliyun_bailian_api_key": get_env("ALIYUN_BAILIAN_API_KEY"),
        "aliyun_bailian_base_url": get_env("ALIYUN_BAILIAN_BASE_URL"),
        "openai_api_key": get_env("OPENAI_API_KEY"),
        "dify_api_key": get_env("DIFY_API_KEY"),
        "dify_base_url": get_env("DIFY_BASE_URL"),
    }


# 飞书配置
def get_feishu_config() -> dict:
    """获取飞书配置"""
    webhook_url = get_env("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        # 检查是否存在 .env.example 文件
        config_file = Path(__file__).resolve()
        project_root = config_file.parent.parent.parent
        env_example = project_root / '.env.example'
        env_file = project_root / '.env'
        
        error_msg = "未配置飞书Webhook URL。\n\n"
        error_msg += "请执行以下步骤之一：\n"
        error_msg += "1. 运行初始化脚本：python scripts/init_env.py\n"
        error_msg += "2. 手动复制配置文件："
        if env_example.exists():
            error_msg += f"\n   Windows: copy .env.example .env\n"
            error_msg += f"   Linux/Mac: cp .env.example .env\n"
        error_msg += "3. 编辑 .env 文件，填入 FEISHU_WEBHOOK_URL\n"
        error_msg += "4. 或设置系统环境变量 FEISHU_WEBHOOK_URL\n\n"
        error_msg += "详细说明请参考：docs/配置指南.md"
        raise ValueError(error_msg)
    secret = get_env("FEISHU_WEBHOOK_SECRET")  # 签名密钥（可选，如果启用了签名校验）
    return {
        "webhook_url": webhook_url,
        "secret": secret,
    }


# OSS配置
def get_oss_config() -> dict:
    """获取OSS配置"""
    return {
        "bucket_name": get_env("OSS_BUCKET_NAME"),
        "endpoint": get_env("OSS_ENDPOINT"),
        "access_key_id": get_env("OSS_ACCESS_KEY_ID"),
        "access_key_secret": get_env("OSS_ACCESS_KEY_SECRET"),
    }

