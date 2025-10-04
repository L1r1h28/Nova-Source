# Nova-Source PyPI 發佈腳本

Write-Host "🚀 Nova-Source v1.0.0 PyPI 發佈工具" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Yellow

# 檢查發佈檔案
Write-Host "`n📦 檢查發佈檔案..." -ForegroundColor Green
if (!(Test-Path "dist\nova_source-1.0.0-py3-none-any.whl") -or !(Test-Path "dist\nova_source-1.0.0.tar.gz")) {
    Write-Host "❌ 發佈檔案不存在！請先運行 'python -m build'" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 發佈檔案存在" -ForegroundColor Green

# 檢查 twine
Write-Host "`n🔧 檢查 twine..." -ForegroundColor Green
try {
    $twineVersion = python -m twine --version 2>$null
    Write-Host "✅ Twine 已安裝: $twineVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Twine 未安裝！運行 'pip install twine'" -ForegroundColor Red
    exit 1
}

# 選擇發佈目標
Write-Host "`n🎯 選擇發佈目標:" -ForegroundColor Cyan
Write-Host "1. 測試 PyPI (test.pypi.org) - 推薦先測試" -ForegroundColor Yellow
Write-Host "2. 正式 PyPI (pypi.org) - 正式發佈" -ForegroundColor Green
$choice = Read-Host "`n請選擇 (1 或 2)"

if ($choice -eq "1") {
    $repository = "testpypi"
    $url = "https://test.pypi.org/"
    Write-Host "`n🧪 將發佈到測試 PyPI" -ForegroundColor Yellow
} elseif ($choice -eq "2") {
    $repository = "pypi"
    $url = "https://pypi.org/"
    Write-Host "`n🚀 將發佈到正式 PyPI" -ForegroundColor Green
} else {
    Write-Host "❌ 無效選擇" -ForegroundColor Red
    exit 1
}

# 獲取憑證
Write-Host "`n🔐 憑證設置:" -ForegroundColor Cyan
Write-Host "需要 PyPI API Token (不是密碼！)" -ForegroundColor Yellow
Write-Host "獲取方式:" -ForegroundColor White
Write-Host "1. 訪問: https://pypi.org/manage/account/token/" -ForegroundColor White
Write-Host "2. 創建新的 API Token" -ForegroundColor White
Write-Host "3. 複製 token (格式: pypi-xxx...)" -ForegroundColor White

$apiToken = Read-Host "`n請輸入您的 PyPI API Token" -AsSecureString
$apiTokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiToken))

if ([string]::IsNullOrEmpty($apiTokenPlain)) {
    Write-Host "❌ Token 不能為空" -ForegroundColor Red
    exit 1
}

# 設置環境變數
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = $apiTokenPlain

# 最終確認
Write-Host "`n⚠️  最終確認:" -ForegroundColor Red
Write-Host "將上傳以下檔案到 $url :" -ForegroundColor White
Get-ChildItem dist/ | Format-Table Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB, 1)}}
Write-Host "`n專案: Nova-Source v1.0.0" -ForegroundColor Cyan
Write-Host "目標: $repository" -ForegroundColor Cyan

$confirm = Read-Host "`n確認發佈？(y/N)"
if ($confirm -notin @("y", "Y", "yes", "Yes", "YES")) {
    Write-Host "❌ 發佈已取消" -ForegroundColor Yellow
    exit 0
}

# 執行發佈
Write-Host "`n📤 開始上傳..." -ForegroundColor Green
try {
    if ($repository -eq "testpypi") {
        python -m twine upload --repository testpypi dist/*
    } else {
        python -m twine upload dist/*
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 發佈成功！" -ForegroundColor Green
        Write-Host "查看您的套件: $url/project/nova-source/" -ForegroundColor Cyan

        # 驗證安裝
        Write-Host "`n🔍 測試安裝..." -ForegroundColor Yellow
        if ($repository -eq "testpypi") {
            pip install --index-url https://test.pypi.org/simple/ nova-source --upgrade
        } else {
            pip install nova-source --upgrade
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 安裝測試成功！" -ForegroundColor Green
            nova --version
        } else {
            Write-Host "⚠️ 安裝測試失敗，請手動測試" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n❌ 發佈失敗！" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ 發佈過程中發生錯誤: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}