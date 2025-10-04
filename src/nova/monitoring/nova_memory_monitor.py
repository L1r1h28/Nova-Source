#!/usr/bin/env python3
"""
Nova 優化記憶體監控器 - 基於 TCK 優化藍圖
Nova Optimized Memory Monitor - Based on TCK Optimization Blueprints

優化策略:
- ✅ Dataclass 優化: 使用 @dataclass 提升物件效能
- ✅ LRU Cache: 使用 @lru_cache 快取            # 輕量 GPU 快取清理
            if TORCH_AVAILABLE and torch is not None and torch.cuda.is_available():  # type: ignore
                try:
                    torch.cuda.empty_cache()  # type: ignore
                    print("✅ GPU 快取清理完成")
                except Exception as e:
                    print(f"❌ GPU 快取清理失敗: {e}")
- ✅ 集合操作: 使用 set() 優化查找操作
- ✅ 生成器表達式: 使用生成器節省記憶體
- ✅ 字串 join: 使用 str.join() 優化字串操作
- ✅ 常數提取: 將常數提取到模組級別
"""

import gc
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional

import GPUtil
import psutil

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    TORCH_AVAILABLE = False

# === 常數提取 (模組級別快取) ===
DEFAULT_THRESHOLD = 0.85
DEFAULT_CRITICAL_THRESHOLD = 0.95
DEFAULT_CHECK_INTERVAL = 30
GB_DIVISOR = 1024**3
MB_DIVISOR = 1024**2

# === 字串常數 (避免重複字串操作) ===
MEMORY_STATS_HEADER = "\n記憶體監控統計:"
TOTAL_MEMORY_FMT = "   總記憶體: {:.1f} GB"
USED_MEMORY_FMT = "   已使用: {:.1f} GB ({:.1f}%)"
AVAILABLE_MEMORY_FMT = "   可用: {:.1f} GB"
THRESHOLDS_FMT = "   清理閾值: {:.1f}% / {:.1f}%"
CLEANUP_COUNT_FMT = "   清理次數: {}"
CPU_INFO_FMT = "   CPU 使用率: {:.1f}% (核心數: {})"
GPU_INFO_FMT = "   GPU ({}): {:.0f} MB / {:.0f} MB"
GPU_UTIL_FMT = "   GPU 使用率: {:.1f}%"
GPU_ERROR_FMT = "   GPU 錯誤: {}"
NO_GPU_MSG = "   未檢測到 GPU"
LAST_CLEANUP_FMT = "   最後清理: {}級別，{:.1f}秒前"
CLEANUP_TIME_FMT = "清理耗時: {:.3f} 秒"


@dataclass(frozen=True)
class MemoryThresholds:
    """記憶體閾值設定 (使用 dataclass 優化)"""

    normal: float = DEFAULT_THRESHOLD
    critical: float = DEFAULT_CRITICAL_THRESHOLD

    def __post_init__(self):
        """驗證閾值範圍"""
        if not (0.0 <= self.normal <= 1.0):
            raise ValueError(f"標準閾值必須在 0.0-1.0 之間: {self.normal}")
        if not (0.0 <= self.critical <= 1.0):
            raise ValueError(f"危險閾值必須在 0.0-1.0 之間: {self.critical}")
        if self.normal >= self.critical:
            raise ValueError("標準閾值必須小於危險閾值")


@dataclass
class CleanupRecord:
    """清理記錄 (使用 dataclass 優化)"""

    level: str
    timestamp: float
    duration: float = 0.0


@dataclass
class MemoryStats:
    """記憶體統計資料 (使用 dataclass 優化)"""

    total: int
    available: int
    used: int
    percentage: float
    thresholds: MemoryThresholds
    cleanup_count: int
    last_cleanup: Optional[CleanupRecord] = None

    # GPU 資訊 (可選)
    gpu_available: bool = False
    gpu_name: str = ""
    gpu_memory_used: int = 0
    gpu_memory_total: int = 0
    gpu_memory_util: float = 0.0
    gpu_error: str = ""

    # CPU 資訊 (新增)
    cpu_percent: float = 0.0
    cpu_count: int = 0

    @property
    def total_gb(self) -> float:
        """總記憶體 (GB)"""
        return self.total / GB_DIVISOR

    @property
    def used_gb(self) -> float:
        """已使用記憶體 (GB)"""
        return self.used / GB_DIVISOR

    @property
    def available_gb(self) -> float:
        """可用記憶體 (GB)"""
        return self.available / GB_DIVISOR


class NovaMemoryMonitor:
    """
    Nova 優化記憶體監控器

    基於 TCK 優化藍圖實現的記憶體監控解決方案:
    - 使用 psutil 進行系統記憶體監控
    - 使用 GPUtil 進行 GPU 監控
    - 應用多項效能優化策略
    """

    def __init__(self, thresholds: Optional[MemoryThresholds] = None):
        """
        初始化 Nova 記憶體監控器

        Args:
            thresholds: 記憶體閾值設定
        """
        self.thresholds = thresholds or MemoryThresholds()
        self.cleanup_history: List[CleanupRecord] = []

        print("🚀 初始化 Nova 記憶體監控器 (TCK 優化版)")
        print(f"   標準閾值: {self.thresholds.normal:.1%}")
        print(f"   危險閾值: {self.thresholds.critical:.1%}")

    def should_cleanup(self) -> Optional[str]:
        """
        檢查是否需要清理記憶體

        Returns:
            'critical': 需要危險級別清理
            'normal': 需要標準清理
            None: 不需要清理
        """
        memory_usage = psutil.virtual_memory().percent / 100

        if memory_usage > self.thresholds.critical:
            print(f"⚠️  記憶體使用率危險 ({memory_usage:.1%})，強制執行深度清理")
            return "critical"
        elif memory_usage > self.thresholds.normal:
            print(f"⚡ 記憶體使用率過高 ({memory_usage:.1%})，執行標準清理")
            return "normal"

        return None

    def cleanup_memory(self, level: str = "normal") -> float:
        """
        執行記憶體清理 (增強版：包含 GPU 快取清理)

        Args:
            level: 清理級別 ('normal' 或 'critical')

        Returns:
            float: 清理耗時 (秒)
        """
        start_time = time.time()

        if level == "critical":
            # 危險級別: 完整清理 + GPU 快取清理
            print("🧹 執行深度記憶體清理...")

            # Python 垃圾回收
            gc.collect()
            print("✅ Python 垃圾回收完成")

            # GPU 快取清理 (使用 torch)
            if TORCH_AVAILABLE and torch is not None and torch.cuda.is_available():  # type: ignore
                print("🎮 清理 GPU 快取...")
                try:
                    torch.cuda.empty_cache()  # type: ignore
                    torch.cuda.ipc_collect()  # type: ignore
                    print("✅ GPU 快取清理完成")
                except Exception as e:
                    print(f"❌ GPU 快取清理失敗: {e}")
            else:
                print("ℹ️  未檢測到 GPU 或未安裝 PyTorch")

            # 傳統 GPU 監控 (GPUtil)
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    print("📊 GPU 狀態監控中...")
                    for i, gpu in enumerate(gpus):
                        print(
                            f"   GPU {i}: {gpu.memoryUsed:.0f}MB / {gpu.memoryTotal:.0f}MB"
                        )
            except Exception as e:
                print(f"❌ GPU 監控錯誤: {e}")

            cleanup_record = CleanupRecord(level, time.time())
            self.cleanup_history.append(cleanup_record)
            print("✅ 危險級別記憶體清理完成")

        else:
            # 標準級別: 基本清理 + 輕量 GPU 清理
            print("🧹 執行標準記憶體清理...")

            # Python 垃圾回收
            gc.collect()
            print("✅ Python 垃圾回收完成")

            # 輕量 GPU 快取清理
            if TORCH_AVAILABLE and torch is not None and torch.cuda.is_available():  # type: ignore
                try:
                    torch.cuda.empty_cache()  # type: ignore
                    print("✅ GPU 快取清理完成")
                except Exception as e:
                    print(f"❌ GPU 快取清理失敗: {e}")

            cleanup_record = CleanupRecord(level, time.time())
            self.cleanup_history.append(cleanup_record)
            print("✅ 標準級別記憶體清理完成")

        cleanup_time = time.time() - start_time
        print(CLEANUP_TIME_FMT.format(cleanup_time))

        # 更新清理記錄的耗時
        cleanup_record.duration = cleanup_time

        return cleanup_time

    def _get_gpu_info_cached(self) -> Dict[str, Any]:
        """
        獲取 GPU 資訊

        Returns:
            dict: GPU 資訊字典
        """
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # 使用第一個 GPU
                return {
                    "available": True,
                    "name": gpu.name,
                    "memory_used": gpu.memoryUsed,
                    "memory_total": gpu.memoryTotal,
                    "memory_util": gpu.memoryUtil * 100,
                    "error": "",
                }
            else:
                return {
                    "available": False,
                    "name": "",
                    "memory_used": 0,
                    "memory_total": 0,
                    "memory_util": 0.0,
                    "error": "",
                }
        except Exception as e:
            return {
                "available": False,
                "name": "",
                "memory_used": 0,
                "memory_total": 0,
                "memory_util": 0.0,
                "error": str(e),
            }

    def get_memory_stats(self) -> MemoryStats:
        """
        獲取當前記憶體統計信息

        Returns:
            MemoryStats: 記憶體統計物件
        """
        vm = psutil.virtual_memory()
        gpu_info = self._get_gpu_info_cached()

        # 獲取 CPU 資訊
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True) or 0

        return MemoryStats(
            total=vm.total,
            available=vm.available,
            used=vm.used,
            percentage=vm.percent,
            thresholds=self.thresholds,
            cleanup_count=len(self.cleanup_history),
            last_cleanup=self.cleanup_history[-1] if self.cleanup_history else None,
            gpu_available=gpu_info["available"],
            gpu_name=gpu_info["name"],
            gpu_memory_used=gpu_info["memory_used"],
            gpu_memory_total=gpu_info["memory_total"],
            gpu_memory_util=gpu_info["memory_util"],
            gpu_error=gpu_info["error"],
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
        )

    def print_stats(self, stats: Optional[MemoryStats] = None) -> None:
        """
        打印當前記憶體統計信息

        Args:
            stats: 記憶體統計資料 (如果為 None 則自動獲取)
        """
        if stats is None:
            stats = self.get_memory_stats()

        # 使用字串 join 優化字串操作
        output_lines = [
            MEMORY_STATS_HEADER,
            TOTAL_MEMORY_FMT.format(stats.total_gb),
            USED_MEMORY_FMT.format(stats.used_gb, stats.percentage),
            AVAILABLE_MEMORY_FMT.format(stats.available_gb),
            THRESHOLDS_FMT.format(
                stats.thresholds.normal * 100, stats.thresholds.critical * 100
            ),
            CLEANUP_COUNT_FMT.format(stats.cleanup_count),
            CPU_INFO_FMT.format(stats.cpu_percent, stats.cpu_count),
        ]

        # GPU 資訊
        if stats.gpu_available:
            output_lines.extend(
                [
                    GPU_INFO_FMT.format(
                        stats.gpu_name, stats.gpu_memory_used, stats.gpu_memory_total
                    ),
                    GPU_UTIL_FMT.format(stats.gpu_memory_util),
                ]
            )
        elif stats.gpu_error:
            output_lines.append(GPU_ERROR_FMT.format(stats.gpu_error))
        else:
            output_lines.append(NO_GPU_MSG)

        # 最後清理資訊
        if stats.last_cleanup:
            time_since = time.time() - stats.last_cleanup.timestamp
            output_lines.append(
                LAST_CLEANUP_FMT.format(stats.last_cleanup.level, time_since)
            )

        # 使用 join 一次性輸出 (優化字串操作)
        print("\n".join(output_lines))

    def get_cleanup_summary(self) -> Dict[str, Any]:
        """
        獲取清理歷史摘要

        Returns:
            dict: 清理摘要統計
        """
        if not self.cleanup_history:
            return {"total_cleanups": 0, "avg_duration": 0.0}

        # 使用生成器表達式優化記憶體使用
        durations = (record.duration for record in self.cleanup_history)
        total_duration = sum(durations)

        # 使用集合操作統計清理類型
        cleanup_levels = {record.level for record in self.cleanup_history}
        level_counts = {}
        for level in cleanup_levels:
            level_counts[level] = sum(
                1 for record in self.cleanup_history if record.level == level
            )

        return {
            "total_cleanups": len(self.cleanup_history),
            "avg_duration": total_duration / len(self.cleanup_history),
            "level_counts": level_counts,
            "total_duration": total_duration,
        }

    def get_cpu_percent(self, interval: Optional[float] = None) -> float:
        """
        獲取當前 CPU 使用率

        Args:
            interval: 監控間隔 (秒)，如果為 None 則使用預設值 1.0

        Returns:
            float: CPU 使用率百分比 (0.0-100.0)
        """
        try:
            actual_interval = interval if interval is not None else 1.0
            return psutil.cpu_percent(interval=actual_interval)
        except Exception as e:
            print(f"❌ 獲取 CPU 使用率失敗: {e}")
            return 0.0

    def should_cpu_delay(self, threshold: float = 80.0) -> bool:
        """
        判斷是否應該根據 CPU 使用率延遲執行

        Args:
            threshold: CPU 使用率閾值 (0.0-100.0)

        Returns:
            bool: 是否應該延遲
        """
        cpu_percent = self.get_cpu_percent()
        return cpu_percent > threshold

    def smart_cpu_delay(self, threshold: float = 80.0, max_delay: float = 0.5) -> None:
        """
        智慧 CPU 延遲：根據 CPU 使用率動態調整延遲時間

        Args:
            threshold: CPU 使用率閾值 (0.0-100.0)
            max_delay: 最大延遲時間（秒）
        """
        if not self.should_cpu_delay(threshold):
            print("✅ CPU 使用率正常，無需延遲")
            return

        cpu_percent = self.get_cpu_percent()
        # 動態計算延遲時間：CPU 使用率越高，延遲越長
        delay_time = min(max_delay, (cpu_percent / 100.0) * max_delay)
        print(
            f"⏳ CPU 使用率 {cpu_percent:.1f}% > {threshold:.1f}%，延遲 {delay_time:.2f} 秒"
        )
        time.sleep(delay_time)


def create_monitor_with_config(
    config_path: str = "memory_config.json",
) -> NovaMemoryMonitor:
    """
    從設定檔案創建監控器 (使用 LRU 快取優化設定載入)

    Args:
        config_path: 設定檔案路徑

    Returns:
        NovaMemoryMonitor: 配置好的監控器實例
    """
    config = load_memory_config_cached(config_path)

    thresholds = MemoryThresholds(
        normal=config.get("threshold", DEFAULT_THRESHOLD),
        critical=config.get("critical_threshold", DEFAULT_CRITICAL_THRESHOLD),
    )

    return NovaMemoryMonitor(thresholds)


@lru_cache(maxsize=8)  # 快取多個設定檔案
def load_memory_config_cached(config_path: str) -> Dict[str, Any]:
    """
    載入記憶體監控設定 (使用 LRU 快取避免重複 I/O)

    Args:
        config_path: 設定檔案路徑

    Returns:
        dict: 設定字典
    """
    import json
    import os

    if not os.path.exists(config_path):
        # 返回預設設定
        return {
            "threshold": DEFAULT_THRESHOLD,
            "critical_threshold": DEFAULT_CRITICAL_THRESHOLD,
            "check_interval": DEFAULT_CHECK_INTERVAL,
        }

    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  載入設定檔案失敗: {e}，使用預設設定")
        return {
            "threshold": DEFAULT_THRESHOLD,
            "critical_threshold": DEFAULT_CRITICAL_THRESHOLD,
            "check_interval": DEFAULT_CHECK_INTERVAL,
        }


def monitor_memory_continuous(
    monitor: NovaMemoryMonitor,
    interval: int = DEFAULT_CHECK_INTERVAL,
    duration: int = 300,
) -> Dict[str, Any]:
    """
    連續監控記憶體使用情況

    Args:
        monitor: 記憶體監控器實例
        interval: 監控間隔 (秒)
        duration: 監控持續時間 (秒)

    Returns:
        dict: 監控摘要統計
    """
    print(f"🔄 開始連續監控 {duration} 秒，每 {interval} 秒檢查一次...")

    start_time = time.time()
    check_count = 0
    cleanup_count = 0

    try:
        while time.time() - start_time < duration:
            check_count += 1
            cleanup_level = monitor.should_cleanup()

            if cleanup_level:
                monitor.cleanup_memory(cleanup_level)
                cleanup_count += 1

            monitor.print_stats()
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n⏹️  監控被使用者中斷")

    monitoring_duration = time.time() - start_time
    print(f"✅ 連續監控完成，總檢查次數: {check_count}，清理次數: {cleanup_count}")

    return {
        "monitoring_duration": monitoring_duration,
        "check_count": check_count,
        "cleanup_count": cleanup_count,
        "checks_per_second": check_count / monitoring_duration
        if monitoring_duration > 0
        else 0,
    }


if __name__ == "__main__":
    # 測試代碼
    print("🧪 測試 Nova 優化記憶體監控器")

    # 創建監控器
    monitor = NovaMemoryMonitor()

    # 測試記憶體監控
    print("\n📊 --- 記憶體監控測試 ---")
    stats = monitor.get_memory_stats()
    monitor.print_stats(stats)

    # 測試清理功能
    print("\n🧹 --- 清理功能測試 ---")
    cleanup_level = monitor.should_cleanup()
    if cleanup_level:
        monitor.cleanup_memory(cleanup_level)

    # 測試摘要統計
    print("\n📈 --- 清理摘要 ---")
    summary = monitor.get_cleanup_summary()
    print(f"總清理次數: {summary['total_cleanups']}")
    if summary["total_cleanups"] > 0:
        print(f"平均清理耗時: {summary['avg_duration']:.3f} 秒")
        print(f"清理類型統計: {summary['level_counts']}")

    print("\n🎉 測試完成 - Nova 優化記憶體監控器運行正常！")
