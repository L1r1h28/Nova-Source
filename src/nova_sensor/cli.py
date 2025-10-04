#!/usr/bin/env python3
"""
Nova CLI - 命令行介面
提供 nova 工具包的命令行訪問
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .nova_memory_monitor import (
    NovaMemoryMonitor,
    create_monitor_with_config,
    monitor_memory_continuous
)


def create_parser() -> argparse.ArgumentParser:
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description="Nova Sensor - 高性能開發工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  nova-sensor monitor                    # 啟動記憶體監控
  nova-sensor monitor --config config.json  # 使用自定義配置
  nova-sensor monitor --continuous 300   # 連續監控 5 分鐘
  nova-sensor test                       # 運行測試套件
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 記憶體監控命令
    monitor_parser = subparsers.add_parser(
        'monitor',
        help='記憶體監控功能'
    )
    monitor_parser.add_argument(
        '--config', '-c',
        type=str,
        default='memory_config.json',
        help='設定檔案路徑 (預設: memory_config.json)'
    )
    monitor_parser.add_argument(
        '--continuous', '-t',
        type=int,
        nargs='?',
        const=300,
        help='連續監控秒數 (預設: 300秒)'
    )
    monitor_parser.add_argument(
        '--interval', '-i',
        type=int,
        default=30,
        help='監控間隔秒數 (預設: 30秒)'
    )

    # 測試命令
    test_parser = subparsers.add_parser(
        'test',
        help='運行測試套件'
    )
    test_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細輸出'
    )

    return parser


def run_monitor(args: argparse.Namespace) -> int:
    """運行記憶體監控"""
    try:
        print("🚀 啟動 Nova 記憶體監控器")

        # 創建監控器
        monitor = create_monitor_with_config(args.config)
        print(f"✅ 設定載入成功: {args.config}")

        if args.continuous:
            # 連續監控模式
            print(f"🔄 開始連續監控 {args.continuous} 秒...")
            result = monitor_memory_continuous(
                monitor,
                interval=args.interval,
                duration=args.continuous
            )

            print("📊 監控完成統計:")
            print(f"   總檢查次數: {result['check_count']}")
            print(f"   清理次數: {result['cleanup_count']}")
            print(f"   平均 CPU 使用率: {result['avg_cpu_percent']:.1f}%")
        else:
            # 單次監控模式
            stats = monitor.get_memory_stats()
            monitor.print_stats()

            cleanup_level = monitor.should_cleanup()
            if cleanup_level:
                duration = monitor.cleanup_memory(cleanup_level)
                print(f"🧹 已執行 {cleanup_level} 級別清理，耗時 {duration:.3f} 秒")
            else:
                print("✅ 記憶體使用正常，無需清理")

        return 0

    except FileNotFoundError:
        print(f"❌ 設定檔案不存在: {args.config}")
        print("💡 提示: 請檢查檔案路徑，或使用預設設定運行")
        return 1
    except Exception as e:
        print(f"❌ 監控過程中發生錯誤: {e}")
        return 1


def run_tests(args: argparse.Namespace) -> int:
    """運行測試套件"""
    try:
        print("🧪 運行 Nova 測試套件")

        # 匯入測試模組
        import subprocess
        import sys

        # 運行測試腳本
        test_script = Path(__file__).parent / "test_nova_memory_monitor.py"
        if not test_script.exists():
            print(f"❌ 測試腳本不存在: {test_script}")
            return 1

        cmd = [sys.executable, str(test_script)]
        if args.verbose:
            cmd.append("--verbose")

        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print("✅ 所有測試通過！")
        else:
            print(f"❌ 測試失敗，退出碼: {result.returncode}")

        return result.returncode

    except Exception as e:
        print(f"❌ 運行測試時發生錯誤: {e}")
        return 1


def main() -> int:
    """主入口點"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'monitor':
        return run_monitor(args)
    elif args.command == 'test':
        return run_tests(args)
    else:
        print(f"❌ 未知命令: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())