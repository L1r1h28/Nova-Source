#!/usr/bin/env python3
"""
效能測試腳本 - 測試 Markdown 格式化器的效能
"""

import time
import os
from pathlib import Path

# 測試資料生成
def generate_test_markdown(num_lines=1000):
    """生成測試用的 Markdown 內容"""
    lines = []

    # 添加各種 Markdown 元素
    for i in range(num_lines):
        if i % 50 == 0:
            lines.append(f"# 標題 {i//50}")
            lines.append("")
        elif i % 10 == 0:
            lines.append(f"## 子標題 {i}")
            lines.append("")
        elif i % 5 == 0:
            lines.append(f"- 列表項目 {i}")
        else:
            # 生成長行來測試行長度處理
            line = f"這是第 {i} 行的內容，包含一些文字來測試格式化器的效能。" * 3
            if len(line) > 100:
                line = line[:100] + "..."  # 截斷長行
            lines.append(line)

        # 添加一些空行
        if i % 20 == 19:
            lines.append("")

    return "\n".join(lines)

def benchmark_formatter(formatter_class, content, iterations=5):
    """效能基準測試"""
    print(f"🔬 測試 {formatter_class.__name__} 效能...")

    # 預熱
    formatter = formatter_class()
    formatter.format_file = lambda x: formatter._fix_trailing_spaces(content)

    # 實際測試
    times = []
    result = None
    for i in range(iterations):
        start_time = time.perf_counter()
        result = formatter._fix_trailing_spaces(content)
        end_time = time.perf_counter()
        times.append(end_time - start_time)
        print(f"   迭代 {i+1}: {end_time - start_time:.3f} 秒")

    avg_time = sum(times) / len(times)
    print(f"   平均時間: {avg_time:.4f} 秒")
    return avg_time, result

def main():
    """主測試函數"""
    print("🚀 Markdown 格式化器效能測試")
    print("=" * 50)

    # 生成測試資料
    print("📝 生成測試資料...")
    test_content = generate_test_markdown(2000)
    print(f"   生成 {len(test_content.split(chr(10)))} 行測試內容")

    # 測試原始版本
    from nova.markdown.formatter import MarkdownFormatter
    original_time, original_result = benchmark_formatter(MarkdownFormatter, test_content)

    print("\n✅ 效能測試完成")
    print(f"   平均處理時間: {original_time:.4f} 秒")
if __name__ == "__main__":
    main()