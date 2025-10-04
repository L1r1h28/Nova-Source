#!/usr/bin/env python3
"""
統一代碼質量檢查工具
整合快速檢查和詳細檢查功能

使用方法:
  nova-audit                    # 快速檢查模式 (當前目錄)
  nova-audit --detailed         # 詳細檢查模式 (包含統計)
  nova-audit --path src/        # 指定路徑檢查
  nova-audit --files file1.py file2.py  # 指定檔案檢查
  nova-audit --help             # 顯示幫助信息
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python < 3.11
    except ImportError:
        print("錯誤：需要安裝 tomli (pip install tomli)")
        sys.exit(1)


class CodeQualityConfig:
    """配置管理類"""
    _config_cache = {}  # TCK優化：配置快取，避免重複檔案I/O

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / "pyproject.toml"
        self.config = self._load_config_cached()

    def _load_config_cached(self) -> dict:
        """載入TOML配置 (TCK優化：使用快取避免重複I/O)"""
        config_path_str = str(self.config_path)

        if config_path_str not in self._config_cache:
            if not self.config_path.exists():
                print(f"⚠️  配置文件不存在: {self.config_path}")
                self._config_cache[config_path_str] = self._get_default_config()
            else:
                try:
                    with open(self.config_path, "rb") as f:
                        self._config_cache[config_path_str] = tomllib.load(f)
                except Exception as e:
                    print(f"⚠️  載入配置失敗: {e}")
                    self._config_cache[config_path_str] = self._get_default_config()

        return self._config_cache[config_path_str]

    def _get_default_config(self) -> dict:
        """獲取默認配置"""
        return {
            "tool": {
                "code-quality": {
                    "root_dir": ".",
                    "include_dirs": [],
                    "exclude_dirs": [
                        ".git",
                        "__pycache__",
                        "build",
                        "dist",
                        "node_modules",
                        ".venv",
                        "venv",
                        ".env",
                        ".pytest_cache",
                        ".mypy_cache",
                        ".ruff_cache",
                    ],
                    "exclude_files": [
                        "*.pyc",
                        "*.pyo",
                        "*.pyd",
                        ".DS_Store",
                        "Thumbs.db",
                    ],
                    "ruff_exclude_patterns": [
                        "*.ipynb",
                        "node_modules/*",
                        "frontend/*",
                        "frontend/**",
                        "*.egg-info/**",
                        ".git/**",
                    ],
                    "format_candidates": ["src", "tests", "docs", "scripts", "tools"],
                    "stats": {"show_all_files": False, "max_files_display": 20},
                }
            }
        }

    def get(self, key: str, default=None):
        """獲取配置值"""
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default


class CodeQualityChecker:
    """代碼質量檢查器"""

    def __init__(
        self,
        config: CodeQualityConfig,
        paths: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
    ):
        self.config = config
        self.specified_paths = [Path(p) for p in (paths or [])]
        self.specified_files = [Path(f) for f in (files or [])]
        root_dir_str = config.get("tool.code-quality.root_dir", ".")
        if isinstance(root_dir_str, str):
            self.root_dir = Path(root_dir_str).resolve()
        else:
            self.root_dir = Path(".").resolve()

    def get_python_files(self) -> List[Path]:
        """獲取要檢查的Python文件"""
        if self.specified_files:
            # 指定檔案模式
            return [
                f.resolve()
                for f in self.specified_files
                if f.exists() and f.suffix == ".py"
            ]

        # 確定要掃描的目錄
        if self.specified_paths:
            scan_dirs = [p.resolve() for p in self.specified_paths if p.exists()]
        else:
            include_dirs = self.config.get("tool.code-quality.include_dirs", [])
            if include_dirs:
                scan_dirs = [
                    self.root_dir / d
                    for d in include_dirs
                    if (self.root_dir / d).exists()
                ]
            else:
                scan_dirs = [self.root_dir]

        # 掃描Python文件
        py_files = []
        exclude_dirs_val = self.config.get("tool.code-quality.exclude_dirs", [])
        exclude_files_val = self.config.get("tool.code-quality.exclude_files", [])
        exclude_dirs = set(
            exclude_dirs_val if isinstance(exclude_dirs_val, list) else []
        )
        # TCK優化：將排除檔案模式轉換為集合以實現O(1)查找
        exclude_files_set = set(
            exclude_files_val if isinstance(exclude_files_val, list) else []
        )

        for scan_dir in scan_dirs:
            for root, dirs, files in os.walk(scan_dir):
                # 過濾目錄
                dirs[:] = [
                    d for d in dirs if d not in exclude_dirs and not d.startswith(".")
                ]

                for file in files:
                    if file.endswith(".py") and file not in exclude_files_set:
                        file_path = Path(root) / file
                        # TCK優化：使用集合查找替代線性查找，避免O(n)路徑匹配
                        should_exclude = False
                        for pattern in exclude_files_set:
                            if file_path.match(pattern):
                                should_exclude = True
                                break
                        if not should_exclude:
                            py_files.append(file_path)
        return py_files

    def _get_ruff_targets(self) -> List[str]:
        """獲取Ruff檢查目標"""
        if self.specified_files:
            return [str(f) for f in self.specified_files]
        elif self.specified_paths:
            return [str(p) for p in self.specified_paths]
        else:
            return ["."]

    def _get_ruff_exclude_str(self) -> str:
        """獲取Ruff排除字符串"""
        exclude_patterns_val = self.config.get(
            "tool.code-quality.ruff_exclude_patterns", []
        )
        exclude_patterns = (
            exclude_patterns_val if isinstance(exclude_patterns_val, list) else []
        )
        return ";".join(exclude_patterns)

    def run_command(
        self,
        cmd: str,
        description: str,
        show_output: bool = True,
        cwd: Optional[Path] = None,
    ) -> bool:
        """運行命令並顯示結果"""
        print(f"🔍 {description}")
        try:
            if cwd is None:
                cwd = self.root_dir

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
            )

            if result.returncode == 0:
                print("✅ 通過")
                if show_output and result.stdout.strip():
                    print(result.stdout)
            else:
                print("❌ 失敗")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return False
        except Exception as e:
            print(f"💥 錯誤: {e}")
            return False
        return True

    def get_project_stats(self) -> dict:
        """獲取項目統計信息"""
        print("\n📊 項目統計信息:")

        py_files = self.get_python_files()

        print(f"   • Python 文件總數: {len(py_files)}")

        show_all = self.config.get("tool.code-quality.stats.show_all_files", False)
        max_display_val = self.config.get(
            "tool.code-quality.stats.max_files_display", 20
        )
        max_display = max_display_val if isinstance(max_display_val, int) else 20

        if show_all or len(py_files) <= max_display:
            for f in py_files:
                try:
                    rel_path = f.relative_to(self.root_dir)
                    print(f"     - {rel_path}")
                except ValueError:
                    print(f"     - {f}")
        elif len(py_files) > max_display:
            for f in py_files[:max_display]:
                try:
                    rel_path = f.relative_to(self.root_dir)
                    print(f"     - {rel_path}")
                except ValueError:
                    print(f"     - {f}")
            print(f"     ... 還有 {len(py_files) - max_display} 個文件")

        # 統計代碼行數
        total_lines = 0
        for py_file in py_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)
            except Exception:
                pass

        stats = {
            "py_files_count": len(py_files),
            "total_lines": total_lines,
            "avg_lines_per_file": total_lines / len(py_files) if py_files else 0,
        }

        print(f"   • 總代碼行數: {stats['total_lines']}")
        print(f"   • 平均每文件行數: {stats['avg_lines_per_file']:.1f}")

        return stats

    def run_ruff_check_and_fix(self) -> bool:
        """運行 Ruff 檢查和修復"""
        exclude_str = self._get_ruff_exclude_str()
        targets = self._get_ruff_targets()

        cmd = f"python -m ruff check --fix --extend-exclude '{exclude_str}' {' '.join(targets)}"
        return self.run_command(cmd, "Ruff 代碼檢查和修復")

    def run_ruff_format(self, check_only: bool = False) -> bool:
        """運行 Ruff 格式化"""
        exclude_str = "*.ipynb;node_modules/*;frontend/*;frontend/**"

        # 確定格式化目標
        if self.specified_files:
            targets = [str(f) for f in self.specified_files]
        else:
            format_candidates = self.config.get(
                "tool.code-quality.format_candidates", []
            )
            targets = []

            if self.specified_paths:
                # 如果指定了路徑，使用這些路徑
                for path in self.specified_paths:
                    if path.exists():
                        targets.append(str(path))
            else:
                # 否則檢查候選目錄
                if isinstance(format_candidates, list):
                    for candidate in format_candidates:
                        candidate_path = self.root_dir / candidate
                        if candidate_path.exists():
                            targets.append(str(candidate_path))

            if not targets:
                print("⚠️  跳過格式化：沒有可格式化的目標目錄。")
                return True

        check_flag = " --check" if check_only else ""
        cmd = f"python -m ruff format --exclude '{exclude_str}'{check_flag} {' '.join(targets)}"

        action = "格式化驗證" if check_only else "代碼格式化"
        return self.run_command(cmd, action)

    def run_final_verification(self) -> bool:
        """運行最終驗證"""
        exclude_str = self._get_ruff_exclude_str()
        targets = self._get_ruff_targets()

        cmd = (
            f"python -m ruff check --extend-exclude '{exclude_str}' {' '.join(targets)}"
        )
        return self.run_command(cmd, "最終驗證")


def quick_check(checker: CodeQualityChecker) -> int:
    """快速檢查模式"""
    print("🚀 開始快速代碼質量檢查...")

    # 1. Ruff 檢查和修復
    if not checker.run_ruff_check_and_fix():
        return 1

    # 2. 代碼格式化
    if not checker.run_ruff_format():
        return 1

    # 3. 最終驗證
    if not checker.run_final_verification():
        return 1

    print("🎉 所有檢查通過！")
    return 0


def detailed_check(checker: CodeQualityChecker) -> int:
    """詳細檢查模式"""
    print("🔍 開始詳細代碼質量檢查...")

    # 顯示項目統計
    checker.get_project_stats()

    # 1. Ruff 檢查和修復
    if not checker.run_ruff_check_and_fix():
        return 1

    # 2. 代碼格式化
    if not checker.run_ruff_format():
        return 1

    # 3. 最終驗證
    if not checker.run_final_verification():
        return 1

    # 4. 格式化驗證
    if not checker.run_ruff_format(check_only=True):
        return 1

    print("\n🎉 所有檢查通過！")
    print("\n💡 使用提示:")
    print("   • 運行 'python code_quality.py' 進行快速檢查")
    print("   • 運行 'python code_quality.py --detailed' 獲取詳細統計")
    print("   • 在 VS Code 中按 Ctrl+Shift+I 進行快速修復")

    return 0


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="統一代碼質量檢查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python code_quality.py                    # 快速檢查模式 (當前目錄)
  python code_quality.py --detailed         # 詳細檢查模式 (包含統計)
  python code_quality.py --path src/        # 指定路徑檢查
  python code_quality.py --files file1.py file2.py  # 指定檔案檢查
  python code_quality.py --config custom.toml  # 指定配置文件
  python code_quality.py --help             # 顯示此幫助信息
        """,
    )

    parser.add_argument(
        "--detailed",
        "-d",
        action="store_true",
        help="啟用詳細檢查模式 (包含項目統計信息)",
    )

    parser.add_argument(
        "--path", "-p", action="append", help="指定要檢查的子目錄路徑 (可多次使用)"
    )

    parser.add_argument("--files", "-f", nargs="+", help="指定要檢查的Python檔案")

    parser.add_argument(
        "--config", "-c", type=Path, help="指定配置文件路徑 (默認: pyproject.toml)"
    )

    args = parser.parse_args()

    # 載入配置
    config = CodeQualityConfig(args.config)

    # 創建檢查器
    checker = CodeQualityChecker(config, args.path, args.files)

    # 運行檢查
    if args.detailed:
        return detailed_check(checker)
    else:
        return quick_check(checker)


if __name__ == "__main__":
    sys.exit(main())
