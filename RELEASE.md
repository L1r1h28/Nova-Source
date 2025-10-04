# Nova-Source 發佈指南

## 版本發佈流程

### 1. 準備階段

- [x] 清理專案結構和臨時檔案
- [x] 更新文檔和配置
- [x] 運行測試套件
- [x] 通過安全檢查
- [x] 建置發佈檔案

### 2. 版本標籤

```bash
git tag -a v1.0.0 -m "Release Nova-Source v1.0.0"
git push origin v1.0.0
```

### 3. 上傳到 PyPI

#### 測試 PyPI (推薦先測試)

```bash
# 安裝 twine (如果尚未安裝)
pip install twine

# 上傳到測試 PyPI
twine upload --repository testpypi dist/*
```

#### 正式 PyPI

```bash
# 上傳到正式 PyPI
twine upload dist/*
```

### 4. 驗證安裝

```bash
# 測試安裝
pip install nova-source

# 驗證 CLI
nova --help

# 運行基本功能測試
nova audit --help
nova monitor --help
```

## 發佈檢查清單

- [x] 所有測試通過
- [x] 安全檢查通過
- [x] 文檔更新完整
- [x] 版本號碼正確
- [x] 依賴聲明完整
- [x] 發佈檔案建置成功
- [x] Twine 檢查通過
- [ ] Git 標籤推送完成
- [ ] PyPI 上傳成功
- [ ] 安裝測試通過

## 版本資訊

### Nova-Source v1.0.0

統一代碼審計、質量檢查和分析平台

#### 主要功能

- 🔍 代碼審計和質量檢查
- 📊 效能測試和記憶體監控
- 📝 Markdown 處理和格式化
- 📢 Discord 通知插件
- 🖥️ 統一的 CLI 介面

#### 技術特點

- 🏗️ 模組化架構設計
- ✅ 完整的測試覆蓋
- 📚 詳細的文檔說明
- 📦 符合現代 Python 打包標準

#### 安裝方式

```bash
pip install nova-source
```

#### 使用方式

```bash
nova --help
```