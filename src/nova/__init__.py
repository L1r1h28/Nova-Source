"""Nova - 統一的開發工具平台

Nova 是一個統一的代碼審計、質量檢查和效能分析平台，
基於 TurboCode Kit (TCK) 優化的高效能實現。
"""

__version__ = "0.2.0"
__author__ = "Nova Team"

# 初始化核心模組
from .core import config, logging, exceptions
from .models import (
    Metric, PerformanceMetrics, TestResult, BenchmarkResult,
    Issue, AuditResult, SystemInfo, Report
)
from .plugins import get_plugin_manager, initialize_plugins, cleanup_plugins
from .utils import timer, time_context, cache_result, retry, format_bytes, format_duration

# 初始化日誌系統
logging.initialize_logging()

# 初始化插件系統
initialize_plugins()

def get_version() -> str:
    """獲取版本信息"""
    return __version__

def get_system_info() -> 'SystemInfo':
    """獲取系統資訊"""
    import platform
    import sys
    import psutil

    return SystemInfo(
        platform=platform.system(),
        python_version=sys.version,
        cpu_count=psutil.cpu_count() or 0,
        memory_total_gb=psutil.virtual_memory().total / (1024**3),
        metadata={
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_implementation': platform.python_implementation()
        }
    )

# 清理函數
def cleanup() -> None:
    """清理所有資源"""
    cleanup_plugins()