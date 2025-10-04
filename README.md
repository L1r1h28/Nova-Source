# Nova Source - 統一代碼審計、質量檢查和分析平台

Nova Source 是一個統一的開發工具平台，提供代碼審計、效能測試、記憶體監控和系統分析功能。

## 專案結構

```text
Nova-Source/
├── .env.example                    # 環境變數範本
├── .gitignore                      # Git 忽略規則
├── .markdownlint.json             # Markdown 格式檢查配置
├── .markdownlintignore            # Markdown 檢查忽略規則
├── LICENSE                         # 授權文件
├── pyproject.toml                  # 專案配置和依賴
├── README.md                       # 專案說明
├── SECURITY.md                     # 安全說明
├── check_security.py              # 安全檢查腳本
├── docs/                          # 文檔目錄
├── src/
│   └── nova/                      # 主套件
│       ├── cli.py                 # 命令行介面
│       ├── __init__.py            # 套件初始化
│       ├── auditing/              # 代碼審計模組
│       │   ├── analyzer.py        # 代碼分析器
│       │   ├── quality.py         # 代碼質量檢查器
│       │   └── __init__.py        # 審計模組初始化
│       ├── config/                # 配置目錄
│       │   └── examples/          # 配置範例
│       │       └── memory_config.json
│       ├── core/                  # 核心基礎設施
│       │   ├── config.py          # 統一配置管理
│       │   ├── exceptions.py      # 自訂異常層次結構
│       │   └── logging.py         # 集中式日誌系統
│       ├── markdown/              # Markdown 處理模組
│       │   ├── backup.py          # 備份功能
│       │   ├── formatter.py       # 格式化器
│       │   ├── README.md          # Markdown 模組說明
│       │   └── __init__.py        # Markdown 模組初始化
│       ├── models/                # 數據模型
│       │   └── __init__.py        # 統一數據結構和模型類
│       ├── monitoring/            # 監控模組
│       │   ├── nova_memory_monitor.py  # 記憶體監控器
│       │   └── __init__.py        # 監控模組初始化
│       ├── plugins/               # 插件系統
│       │   ├── discord.py         # Discord 通知插件
│       │   └── __init__.py        # 插件架構和基類
│       ├── tools/                 # 工具模組
│       │   ├── performance_tester.py     # 效能測試器
│       │   ├── test_memory_monitor.py    # 監控測試
│       │   └── test_performance_example.py  # 效能測試範例
│       └── utils/                 # 工具函數
│           └── __init__.py        # 實用裝飾器和助手函數
└── tests/                         # 測試套件
    └── markdown/                  # Markdown 相關測試
        ├── test_backup.py         # 備份測試
        ├── test_formatter.py      # 格式化器測試
        └── __init__.py            # 測試初始化
```

## 安裝

| 命令 | 說明 |
|-----|------|
| `pip install -e .` | 開發模式安裝 |

## 使用

### 基本命令

| 命令 | 說明 | 範例 |
|-----|------|------|
| `nova system` | 顯示系統資訊 | `nova system` |
| `nova config --show` | 顯示當前配置 | `nova config --show` |
| `nova audit` | 代碼質量檢查 | `nova audit --path src/ --detailed` |
| `nova analyze` | 代碼分析 | `nova analyze --path src/` |
| `nova monitor` | 系統監控 | `nova monitor --continuous 300` |
| `nova cpu` | CPU 監控 | `nova cpu --delay-check 80` |
| `nova cleanup` | 記憶體清理 | `nova cleanup --level critical` |
| `nova markdown` | Markdown 檔案格式化 | `nova markdown docs/ --recursive` |

### 詳細命令說明

#### 代碼審計 (`nova audit`)

| 命令 | 說明 |
|-----|------|
| `nova audit` | 基本檢查 |
| `nova audit --detailed` | 詳細檢查包含統計 |
| `nova audit --path src/nova/` | 檢查特定路徑 |
| `nova audit --files src/nova/cli.py src/nova/core/config.py` | 檢查特定檔案 |

#### 代碼分析 (`nova analyze`)

| 命令 | 說明 |
|-----|------|
| `nova analyze` | 分析當前目錄 |
| `nova analyze --path src/` | 分析特定目錄 |

#### 系統監控 (`nova monitor`)

| 命令 | 說明 |
|-----|------|
| `nova monitor` | 單次監控 |
| `nova monitor --continuous 300` | 連續監控 5 分鐘 |
| `nova monitor --continuous 300 --interval 10` | 每 10 秒監控一次 |

#### CPU 監控 (`nova cpu`)

| 命令 | 說明 |
|-----|------|
| `nova cpu` | 基本 CPU 檢查 |
| `nova cpu --delay-check 80` | 檢查 CPU 延遲 (閾值 80%) |

#### 記憶體清理 (`nova cleanup`)

| 命令 | 說明 |
|-----|------|
| `nova cleanup` | 正常清理 |
| `nova cleanup --level critical` | 關鍵清理 (更激進) |

#### Markdown 處理 (`nova markdown`)

| 命令 | 說明 |
|-----|------|
| `nova markdown README.md` | 格式化單個檔案 |
| `nova markdown docs/` | 格式化整個目錄 |
| `nova markdown . --recursive` | 遞歸處理子目錄 |
| `nova markdown docs/ --dry-run` | 僅檢查不修改 |
| `nova markdown docs/ --max-line-length 100` | 自訂行長度限制 |

## 配置

編輯 `pyproject.toml` 文件來自定義檢查規則：

```toml
[tool.code-quality]
exclude_dirs = ["__pycache__", "build", "dist"]
exclude_files = ["*.pyc", "*.pyo"]
ruff_exclude_patterns = ["*.ipynb", "node_modules/*"]
```

## 開發

項目使用以下技術棧：

- Python 3.8+
- dataclasses 用於數據模型
- pathlib 用於檔案系統操作
- psutil 用於系統監控
- GPUtil 用於 GPU 監控

### 環境設置

| 命令 | 說明 |
|-----|------|
| `python -m venv venv` | 創建虛擬環境 |
| `venv\Scripts\activate` | 啟動虛擬環境 (Windows) |
| `pip install -e ".[dev]"` | 安裝開發依賴 |

### 運行測試

| 命令 | 說明 |
|-----|------|
| `python -m pytest` | 運行所有測試 |

### 代碼格式化

| 命令 | 說明 |
|-----|------|
| `black src/` | 使用 Black 格式化代碼 |
| `ruff check src/ --fix` | 使用 Ruff 檢查並修復代碼 |

## 📦 專案功能總覽

### 🔍 代碼審計模組

| 功能 | 說明 |
|-----|------|
| 代碼質量檢查 | 自動檢查代碼規範和最佳實踐 |
| 詳細統計 | 提供項目規模、複雜度等統計信息 |
| Ruff 集成 | 使用現代 Python 代碼檢查工具 |
| 自動修復 | 支持自動修復常見代碼問題 |

### 📊 系統監控

| 功能 | 說明 |
|-----|------|
| 即時記憶體監控 | 追蹤記憶體使用情況 |
| 連續監控模式 | 支持長時間監控 |
| CPU 效能分析 | 檢查 CPU 使用率和延遲 |
| 自訂監控間隔 | 靈活的監控頻率設置 |

### 🧹 系統清理

| 功能 | 說明 |
|-----|------|
| 記憶體清理 | 釋放系統記憶體 |
| 多級清理 | 正常和關鍵級別清理選項 |
| 安全清理 | 不影響系統穩定性的清理操作 |

### 📝 Markdown 處理

| 功能 | 說明 |
|-----|------|
| 自動格式化 | 統一 Markdown 文件格式 |
| 遞歸處理 | 支持目錄和子目錄批量處理 |
| 自訂規則 | 可配置格式化規則和行長度限制 |
| 備份功能 | 自動備份修改前的文件 |

### 🔧 配置管理

| 功能 | 說明 |
|-----|------|
| 統一配置 | 集中式配置管理系統 |
| 環境變數支持 | 支持 .env 文件配置 |
| 靈活設定 | 可自訂各模組行為 |

### 📢 通知系統

| 功能 | 說明 |
|-----|------|
| Discord 集成 | 自動發送通知到 Discord |
| 自訂通知規則 | 基於事件觸發通知 |
| 插件架構 | 支持擴展更多通知渠道 |
