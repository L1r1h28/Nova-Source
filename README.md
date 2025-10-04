# Nova Source

統一代碼審計和質量檢查平台

## 概述

Nova Source 是一個統一的代碼審計工具包，提供全面的代碼質量檢查、格式化和修復功能。基於 TurboCode Kit (TCK) 優化的高效能實現。

## 功能特點

- 🚀 **高效能檢查**: 基於 TCK 優化的快速代碼質量分析
- 🔧 **自動修復**: 自動修復常見的代碼問題
- 📊 **詳細統計**: 提供項目代碼統計和分析報告
- 🛠️ **靈活配置**: 支持自定義檢查規則和排除模式
- 📦 **統一打包**: 單一 pyproject.toml 配置所有子套件

## 安裝

```bash
pip install -e .
```

## 使用方法

### 快速檢查

```bash
nova-audit
```

### 詳細檢查

```bash
nova-audit --detailed
```

### 指定路徑檢查

```bash
nova-audit --path src/
```

### 指定檔案檢查

```bash
nova-audit --files file1.py file2.py
```

### 代碼分析

```bash
nova-analyze
```

### 記憶體監控

```bash
nova-sensor monitor
```

### 連續監控

```bash
nova-sensor monitor --continuous 300
```

### 工具測試

```bash
nova-sensor test
```

## 子套件

### nova_sensor

TCK 優化的開發工具模組，提供：

- 高性能記憶體監控器 (16.6x 速度提升)
- GPU 記憶體監控
- 自動記憶體清理
- 連續監控模式
- 完整的設定檔案支援

### nova_audit

代碼審計核心模組，提供：

- Ruff 代碼檢查和修復
- 代碼格式化
- 項目統計分析
- 配置管理

#### analyzer 子模組

TCK 優化的代碼分析工具，提供：

- 代碼結構分析 (AST 解析)
- 依賴關係掃描
- 複雜度評估
- 重複代碼檢測
- 高效能集合查找和記憶化快取

## 配置

編輯 `pyproject.toml` 文件來自定義檢查規則：

```toml
[tool.code-quality]
exclude_dirs = ["__pycache__", "build", "dist"]
exclude_files = ["*.pyc", "*.pyo"]
ruff_exclude_patterns = ["*.ipynb", "node_modules/*"]
```

## 開發

### 環境設置

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"
```

### 運行測試

```bash
python -m pytest
```

### 代碼格式化

```bash
black src/
ruff check src/ --fix
```

## 許可證

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！
