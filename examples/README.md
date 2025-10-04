# 📚 Nova-Source 範例

這個目錄包含了 Nova-Source 工具的範例和測試腳本。

## 📁 檔案說明

### `performance_test_formatter.py`

效能測試腳本，用於測試 Markdown 格式化器的效能表現。

**用途：**

- 生成測試用的 Markdown 內容
- 基準測試格式化器的處理速度
- 評估效能優化效果

**使用方法：**

```bash
python examples/performance_test_formatter.py
```

### `nova_optimization_test.py`

Nova 工具優化效能測試腳本，測試應用優化技術後的性能提升。

**用途：**

- 測試記憶體密集任務的優化效果
- 測試 CPU 密集任務的效能
- 驗證 Markdown 格式化器的優化

**使用方法：**

```bash
python examples/nova_optimization_test.py
```

## 🔧 注意事項

這些範例檔案不會包含在 PyPI 發佈包中，它們僅供開發和測試參考。