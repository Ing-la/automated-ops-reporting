"""
图表生成模块

生成运营分析报告所需的图表，采用蓝色简约科技风格
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import platform

# 设置中文字体 - 直接加载字体文件，确保生效
_chinese_font_prop = None

def setup_chinese_font():
    """设置中文字体，优先使用系统已安装的字体文件"""
    global _chinese_font_prop
    
    # 清除matplotlib字体缓存
    try:
        import matplotlib
        matplotlib.font_manager.fontManager.__init__()
    except:
        pass
    
    system = platform.system()
    if system == 'Windows':
        # Windows系统字体路径（按优先级排序）
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑（最常用）
            'C:/Windows/Fonts/simhei.ttf',    # 黑体
            'C:/Windows/Fonts/simsun.ttc',    # 宋体
        ]
        
        # 尝试加载字体文件
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    # 直接使用字体文件路径创建FontProperties
                    _chinese_font_prop = fm.FontProperties(fname=font_path)
                    # 获取字体名称
                    font_name = _chinese_font_prop.get_name()
                    # 设置rcParams - 使用字体名称列表
                    plt.rcParams['font.sans-serif'] = [font_name, 'Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
                    plt.rcParams['axes.unicode_minus'] = False
                    # 强制matplotlib使用这个字体
                    plt.rcParams['font.family'] = 'sans-serif'
                    print(f"✓ 中文字体已设置: {font_name} ({Path(font_path).name})")
                    return _chinese_font_prop
                except Exception as e:
                    continue
        
        # 如果文件加载失败，使用字体名称
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.family'] = 'sans-serif'
        print("✓ 中文字体已设置: Microsoft YaHei (使用字体名称)")
    else:
        # Linux/Mac系统
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.family'] = 'sans-serif'
    
    return None

# 初始化中文字体
setup_chinese_font()

def get_chinese_font():
    """获取中文字体属性对象"""
    return _chinese_font_prop

# 蓝色科技风格配色方案
COLOR_SCHEME = {
    'primary': '#1E88E5',      # 主蓝色
    'secondary': '#42A5F5',     # 浅蓝色
    'accent': '#0D47A1',        # 深蓝色
    'success': '#26A69A',       # 成功绿
    'warning': '#FFA726',       # 警告橙
    'error': '#EF5350',         # 错误红
    'background': '#F5F5F5',    # 背景灰
    'text': '#212121',          # 文本黑
    'grid': '#E0E0E0',          # 网格灰
}

# 图表样式设置
CHART_STYLE = {
    'figure.figsize': (10, 6),
    'figure.dpi': 100,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.color': COLOR_SCHEME['grid'],
    'axes.axisbelow': True,
}


def setup_chart_style():
    """设置图表样式"""
    plt.style.use('default')
    for key, value in CHART_STYLE.items():
        plt.rcParams[key] = value


def save_chart(fig, filename: str, month: str):
    """
    保存图表
    
    Args:
        fig: matplotlib figure对象
        filename: 文件名（不含扩展名）
        month: 月份，格式YYYY-MM
    """
    # 按月份组织输出目录
    output_dir = Path("output") / month.replace('-', '_') / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = output_dir / f"{filename}_{month.replace('-', '_')}.png"
    fig.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    return file_path


def generate_conversion_funnel(metrics_result: Dict[str, Any], month: str) -> Path:
    """
    生成转化漏斗图
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径
    """
    setup_chart_style()
    
    overview = metrics_result.get('overview', {}).get('overall_progress', {})
    
    # 提取数据
    stages = ['总测试记录', '已完成测试', '已明确接入意向', '已开通', '已调用']
    values = [
        overview.get('total_records', 0),
        overview.get('completed_test_count', 0),
        overview.get('has_access_intent_count', 0),
        overview.get('opened_count', 0),
        overview.get('called_count', 0),
    ]
    
    # 计算百分比
    total = values[0]
    percentages = [v / total * 100 if total > 0 else 0 for v in values]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 绘制漏斗
    y_positions = np.arange(len(stages))
    widths = percentages
    
    bars = ax.barh(y_positions, widths, color=COLOR_SCHEME['primary'], alpha=0.8)
    
    # 添加数值标签
    for i, (bar, val, pct) in enumerate(zip(bars, values, percentages)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{val:,} ({pct:.1f}%)',
                ha='left', va='center', fontsize=11, fontweight='bold')
    
    # 设置标签 - 使用中文字体
    font_prop = get_chinese_font()
    ax.set_yticks(y_positions)
    if font_prop:
        ax.set_yticklabels(stages, fontsize=12, fontproperties=font_prop)
        ax.set_xlabel('占比 (%)', fontsize=12, fontweight='bold', fontproperties=font_prop)
        ax.set_title('转化漏斗图', fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
    else:
        ax.set_yticklabels(stages, fontsize=12)
        ax.set_xlabel('占比 (%)', fontsize=12, fontweight='bold')
        ax.set_title('转化漏斗图', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, max(percentages) * 1.15)
    
    # 添加网格
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    return save_chart(fig, 'overview_conversion_funnel', month)


def generate_test_cycle_distribution(metrics_result: Dict[str, Any], month: str) -> Path:
    """
    生成测试周期分布直方图
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径
    """
    setup_chart_style()
    
    process = metrics_result.get('process', {}).get('test_cycle', {})
    
    # 从snapshot中提取测试周期数据
    snapshot_file = Path("data/snapshot") / f"snapshot_{month.replace('-', '_')}.csv"
    if not snapshot_file.exists():
        raise FileNotFoundError(f"未找到snapshot文件：{snapshot_file}")
    
    df = pd.read_csv(snapshot_file)
    
    # 计算测试周期（申请日期到测试返回日期的天数）
    def calculate_cycle(row):
        try:
            if pd.isna(row.get('申请日期')) or pd.isna(row.get('测试返回日期')):
                return None
            apply_date = pd.to_datetime(row['申请日期'])
            return_date = pd.to_datetime(row['测试返回日期'])
            return (return_date - apply_date).days
        except:
            return None
    
    df['测试周期'] = df.apply(calculate_cycle, axis=1)
    cycles = df['测试周期'].dropna()
    
    if len(cycles) == 0:
        # 如果没有数据，创建一个空图表
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '暂无测试周期数据', 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title('测试周期分布', fontsize=16, fontweight='bold')
        return save_chart(fig, 'process_test_cycle_distribution', month)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制直方图
    n_bins = min(30, int(np.sqrt(len(cycles))))
    n, bins, patches = ax.hist(cycles, bins=n_bins, color=COLOR_SCHEME['primary'], 
                                alpha=0.7, edgecolor='white', linewidth=1.5)
    
    # 添加统计线
    mean_cycle = cycles.mean()
    median_cycle = cycles.median()
    ax.axvline(mean_cycle, color=COLOR_SCHEME['accent'], linestyle='--', 
               linewidth=2, label=f'平均值: {mean_cycle:.1f}天')
    ax.axvline(median_cycle, color=COLOR_SCHEME['success'], linestyle='--', 
               linewidth=2, label=f'中位数: {median_cycle:.1f}天')
    
    # 添加超长测试标记（>30天）
    long_test_count = (cycles > 30).sum()
    if long_test_count > 0:
        ax.axvline(30, color=COLOR_SCHEME['warning'], linestyle=':', 
                   linewidth=2, label=f'超长测试阈值: 30天 ({long_test_count}条)')
    
    # 使用中文字体
    font_prop = get_chinese_font()
    if font_prop:
        ax.set_xlabel('测试周期（天）', fontsize=12, fontweight='bold', fontproperties=font_prop)
        ax.set_ylabel('记录数', fontsize=12, fontweight='bold', fontproperties=font_prop)
        ax.set_title('测试周期分布', fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
    else:
        ax.set_xlabel('测试周期（天）', fontsize=12, fontweight='bold')
        ax.set_ylabel('记录数', fontsize=12, fontweight='bold')
        ax.set_title('测试周期分布', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    return save_chart(fig, 'process_test_cycle_distribution', month)


def generate_conversion_rate_comparison(metrics_result: Dict[str, Any], month: str) -> Path:
    """
    生成转化率对比柱状图
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径
    """
    setup_chart_style()
    
    conversion = metrics_result.get('conversion', {}).get('core_conversion', {})
    
    # 提取转化率数据
    metrics = [
        ('整体调用率', conversion.get('overall_call_rate', 0) * 100),
        ('开通→调用转化率', conversion.get('opened_to_call_rate', 0) * 100),
        ('接入意向→调用转化率', conversion.get('intent_to_call_rate', 0) * 100),
    ]
    
    labels = [m[0] for m in metrics]
    values = [m[1] for m in metrics]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制柱状图
    bars = ax.bar(labels, values, color=COLOR_SCHEME['primary'], alpha=0.8, width=0.6)
    
    # 添加数值标签
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.02,
                f'{val:.1f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # 使用中文字体
    font_prop = get_chinese_font()
    if font_prop:
        ax.set_ylabel('转化率 (%)', fontsize=12, fontweight='bold', fontproperties=font_prop)
        ax.set_title('转化率对比', fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
        # 设置x轴标签字体
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontproperties=font_prop, rotation=15, ha='right')
    else:
        ax.set_ylabel('转化率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('转化率对比', fontsize=16, fontweight='bold', pad=20)
        plt.xticks(rotation=15, ha='right')
    ax.set_ylim(0, max(values) * 1.15 if max(values) > 0 else 10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    return save_chart(fig, 'conversion_rate_comparison', month)


def generate_product_top10(metrics_result: Dict[str, Any], month: str) -> Path:
    """
    生成产品调用率TOP 10柱状图
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径
    """
    setup_chart_style()
    
    products = metrics_result.get('conversion', {}).get('product_analysis', {}).get('top_products', [])
    
    if len(products) == 0:
        # 如果没有数据，创建一个空图表
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '暂无产品数据', 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title('产品调用率TOP 10', fontsize=16, fontweight='bold')
        return save_chart(fig, 'conversion_product_top10', month)
    
    # 取TOP 10
    top10 = products[:10]
    
    # 提取数据 - 修复字段名映射
    labels = [p.get('product_name', p.get('product', '未知产品')) for p in top10]
    values = [p.get('call_rate', 0) * 100 for p in top10]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制水平柱状图（便于显示产品名称）
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=COLOR_SCHEME['primary'], alpha=0.8)
    
    # 添加数值标签
    for i, (bar, val) in enumerate(zip(bars, values)):
        width = bar.get_width()
        ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%',
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    # 使用中文字体
    font_prop = get_chinese_font()
    ax.set_yticks(y_pos)
    if font_prop:
        ax.set_yticklabels(labels, fontsize=10, fontproperties=font_prop)
        ax.set_xlabel('调用率 (%)', fontsize=12, fontweight='bold', fontproperties=font_prop)
        ax.set_title('产品调用率TOP 10', fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
    else:
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel('调用率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('产品调用率TOP 10', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, max(values) * 1.15 if max(values) > 0 else 10)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    return save_chart(fig, 'conversion_product_top10', month)


def generate_customer_top10(metrics_result: Dict[str, Any], month: str) -> Path:
    """
    生成客户调用率TOP 10柱状图
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径
    """
    setup_chart_style()
    
    customers = metrics_result.get('conversion', {}).get('customer_analysis', {}).get('high_call_customers', [])
    
    if len(customers) == 0:
        # 如果没有数据，创建一个空图表
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '暂无客户数据', 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title('客户调用率TOP 10', fontsize=16, fontweight='bold')
        return save_chart(fig, 'conversion_customer_top10', month)
    
    # 取TOP 10
    top10 = customers[:10]
    
    # 提取数据 - 修复字段名映射
    labels = [c.get('customer_name', c.get('customer', '未知客户')) for c in top10]
    values = [c.get('call_rate', 0) * 100 for c in top10]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制水平柱状图
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=COLOR_SCHEME['secondary'], alpha=0.8)
    
    # 添加数值标签
    for i, (bar, val) in enumerate(zip(bars, values)):
        width = bar.get_width()
        ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%',
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    # 使用中文字体
    font_prop = get_chinese_font()
    ax.set_yticks(y_pos)
    if font_prop:
        ax.set_yticklabels(labels, fontsize=10, fontproperties=font_prop)
        ax.set_xlabel('调用率 (%)', fontsize=12, fontweight='bold', fontproperties=font_prop)
        ax.set_title('客户调用率TOP 10', fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
    else:
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel('调用率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('客户调用率TOP 10', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, max(values) * 1.15 if max(values) > 0 else 10)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    return save_chart(fig, 'conversion_customer_top10', month)


def generate_risk_scenarios(metrics_result: Dict[str, Any], month: str) -> Path:
    """
    生成滞后场景分布饼图
    
    Args:
        metrics_result: metrics计算结果
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径
    """
    setup_chart_style()
    
    risk = metrics_result.get('risk', {})
    
    # 提取滞后场景数据
    scenarios = [
        ('测试完成但长期无意向', risk.get('completed_no_intent', {}).get('count', 0)),
        ('明确有意向但未开通', risk.get('intent_not_opened', {}).get('count', 0)),
        ('已开通但长期未调用', risk.get('opened_not_called', {}).get('count', 0)),
    ]
    
    labels = [s[0] for s in scenarios]
    values = [s[1] for s in scenarios]
    
    # 过滤掉值为0的场景
    filtered_data = [(l, v) for l, v in zip(labels, values) if v > 0]
    if len(filtered_data) == 0:
        # 如果没有数据，创建一个空图表
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '暂无滞后场景数据', 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title('滞后场景分布', fontsize=16, fontweight='bold')
        return save_chart(fig, 'risk_lag_scenarios', month)
    
    labels, values = zip(*filtered_data)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 配色方案
    colors = [COLOR_SCHEME['primary'], COLOR_SCHEME['secondary'], COLOR_SCHEME['warning']]
    
    # 使用中文字体
    font_prop = get_chinese_font()
    
    # 绘制饼图
    text_props = {'fontsize': 11, 'fontweight': 'bold'}
    if font_prop:
        text_props['fontproperties'] = font_prop
    
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                       colors=colors[:len(labels)], startangle=90,
                                       textprops=text_props)
    
    # 设置百分比文字样式
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        if font_prop:
            autotext.set_fontproperties(font_prop)
    
    # 设置标签字体
    for text in texts:
        if font_prop:
            text.set_fontproperties(font_prop)
    
    # 设置标题和图例
    if font_prop:
        ax.set_title('滞后场景分布', fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
        # 添加图例（包含数量）
        legend_labels = [f'{label}: {value}条' for label, value in zip(labels, values)]
        ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10, prop=font_prop)
    else:
        ax.set_title('滞后场景分布', fontsize=16, fontweight='bold', pad=20)
        # 添加图例（包含数量）
        legend_labels = [f'{label}: {value}条' for label, value in zip(labels, values)]
        ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
    
    plt.tight_layout()
    
    return save_chart(fig, 'risk_lag_scenarios', month)


def generate_all_charts(month: str) -> Dict[str, Path]:
    """
    生成所有图表
    
    Args:
        month: 月份，格式YYYY-MM
    
    Returns:
        图表文件路径字典
    """
    from src.report.generate_report import load_metrics_result
    
    metrics_result = load_metrics_result(month)
    
    charts = {}
    
    try:
        charts['conversion_funnel'] = generate_conversion_funnel(metrics_result, month)
        print(f"✓ 转化漏斗图已生成")
    except Exception as e:
        print(f"✗ 转化漏斗图生成失败: {e}")
    
    try:
        charts['conversion_rate'] = generate_conversion_rate_comparison(metrics_result, month)
        print(f"✓ 转化率对比图已生成")
    except Exception as e:
        print(f"✗ 转化率对比图生成失败: {e}")
    
    try:
        charts['product_top10'] = generate_product_top10(metrics_result, month)
        print(f"✓ 产品TOP 10图已生成")
    except Exception as e:
        print(f"✗ 产品TOP 10图生成失败: {e}")
    
    try:
        charts['customer_top10'] = generate_customer_top10(metrics_result, month)
        print(f"✓ 客户TOP 10图已生成")
    except Exception as e:
        print(f"✗ 客户TOP 10图生成失败: {e}")
    
    return charts

