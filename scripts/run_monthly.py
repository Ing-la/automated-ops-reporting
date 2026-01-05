"""
月度运营分析执行入口

串联整个分析流程：
1. 读取raw数据
2. 生成snapshot
3. 计算metrics
4. 生成报告
"""

import sys
import argparse
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 在主脚本开始时显式加载.env文件（优先于其他模块导入）
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        load_dotenv(env_file, override=True)  # override=True确保.env文件优先
        print(f"[OK] 已加载环境变量配置文件: {env_file}")
    else:
        env_example = PROJECT_ROOT / '.env.example'
        print(f"[WARN] 未找到.env文件: {env_file}")
        if env_example.exists():
            print(f"[提示] 可以运行初始化脚本创建: python scripts/init_env.py")
            print(f"       或手动复制: copy .env.example .env (Windows) 或 cp .env.example .env (Linux/Mac)")
        else:
            print(f"[提示] 请参考 docs/配置指南.md 创建 .env 文件")
except ImportError:
    print("[WARN] python-dotenv未安装，将使用系统环境变量")
except Exception as e:
    print(f"[ERROR] 加载.env文件失败: {e}")

from src.processing.generate_snapshot import generate_monthly_snapshot, RAW_DATA_DIR
from src.metrics.calculate_all import calculate_all_metrics
from src.report.generate_report import generate_monthly_report
from src.utils.file_management import move_raw_to_history, clear_raw_directory
from src.utils.file_validator import validate_excel_structure, detect_month_from_file, find_raw_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='月度运营分析执行脚本')
    parser.add_argument('month', type=str, nargs='?', help='目标月份，格式：YYYY-MM，例如：2025-12（可选，如果不提供则自动检测）')
    parser.add_argument('raw_file', type=str, nargs='?', help='raw数据文件名，例如：ops_data_2025_12.xlsx（可选，如果不提供则自动从raw目录查找）')
    parser.add_argument('--skip-snapshot', action='store_true', help='跳过snapshot生成（如果已生成）')
    parser.add_argument('--skip-metrics', action='store_true', help='跳过metrics计算（如果已计算）')
    parser.add_argument('--skip-report', action='store_true', help='跳过报告生成')
    parser.add_argument('--include-llm', action='store_true', help='在报告中包含LLM生成的分析解读（需要配置LLM API密钥）')
    parser.add_argument('--skip-push', action='store_true', help='跳过报告推送（默认会自动推送到飞书）')
    parser.add_argument('--report-url', type=str, help='完整报告的URL链接（用于推送时提供跳转链接）')
    parser.add_argument('--report-base-url', type=str, help='报告文件的基础URL（用于自动生成报告链接，例如：https://example.com/reports）')
    parser.add_argument('--upload-oss', action='store_true', help='自动上传报告到OSS（需要配置OSS环境变量）')
    
    args = parser.parse_args()
    
    # 自动模式：如果没有提供参数，自动检测
    if args.month is None or args.raw_file is None:
        print("=" * 80)
        print("自动模式：检测raw目录中的文件...")
        print("-" * 80)
        
        raw_dir = PROJECT_ROOT / "data" / "raw"
        raw_files = find_raw_files(raw_dir)
        
        if len(raw_files) == 0:
            print("[ERROR] raw目录中没有找到Excel文件")
            print("请将数据文件放入 data/raw/ 目录，或使用手动模式：")
            print("  python scripts/run_monthly.py YYYY-MM filename.xlsx")
            sys.exit(1)
        
        if len(raw_files) > 1:
            print("[ERROR] raw目录中有多个文件，请确保只有一个文件：")
            for f in raw_files:
                print(f"  - {f.name}")
            print("\n请删除多余文件，或使用手动模式指定文件：")
            print("  python scripts/run_monthly.py YYYY-MM filename.xlsx")
            sys.exit(1)
        
        # 找到唯一的文件
        raw_file_path = raw_files[0]
        print(f"[OK] 找到文件: {raw_file_path.name}")
        
        # 验证文件结构
        is_valid, error_msg = validate_excel_structure(raw_file_path)
        if not is_valid:
            print(f"[ERROR] 文件结构验证失败: {error_msg}")
            sys.exit(1)
        print("[OK] 文件结构验证通过")
        
        # 检测月份
        if args.month is None:
            detected_month = detect_month_from_file(raw_file_path)
            if detected_month is None:
                print("[ERROR] 无法从文件中检测月份，请手动指定：")
                print("  python scripts/run_monthly.py YYYY-MM filename.xlsx")
                sys.exit(1)
            args.month = detected_month
            print(f"[OK] 检测到月份: {args.month}")
        
        args.raw_file = raw_file_path.name
    
    # 手动模式：验证参数
    else:
        # 验证月份格式
        try:
            datetime.strptime(args.month, '%Y-%m')
        except ValueError:
            print(f"[ERROR] 月份格式不正确，应为 YYYY-MM，例如：2025-12")
            sys.exit(1)
        
        # 验证raw文件是否存在
        raw_file_path = PROJECT_ROOT / "data" / "raw" / args.raw_file
        if not raw_file_path.exists():
            print(f"[ERROR] raw数据文件不存在：{raw_file_path}")
            sys.exit(1)
        
        # 验证文件结构
        is_valid, error_msg = validate_excel_structure(raw_file_path)
        if not is_valid:
            print(f"[ERROR] 文件结构验证失败: {error_msg}")
            sys.exit(1)
    
    # 确保raw_file_path已设置（统一处理）
    # 在自动模式下，raw_file_path已在上面设置；在手动模式下，需要在这里设置
    if 'raw_file_path' not in locals() or raw_file_path is None:
        raw_file_path = PROJECT_ROOT / "data" / "raw" / args.raw_file
    
    print("=" * 80)
    print(f"月度运营分析流程 - {args.month}")
    print("=" * 80)
    print()
    
    # 步骤1：生成snapshot
    if not args.skip_snapshot:
        print("【步骤1/5】生成snapshot数据...")
        print("-" * 80)
        try:
            generate_monthly_snapshot(raw_file_path, args.month)
            print("[OK] Snapshot生成完成\n")
        except Exception as e:
            print(f"[ERROR] Snapshot生成失败：{e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("【步骤1/5】跳过snapshot生成（已存在）\n")
    
    # 步骤2：计算metrics
    if not args.skip_metrics:
        print("【步骤2/5】计算运营指标...")
        print("-" * 80)
        try:
            metrics_result = calculate_all_metrics(args.month)
            if metrics_result:
                print("[OK] Metrics计算完成\n")
            else:
                print("[ERROR] Metrics计算失败：未返回结果")
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Metrics计算失败：{e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("【步骤2/5】跳过metrics计算（已存在）\n")
    
    # 步骤3：生成报告
    if not args.skip_report:
        print("【步骤3/5】生成运营分析报告...")
        print("-" * 80)
        try:
            report_path = generate_monthly_report(
                args.month,
                include_llm_insights=args.include_llm
            )
            if report_path and report_path.exists():
                print(f"[OK] 报告生成完成：{report_path}\n")
            else:
                print("[ERROR] 报告生成失败：未生成文件")
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] 报告生成失败：{e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("【步骤3/5】跳过报告生成\n")
    
    # 步骤4：推送报告到飞书
    if not args.skip_push and not args.skip_report:
        print("【步骤4/5】推送报告摘要到飞书...")
        print("-" * 80)
        try:
            from src.delivery.push_report import push_report
            from pathlib import Path
            # 优先使用PDF报告，如果不存在则使用Markdown
            month_str = args.month.replace('-', '_')
            report_dir = PROJECT_ROOT / "output" / month_str / "report"
            pdf_path = report_dir / f"report_{month_str}.pdf"
            md_path = report_dir / f"report_{month_str}.md"
            report_path = pdf_path if pdf_path.exists() else md_path
            if report_path.exists():
                # 尝试加载LLM结论（如果存在）
                llm_insights = None
                llm_insights_file = PROJECT_ROOT / "output" / args.month.replace('-', '_') / "llm_insights" / f"insights_{args.month.replace('-', '_')}.md"
                if llm_insights_file.exists():
                    try:
                        with open(llm_insights_file, 'r', encoding='utf-8') as f:
                            llm_content = f.read()
                            # 跳过文件头部的元信息，提取结论部分
                            llm_insights = llm_content
                    except Exception as e:
                        print(f"   警告：无法读取LLM结论文件: {e}")
                
                # 加载表格文件路径（如果存在）
                table_paths = {}
                tables_dir = PROJECT_ROOT / "output" / month_str / "tables"
                if tables_dir.exists():
                    # 表格名称映射
                    table_files = {
                        'new_opened_list': f'new_opened_list_{month_str}.csv',
                        'new_called_list': f'new_called_list_{month_str}.csv',
                        'long_test_records': f'long_test_records_{month_str}.csv',
                        'intent_not_opened': f'intent_not_opened_{month_str}.csv',
                        'completed_no_intent': f'completed_no_intent_{month_str}.csv',
                        'opened_not_called': f'opened_not_called_{month_str}.csv'
                    }
                    for table_name, filename in table_files.items():
                        table_path = tables_dir / filename
                        if table_path.exists():
                            table_paths[table_name] = table_path
                
                push_report(
                    args.month,
                    report_file_path=report_path,
                    report_url=args.report_url,
                    base_url=args.report_base_url,
                    llm_insights=llm_insights,
                    upload_to_oss=args.upload_oss,
                    table_paths=table_paths if table_paths else None
                )
            else:
                print("[WARN] 报告文件不存在，跳过推送")
            print()
        except Exception as e:
            print(f"[WARN] 推送报告失败：{e}")
            print("   报告已生成，但推送失败，可以手动推送\n")
    else:
        print("【步骤4/5】跳过报告推送\n")
    
    # 步骤5：清理raw数据（移动到history）
    print("【步骤5/5】清理raw数据（移动到history）...")
    print("-" * 80)
    try:
        moved_files = clear_raw_directory(args.month)
        if moved_files:
            print(f"[OK] 已移动 {len(moved_files)} 个文件到history目录")
            for file_path in moved_files:
                print(f"  - {file_path.name}")
        else:
            print("[OK] raw目录已为空，无需清理")
        print()
    except Exception as e:
        print(f"[WARN] 清理raw数据失败：{e}")
        print("   可以手动清理raw目录\n")
    
    print("=" * 80)
    print("月度运营分析流程完成！")
    print("=" * 80)
    print()
    print("输出文件：")
    print(f"  - Snapshot: data/snapshot/snapshot_{args.month.replace('-', '_')}.csv")
    print(f"  - Metrics: output/{args.month.replace('-', '_')}/metrics_result_{args.month.replace('-', '_')}.json")
    if not args.skip_report:
        print(f"  - Report: output/{args.month.replace('-', '_')}/report/report_{args.month.replace('-', '_')}.md")
        print(f"  - Figures: output/{args.month.replace('-', '_')}/figures/")
        print(f"  - Tables: output/{args.month.replace('-', '_')}/tables/")
    if args.include_llm:
        print(f"  - LLM Insights: output/{args.month.replace('-', '_')}/llm_insights/insights_{args.month.replace('-', '_')}.md")
    print(f"  - History: data/history/{args.month.replace('-', '_')}/")


if __name__ == "__main__":
    main()

