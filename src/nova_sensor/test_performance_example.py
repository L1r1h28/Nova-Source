# test_performance_example.py
"""
效能測試範例模組
用於測試 Nova 效能測試器的功能
"""

import time
import math
import random


def simple_calculation(n: int = 1000) -> float:
    """簡單的數學計算"""
    result = 0.0
    for i in range(n):
        result += math.sin(i) * math.cos(i)
    return result


def memory_intensive_task(size: int = 100000) -> list:
    """記憶體密集型任務"""
    data = []
    for i in range(size):
        data.append({
            'id': i,
            'value': random.random(),
            'text': f"item_{i}" * 10
        })
    return data


def cpu_intensive_task(iterations: int = 100000) -> int:
    """CPU 密集型任務"""
    result = 0
    for i in range(iterations):
        result += i * i
        result %= 1000000  # 防止溢位
    return result


def io_simulation_task(file_count: int = 10) -> int:
    """I/O 模擬任務"""
    total_size = 0
    for i in range(file_count):
        # 模擬檔案操作
        filename = f"temp_file_{i}.txt"
        with open(filename, 'w') as f:
            content = f"Test content for file {i}\n" * 100
            f.write(content)
            total_size += len(content)

        # 模擬讀取
        with open(filename, 'r') as f:
            _ = f.read()

        # 清理（實際應用中可能不需要）
        try:
            import os
            os.remove(filename)
        except:
            pass

    return total_size


def optimized_calculation(n: int = 1000) -> float:
    """優化的數學計算版本"""
    # 使用向量化計算（如果有 numpy）
    try:
        import numpy as np
        x = np.arange(n, dtype=np.float64)
        result = np.sum(np.sin(x) * np.cos(x))
        return float(result)
    except ImportError:
        # 回退到簡單版本
        return simple_calculation(n)


def baseline_sorting(data_size: int = 10000) -> list:
    """基準排序算法"""
    data = [random.randint(0, 1000000) for _ in range(data_size)]
    return sorted(data)


def optimized_sorting(data_size: int = 10000) -> list:
    """優化排序算法（使用 timsort 的特性）"""
    data = [random.randint(0, 1000000) for _ in range(data_size)]
    # 對於已經部分排序的數據，timsort 更快
    # 但這裡我們只是模擬
    return sorted(data, reverse=False)


if __name__ == "__main__":
    # 簡單測試
    print("效能測試範例模組")
    print(f"簡單計算結果: {simple_calculation(100)}")
    print(f"CPU 密集任務結果: {cpu_intensive_task(1000)}")
    print("測試完成")