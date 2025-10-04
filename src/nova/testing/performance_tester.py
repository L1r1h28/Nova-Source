# nova_sensor/performance_tester.py
"""
效能測試模組 - 集成進 Nova Source 的效能測試工具

基於通用工具的效能測試框架，提供完整的效能分析功能。
"""

import time
import psutil
import tracemalloc
import cProfile
import pstats
import io
from typing import Callable, Any, Dict, List, Optional
from functools import wraps
import statistics
import json
from pathlib import Path
import unittest
from dataclasses import dataclass, asdict
import gc
import platform
import threading
import importlib.util
import os

# 可選依賴
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class PerformanceResult:
    """效能測試結果數據類"""
    function_name: str
    execution_time: float
    memory_usage: int
    cpu_percent: float
    peak_memory: int
    call_count: int = 1

    # 擴展的系統資源統計
    startup_time: float = 0.0
    io_read_count: int = 0
    io_write_count: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    system_memory_percent: float = 0.0
    system_memory_available_gb: float = 0.0
    disk_usage_percent: float = 0.0
    network_sent_kb: float = 0.0
    network_recv_kb: float = 0.0
    gpu_count: int = 0
    gpu_usage_percent: float = 0.0
    gpu_memory_mb: float = 0.0
    gpu_temperature_c: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class NovaPerformanceTester:
    """Nova 效能測試器 - 集成版"""

    def __init__(self, output_dir: str = "performance_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[PerformanceResult] = []

    def _get_comprehensive_system_stats(self) -> Dict[str, Any]:
        """取得完整系統統計資訊"""
        stats = {
            # 基本程序統計
            'memory_mb': 0.0,
            'virtual_memory_mb': 0.0,
            'memory_percent': 0.0,
            'io_read_count': 0,
            'io_write_count': 0,
            'io_read_bytes': 0,
            'io_write_bytes': 0,
            # 系統資源統計
            'cpu_percent': 0.0,
            'system_memory_percent': 0.0,
            'system_memory_available_gb': 0.0,
            'disk_usage_percent': 0.0,
            'network_sent_kb': 0.0,
            'network_recv_kb': 0.0,
            # GPU 統計
            'gpu_count': 0,
            'gpu_usage_percent': 0.0,
            'gpu_memory_mb': 0.0,
            'gpu_temperature_c': 0.0,
            # 系統訊息
            'platform': platform.system(),
            'cpu_cores': psutil.cpu_count() or 0,
            'threads': threading.active_count()
        }

        try:
            # 程序統計
            process = psutil.Process()
            memory = process.memory_info()
            io_stats = process.io_counters()

            stats.update({
                'memory_mb': memory.rss / 1024 / 1024,
                'virtual_memory_mb': memory.vms / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'io_read_count': io_stats.read_count if io_stats else 0,
                'io_write_count': io_stats.write_count if io_stats else 0,
                'io_read_bytes': io_stats.read_bytes if io_stats else 0,
                'io_write_bytes': io_stats.write_bytes if io_stats else 0
            })

            # 系統資源統計
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            net_info = psutil.net_io_counters()

            stats.update({
                'cpu_percent': cpu_percent,
                'system_memory_percent': memory_info.percent,
                'system_memory_available_gb': memory_info.available / 1024 / 1024 / 1024,
                'disk_usage_percent': (disk_info.used / disk_info.total) * 100,
                'network_sent_kb': net_info.bytes_sent / 1024 if net_info else 0,
                'network_recv_kb': net_info.bytes_recv / 1024 if net_info else 0
            })
        except Exception as e:
            print(f"⚠️ 系統資源監控錯誤: {e}")

        # GPU 監控
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()  # type: ignore
                if gpus:
                    gpu = gpus[0]  # 使用第一個 GPU
                    stats.update({
                        'gpu_count': len(gpus),
                        'gpu_usage_percent': gpu.load * 100,
                        'gpu_memory_mb': gpu.memoryUsed,
                        'gpu_temperature_c': gpu.temperature
                    })
            except Exception as e:
                print(f"⚠️ GPU 監控錯誤: {e}")

        return stats

    def time_function(self, func: Callable, *args, **kwargs) -> PerformanceResult:
        """測試函數執行時間（增強版，包含完整系統統計）"""
        function_name = func.__name__

        # 垃圾回收和系統穩定
        gc.collect()
        time.sleep(0.05)  # 穩定系統狀態

        # 記錄啟動時間
        startup_start = time.perf_counter()

        # 開始記憶體追蹤
        tracemalloc.start()

        # 獲取初始統計
        start_stats = self._get_comprehensive_system_stats()

        startup_time = time.perf_counter() - startup_start

        # 執行函數
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        execution_time = end_time - start_time

        # 獲取結束統計
        end_stats = self._get_comprehensive_system_stats()

        # 停止記憶體追蹤
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # 計算差異統計
        io_read_count = end_stats['io_read_count'] - start_stats['io_read_count']
        io_write_count = end_stats['io_write_count'] - start_stats['io_write_count']
        io_read_bytes = end_stats['io_read_bytes'] - start_stats['io_read_bytes']
        io_write_bytes = end_stats['io_write_bytes'] - start_stats['io_write_bytes']

        perf_result = PerformanceResult(
            function_name=function_name,
            execution_time=execution_time,
            memory_usage=current,
            cpu_percent=end_stats['cpu_percent'],
            peak_memory=peak,
            startup_time=startup_time,
            io_read_count=io_read_count,
            io_write_count=io_write_count,
            io_read_bytes=io_read_bytes,
            io_write_bytes=io_write_bytes,
            system_memory_percent=end_stats['system_memory_percent'],
            system_memory_available_gb=end_stats['system_memory_available_gb'],
            disk_usage_percent=end_stats['disk_usage_percent'],
            network_sent_kb=end_stats['network_sent_kb'] - start_stats['network_sent_kb'],
            network_recv_kb=end_stats['network_recv_kb'] - start_stats['network_recv_kb'],
            gpu_count=end_stats['gpu_count'],
            gpu_usage_percent=end_stats['gpu_usage_percent'],
            gpu_memory_mb=end_stats['gpu_memory_mb'],
            gpu_temperature_c=end_stats['gpu_temperature_c']
        )

        self.results.append(perf_result)
        return perf_result

    def benchmark_function(self, func: Callable, iterations: int = 100,
                          *args, **kwargs) -> Dict[str, Any]:
        """基準測試函數 - 多輪執行統計"""
        function_name = func.__name__
        execution_times = []
        memory_usages = []
        cpu_percents = []

        print(f"🔬 基準測試: {function_name} ({iterations} 次迭代)")

        for i in range(iterations):
            if (i + 1) % 10 == 0:
                print(f"   進度: {i + 1}/{iterations}")

            # 垃圾回收
            gc.collect()

            # 測試單輪
            result = self.time_function(func, *args, **kwargs)
            execution_times.append(result.execution_time)
            memory_usages.append(result.memory_usage)
            cpu_percents.append(result.cpu_percent)

        # 統計分析
        stats = {
            "function_name": function_name,
            "iterations": iterations,
            "execution_time": {
                "mean": statistics.mean(execution_times),
                "median": statistics.median(execution_times),
                "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                "min": min(execution_times),
                "max": max(execution_times)
            },
            "memory_usage": {
                "mean": statistics.mean(memory_usages),
                "median": statistics.median(memory_usages),
                "stdev": statistics.stdev(memory_usages) if len(memory_usages) > 1 else 0,
                "min": min(memory_usages),
                "max": max(memory_usages)
            },
            "cpu_usage": {
                "mean": statistics.mean(cpu_percents),
                "median": statistics.median(cpu_percents),
                "stdev": statistics.stdev(cpu_percents) if len(cpu_percents) > 1 else 0,
                "min": min(cpu_percents),
                "max": max(cpu_percents)
            }
        }

        return stats

    def calculate_performance_score(self, baseline_result: PerformanceResult,
                                  optimized_result: PerformanceResult) -> Dict[str, float]:
        """計算效能改善評分"""
        # 計算改善倍數
        time_improvement = baseline_result.execution_time / optimized_result.execution_time if optimized_result.execution_time > 0 else float('inf')
        memory_change = (optimized_result.memory_usage - baseline_result.memory_usage) / (1024 * 1024)  # MB
        cpu_change = optimized_result.cpu_percent - baseline_result.cpu_percent

        scores = {}

        # 時間改善評分
        if time_improvement >= 100:  # 極大改善
            scores['time_score'] = 100.0
        elif time_improvement >= 10:
            scores['time_score'] = 80.0 + (time_improvement - 10) * 0.5
        elif time_improvement >= 2:
            scores['time_score'] = 60.0 + (time_improvement - 2) * 2.5
        else:
            scores['time_score'] = max(0.0, time_improvement * 30)

        # 記憶體效率評分
        if memory_change <= 0:  # 節省記憶體
            scores['memory_score'] = 100.0
        elif memory_change <= 10:  # 少量增加
            scores['memory_score'] = 90.0 - memory_change * 2
        elif memory_change <= 50:
            scores['memory_score'] = 70.0 - (memory_change - 10) * 1.5
        else:
            scores['memory_score'] = max(10.0, 70.0 - memory_change * 0.5)

        # CPU 效率評分
        if cpu_change <= 0:  # CPU 使用減少
            scores['cpu_score'] = 100.0
        elif cpu_change <= 5:
            scores['cpu_score'] = 90.0 - cpu_change * 2
        else:
            scores['cpu_score'] = max(20.0, 80.0 - cpu_change)

        # I/O 效率評分
        io_improvement = (baseline_result.io_read_count + baseline_result.io_write_count) - \
                        (optimized_result.io_read_count + optimized_result.io_write_count)
        if io_improvement >= 100:
            scores['io_score'] = 100.0
        elif io_improvement >= 50:
            scores['io_score'] = 90.0
        elif io_improvement >= 10:
            scores['io_score'] = 80.0
        elif io_improvement > 0:
            scores['io_score'] = 60.0 + io_improvement * 2
        else:
            scores['io_score'] = 50.0  # 無 I/O 優化

        # 總體評分（加權平均）
        weights = {
            'time_score': 0.4,
            'memory_score': 0.3,
            'cpu_score': 0.2,
            'io_score': 0.1
        }

        total_score = sum(scores[key] * weights[key] for key in scores.keys())
        scores['total_score'] = total_score

        # 效能等級
        if total_score >= 90:
            scores['grade'] = 'A+'
        elif total_score >= 80:
            scores['grade'] = 'A'
        elif total_score >= 70:
            scores['grade'] = 'B+'
        elif total_score >= 60:
            scores['grade'] = 'B'
        elif total_score >= 50:
            scores['grade'] = 'C'
        else:
            scores['grade'] = 'D'

        return scores

    def compare_performance(self, baseline_func: Callable, optimized_func: Callable,
                          *args, **kwargs) -> Dict[str, Any]:
        """比較兩個函數的效能差異"""
        print("🔍 效能比較測試")
        print("-" * 40)

        # 測試基準函數
        baseline_result = self.time_function(baseline_func, *args, **kwargs)
        print(f"📊 基準函數 ({baseline_func.__name__}): {baseline_result.execution_time:.6f}s")

        # 測試優化函數
        optimized_result = self.time_function(optimized_func, *args, **kwargs)
        print(f"⚡ 優化函數 ({optimized_func.__name__}): {optimized_result.execution_time:.6f}s")

        # 計算改善倍數
        time_improvement = baseline_result.execution_time / optimized_result.execution_time if optimized_result.execution_time > 0 else float('inf')
        print(f"🚀 執行時間改善: {time_improvement:.1f} 倍")

        # 計算評分
        scores = self.calculate_performance_score(baseline_result, optimized_result)

        print(f"📈 效能評分: {scores['total_score']:.1f}/100 ({scores['grade']} 級)")
        print(f"⏱️ 時間評分: {scores['time_score']:.1f}/100")
        print(f"💾 記憶體評分: {scores['memory_score']:.1f}/100")
        print(f"⚙️ CPU 評分: {scores['cpu_score']:.1f}/100")
        print(f"💿 I/O 評分: {scores['io_score']:.1f}/100")

        return {
            'baseline_result': baseline_result,
            'optimized_result': optimized_result,
            'improvement_ratio': time_improvement,
            'scores': scores
        }

    def save_results(self, filename: str = "performance_results.json"):
        """保存測試結果"""
        results_dict = [result.to_dict() for result in self.results]
        output_file = self.output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)

        print(f"💾 效能測試結果已保存到: {output_file}")

    def generate_report(self, benchmark_results: Optional[List[Dict]] = None,
                       filename: str = "performance_report.md"):
        """生成效能測試報告"""
        report_file = self.output_dir / filename

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Nova 效能測試報告\n\n")
            f.write(f"生成時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            if benchmark_results:
                f.write("## 基準測試結果\n\n")
                for result in benchmark_results:
                    f.write(f"### {result['function_name']}\n\n")
                    f.write(f"- **測試輪數**: {result['iterations']}\n")
                    f.write(f"- **平均執行時間**: {result['execution_time']['mean']:.6f} 秒\n")
                    f.write(f"- **執行時間標準差**: {result['execution_time']['stdev']:.6f} 秒\n")
                    f.write(f"- **平均記憶體使用**: {result['memory_usage']['mean'] / (1024*1024):.2f} MB\n")
                    f.write(f"- **平均 CPU 使用率**: {result['cpu_usage']['mean']:.2f}%\n")
                    f.write("\n")

            if self.results:
                f.write("## 單次測試結果\n\n")
                f.write("| 函數名稱 | 執行時間(s) | 記憶體使用(MB) | CPU使用率(%) | I/O讀取 | I/O寫入 | GPU使用率(%) |\n")
                f.write("|---------|------------|---------------|---------------|---------|---------|---------------|\n")

                for result in self.results:
                    memory_mb = result.memory_usage / (1024 * 1024)
                    f.write(f"| {result.function_name} | {result.execution_time:.6f} | {memory_mb:.2f} | {result.cpu_percent:.1f} | {result.io_read_count} | {result.io_write_count} | {result.gpu_usage_percent:.1f} |\n")

                # 系統資源總結
                f.write("\n## 系統資源統計\n\n")
                if self.results:
                    latest = self.results[-1]  # 使用最後一個結果的系統統計
                    f.write(f"- **系統記憶體使用率**: {latest.system_memory_percent:.1f}%\n")
                    f.write(f"- **可用記憶體**: {latest.system_memory_available_gb:.2f} GB\n")
                    f.write(f"- **磁碟使用率**: {latest.disk_usage_percent:.1f}%\n")
                    f.write(f"- **網路傳送**: {latest.network_sent_kb:.1f} KB\n")
                    f.write(f"- **網路接收**: {latest.network_recv_kb:.1f} KB\n")

                    if latest.gpu_count > 0:
                        f.write(f"- **GPU 數量**: {latest.gpu_count}\n")
                        f.write(f"- **GPU 記憶體使用**: {latest.gpu_memory_mb:.1f} MB\n")
                        f.write(f"- **GPU 溫度**: {latest.gpu_temperature_c:.1f}°C\n")

                    f.write(f"- **CPU 核心數**: {psutil.cpu_count()}\n")
                    f.write(f"- **執行緒數**: {threading.active_count()}\n")
                    f.write(f"- **平台**: {platform.system()}\n")

        print(f"📋 Nova 效能測試報告已生成: {report_file}")


# 裝飾器版本
def performance_test(iterations: int = 100):
    """效能測試裝飾器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tester = NovaPerformanceTester()

            print(f"🚀 開始效能測試: {func.__name__}")
            benchmark_result = tester.benchmark_function(func, iterations, *args, **kwargs)

            # 生成報告
            tester.generate_report([benchmark_result])

            return benchmark_result
        return wrapper
    return decorator


def compare_with_baseline(baseline_func: Callable):
    """比較優化函數與基準函數的裝飾器"""
    def decorator(optimized_func: Callable):
        @wraps(optimized_func)
        def wrapper(*args, **kwargs):
            tester = NovaPerformanceTester()

            print(f"🔍 效能比較: {baseline_func.__name__} vs {optimized_func.__name__}")
            comparison = tester.compare_performance(baseline_func, optimized_func, *args, **kwargs)

            return comparison
        return wrapper
    return decorator


# 實用工具函數
def get_system_info() -> Dict[str, Any]:
    """獲取系統基本資訊"""
    tester = NovaPerformanceTester()
    return tester._get_comprehensive_system_stats()


def quick_benchmark(func: Callable, iterations: int = 10, *args, **kwargs) -> Dict[str, Any]:
    """快速基準測試"""
    tester = NovaPerformanceTester()
    return tester.benchmark_function(func, iterations, *args, **kwargs)


def memory_profile(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """記憶體剖析"""
    tester = NovaPerformanceTester()
    result = tester.time_function(func, *args, **kwargs)

    return {
        'function': func.__name__,
        'memory_usage_mb': result.memory_usage / (1024 * 1024),
        'peak_memory_mb': result.peak_memory / (1024 * 1024),
        'execution_time': result.execution_time
    }


def discord_notify_benchmark(func: Callable, webhook_url: str, title: Optional[str] = None,
                           mode: str = "general", iterations: int = 10,
                           *args, **kwargs) -> Dict[str, Any]:
    """帶 Discord 通知的基準測試"""
    try:
        from .discord_notifier import Discord
    except ImportError:
        print("⚠️ Discord 通知模組不可用，跳過通知")
        return quick_benchmark(func, iterations, *args, **kwargs)

    # 運行基準測試
    result = quick_benchmark(func, iterations, *args, **kwargs)

    # 準備通知訊息
    message = f"效能測試完成！\n"
    message += f"測試函數: {func.__name__}\n"
    message += f"迭代次數: {iterations}\n"
    message += f"平均執行時間: {result['execution_time']['mean']:.6f} 秒\n"
    message += f"平均記憶體使用: {result['memory_usage']['mean'] / (1024*1024):.2f} MB\n"
    message += f"平均 CPU 使用率: {result['cpu_usage']['mean']:.2f}%\n"
    message += f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    # 發送 Discord 通知
    try:
        Discord(
            message=message,
            title=title or f"Nova 效能測試 - {func.__name__}",
            mode=mode,  # type: ignore
            target_webhook_url=webhook_url
        )
        print("✅ Discord 通知發送成功！")
    except Exception as e:
        print(f"❌ Discord 通知發送失敗: {e}")

    return result