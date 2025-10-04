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

```bash
pip install -e .
```

## 使用

### 基本命令

| 命令 | 說明 | 範例 |
|-----|------|------|
| `nova system` | 顯示系統資訊 | `nova system` |
| `nova config --show` | 顯示當前配置 | `nova config --show` |
| `nova monitor --continuous 300` | 連續記憶體監控 300 秒 | `nova monitor --continuous 300` |
| `nova performance --module my_module.py --function my_function` | 測試特定函數效能 | `nova performance --module test.py --function main` |
| `nova audit --path src/` | 審計指定路徑代碼 | `nova audit --path src/` |

### 舊版命令 (向後相容)

| 舊命令 | 新對應命令 | 說明 |
|--------|-----------|------|
| `nova-audit` | `nova audit` | 代碼審計 |
| `nova-analyze` | `nova audit` | 代碼分析 |
| `nova-sensor` | `nova monitor` / `nova performance` | 監控和效能測試 |

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
