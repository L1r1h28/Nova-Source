#!/usr/bin/env python3
"""
Nova 腳本優化性能測試腳本
測試應用優化技術後的性能提升
"""

import sys
import time
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent / "Nova-Source"
sys.path.insert(0, str(project_root))

try:
    from nova.tools.performance_tester import NovaPerformanceTester
    from nova.tools.test_performance_example import memory_intensive_task, cpu_intensive_task
    from nova.markdown.formatter import MarkdownFormatter
except ImportError as e:
    print(f"匯入錯誤: {e}")
    sys.exit(1)

def test_optimized_functions():
    """測試優化後的函數性能"""
    print("🚀 開始 Nova 腳本優化性能測試")
    print("=" * 50)

    tester = NovaPerformanceTester()

    # 測試記憶體密集任務 (已優化為列表推導式)
    print("\n📊 測試記憶體密集任務 (列表推導式優化)")
    result = tester.benchmark_function(
        memory_intensive_task,
        iterations=5
    )
    print(f"平均執行時間: {result['execution_time']['mean']:.6f} 秒")
    print(f"平均記憶體使用: {result['memory_usage']['mean'] / (1024*1024):.2f} MB")
    print(f"平均 CPU 使用率: {result['cpu_usage']['mean']:.2f}%")

    # 測試 CPU 密集任務
    print("\n⚡ 測試 CPU 密集任務")
    result = tester.benchmark_function(
        cpu_intensive_task,
        iterations=3
    )
    print(f"平均執行時間: {result['execution_time']['mean']:.6f} 秒")
    print(f"平均記憶體使用: {result['memory_usage']['mean'] / (1024*1024):.2f} MB")
    print(f"平均 CPU 使用率: {result['cpu_usage']['mean']:.2f}%")

    # 測試 Markdown 格式化器 (已優化)
    print("\n📝 測試 Markdown 格式化器 (字符串優化)")
    formatter = MarkdownFormatter()

    # 創建測試內容
    test_content = "# 測試標題\n\n這是測試內容   \n\n- 項目1\n- 項目2\n\n```python\ncode block\n```\n\n結束。   "

    result = tester.benchmark_function(
        formatter._fix_trailing_spaces,
        10,
        test_content
    )
    print(f"平均執行時間: {result['execution_time']['mean']:.6f} 秒")
    print(f"平均記憶體使用: {result['memory_usage']['mean'] / (1024*1024):.2f} MB")
    print(f"平均 CPU 使用率: {result['cpu_usage']['mean']:.2f}%")

    print("\n✅ 所有性能測試完成！")
    print("=" * 50)

if __name__ == "__main__":
    test_optimized_functions()