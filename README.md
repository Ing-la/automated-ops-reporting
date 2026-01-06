# Ops Risk Analytics

> 风控运营数据自动化分析工具 · 月度运营分析报告自动生成

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

自动化分析风控服务运营测试数据，生成结构化分析结果与运营报告，支持 LLM 智能解读、可视化图表生成、飞书自动推送和 OSS 自动上传。

## 🎓 项目背景

本项目是一个完整的数据分析应用，用于自动化分析风控服务运营数据并生成月度报告。项目开发过程中采用了 AI Agent（Cursor）协作方式，在 3 天内完成了从需求到部署的完整流程，展示了 AI 协作在应用开发中的高效性。

> 💡 **相关项目**：如果您对 AI Agent 协作方法论感兴趣，欢迎查看 [Multi-Agent Workflow Framework](https://github.com/Ing-la/multi-agent-workflow-framework) 项目。该框架探索了如何使用多 Agent 协作完成数据分析任务，通过规范化的角色分工（数据分析Agent、脚本编写Agent、审阅Agent）和文档驱动的协作机制，实现高效、可控、可追溯的数据分析流程。框架强调安全可控：Agent 仅生成脚本，不访问真实数据，执行由人工完成，确保数据安全的同时充分发挥 AI 能力。而本项目则是一个实际的数据分析应用产品，两者都涉及数据分析领域，但关注点不同：一个是方法论探索，一个是实际应用产品。

## ✨ 特性

- 📊 **自动化月度分析** - 从原始数据到完整报告的自动化流程
- 🤖 **LLM 智能解读** - 支持阿里云百炼、OpenAI、Dify，生成分析结论和建议
- 📈 **可视化图表** - 自动生成转化漏斗图、TOP10 图表等
- 📱 **飞书自动推送** - 报告摘要自动推送到飞书，支持卡片格式
- ☁️ **OSS 自动上传** - 报告和表格附件自动上传到阿里云 OSS
- 🖥️ **GUI 图形界面** - 友好的图形界面，无需命令行操作
- 🔄 **自动模式** - 自动检测文件和月份，简化操作流程
- 📋 **数据快照管理** - 支持跨月数据对比和历史回溯

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/Ing-la/automated-ops-reporting.git
cd "Ops Risk Analytics"

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 初始化配置文件（自动创建 .env 和必要目录）
python scripts/init_env.py

# 编辑 .env 文件，至少配置飞书 Webhook URL
# 详细配置说明请参考：docs/配置指南.md
```

### 运行

#### 方式1：GUI 界面（推荐）

**Windows 用户**：双击 `启动GUI.bat` 文件

**命令行启动**：
```bash
python scripts/gui_app.py
```

#### 方式2：命令行

```bash
# 自动模式（自动检测 raw 目录中的文件）
python scripts/run_monthly.py

# 手动指定参数
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --upload-oss
```

## 📖 文档

- 📘 [详细文档](docs/README.md) - 完整的功能说明、设计原则、工作流程
- ⚙️ [配置指南](docs/配置指南.md) - LLM、飞书、OSS 等详细配置说明
- 🏗️ [项目结构](docs/项目结构.md) - 项目目录结构和模块说明
- 📝 [更新日志](docs/更新日志.md) - 项目更新记录

## 🎯 主要功能

### 数据处理
- 读取 Excel 原始数据（近3个月）
- 与历史快照对齐和合并
- 生成月度全量快照

### 指标计算
- 总体运营盘点
- 流程与进度分析
- 转化与收益分析
- 滞后与风险识别

### 报告生成
- Markdown 和 PDF 报告
- 可视化图表（漏斗图、TOP10 等）
- LLM 智能解读（可选）
- 数据表格附件（CSV）

### 自动推送
- 飞书卡片推送（报告摘要 + LLM 结论）
- OSS 文件上传（报告和表格）
- 数据附件链接展示

## 📋 输出示例

运行后会生成以下文件：

```
output/YYYY_MM/
├── report/
│   ├── report_YYYY_MM.md      # Markdown 报告
│   └── report_YYYY_MM.pdf      # PDF 报告
├── figures/                    # 图表文件
├── tables/                     # 数据表格（CSV）
└── llm_insights/              # LLM 分析结果
```

## 🔧 系统要求

- Python 3.8+
- 依赖包见 `requirements.txt`

## 📄 License

本项目采用 [MIT License](LICENSE) 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请：
1. 查看 [详细文档](docs/README.md)
2. 检查 [配置指南](docs/配置指南.md)
3. 提交 [Issue](https://github.com/Ing-la/automated-ops-reporting/issues)

---

**快速链接**：[详细文档](docs/README.md) | [配置指南](docs/配置指南.md) | [项目结构](docs/项目结构.md)
