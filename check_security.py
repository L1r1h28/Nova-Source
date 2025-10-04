#!/usr/bin/env python3
"""
檢查私人資料安全的腳本
確保沒有意外提交敏感信息
"""

import re
from pathlib import Path


def check_sensitive_files():
    """檢查是否存在敏感文件"""
    sensitive_patterns = [
        r"\.env$",
        r"\.env\.[a-zA-Z]+$",
        r".*secret.*",
        r".*credential.*",
        r".*api.*key.*",
        r".*token.*",
        r".*password.*",
        r".*private.*",
        r".*\.db$",
        r".*\.sqlite.*",
        r".*auth\.json",
        r".*config\.local\.json",
    ]

    # 排除範本文件
    exclude_patterns = [r".*\.example$", r".*\.template$", r".*\.sample$"]

    project_root = Path(__file__).parent
    found_sensitive = []

    for file_path in project_root.rglob("*"):
        if file_path.is_file():
            file_name = file_path.name

            # 檢查是否為範本文件
            is_template = any(
                re.search(pattern, file_name, re.IGNORECASE)
                for pattern in exclude_patterns
            )
            if is_template:
                continue

            # 檢查是否為敏感文件
            is_sensitive = any(
                re.search(pattern, file_name, re.IGNORECASE)
                for pattern in sensitive_patterns
            )
            if is_sensitive:
                found_sensitive.append(str(file_path.relative_to(project_root)))

    return found_sensitive


def check_gitignore_coverage():
    """檢查 .gitignore 是否涵蓋所有必要的規則"""
    required_rules = [
        ".env",
        ".env.*",
        "*.log",
        "secrets.json",
        "credentials/",
        "private/",
        "__pycache__/",
        "*.db",
        "*.sqlite3",
    ]

    gitignore_path = Path(__file__).parent / ".gitignore"

    if not gitignore_path.exists():
        return False, "缺少 .gitignore 文件"

    with open(gitignore_path, encoding="utf-8") as f:
        gitignore_content = f.read()

    missing_rules = [rule for rule in required_rules if rule not in gitignore_content]

    return len(missing_rules) == 0, missing_rules


def main():
    """主檢查函數"""
    print("🔍 檢查私人資料安全...")

    # 檢查敏感文件
    sensitive_files = check_sensitive_files()
    if sensitive_files:
        print("⚠️  發現潛在的敏感文件:")
        for file in sensitive_files:
            print(f"   - {file}")
        print("請確保這些文件已被正確忽略或移除!")
    else:
        print("✅ 未發現敏感文件")

    # 檢查 .gitignore
    gitignore_ok, missing_rules = check_gitignore_coverage()
    if not gitignore_ok:
        print("⚠️  .gitignore 缺少以下規則:")
        for rule in missing_rules:
            print(f"   - {rule}")
    else:
        print("✅ .gitignore 配置完整")

    if sensitive_files or not gitignore_ok:
        print("\n❌ 安全檢查失敗!")
        return 1
    else:
        print("\n✅ 安全檢查通過!")
        return 0


if __name__ == "__main__":
    exit(main())
