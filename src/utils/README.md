# utils 模块说明

## 功能概述

utils模块提供项目通用的工具函数和配置管理功能。

## 模块结构

- `config.py`：配置管理模块（环境变量读取）
- `file_management.py`：文件管理工具（raw数据移动和历史记录）
- `file_validator.py`：文件验证工具（Excel结构验证和月份检测）

## config.py - 配置管理

### 功能

从环境变量读取配置，避免硬编码敏感信息。

### 主要函数

- `get_env(key, default=None, required=False)`：从环境变量读取配置值
- `get_llm_config()`：获取LLM配置（阿里云百炼、OpenAI、Dify）
- `get_feishu_config()`：获取飞书配置（Webhook URL和Secret）
- `get_oss_config()`：获取OSS配置（Bucket、Endpoint、AccessKey等）

### 使用方法

```python
from src.utils.config import get_env, get_llm_config, get_feishu_config, get_oss_config

# 读取单个环境变量
api_key = get_env("ALIYUN_BAILIAN_API_KEY", required=True)

# 获取LLM配置
llm_config = get_llm_config()
api_key = llm_config["aliyun_bailian_api_key"]

# 获取飞书配置
feishu_config = get_feishu_config()
webhook_url = feishu_config["webhook_url"]

# 获取OSS配置
oss_config = get_oss_config()
bucket_name = oss_config["bucket_name"]
```

### 环境变量列表

**LLM配置**：
- `ALIYUN_BAILIAN_API_KEY`：阿里云百炼API密钥
- `ALIYUN_BAILIAN_BASE_URL`：阿里云百炼API基础URL
- `OPENAI_API_KEY`：OpenAI API密钥
- `DIFY_API_KEY`：Dify API密钥
- `DIFY_BASE_URL`：Dify API基础URL

**飞书配置**：
- `FEISHU_WEBHOOK_URL`：飞书Webhook URL（必需）
- `FEISHU_WEBHOOK_SECRET`：飞书Webhook签名密钥（可选）

**OSS配置**：
- `OSS_BUCKET_NAME`：OSS Bucket名称
- `OSS_ENDPOINT`：OSS Endpoint
- `OSS_ACCESS_KEY_ID`：OSS AccessKey ID
- `OSS_ACCESS_KEY_SECRET`：OSS AccessKey Secret

## file_management.py - 文件管理

### 功能

用于管理raw数据的移动和历史记录。

### 主要函数

- `move_raw_to_history(raw_file, month)`：将raw数据文件移动到history目录
- `clear_raw_directory(month, raw_dir=None)`：清理raw目录，将所有文件移动到history

### 使用方法

```python
from src.utils.file_management import move_raw_to_history, clear_raw_directory
from pathlib import Path

# 移动单个文件到history
raw_file = Path("data/raw/ops_data_2025_12.xlsx")
history_file = move_raw_to_history(raw_file, "2025-12")

# 清理整个raw目录
moved_files = clear_raw_directory("2025-12")
```

### 文件路径规则

- **raw目录**：`data/raw/`（不纳入版本控制）
- **history目录**：`data/history/YYYY_MM/`（按月份组织）
- **文件命名**：保留原文件名，如果目标文件已存在，添加时间戳后缀

## file_validator.py - 文件验证

### 功能

验证Excel文件结构，检测月份，查找raw目录中的文件。

### 主要函数

- `validate_excel_structure(file_path)`：验证Excel文件是否包含必需的列
- `detect_month_from_file(file_path)`：从文件中检测月份（优先从"申请时间"字段，否则使用文件修改时间）
- `find_raw_files(raw_dir)`：查找raw目录中的所有Excel文件

### 使用方法

```python
from src.utils.file_validator import validate_excel_structure, detect_month_from_file, find_raw_files
from pathlib import Path

# 验证文件结构
is_valid, error_msg = validate_excel_structure(Path("data/raw/ops_data.xlsx"))
if not is_valid:
    print(f"文件验证失败: {error_msg}")

# 检测月份
month = detect_month_from_file(Path("data/raw/ops_data.xlsx"))
print(f"检测到月份: {month}")  # 输出: 2025-12

# 查找raw目录中的文件
raw_dir = Path("data/raw")
files = find_raw_files(raw_dir)
print(f"找到 {len(files)} 个文件")
```

### 必需列

Excel文件必须包含以下列：
- 客户简称
- 子产品名称
- 申请时间
- 测试返回时间
- 接入意向
- 是否开通
- 是否调用
- 样本量

## 注意事项

1. **配置安全**：不要将包含敏感信息的配置提交到代码仓库
2. **环境变量**：使用 `.env` 文件管理配置，参考 `.env.example`
3. **文件移动**：移动文件前会自动创建目标目录
4. **文件冲突**：如果目标文件已存在，会自动添加时间戳后缀


