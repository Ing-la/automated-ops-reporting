# Ops Risk Analytics · 风控运营数据自动化分析项目

## 项目简介

本项目用于对风控服务运营测试数据进行周期性（月度）自动化分析，覆盖金融机构客户从测试、接入意向、接口开通到真实调用的完整流程，生成结构化分析结果与运营分析报告，并自动推送至飞书。

## 核心设计原则

- **确定性优先**：所有统计与计算均由 Python 明确实现，不依赖大模型推断
- **口径统一**：关键状态与指标采用业务规则统一规范
- **结构化输出**：分析结果先结构化，再生成文本报告
- **大模型仅负责解读**：模型不参与计算、不直接接触原始数据
- **可回溯可审计**：支持跨月数据更新与历史对比

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd "Ops Risk Analytics"

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

**首次使用**：需要创建 `.env` 配置文件。

#### 方式1：使用初始化脚本（推荐）

```bash
python scripts/init_env.py
```

#### 方式2：手动复制配置文件

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

#### 编辑配置文件

创建 `.env` 文件后，编辑该文件，至少配置：
- `FEISHU_WEBHOOK_URL`：飞书Webhook URL（必需）
- `ALIYUN_BAILIAN_API_KEY`：阿里云百炼API密钥（如需LLM分析）

**注意**：`.env` 文件包含敏感信息，不会被提交到代码仓库。首次克隆项目后需要手动创建。

详细配置说明请参考：[配置指南](docs/配置指南.md)

### 3. 运行月度分析

#### 方式1：使用GUI界面（推荐）

**Windows用户**：双击 `启动GUI.bat` 文件即可打开图形界面

**命令行启动**：
```bash
# 启动图形界面
python scripts/gui_app.py
```

GUI界面功能：
- 📁 选择Excel数据文件
- ⚙️ 配置LLM、飞书、OSS参数（支持从.env加载默认值）
- ✅ 选择功能选项（LLM分析、OSS上传、飞书推送）
- 💾 保存配置到.env文件
- 📊 一键执行完整分析流程
- 📝 实时查看运行日志

#### 方式2：使用命令行

```bash
# 基本运行（生成报告）
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx

# 包含LLM分析
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm

# 自动上传到OSS并推送飞书
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --upload-oss

# 自动模式（自动检测raw目录中的文件）
python scripts/run_monthly.py
```

## 项目结构

详细结构说明请参考：[项目结构文档](docs/项目结构.md)

```
Ops Risk Analytics/
├── README.md                 # 项目主文档
├── requirements.txt          # Python依赖
├── .env.example              # 环境变量配置示例
├── .gitignore                # Git忽略规则
├── 启动GUI.bat               # Windows快捷启动脚本
│
├── docs/                     # 文档目录
│   └── 配置指南.md           # 详细配置说明
│
├── data/                     # 数据目录
│   ├── raw/                  # 原始数据（近3个月，不纳入版本控制）
│   ├── snapshot/             # 月度数据快照（全量）
│   └── history/              # 历史数据归档（按月份组织）
│
├── src/                      # 源代码
│   ├── processing/           # 数据处理与快照生成
│   │   ├── generate_snapshot.py
│   │   └── README.md
│   ├── metrics/              # 指标计算
│   │   ├── calculate_all.py
│   │   ├── overview_metrics.py
│   │   ├── process_metrics.py
│   │   ├── conversion_metrics.py
│   │   ├── risk_metrics.py
│   │   ├── status_changes.py
│   │   └── README.md
│   ├── visualization/        # 图表生成
│   │   ├── generate_charts.py
│   │   └── README.md
│   ├── llm/                  # LLM分析解读
│   │   ├── generate_insights.py
│   │   ├── prepare_context.py
│   │   └── README.md
│   ├── report/               # 报告生成
│   │   ├── generate_report.py
│   │   ├── generate_tables.py
│   │   └── README.md
│   ├── delivery/             # 飞书推送与OSS上传
│   │   ├── feishu_client.py
│   │   ├── push_report.py
│   │   ├── oss_uploader.py
│   │   ├── parse_llm_insights.py
│   │   └── README.md
│   └── utils/                # 工具函数
│       ├── config.py
│       ├── file_management.py
│       ├── file_validator.py
│       └── README.md
│
├── scripts/                  # 执行脚本
│   ├── run_monthly.py        # 月度分析主脚本（命令行）
│   ├── gui_app.py            # GUI图形界面（推荐）
│   ├── fix_snapshot_format.py # 快照格式修复工具
│   └── README.md
│
└── output/                   # 输出目录（按月份组织，不纳入版本控制）
    └── YYYY_MM/
        ├── figures/          # 图表
        ├── tables/           # 数据表格（CSV）
        ├── report/           # 报告文件（Markdown + PDF）
        ├── llm_insights/     # LLM分析结果
        └── metrics_result_YYYY_MM.json  # 指标计算结果
```

## 核心业务口径

### 收益判断标准

**是否调用 = 是否产生收益（唯一标准）**

- 不使用测试状态、接入意向、是否开通作为收益判断依据
- 上述字段仅用于流程与效率分析

### 状态字段定义

- **测试状态与接入意向**：仅代表测试流程或客户意向，不代表真实业务接入
- **已开通**：表示公司已为客户完成接口开通流程，属于流程性结果
- **已调用**：表示客户已开始真实调用接口，是唯一直接产生业务收益的关键指标

## 工作流程

```
raw数据导入（近3个月）
    ↓
与上月snapshot对齐
    ↓
状态与口径标准化
    ↓
snapshot生成（全量）
    ↓
指标统计与转化分析
    ↓
历史对比与变化识别
    ↓
异常与关注点标记
    ↓
大模型生成分析解读（可选）
    ↓
报告生成（Markdown + PDF）
    ↓
自动推送到飞书（可选）
```

## 输出内容

### 报告结构

1. **核心结论摘要**：LLM生成的3-5条核心结论和行动建议
2. **总体运营盘点**：规模与结构、整体进展、本月新增
3. **流程与进度分析**：测试流程进度、测试周期与效率
4. **转化与收益分析**：转化核心指标、产品维度分析、客户维度分析
5. **滞后与风险识别**：关键滞后场景、风险提示

### 输出格式

- **Markdown报告**：`output/YYYY_MM/report/report_YYYY_MM.md`
- **PDF报告**：`output/YYYY_MM/report/report_YYYY_MM.pdf`
- **图表**：`output/YYYY_MM/figures/`
- **数据表格**：`output/YYYY_MM/tables/`（仅生成PDF中超过15行的表格）
- **LLM分析**：`output/YYYY_MM/llm_insights/`

**注意**：如果启用了OSS上传（`--upload-oss`），报告和表格附件会自动上传到OSS，并在飞书卡片中显示下载链接。

## 模块说明

### 数据处理模块 (`src/processing/`)

- 读取raw数据（近3个月）
- 与历史snapshot对齐
- 生成当月snapshot（全量）

### 指标计算模块 (`src/metrics/`)

- 总体运营指标
- 流程进度指标
- 转化率指标
- 风险识别指标

### 可视化模块 (`src/visualization/`)

- 转化漏斗图
- 转化率对比图
- 产品/客户TOP10图表

### LLM分析模块 (`src/llm/`)

- 基于结构化指标生成分析解读
- 输出核心结论和行动建议

### 报告生成模块 (`src/report/`)

- 整合指标、图表、LLM分析
- 生成Markdown和PDF报告

### 推送模块 (`src/delivery/`)

- 飞书推送（卡片格式）
- OSS上传（报告和表格附件）
- 自动上传PDF报告和Excel表格到OSS
- 在飞书卡片中显示数据附件链接

## 配置说明

### 必需配置

- **飞书Webhook URL**：用于推送报告摘要
  - 配置方式：在 `.env` 文件中设置 `FEISHU_WEBHOOK_URL`
  - 详细说明：[配置指南](docs/配置指南.md)

### 可选配置

- **LLM API**：用于生成分析解读
  - 支持：阿里云百炼（优先）、OpenAI、Dify
  - 配置方式：在 `.env` 文件中设置对应的API密钥
  - 详细说明：[配置指南](docs/配置指南.md)

- **OSS配置**：用于上传报告文件
  - 配置方式：在 `.env` 文件中设置OSS相关环境变量
  - 详细说明：[配置指南](docs/配置指南.md)

## 脚本说明

### `scripts/run_monthly.py`

月度分析主脚本，执行完整分析流程。

**参数**：
- `month`：目标月份，格式 YYYY-MM（可选，自动模式会自动检测）
- `raw_file`：raw数据文件名（可选，自动模式会自动检测）
- `--include-llm`：包含LLM分析
- `--upload-oss`：自动上传报告到OSS
- `--skip-snapshot`：跳过snapshot生成
- `--skip-metrics`：跳过指标计算
- `--skip-report`：跳过报告生成
- `--skip-push`：跳过飞书推送

**示例**：
```bash
# 自动模式（推荐）
python scripts/run_monthly.py

# 手动指定参数
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --upload-oss
```

### `scripts/gui_app.py`

图形界面程序，提供可视化操作界面。

**启动方式**：
- Windows：双击 `启动GUI.bat`
- 命令行：`python scripts/gui_app.py`

**功能**：
- 文件选择与验证
- 配置管理（LLM、飞书、OSS）
- 一键执行完整流程
- 实时日志查看

### `scripts/fix_snapshot_format.py`

修复历史snapshot格式，用于快照schema变更后的数据迁移。

**用法**：
```bash
python scripts/fix_snapshot_format.py snapshot_2025_11.csv
```

## 开发指南

### 添加新指标

1. 在 `src/metrics/` 对应模块中添加计算函数
2. 在 `src/metrics/calculate_all.py` 中集成
3. 在报告模板中添加展示

### 添加新图表

1. 在 `src/visualization/generate_charts.py` 中添加生成函数
2. 在报告生成模块中调用

### 扩展LLM分析

1. 修改 `src/llm/generate_insights.py` 中的提示词模板
2. 调整输出格式解析逻辑

## 注意事项

1. **数据安全**：不要将包含敏感信息的文件提交到代码仓库
2. **环境变量**：使用 `.env` 文件管理配置，不要硬编码密钥
3. **数据备份**：定期备份 `data/snapshot/` 目录
4. **版本控制**：`data/raw/` 和 `output/` 目录不纳入版本控制
5. **月份格式**：所有月份使用 `YYYY-MM` 格式（如：`2025-12`）
6. **首次运行**：如果上个月snapshot不存在，系统会自动处理（适用于首次初始化）

## 文档

- [配置指南](docs/配置指南.md) - 详细配置说明
- [项目结构](docs/项目结构.md) - 项目结构和模块说明
- [更新日志](docs/更新日志.md) - 项目更新记录

## 技术支持

如有问题，请检查：
1. 环境变量配置是否正确（参考 [配置指南](docs/配置指南.md)）
2. 依赖包是否安装完整（`pip install -r requirements.txt`）
3. 数据文件格式是否正确（参考各模块README）

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

详细更新记录请参考：[更新日志](docs/更新日志.md)
