# 安全指南

## 私人資料保護

本項目嚴格保護私人資料和敏感信息。請遵循以下指南：

### 🔒 敏感文件類型

以下文件類型**絕對不能**提交到版本控制：

- `.env*` - 環境變數文件
- `*secret*` - 包含密鑰的文件
- `*credential*` - 憑證文件
- `*api*key*` - API 金鑰
- `*token*` - 認證令牌
- `*.db`, `*.sqlite*` - 數據庫文件
- `*auth.json` - 認證配置
- `config.local.json` - 本地配置

### 🛡️ 安全檢查

運行安全檢查腳本確保沒有意外提交敏感信息：

```bash
python check_security.py
```

### 📝 最佳實踐

1. **永遠不要**在代碼中硬編碼密鑰或憑證
2. **使用環境變數**存儲敏感配置
3. **定期檢查** `.gitignore` 規則
4. **在提交前**運行安全檢查
5. **使用 `.env.example`** 作為範本文件

### 🔧 環境變數範例

創建 `.env.example` 文件作為範本：

```bash
# 複製此文件為 .env 並填入實際值
DISCORD_WEBHOOK_URL=your_webhook_url_here
API_KEY=your_api_key_here
DATABASE_URL=your_database_url_here
```

### 🚨 緊急情況

如果意外提交了敏感信息：

1. **立即刪除**相關提交
2. **輪換所有受影響的密鑰**
3. **通知相關人員**
4. **更新 `.gitignore` 規則**

### 📞 聯繫

如有安全疑慮，請立即聯繫項目維護者。
