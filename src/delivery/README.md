# 推送模块说明

## 功能概述

推送模块负责将生成的报告摘要推送到飞书，方便团队成员及时查看运营分析结果。

## 模块结构

- `feishu_client.py`: 飞书推送客户端
- `push_report.py`: 推送主函数，从metrics结果中提取关键指标并生成摘要
- `oss_uploader.py`: OSS文件上传模块
- `parse_llm_insights.py`: LLM结论解析模块

## 配置

### 环境变量

在 `.env` 文件中配置飞书Webhook URL：

```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url
```

### 获取飞书Webhook URL

1. 在飞书群聊中添加"自定义机器人"
2. 设置机器人名称和描述
3. 复制生成的Webhook URL
4. 将URL配置到环境变量中

## 使用方法

### 自动推送（推荐）

在运行月度分析脚本时，会自动推送报告摘要到飞书：

```bash
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm
```

### 跳过推送

如果不想推送，可以使用 `--skip-push` 参数：

```bash
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --skip-push
```

### 提供报告链接

如果报告已上传到服务器或云存储，可以提供完整报告URL或基础URL，飞书消息中会显示"查看完整报告"按钮：

```bash
# 方式1：提供完整报告URL
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --report-url https://example.com/reports/2025_12/report_2025_12.pdf

# 方式2：提供基础URL，自动生成报告链接
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --report-base-url https://example.com/reports
```

**注意**：如果没有提供报告链接，飞书消息中会显示报告文件的本地路径，但无法直接点击跳转。如果需要可点击的链接，请使用 `--report-url` 或 `--report-base-url` 参数。

### 手动推送

也可以单独调用推送函数：

```python
from src.delivery.push_report import push_report

# 推送报告摘要
push_report(
    month='2025-12',
    report_url='https://example.com/reports/2025_12/report_2025_12.pdf'
)
```

## 推送内容

推送的摘要包含以下关键指标：

1. **本月新增**
   - 新增测试量、客户数、子产品数
   - 新完成测试、新开通、新调用数量

2. **全量汇总**
   - 总测试记录数
   - 已完成测试、已明确接入意向、已开通、已调用数量及占比

3. **转化指标**
   - 整体调用率
   - 开通→调用转化率
   - 接入意向→调用转化率

4. **风险提示**
   - 超长测试周期记录数
   - 长期无意向记录数
   - 有意向但未开通记录数
   - 已开通但未调用记录数

## OSS上传功能

如果配置了OSS，可以使用 `--upload-oss` 参数自动上传报告和表格附件到OSS：

```bash
python scripts/run_monthly.py 2025-12 ops_data_2025_12.xlsx --include-llm --upload-oss
```

### OSS配置

在 `.env` 文件中配置OSS信息：

```bash
OSS_BUCKET_NAME=feishu-try
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_ACCESS_KEY_ID=your-access-key-id
OSS_ACCESS_KEY_SECRET=your-access-key-secret
```

### 安装OSS依赖

```bash
pip install oss2
```

详细配置说明请参考 [配置指南](../../docs/配置指南.md)。

### OSS URL格式

**报告文件URL格式**：
```
https://{bucket_name}.{endpoint}/reports/{YYYY_MM}/report_{YYYY_MM}.pdf
```

**表格附件URL格式**：
```
https://{bucket_name}.{endpoint}/reports/{YYYY_MM}/tables/{table_name}_{YYYY_MM}.csv
```

例如：
```
https://feishu-try.oss-cn-beijing.aliyuncs.com/reports/2025_12/report_2025_12.pdf
https://feishu-try.oss-cn-beijing.aliyuncs.com/reports/2025_12/tables/new_opened_list_2025_12.csv
```

### 上传内容

**报告文件**：
- 系统会优先上传PDF报告文件
- 如果PDF文件不存在，才会上传Markdown文件

**表格附件**：
- 自动上传PDF中超过15行的表格（CSV格式）
- 包括：本月新开通列表、本月新调用列表、超长测试周期记录、有意向但未开通列表、长期无意向记录、长期未调用记录
- 表格链接会在飞书卡片中显示为"数据附件"部分

## 卡片显示内容

飞书卡片现在包含以下完整信息：

1. **报告元信息**：报告范围、生成时间
2. **关键指标**：
   - 新增测试量
   - 新调用（核心收益）
   - 整体调用率
   - 开通→调用转化率
   - 全量已调用
3. **核心结论**：LLM生成的3-5条结论
4. **重点行动**：LLM生成的行动建议表格
5. **数据附件**：Excel表格链接（如果启用了OSS上传）
   - 本月新开通列表
   - 本月新调用列表
   - 超长测试周期记录
   - 有意向但未开通列表
   - 长期无意向记录
   - 长期未调用记录
6. **操作按钮**：查看完整报告（如果提供了URL）

## 注意事项

1. **Webhook URL安全**：不要将Webhook URL提交到代码仓库，使用环境变量管理
2. **推送失败不影响主流程**：如果推送失败，报告仍会正常生成
3. **报告链接**：如果提供了 `--report-url`、`--report-base-url` 或启用了 `--upload-oss`，飞书消息中会包含跳转按钮
4. **消息格式**：推送的消息使用飞书卡片格式，支持Markdown渲染（使用 `lark_md` 标签）
5. **签名校验**：如果机器人未启用签名校验，可以不设置 `FEISHU_WEBHOOK_SECRET` 环境变量
6. **OSS上传优先级**：如果同时提供了 `--report-url` 和 `--upload-oss`，优先使用 `--report-url`
7. **表格附件**：只有PDF中超过15行的表格才会生成CSV文件并上传到OSS
8. **表格链接**：表格附件链接会在飞书卡片的"数据附件"部分显示，点击可直接下载CSV文件

