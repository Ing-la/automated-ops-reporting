"""
初始化环境配置文件
从 .env.example 复制创建 .env 文件（如果不存在）
"""
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ENV_EXAMPLE = PROJECT_ROOT / '.env.example'
ENV_FILE = PROJECT_ROOT / '.env'

def init_env():
    """初始化 .env 文件"""
    if ENV_FILE.exists():
        print(f"✓ .env 文件已存在: {ENV_FILE}")
        print("  如需重新初始化，请先删除现有 .env 文件")
        return False
    
    if not ENV_EXAMPLE.exists():
        print(f"✗ 未找到 .env.example 文件: {ENV_EXAMPLE}")
        print("  请确保项目包含 .env.example 文件")
        return False
    
    try:
        shutil.copy2(ENV_EXAMPLE, ENV_FILE)
        print(f"✓ 已创建 .env 文件: {ENV_FILE}")
        print("  请编辑 .env 文件，填入您的实际配置")
        print(f"  参考文档: docs/配置指南.md")
        return True
    except Exception as e:
        print(f"✗ 创建 .env 文件失败: {e}")
        return False

if __name__ == '__main__':
    init_env()

