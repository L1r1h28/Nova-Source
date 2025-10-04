#!/usr/bin/env python3
"""
🔍 Nova AI 代碼分析工具
=====================================
整合代碼結構分析和依賴關係掃描
"""

import ast
import importlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class CodeAnalyzer:
    """代碼分析器 - 整合結構分析和依賴掃描"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.python_files = []
        self.analysis_results = {}
        self.dependency_map = {}
        self.refactor_suggestions = []
        self.missing_imports = []
        self.circular_imports = []
        self.local_modules = set()

    def scan_python_files(self) -> List[Path]:
        """掃描所有Python文件"""
        print("掃描Python文件...")

        # 掃描根目錄和core目錄
        patterns = ["*.py", "core/*.py", "tools/*.py"]
        py_files = []

        for pattern in patterns:
            py_files.extend(self.root_dir.glob(pattern))

        self.python_files = sorted(py_files)

        print(f"   發現 {len(self.python_files)} 個Python文件")
        for file in self.python_files:
            print(f"   {file.relative_to(self.root_dir)}")
            # 記錄本地模組名稱
            self.local_modules.add(file.stem)

        return self.python_files

    def analyze_file_complexity(self, file_path: Path) -> Dict[str, Any]:
        """分析單個文件的複雜度"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            analysis = {
                "file_path": str(file_path.relative_to(self.root_dir)),
                "lines_of_code": len(content.splitlines()),
                "classes": [],
                "functions": [],
                "imports": {
                    "standard_library": [],
                    "third_party": [],
                    "local_imports": [],
                    "relative_imports": [],
                },
                "complexity_score": 0,
            }

            # 分析類別
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "methods": [],
                        "line_start": node.lineno,
                        "docstring": ast.get_docstring(node) or "",
                    }

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append(
                                {
                                    "name": item.name,
                                    "line_start": item.lineno,
                                    "args_count": len(item.args.args),
                                }
                            )

                    analysis["classes"].append(class_info)

                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # 只記錄頂層函數
                    function_info = {
                        "name": node.name,
                        "line_start": node.lineno,
                        "args_count": len(node.args.args),
                        "docstring": ast.get_docstring(node) or "",
                    }
                    analysis["functions"].append(function_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    # 分析導入
                    self._analyze_import_node(node, analysis["imports"])

            # 計算複雜度分數
            analysis["complexity_score"] = self._calculate_complexity_score(analysis)

            return analysis

        except Exception as e:
            return {
                "file_path": str(file_path.relative_to(self.root_dir)),
                "error": str(e),
                "lines_of_code": 0,
                "complexity_score": 0,
            }

    def _analyze_import_node(self, node, imports_dict):
        """分析導入節點"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                self._categorize_import(module_name, imports_dict)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.level > 0:  # 相對導入
                    imports_dict["relative_imports"].append(
                        {
                            "module": node.module or "",
                            "level": node.level,
                            "names": [alias.name for alias in node.names],
                        }
                    )
                else:
                    self._categorize_import(node.module, imports_dict)

    def _categorize_import(self, module_name: str, imports_dict):
        """分類導入模組 - TCK優化：使用集合查找加速"""
        # TCK優化：預先將模組集合轉換為集合以實現O(1)查找
        standard_modules = {
            "os",
            "sys",
            "json",
            "time",
            "datetime",
            "pathlib",
            "typing",
            "ast",
            "importlib",
            "traceback",
            "collections",
            "re",
        }

        third_party_modules = {
            "torch",
            "transformers",
            "numpy",
            "pandas",
            "matplotlib",
            "requests",
            "flask",
            "django",
            "scipy",
            "sklearn",
        }

        root_module = module_name.split(".")[0]

        # TCK優化：集合查找 O(1) 而非列表查找 O(n)
        if root_module in standard_modules:
            imports_dict["standard_library"].append(module_name)
        elif root_module in third_party_modules:
            imports_dict["third_party"].append(module_name)
        elif (
            root_module in self.local_modules
            or module_name.startswith("core.")
            or module_name.startswith("tools.")
        ):
            imports_dict["local_imports"].append(module_name)
        else:
            # 假設是第三方庫
            imports_dict["third_party"].append(module_name)

    def _calculate_complexity_score(self, analysis: Dict) -> int:
        """計算複雜度分數"""
        score = 0

        # 基於代碼行數
        lines = analysis["lines_of_code"]
        if lines > 500:
            score += 50
        elif lines > 200:
            score += 20
        elif lines > 100:
            score += 10

        # 基於類別數量
        score += len(analysis["classes"]) * 5

        # 基於函數數量
        score += len(analysis["functions"]) * 2

        # TCK優化：使用sum()內建函數進行統計計算
        total_imports = sum(
            len(analysis["imports"][category])
            for category in ["standard_library", "third_party", "local_imports"]
        )
        score += total_imports

        return score

    def check_dependency_issues(self) -> Dict[str, List]:
        """檢查依賴問題"""
        print("\n檢查依賴問題...")

        issues = {"missing_imports": [], "circular_imports": [], "unused_imports": []}

        # 檢查每個文件的導入
        for file_path in self.python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        self._check_import_validity(node, file_path, issues)

            except Exception as e:
                issues["missing_imports"].append(
                    {
                        "file": str(file_path.relative_to(self.root_dir)),
                        "error": f"解析錯誤: {e}",
                    }
                )

        return issues

    def _check_import_validity(self, node, file_path, issues):
        """檢查導入的有效性"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                if not self._can_import_module(module_name):
                    issues["missing_imports"].append(
                        {
                            "file": str(file_path.relative_to(self.root_dir)),
                            "module": module_name,
                            "line": node.lineno,
                        }
                    )

        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.level == 0:  # 絕對導入
                if not self._can_import_module(node.module):
                    issues["missing_imports"].append(
                        {
                            "file": str(file_path.relative_to(self.root_dir)),
                            "module": node.module,
                            "line": node.lineno,
                        }
                    )

    def _can_import_module(self, module_name: str) -> bool:
        """檢查模組是否可以導入"""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            # 檢查是否為本地模組
            if module_name in self.local_modules:
                return True
            # 檢查是否為core模組
            if module_name.startswith("core."):
                module_file = self.root_dir / f"{module_name.replace('.', '/')}.py"
                return module_file.exists()
            return False

    def find_duplicate_functionality(self) -> List[Dict]:
        """尋找重複功能"""
        print("\n尋找重複功能...")

        duplicates = []
        function_signatures = {}

        for analysis in self.analysis_results.values():
            if "error" in analysis:
                continue

            file_path = analysis["file_path"]

            # 檢查函數重複
            for func in analysis["functions"]:
                signature = f"{func['name']}_{func['args_count']}"

                if signature in function_signatures:
                    duplicates.append(
                        {
                            "type": "function",
                            "name": func["name"],
                            "files": [function_signatures[signature], file_path],
                            "suggestion": f"考慮合併或重命名函數 '{func['name']}'",
                        }
                    )
                else:
                    function_signatures[signature] = file_path

            # TCK優化：檢查類別重複 - 使用集合查找避免重複比較
            common_class_names = {"Config", "NovaSystem"}
            for cls in analysis["classes"]:
                if cls["name"] in common_class_names:
                    continue  # 跳過常見的類別名

                # TCK優化：收集所有其他文件的類別名稱以避免重複巢狀查找
                other_class_names = set()
                for other_file, other_analysis in self.analysis_results.items():
                    if other_file != file_path and "classes" in other_analysis:
                        other_class_names.update(
                            other_cls["name"] for other_cls in other_analysis["classes"]
                        )

                if cls["name"] in other_class_names:
                    # 找到重複，記錄詳細信息
                    duplicate_files = [file_path]
                    for other_file, other_analysis in self.analysis_results.items():
                        if (
                            other_file != file_path
                            and "classes" in other_analysis
                            and any(
                                other_cls["name"] == cls["name"]
                                for other_cls in other_analysis["classes"]
                            )
                        ):
                            duplicate_files.append(other_analysis["file_path"])

                    duplicates.append(
                        {
                            "type": "class",
                            "name": cls["name"],
                            "files": duplicate_files,
                            "suggestion": f"考慮合併或重命名類別 '{cls['name']}'",
                        }
                    )

        return duplicates

    def analyze_all_files(self) -> Dict[str, Any]:
        """分析所有文件"""
        print("Nova AI 代碼分析開始")
        print("=" * 60)

        # 掃描文件
        self.scan_python_files()

        # 分析每個文件
        print(f"\n分析 {len(self.python_files)} 個文件的複雜度...")

        for file_path in self.python_files:
            print(f"   分析: {file_path.relative_to(self.root_dir)}")
            analysis = self.analyze_file_complexity(file_path)
            self.analysis_results[str(file_path)] = analysis

        # 檢查依賴問題
        dependency_issues = self.check_dependency_issues()

        # 尋找重複功能
        duplicates = self.find_duplicate_functionality()

        # 生成總結
        total_lines = sum(
            a.get("lines_of_code", 0) for a in self.analysis_results.values()
        )

        avg_complexity = (
            sum(a.get("complexity_score", 0) for a in self.analysis_results.values())
            / len(self.analysis_results)
            if self.analysis_results
            else 0
        )

        summary = {
            "total_files": len(self.python_files),
            "total_lines": total_lines,
            "average_complexity": round(avg_complexity, 2),
            "dependency_issues": len(dependency_issues["missing_imports"]),
            "duplicate_functions": len(
                [d for d in duplicates if d["type"] == "function"]
            ),
            "duplicate_classes": len([d for d in duplicates if d["type"] == "class"]),
        }

        results = {
            "summary": summary,
            "file_analyses": self.analysis_results,
            "dependency_issues": dependency_issues,
            "duplicates": duplicates,
            "timestamp": datetime.now().isoformat(),
        }

        # 顯示總結
        print("\n" + "=" * 60)
        print("代碼分析總結")
        print("=" * 60)
        print(f"總文件數: {summary['total_files']}")
        print(f"總代碼行數: {summary['total_lines']}")
        print(f"平均複雜度: {summary['average_complexity']}")
        print(f"依賴問題: {summary['dependency_issues']}")
        print(f"重複函數: {summary['duplicate_functions']}")
        print(f"重複類別: {summary['duplicate_classes']}")

        if duplicates:
            print(f"\n發現 {len(duplicates)} 個重複項目:")
            for dup in duplicates[:5]:  # 只顯示前5個
                print(f"   - {dup['type']}: {dup['name']} ({len(dup['files'])} 個文件)")

        return results
