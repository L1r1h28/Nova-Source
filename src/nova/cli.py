#!/usr/bin/env python3
"""
Nova CLI - 統一的命令行介面
"""

import argparse
import sys
from pathlib import Path

# 初始化 Nova
import nova
from nova.core.logging import get_logger

logger = get_logger("cli")


def create_parser() -> argparse.ArgumentParser:
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description="Nova - 統一的開發工具平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  nova system                    # 顯示系統資訊
  nova config --show             # 顯示配置
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 系統資訊命令
    subparsers.add_parser("system", help="顯示系統資訊")

    # 配置命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("--show", action="store_true", help="顯示當前配置")

    # Markdown 格式化命令
    markdown_parser = subparsers.add_parser("markdown", help="Markdown 檔案格式化")
    markdown_parser.add_argument("path", help="要格式化的檔案或目錄路徑")
    markdown_parser.add_argument(
        "-r", "--recursive", action="store_true", help="遞歸處理子目錄"
    )
    markdown_parser.add_argument("--rules", nargs="+", help="要修復的特定規則")
    markdown_parser.add_argument("--exclude", nargs="+", help="要排除的檔案模式")
    markdown_parser.add_argument(
        "--dry-run", action="store_true", help="僅顯示將要進行的更改"
    )
    markdown_parser.add_argument(
        "--max-line-length",
        type=int,
        default=80,
        metavar="LENGTH",
        help="最大行長度限制 (預設: 80)",
    )

    # 監控命令
    monitor_parser = subparsers.add_parser("monitor", help="系統監控")
    monitor_parser.add_argument(
        "--continuous", type=int, metavar="SECONDS", help="連續監控秒數"
    )
    monitor_parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="監控間隔秒數 (預設: 30)",
    )

    # CPU 監控命令
    cpu_parser = subparsers.add_parser("cpu", help="CPU 監控")
    cpu_parser.add_argument(
        "--delay-check",
        type=float,
        metavar="THRESHOLD",
        help="檢查是否需要 CPU 延遲 (閾值 0-100)",
    )

    # 清理命令
    cleanup_parser = subparsers.add_parser("cleanup", help="記憶體清理")
    cleanup_parser.add_argument(
        "--level",
        choices=["normal", "critical"],
        default="normal",
        help="清理級別 (預設: normal)",
    )

    # 代碼分析命令
    analyze_parser = subparsers.add_parser("analyze", help="代碼分析")
    analyze_parser.add_argument(
        "--path", "-p", type=str, default=".", help="要分析的目錄路徑 (預設: 當前目錄)"
    )

    # 代碼質量檢查命令
    audit_parser = subparsers.add_parser("audit", help="代碼質量檢查")
    audit_parser.add_argument(
        "--detailed", "-d", action="store_true", help="啟用詳細檢查模式 (包含統計)"
    )
    audit_parser.add_argument(
        "--path", "-p", action="append", help="指定要檢查的子目錄路徑 (可多次使用)"
    )
    audit_parser.add_argument("--files", "-f", nargs="+", help="指定要檢查的Python檔案")

    return parser


def run_system_info(args: argparse.Namespace) -> int:
    """顯示系統資訊"""
    try:
        logger.info("� 系統資訊:")

        system_info = nova.get_system_info()
        print(f"   平台: {system_info.platform}")
        print(f"   Python 版本: {system_info.python_version}")
        print(f"   CPU 核心數: {system_info.cpu_count}")
        print(f"   記憶體總量: {system_info.memory_total_gb:.1f} GB")
        print(f"   GPU 可用: {system_info.gpu_available}")
        if system_info.gpu_available:
            print(f"   GPU 數量: {system_info.gpu_count}")

        return 0

    except Exception as e:
        logger.error(f"❌ 獲取系統資訊時發生錯誤: {e}")
        return 1


def run_config(args: argparse.Namespace) -> int:
    """配置管理"""
    try:
        from nova.core.config import get_config

        config = get_config()

        if args.show:
            # 顯示當前配置
            logger.info("📋 當前配置:")
            print(f"項目根目錄: {config.project_root}")
            print(f"配置文件: {config.config_file}")

        return 0

    except Exception as e:
        logger.error(f"❌ 配置管理過程中發生錯誤: {e}")
        return 1


def run_markdown(args: argparse.Namespace) -> int:
    """Markdown 檔案格式化"""
    try:
        from nova.markdown.formatter import MarkdownFormatter

        # 檢查路徑是否存在
        path = Path(args.path)
        if not path.exists():
            logger.error(f"❌ 路徑 '{path}' 不存在")
            return 1

        # 創建格式化器
        formatter = MarkdownFormatter(max_line_length=args.max_line_length)

        if args.dry_run:
            logger.info(f"🔍 將格式化路徑: {path} (dry-run 模式)")

            if path.is_file():
                # 在 dry-run 模式下運行檢測規則
                if args.rules:
                    # 如果用戶指定了特定規則，使用這些規則
                    formatter.detect_issues(str(path), rules_to_check=args.rules)
                else:
                    # 否則使用所有檢測規則
                    formatter.detect_issues(
                        str(path),
                        rules_to_check=[
                            "MD013",
                            "MD024",
                            "MD025",
                            "MD033",
                            "MD036",
                            "MD051",
                            "MD055",
                            "MD056",
                        ],
                    )
                logger.info(f"✅ 檢測完成: {path}")
            else:
                # 處理目錄的 dry-run - 這裡需要修改 format_directory 來支持檢測模式
                # 暫時使用現有邏輯，但只運行檢測規則
                stats = formatter.format_directory(
                    str(path),
                    recursive=args.recursive,
                    rules_to_fix=[
                        "MD024",
                        "MD025",
                        "MD036",
                        "MD051",
                        "MD055",
                    ],  # 只運行檢測規則
                    exclude_patterns=args.exclude,
                )
                logger.info("📊 檢測完成:")
                print(f"   處理檔案數: {stats['processed']}")
                print(
                    f"   檢測到問題檔案數: {stats['formatted']}"
                )  # 這裡的 formatted 實際上是檢測到的問題數
                print(f"   錯誤數: {stats['errors']}")

            return 0

        if path.is_file():
            # 處理單個檔案
            success = formatter.format_file(str(path), args.rules)
            if success:
                logger.info(f"✅ 已格式化: {path}")
            else:
                logger.info(f"ℹ️  無需更改: {path}")
        else:
            # 處理目錄
            stats = formatter.format_directory(
                str(path),
                recursive=args.recursive,
                rules_to_fix=args.rules,
                exclude_patterns=args.exclude,
            )

            logger.info("📊 格式化完成:")
            print(f"   處理檔案數: {stats['processed']}")
            print(f"   格式化檔案數: {stats['formatted']}")
            print(f"   錯誤數: {stats['errors']}")

            if stats["errors"] > 0:
                logger.warning("⚠️  發現錯誤的檔案:")
                for file_info in stats["files"]:
                    if file_info["status"] == "error":
                        print(f"     ❌ {file_info['path']}: {file_info['error']}")

        return 0

    except Exception as e:
        logger.error(f"❌ Markdown 格式化過程中發生錯誤: {e}")
        return 1


def run_monitor(args: argparse.Namespace) -> int:
    """系統監控"""
    try:
        from nova.monitoring import NovaMemoryMonitor, monitor_memory_continuous

        logger.info("🔍 啟動 Nova Sensor 監控")

        # 創建監控器
        monitor = NovaMemoryMonitor()

        if args.continuous:
            # 連續監控
            logger.info(
                f"🔄 開始連續監控 {args.continuous} 秒，每 {args.interval} 秒檢查一次"
            )
            result = monitor_memory_continuous(
                monitor, interval=args.interval, duration=args.continuous
            )
            logger.info("✅ 連續監控完成")
            print(f"   監控持續時間: {result['monitoring_duration']:.1f} 秒")
            print(f"   平均記憶體使用率: {result['avg_memory_percent']:.1f}%")
            print(f"   峰值記憶體使用率: {result['peak_memory_percent']:.1f}%")
        else:
            # 單次監控
            stats = monitor.get_memory_stats()
            logger.info("📊 系統狀態:")
            print(f"   CPU 使用率: {stats.cpu_percent:.1f}%")
            print(f"   記憶體使用率: {stats.percentage:.1f}%")
            print(f"   可用記憶體: {stats.available_gb:.1f} GB")

        return 0

    except Exception as e:
        logger.error(f"❌ 監控過程中發生錯誤: {e}")
        return 1


def run_cpu(args: argparse.Namespace) -> int:
    """CPU 監控"""
    try:
        from nova.monitoring import NovaMemoryMonitor

        monitor = NovaMemoryMonitor()
        stats = monitor.get_memory_stats()

        logger.info("🖥️  CPU 狀態:")
        print(f"   CPU 使用率: {stats.cpu_percent:.1f}%")
        print(f"   CPU 核心數: {stats.cpu_count}")

        if args.delay_check is not None:
            if stats.cpu_percent > args.delay_check:
                logger.warning(
                    f"⚠️  CPU 使用率過高 ({stats.cpu_percent:.1f}%)，建議延遲處理"
                )
                return 1
            else:
                logger.info(f"✅ CPU 使用率正常 ({stats.cpu_percent:.1f}%)")
                return 0

        return 0

    except Exception as e:
        logger.error(f"❌ CPU 監控過程中發生錯誤: {e}")
        return 1


def run_cleanup(args: argparse.Namespace) -> int:
    """記憶體清理"""
    try:
        from nova.monitoring import NovaMemoryMonitor

        monitor = NovaMemoryMonitor()

        logger.info(f"🧹 開始記憶體清理 (級別: {args.level})")

        if args.level == "critical":
            # 關鍵級別清理
            freed_gb = monitor.cleanup_memory("critical")
        else:
            # 正常級別清理
            freed_gb = monitor.cleanup_memory("normal")

        logger.info("✅ 記憶體清理完成")
        print(f"   釋放記憶體: {freed_gb:.1f} GB")

        return 0

    except Exception as e:
        logger.error(f"❌ 記憶體清理過程中發生錯誤: {e}")
        return 1


def run_analyze(args: argparse.Namespace) -> int:
    """代碼分析"""
    try:
        import json

        from nova.auditing.analyzer import CodeAnalyzer

        logger.info("🔍 開始代碼分析")

        # 創建分析器並運行分析
        analyzer = CodeAnalyzer(args.path)
        results = analyzer.analyze_all_files()

        # 保存結果
        results_file = Path("code_analysis_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"✅ 分析完成，結果已保存到: {results_file}")
        print(f"   分析檔案數: {results.get('total_files', 0)}")
        print(f"   發現問題數: {results.get('total_issues', 0)}")

        return 0

    except Exception as e:
        logger.error(f"❌ 代碼分析過程中發生錯誤: {e}")
        return 1


def run_audit(args: argparse.Namespace) -> int:
    """代碼質量檢查"""
    try:
        from nova.auditing.quality import (
            CodeQualityChecker,
            CodeQualityConfig,
            detailed_check,
            quick_check,
        )

        logger.info("🔍 開始代碼質量檢查")

        # 載入配置
        config = CodeQualityConfig()

        # 創建檢查器
        checker = CodeQualityChecker(config, args.path, args.files)

        # 運行檢查
        if args.detailed:
            return detailed_check(checker)
        else:
            return quick_check(checker)

    except Exception as e:
        logger.error(f"❌ 代碼質量檢查過程中發生錯誤: {e}")
        return 1


def main() -> int:
    """主入口點"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 根據命令調用對應的處理函數
    command_handlers = {
        "system": run_system_info,
        "config": run_config,
        "markdown": run_markdown,
        "monitor": run_monitor,
        "cpu": run_cpu,
        "cleanup": run_cleanup,
        "analyze": run_analyze,
        "audit": run_audit,
    }

    if args.command in command_handlers:
        return command_handlers[args.command](args)
    else:
        logger.error(f"❌ 未知命令: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
