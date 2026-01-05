"""
月度运营分析报告生成模块

将metrics计算结果转换为Markdown格式的报告
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def load_metrics_result(month: str) -> Dict[str, Any]:
    """
    加载metrics计算结果（按月份组织）
    
    Args:
        month: 月份，格式YYYY-MM
    
    Returns:
        metrics结果字典
    """
    output_dir = Path("output") / month.replace('-', '_')
    metrics_file = output_dir / f"metrics_result_{month.replace('-', '_')}.json"
    
    if not metrics_file.exists():
        raise FileNotFoundError(f"未找到metrics结果文件：{metrics_file}")
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_number(num: Any, decimal_places: int = 0) -> str:
    """格式化数字"""
    if num is None:
        return "-"
    try:
        if decimal_places == 0:
            return f"{int(num):,}"
        else:
            return f"{float(num):,.{decimal_places}f}"
    except:
        return str(num)


def format_percentage(num: Any, decimal_places: int = 1) -> str:
    """格式化百分比"""
    if num is None:
        return "-"
    try:
        return f"{float(num) * 100:.{decimal_places}f}%"
    except:
        return str(num)


def generate_overview_section(overview: Dict[str, Any], month: str, chart_paths: Dict[str, Path] = None) -> str:
    """生成第二部分：总体运营盘点"""
    content = []
    content.append("## 二、总体运营盘点\n")
    
    # 1. 规模与结构概览
    scale = overview.get('scale_and_structure', {})
    content.append("### 1. 规模与结构概览（本月新增）\n")
    content.append(f"- **本月新增测试量**：{format_number(scale.get('new_test_count', 0))} 条")
    content.append(f"- **新增客户数**：{format_number(scale.get('new_customer_count', 0))} 个")
    content.append(f"- **新增子产品数**：{format_number(scale.get('new_product_count', 0))} 个")
    
    sample_size = scale.get('sample_size_distribution', {})
    if sample_size:
        content.append(f"- **样本量统计**：")
        content.append(f"  - 总计：{format_number(sample_size.get('total', 0))}")
        content.append(f"  - 平均：{format_number(sample_size.get('mean', 0), 1)}")
        content.append(f"  - 中位数：{format_number(sample_size.get('median', 0), 1)}")
    
    content.append("")
    
    # 2. 截至本月的整体进展
    overall = overview.get('overall_progress', {})
    content.append("### 2. 截至本月的整体进展（全量汇总）\n")
    date_range = overall.get('date_range', '未知')
    if date_range == '未知' or not date_range:
        date_range = '历史数据（起止日期计算中）'
    content.append(f"**数据起止日期**：{date_range}\n")
    
    # 添加核心指标表格
    total = overall.get('total_records', 0)
    completed = overall.get('completed_test_count', 0)
    intent = overall.get('has_access_intent_count', 0)
    opened = overall.get('opened_count', 0)
    called = overall.get('called_count', 0)
    
    content.append("| 指标 | 数值 | 占比 |")
    content.append("|------|------|------|")
    content.append(f"| 总测试记录数 | {format_number(total)} 条 | 100% |")
    if total > 0:
        content.append(f"| 已完成测试数量 | {format_number(completed)} 条 | {format_percentage(completed/total)} |")
        content.append(f"| 已明确接入意向数量 | {format_number(intent)} 条 | {format_percentage(intent/total)} |")
        content.append(f"| 已开通数量 | {format_number(opened)} 条 | {format_percentage(opened/total)} |")
        content.append(f"| **已调用数量（核心收益指标）** | **{format_number(called)} 条** | **{format_percentage(called/total)}** |")
    else:
        content.append(f"| 已完成测试数量 | {format_number(completed)} 条 | - |")
        content.append(f"| 已明确接入意向数量 | {format_number(intent)} 条 | - |")
        content.append(f"| 已开通数量 | {format_number(opened)} 条 | - |")
        content.append(f"| **已调用数量（核心收益指标）** | **{format_number(called)} 条** | **-** |")
    content.append("")
    
    # 添加转化漏斗图（路径按月份组织）
    if chart_paths and 'conversion_funnel' in chart_paths:
        chart_path = chart_paths['conversion_funnel']
        # 计算相对路径（从report目录到figures目录）
        month_str = month.replace('-', '_')
        relative_path = f"../figures/{chart_path.name}"
        content.append("#### 转化漏斗图\n")
        content.append(f"![转化漏斗图]({relative_path})\n")
        content.append("")
    
    content.append("")
    
    # 3. 本月新增进展
    monthly = overview.get('monthly_new_progress', {})
    content.append("### 3. 本月新增进展\n")
    content.append(f"- **本月新完成测试**：{format_number(monthly.get('new_completed_test', 0))} 条")
    content.append(f"- **本月新开通**：{format_number(monthly.get('new_opened', 0))} 条")
    content.append(f"- **本月新调用**（核心收益指标）：{format_number(monthly.get('new_called', 0))} 条")
    content.append("")
    
    # 4. 本月新开通和新调用详细列表（重要数据，完整展示）
    new_opened_list = monthly.get('new_opened_list', [])
    if new_opened_list:
        content.append("### 4. 本月新开通详细列表\n")
        content.append(f"**总数**：{format_number(len(new_opened_list))} 条\n")
        content.append("| 序号 | 客户简称 | 子产品名称 | 申请日期 | 类型 |")
        content.append("|-----|---------|-----------|---------|------|")
        for idx, item in enumerate(new_opened_list, 1):
            content.append(f"| {idx} | {item.get('customer', '')} | {item.get('product', '')} | {item.get('apply_date', '')} | {item.get('type', '')} |")
        content.append("")
    else:
        content.append("### 4. 本月新开通详细列表\n")
        content.append("**本月无新开通记录**\n")
        content.append("")
    
    new_called_list = monthly.get('new_called_list', [])
    if new_called_list:
        content.append("### 5. 本月新调用详细列表（核心收益指标）\n")
        content.append(f"**总数**：{format_number(len(new_called_list))} 条\n")
        content.append("| 序号 | 客户简称 | 子产品名称 | 申请日期 | 类型 |")
        content.append("|-----|---------|-----------|---------|------|")
        for idx, item in enumerate(new_called_list, 1):
            content.append(f"| {idx} | {item.get('customer', '')} | {item.get('product', '')} | {item.get('apply_date', '')} | {item.get('type', '')} |")
        content.append("")
    else:
        content.append("### 5. 本月新调用详细列表（核心收益指标）\n")
        content.append("**本月无新调用记录**\n")
        content.append("")
    
    return "\n".join(content)


def generate_process_section(process: Dict[str, Any], month: str, chart_paths: Dict[str, Path] = None) -> str:
    """生成第三部分：流程与进度分析"""
    content = []
    content.append("## 三、流程与进度分析（近3个月数据）\n")
    
    # 1. 测试流程进度分析
    test_progress = process.get('test_progress', {})
    content.append("### 1. 测试流程进度分析\n")
    period = test_progress.get('period', '未知')
    if period == '未知' or not period:
        period = '近3个月（基于申请日期）'
    content.append(f"**数据范围**：{period}\n")
    content.append(f"- **总记录数**：{format_number(test_progress.get('total_count', 0))} 条")
    content.append(f"- **有测试返回日期记录数**：{format_number(test_progress.get('has_test_return_date_count', 0))} 条")
    status_dist = test_progress.get('status_distribution', {})
    applied_count = status_dist.get('applied_test', 0)
    completed_count = status_dist.get('completed_test', 0)
    content.append(f"- **测试完成率**：{format_percentage(test_progress.get('test_completion_rate', 0))}（完成测试/{applied_count}条申请测试）")
    
    status_dist = test_progress.get('status_distribution', {})
    if status_dist:
        # 使用表格格式美化显示
        content.append("| 状态 | 数量 |")
        content.append("|------|------|")
        content.append(f"| 申请测试 | {format_number(status_dist.get('applied_test', 0))} 条 |")
        content.append(f"| 完成测试 | {format_number(status_dist.get('completed_test', 0))} 条 |")
        content.append(f"| 可接入 | {format_number(status_dist.get('accessible', 0))} 条 |")
        content.append(f"| 不接入 | {format_number(status_dist.get('not_accessible', 0))} 条 |")
    content.append("")
    
    # 2. 测试周期与效率
    test_cycle = process.get('test_cycle', {})
    content.append("### 2. 测试周期与效率\n")
    period = test_cycle.get('period', '未知')
    if period == '未知' or not period:
        period = '近3个月'
    content.append(f"**数据范围**：{period}\n")
    content.append(f"- **有效测试周期记录数**：{format_number(test_cycle.get('count', 0))} 条")
    if test_cycle.get('count', 0) > 0:
        content.append(f"- **平均测试周期**：{format_number(test_cycle.get('mean', 0), 1)} 天")
        content.append(f"- **中位数测试周期**：{format_number(test_cycle.get('median', 0), 1)} 天")
        content.append(f"- **最短测试周期**：{format_number(test_cycle.get('min', 0))} 天")
        content.append(f"- **最长测试周期**：{format_number(test_cycle.get('max', 0))} 天")
        content.append(f"- **超长测试数量**（>{test_cycle.get('long_test_threshold', 30)}天）：{format_number(test_cycle.get('long_test_count', 0))} 条")
    
    long_test_records = test_cycle.get('long_test_records', [])
    if long_test_records:
        content.append("\n#### 超长测试周期记录（前10条）\n")
        content.append("| 客户简称 | 子产品名称 | 申请日期 | 测试返回日期 | 测试周期（天） |")
        content.append("|---------|-----------|---------|------------|--------------|")
        for item in long_test_records[:10]:
            content.append(f"| {item.get('customer', '')} | {item.get('product', '')} | {item.get('apply_date', '')} | {item.get('return_date', '')} | {item.get('days', 0)} |")
        if len(long_test_records) > 10:
            content.append(f"\n*注：完整数据（共{len(long_test_records)}条）请查看附件中的《超长测试周期记录》Excel文件*\n")
    content.append("")
    
    return "\n".join(content)


def generate_conversion_section(conversion: Dict[str, Any], month: str, chart_paths: Dict[str, Path] = None) -> str:
    """生成第四部分：转化与收益分析"""
    content = []
    content.append("## 四、转化与收益分析（核心，近3个月数据）\n")
    
    # 1. 收益转化核心指标
    core = conversion.get('core_conversion', {})
    content.append("### 1. 收益转化核心指标\n")
    period = core.get('period', '未知')
    if period == '未知' or not period:
        period = '近3个月（基于申请日期）'
    content.append(f"**数据范围**：{period}\n")
    content.append(f"- **整体调用率**：{format_percentage(core.get('overall_call_rate', 0))}")
    content.append(f"- **开通→调用转化率**：{format_percentage(core.get('opened_to_call_rate', 0))}")
    content.append(f"- **接入意向→调用转化率**：{format_percentage(core.get('intent_to_call_rate', 0))}")
    content.append(f"- **已调用总数**：{format_number(core.get('total_called', 0))} 条")
    content.append(f"- **已开通总数**：{format_number(core.get('total_opened', 0))} 条")
    content.append(f"- **有接入意向总数**：{format_number(core.get('total_with_intent', 0))} 条")
    content.append("")
    
    # 添加转化率对比图（路径按月份组织）
    if chart_paths and 'conversion_rate' in chart_paths:
        chart_path = chart_paths['conversion_rate']
        relative_path = f"../figures/{chart_path.name}"
        content.append("#### 转化率对比\n")
        content.append(f"![转化率对比图]({relative_path})\n")
        content.append("")
    
    # 2. 产品维度收益分析
    product_analysis = conversion.get('product_analysis', {})
    top_products = product_analysis.get('top_products', [])
    if top_products:
        content.append("### 2. 产品维度收益分析\n")
        content.append("#### 调用率Top 10产品\n")
        content.append("| 排名 | 子产品名称 | 总测试数 | 已调用数 | 调用率 |")
        content.append("|-----|-----------|---------|---------|--------|")
        for idx, product in enumerate(top_products[:10], 1):
            content.append(f"| {idx} | {product.get('product_name', '')} | {format_number(product.get('total_count', 0))} | {format_number(product.get('called_count', 0))} | {format_percentage(product.get('call_rate', 0))} |")
        content.append("")
        
        # 添加产品TOP 10图表（路径按月份组织）
        if chart_paths and 'product_top10' in chart_paths:
            chart_path = chart_paths['product_top10']
            relative_path = f"../figures/{chart_path.name}"
            content.append(f"![产品调用率TOP 10]({relative_path})\n")
            content.append("")
    
    # 3. 客户维度收益分析
    customer_analysis = conversion.get('customer_analysis', {})
    high_call_customers = customer_analysis.get('high_call_customers', [])
    if high_call_customers:
        content.append("### 3. 客户维度收益分析\n")
        content.append("#### 高调用客户（Top 10）\n")
        content.append("| 排名 | 客户简称 | 总测试数 | 已调用数 | 调用率 |")
        content.append("|-----|---------|---------|---------|--------|")
        for idx, customer in enumerate(high_call_customers[:10], 1):
            content.append(f"| {idx} | {customer.get('customer_name', '')} | {format_number(customer.get('total_count', 0))} | {format_number(customer.get('called_count', 0))} | {format_percentage(customer.get('call_rate', 0))} |")
        content.append("")
        
        # 添加客户TOP 10图表（路径按月份组织）
        if chart_paths and 'customer_top10' in chart_paths:
            chart_path = chart_paths['customer_top10']
            relative_path = f"../figures/{chart_path.name}"
            content.append(f"![客户调用率TOP 10]({relative_path})\n")
            content.append("")
    
    # 4. 有意向但未开通列表
    intent_not_opened = conversion.get('intent_not_opened_list', {})
    if intent_not_opened.get('total_count', 0) > 0:
        content.append("### 4. 有意向但未开通列表（近3个月）\n")
        content.append(f"**总数**：{format_number(intent_not_opened.get('total_count', 0))} 条\n")
        records = intent_not_opened.get('records', [])
        if records:
            content.append("| 客户简称 | 子产品名称 | 申请日期 |")
            content.append("|---------|-----------|---------|")
            # 如果记录数超过15条，只显示前15条，并添加说明
            display_count = min(15, len(records))
            for item in records[:display_count]:
                content.append(f"| {item.get('客户简称', '')} | {item.get('子产品名称', '')} | {item.get('申请日期', '')} |")
            if len(records) > 15:
                content.append(f"\n*注：完整数据（共{len(records)}条）请查看附件中的《有意向但未开通列表》Excel文件*\n")
        content.append("")
    
    return "\n".join(content)


def generate_risk_section(risk: Dict[str, Any], month: str, chart_paths: Dict[str, Path] = None) -> str:
    """生成第五部分：滞后与风险识别"""
    content = []
    content.append("## 五、滞后与风险识别（近3个月数据）\n")
    
    # 汇总滞后场景数据
    completed_no_intent = risk.get('completed_no_intent', {})
    intent_not_opened = risk.get('intent_not_opened', {})
    opened_not_called = risk.get('opened_not_called', {})
    
    # 1. 测试完成但长期无意向
    content.append("### 1. 测试完成但长期无意向\n")
    period = completed_no_intent.get('period', '未知')
    if period == '未知' or not period:
        period = '近3个月（基于申请日期）'
    content.append(f"**数据范围**：{period}\n")
    content.append(f"- **总数**：{format_number(completed_no_intent.get('total_count', 0))} 条")
    content.append(f"- **长期无意向**（>30天）：{format_number(completed_no_intent.get('long_term_count', 0))} 条")
    
    long_term_records = completed_no_intent.get('long_term_records', [])
    if long_term_records:
        content.append("\n#### 长期无意向记录（前10条）\n")
        content.append("| 客户简称 | 子产品名称 | 距离测试返回天数 |")
        content.append("|---------|-----------|----------------|")
        for item in long_term_records[:10]:
            content.append(f"| {item.get('customer', '')} | {item.get('product', '')} | {item.get('days_since_return', 0)} 天 |")
        if len(long_term_records) > 10:
            content.append(f"\n*注：完整数据（共{len(long_term_records)}条）请查看附件中的《长期无意向记录》Excel文件*\n")
    content.append("")
    
    # 2. 明确有意向但未开通
    content.append("### 2. 明确有意向但未开通\n")
    content.append(f"**数据范围**：{intent_not_opened.get('period', '未知')}\n")
    content.append(f"- **总数**：{format_number(intent_not_opened.get('total_count', 0))} 条")
    
    records = intent_not_opened.get('records', [])
    if records:
        content.append("\n#### 有意向但未开通记录（前10条）\n")
        content.append("| 客户简称 | 子产品名称 | 申请日期 |")
        content.append("|---------|-----------|---------|")
        for item in records[:10]:
            content.append(f"| {item.get('客户简称', '')} | {item.get('子产品名称', '')} | {item.get('申请日期', '')} |")
        if len(records) > 10:
            content.append(f"\n*注：完整数据（共{len(records)}条）请查看附件中的《有意向但未开通列表》Excel文件*\n")
    content.append("")
    
    # 3. 已开通但长期未调用
    opened_not_called = risk.get('opened_not_called', {})
    content.append("### 3. 已开通但长期未调用（重点风险）\n")
    content.append(f"**数据范围**：{opened_not_called.get('period', '未知')}\n")
    content.append(f"- **总数**：{format_number(opened_not_called.get('total_count', 0))} 条")
    content.append(f"- **长期未调用**（>60天）：{format_number(opened_not_called.get('long_term_count', 0))} 条")
    
    long_term_no_call = opened_not_called.get('long_term_records', [])
    if long_term_no_call:
        content.append("\n#### 长期未调用记录（前10条）\n")
        content.append("| 客户简称 | 子产品名称 | 距离申请天数 |")
        content.append("|---------|-----------|------------|")
        for item in long_term_no_call[:10]:
            content.append(f"| {item.get('customer', '')} | {item.get('product', '')} | {item.get('days_since_apply', 0)} 天 |")
        if len(long_term_no_call) > 10:
            content.append(f"\n*注：完整数据（共{len(long_term_no_call)}条）请查看附件中的《长期未调用记录》Excel文件*\n")
    content.append("")
    
    return "\n".join(content)


def generate_monthly_report(
    month: str,
    include_llm_insights: bool = False,
    llm_client = None,
    generate_pdf: bool = True
) -> Path:
    """
    生成月度运营分析报告
    
    Args:
        month: 月份，格式YYYY-MM
        include_llm_insights: 是否包含LLM生成的解读文本，默认False
        llm_client: LLM客户端实例，如果include_llm_insights为True且未提供，会尝试自动创建
        generate_pdf: 是否生成PDF版本，默认True
    
    Returns:
        报告文件路径（Markdown）
    """
    print(f"正在生成 {month} 的运营分析报告...")
    
    # 加载metrics结果
    metrics_result = load_metrics_result(month)
    
    # 生成图表
    print("\n正在生成图表...")
    try:
        from src.visualization import generate_all_charts
        chart_paths = generate_all_charts(month)
        print("✅ 所有图表生成完成")
    except Exception as e:
        print(f"⚠️  图表生成失败: {e}")
        chart_paths = {}
    
    # 生成表格文件
    try:
        from src.report.generate_tables import generate_all_tables
        table_paths = generate_all_tables(metrics_result, month)
    except Exception as e:
        print(f"⚠️  表格生成失败: {e}")
        table_paths = {}
    
    # 准备LLM结论和建议（仅在报告开头）
    llm_conclusions = None
    
    if include_llm_insights:
        try:
            from src.llm import generate_llm_insights, save_llm_insights
            print("\n正在生成LLM分析结论...")
            llm_conclusions = generate_llm_insights(month, llm_client=llm_client)
            # 保存LLM结论到文件（供推送时读取）
            if llm_conclusions:
                save_llm_insights(month, llm_conclusions)
            print("✅ LLM结论已生成并保存")
        except Exception as e:
            print(f"⚠️  LLM结论生成失败: {e}")
            print("   报告将继续生成，但不包含LLM结论部分")
    
    # 生成报告内容
    report_content = []
    report_content.append(f"# 风控运营月度分析报告 - {month}\n")
    report_content.append(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_content.append("---\n")
    
    # 第一部分：核心结论摘要（LLM生成）
    if llm_conclusions:
        report_content.append("## 一、核心结论摘要\n")
        report_content.append(llm_conclusions)
        report_content.append("\n---\n")
    
    # 第二部分：总体运营盘点
    overview = metrics_result.get('overview', {})
    report_content.append(generate_overview_section(overview, month, chart_paths))
    report_content.append("\n---\n")
    
    # 第三部分：流程与进度分析
    process = metrics_result.get('process', {})
    report_content.append(generate_process_section(process, month, chart_paths))
    report_content.append("\n---\n")
    
    # 第四部分：转化与收益分析（核心）
    conversion = metrics_result.get('conversion', {})
    report_content.append(generate_conversion_section(conversion, month, chart_paths))
    report_content.append("\n---\n")
    
    # 第五部分：滞后与风险识别
    risk = metrics_result.get('risk', {})
    report_content.append(generate_risk_section(risk, month, chart_paths))
    
    # 保存Markdown报告（按月份组织）
    output_dir = Path("output") / month.replace('-', '_') / "report"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / f"report_{month.replace('-', '_')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_content))
    
    print(f"\n✅ Markdown报告已保存到：{report_file}")
    
    # 生成PDF版本
    if generate_pdf:
        try:
            pdf_file = generate_pdf_report(report_file, month, table_paths)
            print(f"✅ PDF报告已保存到：{pdf_file}")
        except Exception as e:
            print(f"⚠️  PDF生成失败: {e}")
            print("   Markdown报告已生成，可以手动转换为PDF")
    
    return report_file


def generate_pdf_report(md_file: Path, month: str, table_paths: Dict[str, Path] = None) -> Path:
    """
    将Markdown报告转换为PDF
    
    Args:
        md_file: Markdown文件路径
        month: 月份，格式YYYY-MM
        table_paths: 表格文件路径字典，用于添加Excel链接
    
    Returns:
        PDF文件路径
    """
    try:
        import markdown
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.colors import HexColor, black, white, blue
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from html.parser import HTMLParser
        import re
        
        # 读取Markdown文件
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 转换为HTML
        html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        # 创建PDF（按月份组织）
        output_dir = Path("output") / month.replace('-', '_') / "report"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = output_dir / f"report_{month.replace('-', '_')}.pdf"
        
        doc = SimpleDocTemplate(str(pdf_file), pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # 注册中文字体（ReportLab需要）
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',      # 黑体
            'C:/Windows/Fonts/msyh.ttc',         # 微软雅黑
            'C:/Windows/Fonts/simsun.ttc',       # 宋体
        ]
        
        chinese_font_name = None
        for font_path in font_paths:
            font_file = Path(font_path)
            if font_file.exists():
                try:
                    # 注册字体
                    font_name = font_file.stem.replace('_', '')
                    pdfmetrics.registerFont(TTFont(font_name, str(font_file)))
                    chinese_font_name = font_name
                    print(f"✓ PDF中文字体已注册: {font_name}")
                    break
                except Exception as e:
                    continue
        
        # 准备内容
        story = []
        styles = getSampleStyleSheet()
        
        # 如果有中文字体，更新样式
        if chinese_font_name:
            for style_name in ['Normal', 'Heading1', 'Heading2', 'Heading3']:
                if hasattr(styles[style_name], 'fontName'):
                    styles[style_name].fontName = chinese_font_name
        
        # 添加标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1E88E5',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        if chinese_font_name:
            title_style.fontName = chinese_font_name
        
        # 解析Markdown并添加到story
        lines = md_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                story.append(Spacer(1, 12))
                i += 1
                continue
            
            # 处理标题
            if line.startswith('# '):
                text = line[2:].strip()
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 12))
                i += 1
            elif line.startswith('## '):
                text = line[3:].strip()
                story.append(Paragraph(text, styles['Heading2']))
                story.append(Spacer(1, 12))
                i += 1
            elif line.startswith('### '):
                text = line[4:].strip()
                story.append(Paragraph(text, styles['Heading3']))
                story.append(Spacer(1, 12))
                i += 1
            elif line.startswith('![') and '](' in line:
                # 处理图片
                match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
                if match:
                    alt_text, img_path = match.groups()
                    img_path_full = Path("output") / img_path
                    if not img_path_full.exists():
                        month_str = month.replace('-', '_')
                        img_path_full = Path("output") / month_str / "figures" / Path(img_path).name
                    if img_path_full.exists():
                        try:
                            img = Image(str(img_path_full), width=6*inch, height=4*inch)
                            story.append(img)
                            story.append(Spacer(1, 12))
                        except:
                            pass
                i += 1
            elif line.startswith('|'):
                # 处理表格：收集所有表格行
                table_lines = []
                table_start_idx = i
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                
                if len(table_lines) >= 2:  # 至少要有表头和一行数据
                    # 查找表格前的标题，用于识别表格类型
                    table_title = ""
                    for j in range(max(0, table_start_idx - 5), table_start_idx):
                        prev_line = lines[j].strip()
                        if prev_line.startswith('###') or prev_line.startswith('####'):
                            table_title = prev_line.replace('#', '').strip()
                            break
                    
                    # 解析表格
                    table_data = []
                    for table_line in table_lines:
                        # 分割单元格，去除首尾的|
                        cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                        # 跳过分隔行（如 |---|---|）
                        if not all(cell.replace('-', '').replace(':', '').strip() == '' for cell in cells):
                            table_data.append(cells)
                    
                    if len(table_data) > 0:
                        # 限制PDF中显示的行数：超过15条显示10条，不超过15条全部显示
                        MAX_DISPLAY_THRESHOLD = 15  # 超过这个数量才限制显示
                        MAX_PDF_ROWS = 10  # 限制显示时的最大行数
                        total_rows = len(table_data)
                        
                        # 判断是否需要限制显示
                        if total_rows > MAX_DISPLAY_THRESHOLD:
                            display_rows = MAX_PDF_ROWS + 1  # +1 for header
                            table_data_display = table_data[:display_rows]
                        else:
                            # 不超过15条，全部显示
                            display_rows = total_rows
                            table_data_display = table_data
                        
                        # 创建表格
                        # 转换单元格内容为Paragraph对象以支持中文
                        table_paragraphs = []
                        for row in table_data_display:
                            row_paragraphs = []
                            for cell in row:
                                # 清理Markdown格式
                                cell_text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', cell)
                                cell_text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', cell_text)
                                para = Paragraph(cell_text, styles['Normal'])
                                row_paragraphs.append(para)
                            table_paragraphs.append(row_paragraphs)
                        
                        # 创建Table对象
                        pdf_table = Table(table_paragraphs)
                        
                        # 设置表格样式
                        table_style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1E88E5')),  # 表头背景色
                            ('TEXTCOLOR', (0, 0), (-1, 0), white),  # 表头文字颜色
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), chinese_font_name if chinese_font_name else 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('TOPPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), white),
                            ('TEXTCOLOR', (0, 1), (-1, -1), black),
                            ('FONTNAME', (0, 1), (-1, -1), chinese_font_name if chinese_font_name else 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 0.5, black),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
                        ])
                        
                        pdf_table.setStyle(table_style)
                        story.append(pdf_table)
                        
                        # 检查Markdown中是否已经有说明（跳过Markdown中的说明行）
                        # 如果表格后面有"注："开头的行，说明Markdown中已经有说明，PDF中不需要重复添加
                        has_note_in_markdown = False
                        if i < len(lines):
                            # 检查表格后面的几行是否有"注："或"*注："
                            for check_idx in range(i, min(i + 3, len(lines))):
                                check_line = lines[check_idx].strip()
                                if check_line.startswith('*注：') or check_line.startswith('注：'):
                                    has_note_in_markdown = True
                                    # 跳过Markdown中的说明行
                                    while check_idx < len(lines) and (lines[check_idx].strip().startswith('*注：') or lines[check_idx].strip().startswith('注：') or lines[check_idx].strip() == ''):
                                        check_idx += 1
                                    i = check_idx
                                    break
                        
                        # 如果Markdown中没有说明，且表格行数超过限制，才添加说明
                        if not has_note_in_markdown:
                            if total_rows > MAX_DISPLAY_THRESHOLD:
                                # 根据表格标题匹配Excel文件名
                                excel_file_name = None
                                if '新开通' in table_title:
                                    excel_file_name = 'new_opened_list'
                                elif '新调用' in table_title:
                                    excel_file_name = 'new_called_list'
                                elif '有意向但未开通' in table_title:
                                    excel_file_name = 'intent_not_opened'
                                elif '长期无意向' in table_title or '完成但长期无意向' in table_title:
                                    excel_file_name = 'completed_no_intent'
                                elif '长期未调用' in table_title or '已开通但长期未调用' in table_title:
                                    excel_file_name = 'opened_not_called'
                                elif '超长测试' in table_title:
                                    excel_file_name = 'long_test_records'
                                
                                # 生成Excel文件名（中文描述）
                                excel_desc_map = {
                                    'new_opened_list': '本月新开通详细列表',
                                    'new_called_list': '本月新调用详细列表',
                                    'intent_not_opened': '有意向但未开通列表',
                                    'completed_no_intent': '长期无意向记录',
                                    'opened_not_called': '长期未调用记录',
                                    'long_test_records': '超长测试周期记录'
                                }
                                
                                if excel_file_name and excel_file_name in excel_desc_map:
                                    excel_desc = excel_desc_map[excel_file_name]
                                    note_text = f'<i>注：PDF中仅显示前{MAX_PDF_ROWS}条，完整数据（共{total_rows-1}条）请查看附件中的《{excel_desc}》Excel文件</i>'
                                else:
                                    note_text = f'<i>注：PDF中仅显示前{MAX_PDF_ROWS}条，完整数据（共{total_rows-1}条）请查看附件Excel文件</i>'
                                
                                note_para = Paragraph(note_text, styles['Normal'])
                                story.append(Spacer(1, 6))
                                story.append(note_para)
                        
                        story.append(Spacer(1, 12))
            else:
                # 普通文本
                if line:
                    # 清理Markdown格式
                    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line)
                    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
                    story.append(Paragraph(text, styles['Normal']))
                    story.append(Spacer(1, 6))
                i += 1
        
        # 生成PDF
        doc.build(story)
        
        return pdf_file
        
    except ImportError:
        raise ImportError("PDF生成需要安装: pip install markdown reportlab")
    except Exception as e:
        raise Exception(f"PDF生成失败: {e}")

