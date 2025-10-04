"""Nova - 統一的開發工具平台

Nova 是一個統一的代碼審計、質量檢查和效能分析平台，
基於 TurboCode Kit (TCK) 優化的高效能實現。
"""

__version__ = "1.0.0"
__author__ = "Nova Team"

__all__ = [
    # 核心模組
    "config",
    "exceptions",
    "logging",
    # 模型
    "AuditResult",
    "BenchmarkResult",
    "Issue",
    "Metric",
    "PerformanceMetrics",
    "Report",
    "SystemInfo",
    "TestResult",
    # 插件
    "cleanup_plugins",
    "get_plugin_manager",
    "initialize_plugins",
    # 工具函數
    "cache_result",
    "format_bytes",
    "format_duration",
    "retry",
    "time_context",
    "timer",
    # 函數
    "get_version",
    "get_system_info",
    "cleanup",
]

# 初始化核心模組
from .core import config, exceptions, logging
from .models import (
    AuditResult,
    BenchmarkResult,
    Issue,
    Metric,
    PerformanceMetrics,
    Report,
    SystemInfo,
    TestResult,
)
from .plugins import cleanup_plugins, get_plugin_manager, initialize_plugins
from .utils import (
    cache_result,
    format_bytes,
    format_duration,
    retry,
    time_context,
    timer,
)

# 初始化日誌系統
logging.initialize_logging()

# 初始化插件系統
initialize_plugins()


def get_version() -> str:
    """獲取版本信息"""
    return __version__


def get_system_info() -> "SystemInfo":
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
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_implementation": platform.python_implementation(),
        },
    )


# 清理函數
def cleanup() -> None:
    """清理所有資源"""
    cleanup_plugins()
