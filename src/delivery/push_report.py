"""
报告推送主函数

从metrics结果中提取关键指标，生成摘要并推送到飞书
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from .feishu_client import push_to_feishu


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


def extract_key_metrics(metrics_result: Dict[str, Any], month: str) -> Dict[str, Any]:
    """
    从metrics结果中提取关键指标
    
    Args:
        metrics_result: metrics计算结果
        month: 月份
    
    Returns:
        关键指标字典
    """
    overview = metrics_result.get('overview', {})
    process = metrics_result.get('process', {})
    conversion = metrics_result.get('conversion', {})
    risk = metrics_result.get('risk', {})
    
    # 总体运营指标
    scale = overview.get('scale_and_structure', {})
    overall = overview.get('overall_progress', {})
    monthly = overview.get('monthly_new_progress', {})
    
    # 流程指标
    test_progress = process.get('test_progress', {})
    status_dist = test_progress.get('status_distribution', {})
    
    # 转化指标（注意：JSON中存储在 core_conversion 下，不是 conversion_metrics）
    core_conversion = conversion.get('core_conversion', {})
    
    # 风险指标
    risk_summary = risk.get('risk_summary', {})
    
    return {
        # 本月新增
        "new_test_count": scale.get('new_test_count', 0),
        "new_customer_count": scale.get('new_customer_count', 0),
        "new_product_count": scale.get('new_product_count', 0),
        "new_completed_test": monthly.get('new_completed_test', 0),
        "new_opened": monthly.get('new_opened', 0),
        "new_called": monthly.get('new_called', 0),
        
        # 全量汇总
        "total_records": overall.get('total_records', 0),
        "completed_test_count": overall.get('completed_test_count', 0),
        "has_access_intent_count": overall.get('has_access_intent_count', 0),
        "opened_count": overall.get('opened_count', 0),
        "called_count": overall.get('called_count', 0),
        
        # 流程指标
        "test_completion_rate": test_progress.get('test_completion_rate', 0),
        "applied_test_count": status_dist.get('applied_test', 0),
        "completed_test_count_recent": status_dist.get('completed_test', 0),
        
        # 转化指标（从 core_conversion 中获取）
        "overall_call_rate": core_conversion.get('overall_call_rate', 0),
        "opened_to_call_rate": core_conversion.get('opened_to_call_rate', 0),
        "intent_to_call_rate": core_conversion.get('intent_to_call_rate', 0),
        
        # 风险指标
        "long_test_count": risk_summary.get('long_test_count', 0),
        "no_intent_count": risk_summary.get('no_intent_count', 0),
        "intent_not_opened_count": risk_summary.get('intent_not_opened_count', 0),
        "opened_not_called_count": risk_summary.get('opened_not_called_count', 0),
    }


def generate_summary(metrics_result: Dict[str, Any], month: str) -> str:
    """
    生成报告摘要（飞书卡片格式的Markdown）
    
    Args:
        metrics_result: metrics计算结果
        month: 月份
    
    Returns:
        摘要文本（飞书Markdown格式）
    """
    key_metrics = extract_key_metrics(metrics_result, month)
    
    summary_lines = []
    
    # 本月新增（使用飞书Markdown格式）
    summary_lines.append("**🆕 本月新增**")
    summary_lines.append(f"新增测试量：`{format_number(key_metrics['new_test_count'])}` 条")
    summary_lines.append(f"新增客户数：`{format_number(key_metrics['new_customer_count'])}` 个")
    summary_lines.append(f"新增子产品数：`{format_number(key_metrics['new_product_count'])}` 个")
    summary_lines.append(f"新完成测试：`{format_number(key_metrics['new_completed_test'])}` 条")
    summary_lines.append(f"新开通：`{format_number(key_metrics['new_opened'])}` 条")
    summary_lines.append(f"**新调用（核心收益）**：`{format_number(key_metrics['new_called'])}` 条")
    summary_lines.append("")
    
    # 全量汇总
    summary_lines.append("**📈 全量汇总（截至本月）**")
    total = key_metrics['total_records']
    summary_lines.append(f"总测试记录数：`{format_number(total)}` 条")
    if total > 0:
        summary_lines.append(f"已完成测试：`{format_number(key_metrics['completed_test_count'])}` 条（{format_percentage(key_metrics['completed_test_count']/total)}）")
        summary_lines.append(f"已明确接入意向：`{format_number(key_metrics['has_access_intent_count'])}` 条（{format_percentage(key_metrics['has_access_intent_count']/total)}）")
        summary_lines.append(f"已开通：`{format_number(key_metrics['opened_count'])}` 条（{format_percentage(key_metrics['opened_count']/total)}）")
        summary_lines.append(f"**已调用（核心收益）**：`{format_number(key_metrics['called_count'])}` 条（{format_percentage(key_metrics['called_count']/total)}）")
    summary_lines.append("")
    
    # 转化指标
    summary_lines.append("**💰 转化指标（近3个月）**")
    summary_lines.append(f"整体调用率：`{format_percentage(key_metrics['overall_call_rate'])}`")
    summary_lines.append(f"开通→调用转化率：`{format_percentage(key_metrics['opened_to_call_rate'])}`")
    summary_lines.append(f"接入意向→调用转化率：`{format_percentage(key_metrics['intent_to_call_rate'])}`")
    summary_lines.append("")
    
    # 风险提示
    risk_items = []
    if key_metrics['long_test_count'] > 0:
        risk_items.append(f"超长测试周期：`{format_number(key_metrics['long_test_count'])}` 条")
    if key_metrics['no_intent_count'] > 0:
        risk_items.append(f"长期无意向：`{format_number(key_metrics['no_intent_count'])}` 条")
    if key_metrics['intent_not_opened_count'] > 0:
        risk_items.append(f"有意向但未开通：`{format_number(key_metrics['intent_not_opened_count'])}` 条")
    if key_metrics['opened_not_called_count'] > 0:
        risk_items.append(f"已开通但未调用：`{format_number(key_metrics['opened_not_called_count'])}` 条")
    
    if risk_items:
        summary_lines.append("**⚠️ 风险提示**")
        for item in risk_items:
            summary_lines.append(f"- {item}")
    
    return "\n".join(summary_lines)


def _generate_key_metrics_summary(key_metrics: Dict[str, Any]) -> str:
    """
    生成关键指标摘要（用于飞书卡片显示）
    
    Args:
        key_metrics: 关键指标字典
    
    Returns:
        关键指标摘要文本（Markdown格式）
    """
    lines = []
    
    # 核心指标（简化版）
    lines.append("**📊 核心指标**")
    lines.append(f"• 新增测试量：`{format_number(key_metrics.get('new_test_count', 0))}` 条")
    lines.append(f"• 新调用（核心收益）：`{format_number(key_metrics.get('new_called', 0))}` 条")
    lines.append(f"• 整体调用率：`{format_percentage(key_metrics.get('overall_call_rate', 0))}`")
    lines.append(f"• 开通→调用转化率：`{format_percentage(key_metrics.get('opened_to_call_rate', 0))}`")
    
    # 全量汇总（简化）
    total = key_metrics.get('total_records', 0)
    if total > 0:
        called_count = key_metrics.get('called_count', 0)
        lines.append(f"• 全量已调用：`{format_number(called_count)}` 条（{format_percentage(called_count/total)}）")
    
    return "\n".join(lines)


def push_report(
    month: str,
    report_file_path: Optional[Path] = None,
    report_url: Optional[str] = None,
    webhook_url: Optional[str] = None,
    base_url: Optional[str] = None,
    llm_insights: Optional[str] = None,
    upload_to_oss: bool = False,
    table_paths: Optional[Dict[str, Path]] = None
) -> bool:
    """
    推送报告摘要到飞书（新版卡片格式）
    
    Args:
        month: 月份，格式YYYY-MM
        report_file_path: 报告文件路径（用于生成链接，可选）
        report_url: 完整报告URL（如果提供则优先使用）
        webhook_url: 飞书Webhook URL（可选，默认从环境变量读取）
        base_url: 报告文件的基础URL（用于自动生成报告链接，例如：https://example.com/reports）
        llm_insights: LLM生成的结论文本（可选，如果提供则解析并显示）
        upload_to_oss: 是否上传到OSS（如果为True且未提供report_url，则自动上传到OSS）
        table_paths: 表格文件路径字典，键为表格名称，值为文件路径（可选）
        table_paths: 表格文件路径字典，键为表格名称，值为文件路径（可选）
    
    Returns:
        是否推送成功
    """
    try:
        from datetime import datetime
        from .parse_llm_insights import parse_llm_insights
        
        # 加载metrics结果（用于获取数据范围）
        output_dir = Path("output") / month.replace('-', '_')
        metrics_file = output_dir / f"metrics_result_{month.replace('-', '_')}.json"
        
        if not metrics_file.exists():
            print(f"⚠️  未找到metrics结果文件：{metrics_file}")
            return False
        
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_result = json.load(f)
        
        # 生成标题
        title = f"📊 风控运营分析报告｜{month}"
        
        # 生成报告元信息
        conversion = metrics_result.get('conversion', {})
        core_conversion = conversion.get('core_conversion', {})
        period = core_conversion.get('period', '近3个月')
        report_meta = f"**报告范围**：{period}数据\n**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 提取关键指标用于卡片显示
        key_metrics = extract_key_metrics(metrics_result, month)
        
        # 生成关键指标摘要
        key_metrics_summary = _generate_key_metrics_summary(key_metrics)
        
        # 解析LLM结论（如果提供）
        conclusions = []
        actions = []
        
        if llm_insights:
            parsed = parse_llm_insights(llm_insights, debug=True)
            conclusions = parsed.get("conclusions", [])
            actions = parsed.get("actions", [])
            if conclusions:
                print(f"✅ 从提供的LLM文本中解析出 {len(conclusions)} 条结论")
            else:
                print("⚠️  提供的LLM文本中未找到结论")
        
        # 如果没有LLM结论，尝试从保存的文件中读取
        if not conclusions and not actions:
            llm_insights_file = output_dir / "llm_insights" / f"insights_{month.replace('-', '_')}.md"
            if llm_insights_file.exists():
                print(f"📄 尝试从文件读取LLM结论: {llm_insights_file}")
                with open(llm_insights_file, 'r', encoding='utf-8') as f:
                    llm_content = f.read()
                    # 跳过文件头部的元信息，查找结论部分（启用调试模式）
                    parsed = parse_llm_insights(llm_content, debug=True)
                    conclusions = parsed.get("conclusions", [])
                    actions = parsed.get("actions", [])
                    if conclusions:
                        print(f"✅ 从文件中解析出 {len(conclusions)} 条结论")
                    else:
                        print("⚠️  文件中未找到结论，请检查LLM输出格式")
                        # 调试：输出文件前1000字符
                        preview = llm_content[:1000].replace('\n', '\\n')
                        print(f"   文件内容预览: {preview}...")
            else:
                print(f"⚠️  LLM结论文件不存在: {llm_insights_file}")
        
        # 确定报告链接
        final_report_url = report_url
        
        # 如果启用了OSS上传，尝试上传到OSS
        if not final_report_url and upload_to_oss and report_file_path:
            try:
                from .oss_uploader import upload_report_to_oss
                print("正在上传报告到OSS...")
                # 优先上传PDF文件，如果当前文件是Markdown，尝试查找对应的PDF文件
                if report_file_path.suffix == '.pdf':
                    final_report_url = upload_report_to_oss(report_file_path, month, file_type="pdf")
                elif report_file_path.suffix == '.md':
                    # 如果当前是Markdown文件，尝试查找对应的PDF文件
                    pdf_path = report_file_path.with_suffix('.pdf')
                    if pdf_path.exists():
                        print("找到PDF文件，优先上传PDF...")
                        final_report_url = upload_report_to_oss(pdf_path, month, file_type="pdf")
                    else:
                        # PDF不存在，上传Markdown
                        print("PDF文件不存在，上传Markdown文件...")
                        final_report_url = upload_report_to_oss(report_file_path, month, file_type="md")
                
                if final_report_url:
                    print(f"✅ 报告已上传到OSS: {final_report_url}")
                else:
                    print("⚠️  OSS上传失败，将使用其他方式生成链接")
            except Exception as e:
                print(f"⚠️  OSS上传异常: {e}")
        
        # 如果还没有URL，尝试使用base_url生成
        if not final_report_url and report_file_path:
            if base_url:
                # 如果提供了base_url，可以生成完整的报告URL
                report_file_name = report_file_path.name
                # 移除base_url末尾的斜杠
                base_url_clean = base_url.rstrip('/')
                final_report_url = f"{base_url_clean}/output/{month.replace('-', '_')}/report/{report_file_name}"
        
        # 上传表格文件到OSS（如果启用）
        table_urls = []
        if upload_to_oss and table_paths:
            try:
                from .oss_uploader import upload_table_to_oss
                print("\n正在上传表格文件到OSS...")
                for table_name, table_path in table_paths.items():
                    if table_path and table_path.exists():
                        try:
                            table_url = upload_table_to_oss(table_path, month, table_name)
                            if table_url:
                                table_urls.append({
                                    'name': table_name,
                                    'url': table_url
                                })
                                print(f"  ✓ {table_name}: {table_url}")
                            else:
                                print(f"  ⚠️  {table_name}: 上传失败")
                        except Exception as e:
                            print(f"  ⚠️  {table_name}: 上传异常 - {e}")
                
                if table_urls:
                    print(f"✅ 已上传 {len(table_urls)} 个表格文件到OSS")
                else:
                    print("⚠️  没有表格文件上传成功")
            except Exception as e:
                print(f"⚠️  表格上传过程异常: {e}")
        
        # 推送到飞书（使用新版卡片格式）
        from .feishu_client import FeishuClient
        client = FeishuClient(webhook_url=webhook_url)
        
        success = client.send_report_card(
            title=title,
            report_meta=report_meta,
            key_metrics=key_metrics_summary,
            conclusions=conclusions,
            actions=actions,
            report_url=final_report_url,
            table_urls=table_urls if table_urls else None
        )
        
        if success:
            print("✅ 报告摘要已推送到飞书")
        else:
            print("⚠️  报告摘要推送失败")
        
        return success
        
    except Exception as e:
        print(f"⚠️  推送报告失败: {e}")
        import traceback
        traceback.print_exc()
        return False

