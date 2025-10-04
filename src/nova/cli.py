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

logger = get_logger('cli')


def create_parser() -> argparse.ArgumentParser:
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description="Nova - 統一的開發工具平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  nova system                    # 顯示系統資訊
  nova config --show             # 顯示配置
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 系統資訊命令
    system_parser = subparsers.add_parser(
        'system',
        help='顯示系統資訊'
    )

    # 配置命令
    config_parser = subparsers.add_parser(
        'config',
        help='配置管理'
    )
    config_parser.add_argument(
        '--show',
        action='store_true',
        help='顯示當前配置'
    )

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


def main() -> int:
    """主入口點"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 根據命令調用對應的處理函數
    command_handlers = {
        'system': run_system_info,
        'config': run_config
    }

    if args.command in command_handlers:
        return command_handlers[args.command](args)
    else:
        logger.error(f"❌ 未知命令: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())