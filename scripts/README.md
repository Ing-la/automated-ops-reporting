# scripts 模块说明

## 功能概述

scripts模块包含项目的主要执行脚本，用于运行完整的月度分析流程。

## 脚本列表

### `gui_app.py` - GUI图形界面（推荐）

**功能**：提供可视化的图形界面，方便非技术用户使用。

**启动方式**：
- **Windows**：双击 `启动GUI.bat` 文件
- **命令行**：`python scripts/gui_app.py`

**功能特点**：
- 📁 **文件选择**：点击按钮选择Excel数据文件，自动验证文件结构
- ⚙️ **配置管理**：3个选项卡分别配置LLM、飞书、OSS参数
  - 自动从 `.env` 文件加载默认值
  - 支持保存配置到 `.env` 文件
- ✅ **功能选项**：勾选启用/禁用LLM分析、OSS上传、飞书推送
- 📊 **一键执行**：点击"开始分析"执行完整流程
- 📝 **实时日志**：实时查看运行状态和输出信息
- 🔍 **智能检测**：自动检测当前使用的LLM提供商

**使用流程**：
1. 启动GUI界面
2. 点击"选择Excel文件"选择数据文件
3. 在配置选项卡中填写或修改配置（留空则使用.env默认值）
4. 勾选需要的功能选项
5. 点击"保存配置"保存到.env（可选）
6. 点击"开始分析"执行完整流程
7. 在日志区域查看运行状态

**注意事项**：
- 如果选择的文件已在 `data/raw/` 目录中，不会重复复制
- 配置项留空则使用 `.env` 文件中的默认值
- 运行前会自动验证必需配置

### `run_monthly.py` - 月度分析主脚本（命令行）

**功能**：执行完整的月度运营分析流程，从raw数据到报告生成和推送。

**完整流程**：
1. **生成snapshot**：读取raw数据，与上月snapshot对齐，生成当月snapshot
2. **计算metrics**：基于snapshot计算所有运营指标
3. **生成报告**：整合指标、图表、LLM分析，生成Markdown和PDF报告
4. **推送报告**：自动推送报告摘要到飞书（可选）
5. **清理数据**：将raw数据移动到history目录

**使用方法**：

```bash
# 自动模式（推荐）- 自动检测raw目录中的文件
python scripts/run_monthly.py

# 手动指定参数
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx

# 包含LLM分析
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm

# 自动上传到OSS并推送飞书
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --upload-oss

# 跳过某些步骤
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --skip-snapshot --skip-metrics
```

**参数说明**：

可选参数（自动模式）：
- 如果不提供参数，脚本会自动检测 `data/raw/` 目录中的Excel文件
- 自动验证文件结构
- 自动检测月份（从文件中的"申请时间"字段或文件修改时间）

必需参数（手动模式）：
- `month`：目标月份，格式 YYYY-MM（例如：2025-12）
- `raw_file`：raw数据文件名（例如：ops_data_2025_12.xlsx）

可选参数：
- `--include-llm`：在报告中包含LLM生成的分析解读（需要配置LLM API密钥）
- `--upload-oss`：自动上传报告到OSS（需要配置OSS环境变量）
- `--skip-snapshot`：跳过snapshot生成（如果已生成）
- `--skip-metrics`：跳过metrics计算（如果已计算）
- `--skip-report`：跳过报告生成
- `--skip-push`：跳过报告推送（默认会自动推送到飞书）
- `--report-url`：完整报告的URL链接（用于推送时提供跳转链接）
- `--report-base-url`：报告文件的基础URL（用于自动生成报告链接）

**输出文件**：

脚本执行后会生成以下文件：
- `data/snapshot/snapshot_YYYY_MM.csv`：当月snapshot
- `output/YYYY_MM/metrics_result_YYYY_MM.json`：指标计算结果
- `output/YYYY_MM/report/report_YYYY_MM.md`：Markdown报告
- `output/YYYY_MM/report/report_YYYY_MM.pdf`：PDF报告
- `output/YYYY_MM/figures/`：图表文件
- `output/YYYY_MM/tables/`：数据表格
- `output/YYYY_MM/llm_insights/`：LLM分析结果（如果启用）
- `data/history/YYYY_MM/`：历史数据归档

**注意事项**：

1. **首次运行**：如果上个月的snapshot不存在，脚本会自动处理（适用于首次初始化）
2. **错误处理**：如果某个步骤失败，脚本会输出错误信息并退出
3. **推送失败不影响主流程**：如果推送失败，报告仍会正常生成
4. **数据清理**：raw数据会在最后自动移动到history目录

### `init_env.py` - 环境配置初始化脚本

**功能**：从 `.env.example` 复制创建 `.env` 配置文件（如果不存在）。

**使用方法**：

```bash
python scripts/init_env.py
```

**功能**：
- 检查 `.env` 文件是否存在
- 如果不存在，从 `.env.example` 复制创建
- 如果已存在，提示用户无需重复初始化

**使用场景**：
- 首次克隆项目后初始化配置
- 配置丢失后快速恢复
- 新环境部署时快速设置

**注意事项**：
- 脚本只会创建 `.env` 文件，不会覆盖已存在的文件
- 创建后需要手动编辑 `.env` 文件填入实际配置值
- 详细配置说明请参考：`docs/配置指南.md`

### `fix_snapshot_format.py` - 快照格式修复工具

**功能**：修复历史snapshot格式，用于快照schema变更后的数据迁移。

**使用方法**：

```bash
python scripts/fix_snapshot_format.py 2025-11
```

**功能**：
- 删除"测试中"列（如果存在）
- 添加"申请测试"列（基于申请日期）
- 验证"完成测试"列的逻辑（基于测试返回日期）

**注意事项**：
- 脚本会自动备份原文件（添加.backup后缀）
- 修改前请确认备份文件已正确创建

## 完整流程验证

主脚本 `run_monthly.py` 可以完成以下完整流程：

✅ **步骤1：生成snapshot**
- 读取raw数据（近3个月）
- 与上月snapshot对齐
- 生成当月snapshot（全量）

✅ **步骤2：计算metrics**
- 总体运营指标
- 流程进度指标
- 转化率指标
- 风险识别指标

✅ **步骤3：生成报告**
- 生成图表
- 生成数据表格
- 调用LLM生成分析（可选）
- 生成Markdown和PDF报告

✅ **步骤4：推送报告**
- 提取关键指标
- 解析LLM结论（如果存在）
- 上传到OSS（可选）
- 推送到飞书

✅ **步骤5：清理数据**
- 将raw数据移动到history目录

## 依赖关系

脚本依赖以下模块：
- `src.processing.generate_snapshot`：snapshot生成
- `src.metrics.calculate_all`：指标计算
- `src.report.generate_report`：报告生成
- `src.delivery.push_report`：报告推送
- `src.utils.file_management`：文件管理

## 环境要求

- Python 3.7+
- 所有依赖包（见 `requirements.txt`）
- 环境变量配置（见 `.env.example`）


