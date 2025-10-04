#!/usr/bin/env python3
"""
Nova 記憶體監控器測試腳本
Nova Memory Monitor Test Script
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from nova_memory_monitor import NovaMemoryMonitor, create_monitor_with_config, monitor_memory_continuous

def test_basic_functionality():
    """測試基本功能"""
    print("🧪 測試基本功能")

    # 創建監控器
    monitor = NovaMemoryMonitor()

    # 測試統計獲取
    stats = monitor.get_memory_stats()
    print(f"✅ 記憶體統計獲取成功: {stats.percentage:.1f}% 使用率")

    # 測試打印功能
    monitor.print_stats()

    # 測試清理功能
    cleanup_level = monitor.should_cleanup()
    if cleanup_level:
        duration = monitor.cleanup_memory(cleanup_level)
        print(f"✅ 清理完成，耗時: {duration:.3f} 秒")
    else:
        print("✅ 無需清理")

    return True

def test_config_loading():
    """測試設定載入功能"""
    print("\n🧪 測試設定載入功能")

    try:
        # 從設定檔案創建監控器
        monitor = create_monitor_with_config("memory_config.json")
        print("✅ 設定檔案載入成功")

        # 驗證設定
        stats = monitor.get_memory_stats()
        print(f"✅ 設定應用成功 - 閾值: {monitor.thresholds.normal:.1%}")

        return True
    except Exception as e:
        print(f"❌ 設定載入測試失敗: {e}")
        return False

def test_continuous_monitoring():
    """測試連續監控功能 (短時間測試)"""
    print("\n🧪 測試連續監控功能")

    try:
        monitor = NovaMemoryMonitor()
        # 只監控 10 秒，每 3 秒檢查一次
        result = monitor_memory_continuous(monitor, interval=3, duration=10)

        print("✅ 連續監控測試成功")
        print(f"   監控持續時間: {result['monitoring_duration']:.1f} 秒")
        print(f"   檢查次數: {result['check_count']}")
        print(f"   清理次數: {result['cleanup_count']}")

        return True
    except Exception as e:
        print(f"❌ 連續監控測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 Nova 記憶體監控器完整測試套件\n")

    tests = [
        ("基本功能測試", test_basic_functionality),
        ("設定載入測試", test_config_loading),
        ("連續監控測試", test_continuous_monitoring)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通過")
            else:
                print(f"❌ {test_name} - 失敗")
        except Exception as e:
            print(f"❌ {test_name} - 異常: {e}")

    print(f"\n📊 測試結果: {passed}/{total} 通過")

    if passed == total:
        print("🎉 所有測試通過！Nova 記憶體監控器準備就緒！")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())