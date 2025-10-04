# Nova Source Markdown Tools

自動化調整 Markdown 檔案以符合 markdownlint 規範的工具，並提供完整的備份和恢復功能。

## 功能特點

### Markdown 格式化

- **自動修復**: 自動修### 命令行參數

#### 格式化命令參數

- `path`: 要格式化的檔案或目錄路徑（必需）
- `-r, --recursive`: 遞歸處理子目錄
- `-v, --verbose`: 詳細輸出
- `--rules`: 要修復的特定規則列表
- `--exclude`: 要排除的檔案模式列表
- `--dry-run`: 僅顯示更改，不實際修改檔案

#### 備份命令參數

- `path`: 要備份的檔案或目錄路徑（必需）
- `--name`: 備份名稱（可選）
- `--no-incremental`: 停用增量備份
- `--backup-dir`: 備份目錄路徑（預設: ./backups）

#### 恢復命令參數

- `backup_name`: 要恢復的備份名稱（必需）
- `--restore-path`: 恢復目標路徑（可選）
- `--backup-dir`: 備份目錄路徑（預設: ./backups）

#### 清理命令參數

- `--keep-days`: 保留天數（預設: 30）
- `--keep-count`: 保留數量（預設: 10）
- `--backup-dir`: 備份目錄路徑（預設: ./backups）

#### 通用參數

- `-v, --verbose`: 詳細輸出（適用於所有命令）kdownlint 錯誤
- **靈活配置**: 支持指定特定規則進行修復
- **批次處理**: 支持處理單個檔案或整個目錄
- **遞歸處理**: 可選的遞歸處理子目錄
- **排除模式**: 支持排除特定檔案模式
- **詳細日誌**: 提供詳細的處理結果統計

### 備份管理

- **增量備份**: 只備份已修改的檔案
- **完整備份**: 備份整個目錄結構
- **版本控制**: 時間戳版本控制和命名
- **恢復功能**: 一鍵恢復到指定版本
- **自動清理**: 自動清理舊備份以節省空間
- **清單管理**: 詳細的備份清單和統計資訊

## 支持的規則

目前支持修復以下 markdownlint 規則：

- **MD009**: 行尾空格
- **MD010**: 硬製表符
- **MD012**: 多個連續空行
- **MD018**: atx 樣式標題井號後無空格
- **MD019**: atx 樣式標題井號後多個空格
- **MD022**: 標題周圍應有空行
- **MD023**: 標題必須從行首開始
- **MD032**: 清單周圍應有空行
- **MD040**: 程式碼區塊應指定語言
- **MD047**: 檔案應以單個換行符結束

## 安裝

```bash
# 安裝 Nova Source 及其 markdown 依賴
pip install -e ".[markdown]"
```

## 使用方法

### 格式化命令

#### 基本用法

```bash
# 格式化單個檔案
nova-markdown format path/to/file.md

# 格式化整個目錄
nova-markdown format path/to/directory/

# 遞歸處理子目錄
nova-markdown format -r path/to/directory/
```

#### 進階選項

```bash
# 指定特定規則進行修復
nova-markdown format --rules MD009 MD012 MD022 path/to/file.md

# 排除特定檔案模式
nova-markdown format --exclude "*.bak" "*/temp/*" path/to/directory/

# 詳細輸出
nova-markdown format -v path/to/file.md

# 僅顯示將要進行的更改（不實際修改）
nova-markdown format --dry-run path/to/file.md
```

### 備份命令

#### 創建備份

```bash
# 備份單個檔案
nova-markdown backup path/to/file.md

# 備份整個目錄
nova-markdown backup path/to/directory/

# 指定備份名稱
nova-markdown backup --name my_backup path/to/directory/

# 停用增量備份（強制完整備份）
nova-markdown backup --no-incremental path/to/directory/

# 指定備份目錄
nova-markdown backup --backup-dir /path/to/backups path/to/directory/
```

#### 列出備份

```bash
# 列出所有備份
nova-markdown list

# 指定備份目錄
nova-markdown list --backup-dir /path/to/backups
```

#### 恢復備份

```bash
# 恢復到原始位置
nova-markdown restore backup_name

# 恢復到指定位置
nova-markdown restore backup_name --restore-path /path/to/restore/

# 指定備份目錄
nova-markdown restore backup_name --backup-dir /path/to/backups
```

#### 清理備份

```bash
# 清理舊備份（保留最近 10 個，30 天內的）
nova-markdown cleanup

# 自定義保留規則
nova-markdown cleanup --keep-count 5 --keep-days 7

# 指定備份目錄
nova-markdown cleanup --backup-dir /path/to/backups
```

### 命令行參數

- `path`: 要格式化的檔案或目錄路徑（必需）
- `-r, --recursive`: 遞歸處理子目錄
- `-v, --verbose`: 詳細輸出
- `--rules`: 要修復的特定規則列表
- `--exclude`: 要排除的檔案模式列表
- `--dry-run`: 僅顯示更改，不實際修改檔案

## 範例

### 格式化專案文檔

```bash
# 格式化整個 docs 目錄，排除臨時檔案
nova-markdown format -r --exclude "*.tmp" "*/backup/*" docs/
```

### 修復特定問題

```bash
# 只修復行尾空格和多個空行問題
nova-markdown format --rules MD009 MD012 README.md
```

### 備份專案文檔

```bash
# 創建專案文檔備份
nova-markdown backup --name "docs_backup_$(date +%Y%m%d)" docs/

# 增量備份（只備份修改的檔案）
nova-markdown backup docs/
```

### 管理備份

```bash
# 查看所有可用備份
nova-markdown list

# 恢復到特定版本
nova-markdown restore docs_backup_20231001 --restore-path docs_restored/

# 清理舊備份（保留最近 5 個）
nova-markdown cleanup --keep-count 5
```

### 批次處理多個專案

```bash
# 處理多個專案的文檔目錄
for project in project1 project2 project3; do
    nova-markdown format -r "${project}/docs/"
    nova-markdown backup --name "${project}_backup" "${project}/docs/"
done
```

## 整合到 CI/CD

可以將此工具整合到 CI/CD 流程中：

```yaml
# .github/workflows/markdown-workflow.yml
name: Markdown Workflow
on: [push, pull_request]

jobs:
  markdown-process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[markdown]"
      - name: Format markdown files
        run: |
          nova-markdown format -r docs/
      - name: Create backup before formatting
        run: |
          nova-markdown backup --name "pre_format_$(date +%Y%m%d_%H%M%S)" docs/
      - name: Check for formatting changes
        run: |
          if [ -n "$(git status --porcelain docs/)" ]; then
            echo "Markdown files were formatted. Please review and commit the changes."
            nova-markdown list  # 顯示可用備份
            exit 1
          fi
      - name: Cleanup old backups
        run: |
          nova-markdown cleanup --keep-count 5
```

### 自動備份策略

```yaml
# 每日備份工作流程
name: Daily Markdown Backup
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨 2 點
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[markdown]"
      - name: Create daily backup
        run: |
          nova-markdown backup --name "daily_$(date +%Y%m%d)" docs/
      - name: Cleanup old backups
        run: |
          nova-markdown cleanup --keep-days 30 --keep-count 10
```

## 開發

### 添加新規則

要添加對新 markdownlint 規則的支持：

1. 在 `formatter.py` 的 `MarkdownFormatter.rules` 字典中添加新規則
2. 實現對應的修復方法 `_fix_rule_name`
3. 更新文檔

### 測試

```bash
# 運行測試
python -m pytest tests/markdown/

# 測試特定規則
python -c "
from nova.markdown.formatter import MarkdownFormatter
formatter = MarkdownFormatter()
result = formatter.format_file('test.md', ['MD009'])
print('Formatted:', result)
"
```

## 授權

MIT License
