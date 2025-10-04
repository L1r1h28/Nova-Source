#!/usr/bin/env python3
"""
Nova CLI - 命令行介面
提供 nova 工具包的命令行訪問
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import importlib.util

from .nova_memory_monitor import (
    NovaMemoryMonitor,
    create_monitor_with_config,
    monitor_memory_continuous
)
from .performance_tester import (
    NovaPerformanceTester,
    performance_test,
    compare_with_baseline,
    quick_benchmark,
    memory_profile,
    get_system_info
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
  nova-sensor performance                # 運行預設效能測試
  nova-sensor performance --system-info  # 顯示系統資訊
  nova-sensor performance --module test.py --function my_func  # 測試特定函數
  nova-sensor performance --iterations 1000  # 自定義迭代次數
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

    # 效能測試命令
    perf_parser = subparsers.add_parser(
        'performance',
        help='效能測試和基準測試功能'
    )
    perf_parser.add_argument(
        '--iterations', '-n',
        type=int,
        default=100,
        help='基準測試迭代次數 (預設: 100)'
    )
    perf_parser.add_argument(
        '--output', '-o',
        type=str,
        default='performance_results',
        help='輸出目錄 (預設: performance_results)'
    )
    perf_parser.add_argument(
        '--function', '-f',
        type=str,
        help='要測試的函數名稱 (用於基準測試)'
    )
    perf_parser.add_argument(
        '--module', '-m',
        type=str,
        help='要載入的測試模組路徑'
    )
    perf_parser.add_argument(
        '--compare', '-c',
        type=str,
        nargs=2,
        metavar=('BASELINE', 'OPTIMIZED'),
        help='比較兩個函數的效能 (基準函數, 優化函數)'
    )
    perf_parser.add_argument(
        '--system-info', '-s',
        action='store_true',
        help='顯示系統資訊'
    )
    perf_parser.add_argument(
        '--memory-profile', '-p',
        action='store_true',
        help='執行記憶體剖析'
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


def run_performance(args: argparse.Namespace) -> int:
    """運行效能測試"""
    try:
        print("🚀 啟動 Nova 效能測試器")

        tester = NovaPerformanceTester(args.output)

        if args.system_info:
            # 顯示系統資訊
            print("📊 系統資訊:")
            system_info = get_system_info()
            for key, value in system_info.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
            return 0

        if args.module:
            # 載入測試模組
            print(f"📦 載入測試模組: {args.module}")
            try:
                spec = importlib.util.spec_from_file_location("test_module", args.module)
                if spec is None:
                    print(f"❌ 無法載入模組: {args.module}")
                    return 1

                if spec.loader is None:
                    print(f"❌ 模組載入器無效: {args.module}")
                    return 1

                test_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(test_module)

                if args.function:
                    # 測試特定函數
                    if hasattr(test_module, args.function):
                        func = getattr(test_module, args.function)
                        print(f"🧪 測試函數: {args.function}")

                        if args.memory_profile:
                            # 記憶體剖析
                            profile_result = memory_profile(func)
                            print("📊 記憶體剖析結果:")
                            for key, value in profile_result.items():
                                if isinstance(value, float):
                                    print(f"   {key}: {value:.6f}")
                                else:
                                    print(f"   {key}: {value}")
                            benchmark_result = None  # 記憶體剖析沒有基準測試結果
                        else:
                            # 基準測試
                            benchmark_result = quick_benchmark(func, args.iterations)
                            print("📊 基準測試結果:")
                            print(f"   函數: {benchmark_result['function_name']}")
                            print(f"   迭代次數: {benchmark_result['iterations']}")
                            print(f"   平均執行時間: {benchmark_result['execution_time']['mean']:.6f} 秒")
                            print(f"   平均記憶體使用: {benchmark_result['memory_usage']['mean'] / (1024*1024):.2f} MB")
                            print(f"   平均 CPU 使用率: {benchmark_result['cpu_usage']['mean']:.2f}%")

                        # 生成報告
                        if benchmark_result is not None:
                            tester.generate_report([benchmark_result])
                    else:
                        print(f"❌ 函數 '{args.function}' 在模組中不存在")
                        return 1
                else:
                    print("❌ 請指定要測試的函數名稱 (--function)")
                    return 1

            except Exception as e:
                print(f"❌ 載入模組時發生錯誤: {e}")
                return 1

        elif args.compare:
            # 比較兩個函數
            baseline_name, optimized_name = args.compare
            print(f"🔍 效能比較: {baseline_name} vs {optimized_name}")

            # 這裡需要從模組載入函數，簡化版本先跳過
            print("⚠️ 比較功能需要指定模組 (--module)")
            return 1

        else:
            # 預設測試記憶體監控功能
            print("🧪 運行預設效能測試 (記憶體監控)")

            from .nova_memory_monitor import NovaMemoryMonitor

            def test_memory_monitor():
                monitor = NovaMemoryMonitor()
                stats = monitor.get_memory_stats()
                return stats

            benchmark_result = quick_benchmark(test_memory_monitor, args.iterations)
            print("📊 記憶體監控效能測試結果:")
            print(f"   平均執行時間: {benchmark_result['execution_time']['mean']:.6f} 秒")
            print(f"   平均記憶體使用: {benchmark_result['memory_usage']['mean'] / (1024*1024):.2f} MB")
            print(f"   平均 CPU 使用率: {benchmark_result['cpu_usage']['mean']:.2f}%")

            # 生成報告
            tester.generate_report([benchmark_result])

        # 保存結果
        tester.save_results()

        print("✅ 效能測試完成！")
        return 0

    except Exception as e:
        print(f"❌ 效能測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
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
    elif args.command == 'performance':
        return run_performance(args)
    else:
        print(f"❌ 未知命令: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())