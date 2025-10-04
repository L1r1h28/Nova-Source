# 🚀 Nova-Source 本地使用指南

## ✅ 專案已準備就緒

Nova-Source v1.0.0 已經成功安裝並可以本地使用，無需發佈到 PyPI！

## 📋 當前狀態

✅ **本地安裝完成**

- 開發模式安裝成功
- CLI 工具正常工作
- 所有功能可用

✅ **專案結構完整**

- 模組化架構
- 完整的測試套件
- 詳細的文檔

## 🎯 立即開始使用

### 基本命令

```bash
# 顯示系統資訊
nova system

# 顯示配置
nova config --show

# 代碼質量檢查
nova audit --help

# 代碼分析
nova analyze --help

# 系統監控
nova monitor --help

# CPU 監控
nova cpu --help

# 記憶體清理
nova cleanup --help

# Markdown 處理
nova markdown --help
```

### 進階功能

```bash
# 詳細代碼審計
nova audit --detailed --path src/

# 連續系統監控 5 分鐘
nova monitor --continuous 300

# CPU 延遲檢查
nova cpu --delay-check 80

# 關鍵級別記憶體清理
nova cleanup --level critical

# 遞歸 Markdown 格式化
nova markdown . --recursive --dry-run
```

## 🛠️ 開發和測試

### 運行測試

```bash
# 運行所有測試
python -m pytest

# 運行特定測試
python -m pytest tests/markdown/
```

### 程式碼檢查

```bash
# 使用 ruff 檢查
python -m ruff check src/

# 格式化程式碼
python -m ruff format src/
```

## 📦 專案功能總覽

### 🔍 代碼審計模組

- **代碼質量檢查**: 自動檢查代碼規範和最佳實踐
- **詳細統計**: 提供項目規模、複雜度等統計信息
- **Ruff 集成**: 使用現代 Python 代碼檢查工具
- **自動修復**: 支持自動修復常見代碼問題

### 📊 系統監控

- **即時記憶體監控**: 追蹤記憶體使用情況
- **連續監控模式**: 支持長時間監控
- **CPU 效能分析**: 檢查 CPU 使用率和延遲
- **自訂監控間隔**: 靈活的監控頻率設置

### 🧹 系統清理

- **記憶體清理**: 釋放系統記憶體
- **多級清理**: 正常和關鍵級別清理選項
- **安全清理**: 不影響系統穩定性的清理操作

### 📝 Markdown 處理

- **自動格式化**: 統一 Markdown 文件格式
- **遞歸處理**: 支持目錄和子目錄批量處理
- **自訂規則**: 可配置格式化規則和行長度限制
- **備份功能**: 自動備份修改前的文件

### 🔧 配置管理

- **統一配置**: 集中式配置管理系統
- **環境變數支持**: 支持 .env 文件配置
- **靈活設定**: 可自訂各模組行為

### 📢 通知系統

- **Discord 集成**: 自動發送通知到 Discord
- **自訂通知規則**: 基於事件觸發通知
- **插件架構**: 支持擴展更多通知渠道

## 🔧 自訂配置

編輯 `.env` 檔案進行配置：

```bash
# 複製範本
cp .env.example .env

# 編輯配置
notepad .env
```

## 📚 進一步開發

### 添加新功能

1. 在 `src/nova/` 下創建新模組
2. 更新 `cli.py` 添加命令
3. 添加對應的測試

### 發佈準備

如果將來需要發佈到 PyPI：

```bash
# 重新建置
python -m build

# 使用發佈腳本
.\publish.ps1
```

## 🎉 享受使用 Nova-Source

您的統一開發工具平台已經準備就緒，開始提升您的開發效率吧！

**主要亮點：**

- 🖥️ 統一 CLI 介面
- 🔍 智慧代碼分析
- 📊 即時效能監控
- 📝 自動化文檔處理
- 📢 靈活通知系統