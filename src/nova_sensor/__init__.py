"""Nova Sensor - 高性能開發工具集合

Nova Sensor 是一個基於 TurboCode Kit (TCK) 優化藍圖的高性能開發工具包，
提供記憶體監控、效能分析等實用工具。

主要模組:
- nova_memory_monitor: TCK 優化的記憶體監控器
"""

from .nova_memory_monitor import (
    NovaMemoryMonitor,
    create_monitor_with_config,
    monitor_memory_continuous,
    MemoryThresholds,
    MemoryStats,
    CleanupRecord
)

# CLI 模組 (延遲匯入以避免循環依賴)
def cli():
    """啟動 Nova CLI 介面"""
    from .cli import main
    main()

__version__ = "0.1.0"
__author__ = "Nova Team"

__all__ = [
    "NovaMemoryMonitor",
    "create_monitor_with_config",
    "monitor_memory_continuous",
    "MemoryThresholds",
    "MemoryStats",
    "CleanupRecord"
]