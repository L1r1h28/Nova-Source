"""
Markdown Auto-Formatter for Nova Source

Automatically formats and fixes markdown files to conform to markdownlint standards.
"""

import logging
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """自動化Markdown格式化器，修復常見的markdownlint錯誤"""

    def __init__(self, max_line_length: int = 80):
        """初始化格式化器

        Args:
            max_line_length: 最大行長度限制 (預設80字符)
        """
        self.max_line_length = max_line_length
        # 自動修復規則：確定性強、低風險的格式問題
        self.auto_fix_rules = {
            "MD009": self._fix_trailing_spaces,  # Trailing spaces
            "MD010": self._fix_hard_tabs,  # Hard tabs
            "MD012": self._fix_multiple_blanks,  # Multiple consecutive blank lines
            "MD018": self._fix_no_space_after_hash,  # No space after hash on atx style header
            "MD019": self._fix_multiple_spaces_after_hash,  # Multiple spaces after hash on atx style header
            "MD020": self._fix_no_space_inside_hashes,  # No space inside hashes on closed atx style header
            "MD021": self._fix_multiple_spaces_inside_hashes,  # Multiple spaces inside hashes on closed atx style header
            "MD022": self._fix_blanks_around_headers,  # Headers should be surrounded by blank lines
            "MD023": self._fix_header_start_left,  # Headers must start at the beginning of the line
            "MD003": self._fix_header_style,  # Header style
            "MD027": self._fix_multiple_spaces_after_bq,  # Multiple spaces after blockquote symbol
            "MD028": self._fix_blank_line_inside_bq,  # Blank line inside blockquote
            "MD029": self._fix_ol_prefix,  # Ordered list item prefix
            "MD030": self._fix_ol_indent,  # Spaces after list markers
            "MD031": self._fix_blanks_around_fences,  # Fences should be surrounded by blank lines
            "MD032": self._fix_blanks_around_lists,  # Lists should be surrounded by blank lines
            "MD034": self._fix_bare_url,  # Bare URL used
            "MD037": self._fix_spaces_inside_emphasis,  # Spaces inside emphasis markers
            "MD038": self._fix_spaces_inside_code_span,  # Spaces inside code span elements
            "MD039": self._fix_no_space_inside_link,  # Spaces inside link text
            "MD041": self._fix_first_line_header,  # First line in file should be a top level header
            "MD047": self._fix_file_end_newline,  # Files should end with a single newline character
            "MD055": self._fix_table_pipe_style,  # Table pipe style
        }

        # 檢測模式規則：需要人工判斷的內容相關問題，只輸出警告
        self.detection_only_rules = {
            "MD013": self._detect_line_length,  # Line length
            "MD024": self._fix_multiple_headers_same_content,  # Multiple headers with the same content
            "MD025": self._fix_multiple_top_level_headers,  # Multiple top level headers in the same document
            "MD033": self._detect_inline_html,  # Inline HTML
            "MD036": self._fix_no_emphasis_only,  # Emphasis used instead of a header
            "MD051": self._fix_link_fragments,  # Link fragments should be valid
            "MD055": self._detect_table_pipe_style,  # Table pipe style
            "MD056": self._detect_table_multiline_cells,  # Table cells should not span multiple lines
        }

    # 輔助方法：重複使用的正則表達式模式
    def _is_header_line(self, line: str) -> bool:
        """檢查是否為標題行"""
        return bool(re.match(r"^#{1,6}", line.strip()))

    def _is_unordered_list_line(self, line: str) -> bool:
        """檢查是否為無序列表行"""
        return bool(re.match(r"^[\s]*[-\*\+]\s", line))

    def _is_ordered_list_line(self, line: str) -> bool:
        """檢查是否為有序列表行"""
        return bool(re.match(r"^[\s]*\d+\.\s", line))

    def _is_table_line(self, line: str) -> bool:
        """檢查是否為表格行"""
        return line.strip().startswith("|")

    def _extract_header_info(self, line: str) -> Optional[tuple]:
        """提取標題資訊，返回 (level, title) 或 None"""
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            return len(match.group(1)), match.group(2).strip()
        return None

    def _extract_ordered_list_info(self, line: str) -> Optional[tuple]:
        """提取有序列表資訊，返回 (indent, number, text) 或 None"""
        match = re.match(r"^(\s*)(\d+)\.\s+(.+)$", line.rstrip())
        if match:
            return match.group(1), int(match.group(2)), match.group(3)
        return None

    def detect_issues(
        self, file_path: str, rules_to_check: Optional[List[str]] = None
    ) -> None:
        """
        檢測檔案中的問題但不修改檔案

        Args:
            file_path: 檔案路徑
            rules_to_check: 要檢查的規則列表，None表示檢查所有檢測規則
        """
        try:
            # 嘗試不同的編碼
            encodings = ["utf-8", "utf-8-sig", "gbk", "cp950"]
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                logger.error(f"無法讀取檔案 {file_path}，編碼不支援")
                return

            # 應用檢測規則
            if rules_to_check:
                detection_rules = [
                    r for r in rules_to_check if r in self.detection_only_rules
                ]
            else:
                detection_rules = list(self.detection_only_rules.keys())

            for rule in detection_rules:
                if rule in self.detection_only_rules:
                    self.detection_only_rules[rule](content)

        except Exception as e:
            logger.error(f"Error detecting issues in {file_path}: {e}")

    def format_file(
        self, file_path: str, rules_to_fix: Optional[List[str]] = None
    ) -> bool:
        """
        格式化單個markdown檔案

        Args:
            file_path: 檔案路徑
            rules_to_fix: 要修復的規則列表，None表示修復所有規則

        Returns:
            bool: 是否成功格式化
        """
        try:
            # 嘗試不同的編碼
            encodings = ["utf-8", "utf-8-sig", "gbk", "cp950"]
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                logger.error(f"無法讀取檔案 {file_path}，編碼不支援")
                return False

            original_content = content

            # 分離自動修復規則和檢測模式規則
            if rules_to_fix:
                # 如果指定了特定規則，只應用這些規則
                auto_rules = [r for r in rules_to_fix if r in self.auto_fix_rules]
                detection_rules = [
                    r for r in rules_to_fix if r in self.detection_only_rules
                ]
            else:
                # 默認應用所有規則
                auto_rules = list(self.auto_fix_rules.keys())
                detection_rules = list(self.detection_only_rules.keys())

            # 先應用檢測模式規則（只輸出警告，不修改內容）
            for rule in detection_rules:
                if rule in self.detection_only_rules:
                    self.detection_only_rules[rule](content)

            # 然後應用自動修復規則（會修改內容）
            for rule in auto_rules:
                if rule in self.auto_fix_rules:
                    content = self.auto_fix_rules[rule](content)

            # 如果內容有變化，寫回檔案
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Formatted {file_path}")
                return True
            else:
                logger.info(f"No changes needed for {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error formatting {file_path}: {e}")
            return False

    def format_directory(
        self,
        directory: str,
        recursive: bool = True,
        rules_to_fix: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        格式化目錄中的所有markdown檔案

        Args:
            directory: 目錄路徑
            recursive: 是否遞歸處理子目錄
            rules_to_fix: 要修復的規則列表
            exclude_patterns: 排除的檔案模式

        Returns:
            Dict: 處理結果統計
        """
        stats = {"processed": 0, "formatted": 0, "errors": 0, "files": []}

        path_obj = Path(directory)

        if recursive:
            pattern = "**/*.md"
        else:
            pattern = "*.md"

        for md_file in path_obj.glob(pattern):
            # 檢查是否在排除模式中
            if exclude_patterns:
                should_exclude = any(
                    pattern in str(md_file) for pattern in exclude_patterns
                )
                if should_exclude:
                    continue

            stats["processed"] += 1

            try:
                formatted = self.format_file(str(md_file), rules_to_fix)
                if formatted:
                    stats["formatted"] += 1
                    stats["files"].append({"path": str(md_file), "status": "formatted"})
                else:
                    stats["files"].append(
                        {"path": str(md_file), "status": "no_changes"}
                    )
            except Exception as e:
                stats["errors"] += 1
                stats["files"].append(
                    {"path": str(md_file), "status": "error", "error": str(e)}
                )
                logger.error(f"Error processing {md_file}: {e}")

        return stats

    # 修復規則實現
    def _fix_trailing_spaces(self, content: str) -> str:
        """修復行尾空格 (MD009)"""
        lines = content.split("\n")
        fixed_lines = []
        for line in lines:
            # 保留markdown表格中的尾隨空格
            if "|" in line and not line.strip().startswith("|"):
                fixed_lines.append(line)
            else:
                fixed_lines.append(line.rstrip())
        return "\n".join(fixed_lines)

    def _fix_multiple_blanks(self, content: str) -> str:
        """修復多個連續空行 (MD012)"""
        # 將多個連續空行替換為單個空行
        return re.sub(r"\n{3,}", "\n\n", content)

    def _fix_blanks_around_headers(self, content: str) -> str:
        """修復標題周圍的空行 (MD022)"""
        lines = content.split("\n")
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 如果是標題行
            if line.strip().startswith("#"):
                # 在標題前添加空行（如果前面不是空行且不是第一行）
                if i > 0 and lines[i - 1].strip() != "":
                    result.append("")

                result.append(line)

                # 在標題後添加空行（如果後面不是空行且不是最後一行）
                if i < len(lines) - 1 and lines[i + 1].strip() != "":
                    result.append("")
            else:
                result.append(line)

            i += 1

        return "\n".join(result)

    def _fix_blanks_around_lists(self, content: str) -> str:
        """修復清單周圍的空行 (MD032)"""
        lines = content.split("\n")
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 如果是清單項目
            if self._is_unordered_list_line(line.strip()) or self._is_ordered_list_line(
                line.strip()
            ):
                # 在清單前添加空行（如果前面不是空行且不是第一行）
                if i > 0 and lines[i - 1].strip() != "":
                    result.append("")

                result.append(line)

                # 找到清單的結尾
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() == "" or not (
                        self._is_unordered_list_line(next_line.strip())
                        or self._is_ordered_list_line(next_line.strip())
                    ):
                        break
                    result.append(next_line)
                    j += 1

                # 在清單後添加空行（如果後面不是空行且不是最後一行）
                if j < len(lines) - 1 and lines[j].strip() != "":
                    result.append("")

                i = j - 1
            else:
                result.append(line)

            i += 1

        return "\n".join(result)

    def _fix_file_end_newline(self, content: str) -> str:
        """確保檔案以單個換行符結束 (MD047)"""
        if not content.endswith("\n"):
            content += "\n"
        return content

    def _fix_fenced_code_language(self, content: str) -> str:
        """為程式碼區塊指定語言 (MD040)"""
        # 這個規則很複雜，因為需要猜測語言
        # 這裡只處理明顯的程式碼區塊
        lines = content.split("\n")
        result = []
        in_code_block = False

        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                if not in_code_block:
                    # 程式碼區塊開始
                    in_code_block = True
                    # 如果沒有指定語言，嘗試添加
                    if line.strip() == "```":
                        # 簡單的語言檢測邏輯
                        # 檢查後續幾行是否有明顯的語言特徵
                        language = self._detect_language(
                            lines[i + 1 : i + 5]
                            if i + 5 < len(lines)
                            else lines[i + 1 :]
                        )
                        if language:
                            line = f"```{language}"
                else:
                    # 程式碼區塊結束
                    in_code_block = False

            result.append(line)

        return "\n".join(result)

    def _detect_language(self, code_lines: List[str]) -> Optional[str]:
        """簡單的程式碼語言檢測"""
        code_text = "\n".join(code_lines).lower()

        # Python 特徵
        if any(
            keyword in code_text for keyword in ["def ", "import ", "class ", "print("]
        ):
            return "python"

        # JavaScript 特徵
        if any(
            keyword in code_text
            for keyword in ["function ", "const ", "let ", "console.log"]
        ):
            return "javascript"

        # Shell/Bash 特徵
        if any(
            keyword in code_text
            for keyword in ["#!/bin/", "apt-get", "pip install", "npm "]
        ):
            return "bash"

        # SQL 特徵
        if any(
            keyword in code_text
            for keyword in ["select ", "from ", "where ", "insert ", "update "]
        ):
            return "sql"

        # JSON 特徵
        if code_text.strip().startswith("{") and code_text.strip().endswith("}"):
            return "json"

        return None

    # 其他規則的佔位符實現
    def _fix_header_levels(self, content: str) -> str:
        """修復標題級別 (MD001)"""
        # 這個需要更複雜的邏輯來確保標題級別正確遞增
        return content

    def _fix_first_header(self, content: str) -> str:
        """修復第一個標題 (MD002)"""
        return content

    def _fix_header_style(self, content: str) -> str:
        """修復標題樣式 (MD003)"""
        import re

        lines = content.split("\n")
        processed_lines = []

        # 檢測文件中使用的標題樣式
        has_atx = False
        has_setext = False

        for line in lines:
            line = line.rstrip()
            if self._is_header_line(line) and re.match(r"^#{1,6}\s+", line.strip()):
                has_atx = True
            elif (
                re.match(r"^[-=]+\s*$", line)
                and processed_lines
                and re.match(r"^[^\s]", processed_lines[-1])
            ):
                # 這是 Setext 標題的底線
                has_setext = True

        # 如果只有一種樣式，保持不變
        if (has_atx and has_setext) or (not has_atx and not has_setext):
            # 混合使用或沒有標題，預設使用 ATX 樣式
            target_style = "atx"
        elif has_atx:
            target_style = "atx"
        else:
            target_style = "setext"

        i = 0
        while i < len(lines):
            line = lines[i]
            original_line = line
            line = line.rstrip()

            # 處理 ATX 樣式標題
            header_info = self._extract_header_info(line)
            if header_info:
                level, title = header_info

                if target_style == "setext":
                    # 轉換為 Setext 樣式
                    processed_lines.append(title)
                    if level == 1:
                        processed_lines.append("=" * len(title))
                    else:
                        processed_lines.append("-" * len(title))
                else:
                    # 保持 ATX 樣式，但確保格式正確
                    processed_lines.append(f"{'#' * level} {title}")
            # 處理 Setext 樣式標題
            elif (
                i + 1 < len(lines)
                and re.match(r"^[^\s]", line)
                and re.match(r"^[-=]+\s*$", lines[i + 1].rstrip())
            ):
                title = line.strip()
                underline = lines[i + 1].rstrip()

                if target_style == "atx":
                    # 轉換為 ATX 樣式
                    if "=" in underline:
                        level = 1
                    else:
                        level = 2
                    processed_lines.append(f"{'#' * level} {title}")
                else:
                    # 保持 Setext 樣式
                    processed_lines.append(title)
                    processed_lines.append(underline)

                i += 1  # 跳過底線行
            else:
                # 非標題行
                processed_lines.append(original_line)

            i += 1

        return "\n".join(processed_lines)

    def _fix_ul_style(self, content: str) -> str:
        """修復無序清單樣式 (MD004)"""
        return content

    def _fix_list_indent(self, content: str) -> str:
        """修復清單縮排 (MD005)"""
        return content

    def _fix_ul_start_left(self, content: str) -> str:
        """修復無序清單起始位置 (MD006)"""
        return content

    def _fix_ul_indent(self, content: str) -> str:
        """修復無序清單縮排 (MD007)"""
        return content

    def _fix_hard_tabs(self, content: str) -> str:
        """修復硬製表符 (MD010)"""
        return content.replace("\t", "    ")

    def _fix_reversed_link(self, content: str) -> str:
        """修復反轉連結語法 (MD011)"""
        return content

    def _fix_line_length(self, content: str) -> str:
        """修復行長度 (MD013) - 優化版本：使用列表推導式減少函數調用開銷"""
        lines = content.split("\n")
        max_length = self.max_line_length

        def process_line(line: str) -> List[str]:
            """處理單行，根據行長度決定是否需要換行"""
            # 跳過程式碼區塊、表格行、標題、列表等不應換行的特殊行
            if (
                line.strip().startswith("```")
                or self._is_table_line(line)  # 表格行不換行
                or self._is_header_line(line)  # 標題
                or self._is_unordered_list_line(line)  # 無序列表
                or self._is_ordered_list_line(line)  # 有序列表
                or line.strip() == ""
            ):  # 空行
                return [line]

            # 如果行長度超過限制，使用 textwrap 進行智能換行
            if len(line) > max_length:
                # 首先嘗試在句子結束、逗號、空格等位置斷行
                wrapped = textwrap.fill(
                    line,
                    width=max_length,
                    break_long_words=False,
                    break_on_hyphens=True,
                )

                # 如果textwrap沒有斷行（可能是因為沒有合適的斷行點），強制斷行
                if len(wrapped.replace("\n", "")) == len(line):
                    # 強制在max_length處斷行 - 使用列表推導式優化
                    wrapped_lines = []
                    remaining = line
                    while len(remaining) > max_length:
                        # 找到最後一個合適的斷行點（空格、逗號、句號等）
                        break_pos = max_length
                        for i in range(max_length - 1, max_length // 2, -1):
                            if remaining[i] in " ，。！？；：":
                                break_pos = i + 1
                                break
                        wrapped_lines.append(remaining[:break_pos])
                        remaining = remaining[break_pos:]
                    if remaining:
                        wrapped_lines.append(remaining)
                    return wrapped_lines

                return wrapped.split("\n")
            else:
                return [line]

        # 使用列表推導式處理所有行，減少中間列表創建
        result_lines = [
            processed_line for line in lines for processed_line in process_line(line)
        ]

        # 使用 join() 一次性構建最終結果
        return "\n".join(result_lines)

    def _fix_commands_show_output(self, content: str) -> str:
        """修復命令顯示輸出 (MD014)"""
        return content

    def _fix_no_space_after_hash(self, content: str) -> str:
        """修復井號後無空格 (MD018)"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # 檢查是否是沒有空格的標題 (MD018: No space after hash on atx style header)
            if re.match(r"^#{1,6}[^\s]", line) and not re.match(
                r"^#{1,6}\s+", line.strip()
            ):
                lines[i] = re.sub(r"^(#{1,6})([^\s])", r"\1 \2", line)
        return "\n".join(lines)

    def _fix_multiple_spaces_after_hash(self, content: str) -> str:
        """修復井號後多個空格 (MD019)"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line.strip()) and re.match(
                r"^#{1,6}\s{2,}", line
            ):
                lines[i] = re.sub(r"^(#{1,6})\s{2,}", r"\1 ", line)
        return "\n".join(lines)

    def _fix_no_space_inside_hashes(self, content: str) -> str:
        """修復井號內無空格 (MD020)"""
        return content

    def _fix_multiple_spaces_inside_hashes(self, content: str) -> str:
        """修復井號內多個空格 (MD021)"""
        return content

    def _fix_header_start_left(self, content: str) -> str:
        """修復標題起始位置 (MD023)"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                # 移除前導空格
                lines[i] = line.lstrip()
        return "\n".join(lines)

    def _fix_multiple_headers_same_content(self, content: str) -> str:
        """修復相同內容的多個標題 (MD024) - 檢測並報告問題"""
        lines = content.split("\n")
        headers = {}
        issues = []

        for i, line in enumerate(lines):
            # 檢測標題
            match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if match:
                title = match.group(2).strip()

                if title in headers:
                    issues.append(
                        {
                            "line": i + 1,
                            "title": title,
                            "previous_line": headers[title],
                            "context": line.strip(),
                        }
                    )
                else:
                    headers[title] = i + 1

        if issues:
            print("🔍 發現重複標題問題 (MD024):")
            for issue in issues:
                print(f"  第{issue['line']}行: 重複標題 '{issue['title']}'")
                print(f"    之前出現於第{issue['previous_line']}行")
                print(f"    內容: {issue['context']}")
            print("  💡 建議: 為重複標題添加區分性內容或重新命名")
            print()

        return content

    def _fix_multiple_top_level_headers(self, content: str) -> str:
        """修復多個頂級標題 (MD025) - 檢測並報告問題"""
        lines = content.split("\n")
        top_level_headers = []

        for i, line in enumerate(lines):
            # 檢測頂級標題（只有一個 # 的標題）
            header_info = self._extract_header_info(line)
            if header_info and header_info[0] == 1:
                title = header_info[1]
                top_level_headers.append(
                    {"line": i + 1, "title": title, "content": line.strip()}
                )

        if len(top_level_headers) > 1:
            print("🔍 發現多個頂級標題問題 (MD025):")
            for i, header in enumerate(top_level_headers):
                print(f"  第{header['line']}行: 頂級標題 '{header['title']}'")
                if i > 0:
                    print(f"    之前頂級標題在第{top_level_headers[0]['line']}行")
                print(f"    內容: {header['content']}")
            print(
                "  💡 建議: 每個文檔應該只有一個頂級標題，將其他標題改為適當的子標題級別"
            )
            print()

        return content

    def _fix_trailing_punctuation(self, content: str) -> str:
        """修復標題尾隨標點 (MD026)"""
        return content

    def _fix_multiple_spaces_after_bq(self, content: str) -> str:
        """修復引用符號後多個空格 (MD027)"""
        return content

    def _fix_blank_line_inside_bq(self, content: str) -> str:
        """修復引用內空行 (MD028)"""
        return content

    def _fix_ol_prefix(self, content: str) -> str:
        """修復有序列表項目前綴 (MD029)"""
        lines = content.split("\n")
        result_lines = []
        list_contexts = {}  # indent -> last_number

        for i, line in enumerate(lines):
            # 檢查是否為有序列表項目
            list_info = self._extract_ordered_list_info(line)
            if list_info:
                indent, current_number, text = list_info

                # 檢查前一行是否也是相同縮進的有序列表項目
                prev_line_is_list = False
                if i > 0:
                    prev_stripped = (
                        result_lines[-1] if result_lines else lines[i - 1].rstrip()
                    )
                    prev_list_info = self._extract_ordered_list_info(prev_stripped)
                    if prev_list_info and prev_list_info[0] == indent:
                        prev_line_is_list = True

                if not prev_line_is_list:
                    # 這是列表的開始，應該是1
                    expected_number = 1
                    list_contexts[indent] = 1
                else:
                    # 這是現有列表的延續
                    if indent in list_contexts:
                        expected_number = list_contexts[indent] + 1
                    else:
                        expected_number = 1
                    list_contexts[indent] = expected_number

                if current_number != expected_number:
                    # 編號不正確，修復它
                    fixed_line = f"{indent}{expected_number}. {text}"
                    result_lines.append(fixed_line)
                else:
                    # 編號正確，更新上下文
                    list_contexts[indent] = current_number
                    result_lines.append(line)
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _fix_ol_indent(self, content: str) -> str:
        """修復有序清單縮排 (MD030)"""
        return content

    def _fix_blanks_around_fences(self, content: str) -> str:
        """修復程式碼區塊周圍空行 (MD031)"""
        return content

    def _fix_no_inline_html(self, content: str) -> str:
        """修復內聯HTML (MD033)"""
        return content

    def _fix_bare_url(self, content: str) -> str:
        """修復裸URL (MD034) - 優化版本：使用 join() 避免 O(n²) 字串累加"""
        import re

        lines = content.split("\n")
        processed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 檢查是否有未完成的 URL（包含 <http 或 <https 且不真正以 > 結尾）
            line_ends_with_gt = line.strip().endswith(">") and not (
                len(line.strip()) >= 2 and line.strip()[-2:] == "->"
            )
            if ("<http://" in line or "<https://" in line) and not line_ends_with_gt:
                # 找到最後一個 <
                start_pos = line.rfind("<")
                remaining = line[start_pos + 1 :]
                # 收集完整的 URL - 使用列表累加然後 join()
                url_parts = [remaining[:-2] if remaining.endswith("->") else remaining]

                j = i + 1
                url_found = False
                while j < len(lines):
                    next_line = lines[j]
                    if ">" in next_line:
                        # 找到結尾 - 使用列表推導式優化
                        end_pos = next_line.find(">")
                        url_parts.append("-" + next_line[:end_pos])
                        # 重建完整的行 - 使用 join() 一次性構建
                        complete_url = "<" + "".join(url_parts) + ">"
                        new_line = (
                            line[:start_pos] + complete_url + next_line[end_pos + 1 :]
                        )
                        processed_lines.append(new_line)
                        i = j  # 跳過已處理的行
                        url_found = True
                        break
                    else:
                        # 繼續收集
                        url_parts.append(next_line)
                        j += 1

                if not url_found:
                    # 沒有找到結尾，保持原樣
                    processed_lines.append(line)
            # 檢查是否有被自動換行的裸 URL（以 - 結尾且包含 http:// 或 https://）
            elif line.strip().endswith("-") and (
                "http://" in line or "https://" in line
            ):
                # 檢查是否是 URL 的中間部分
                url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+-?$', line)
                if url_match:
                    url_start = url_match.group(0)
                    # 收集完整的 URL - 使用列表優化
                    url_parts = [url_start.rstrip("-")]

                    j = i + 1
                    url_completed = False
                    while j < len(lines):
                        next_line = lines[j].strip()
                        # 檢查下一行是否繼續 URL
                        if next_line and not next_line.startswith(
                            ("#", "-", "*", ">", "`", "|", "[")
                        ):
                            # 檢查是否包含空格 - 如果包含空格，只有在空格前的部分可能是 URL
                            if " " in next_line:
                                url_part = next_line.split(" ")[0]
                                if url_part and not url_part.startswith(
                                    ("http://", "https://")
                                ):
                                    # 使用條件運算符優化
                                    url_parts.append(
                                        "-"
                                        + (
                                            url_part.rstrip("-")
                                            if next_line.endswith("-")
                                            else url_part
                                        )
                                    )
                                    if not next_line.endswith("-"):
                                        # 完整的 URL - 使用 join() 一次性構建
                                        complete_url = "".join(url_parts)
                                        remaining_text = next_line[len(url_part) :]
                                        wrapped_url = f"<{complete_url}>"
                                        new_line = (
                                            line.replace(url_start, wrapped_url)
                                            + remaining_text
                                        )
                                        processed_lines.append(new_line)
                                        i = j
                                        url_completed = True
                                        break
                                else:
                                    # 不繼續，處理普通行
                                    processed_lines.append(
                                        self._process_line_for_urls(line)
                                    )
                                    url_completed = True
                                    break
                            else:
                                # 沒有空格，整行都是 URL 延續 - 使用條件運算符
                                url_parts.append(
                                    "-"
                                    + (
                                        next_line.rstrip("-")
                                        if next_line.endswith("-")
                                        else next_line
                                    )
                                )
                                if not next_line.endswith("-"):
                                    # 完整的 URL - 使用 join() 一次性構建
                                    complete_url = "".join(url_parts)
                                    wrapped_url = f"<{complete_url}>"
                                    new_line = line.replace(url_start, wrapped_url)
                                    processed_lines.append(new_line)
                                    # 刪除已處理的行
                                    i = j
                                    url_completed = True
                                    break
                        else:
                            # 不繼續，處理普通行
                            processed_lines.append(self._process_line_for_urls(line))
                            url_completed = True
                            break
                        j += 1

                    if not url_completed:
                        # 沒有找到延續，處理普通行中的裸 URL
                        processed_lines.append(self._process_line_for_urls(line))
                else:
                    # 處理普通行中的裸 URL
                    processed_lines.append(self._process_line_for_urls(line))
            else:
                # 處理普通行中的裸 URL
                processed_lines.append(self._process_line_for_urls(line))

            i += 1

        # 使用 join() 一次性構建最終結果，避免多次字串累加
        return "\n".join(processed_lines)

    def _process_line_for_urls(self, line: str) -> str:
        """處理單行中的裸 URL"""
        import re

        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        def replace_bare_url(match):
            url = match.group(0)
            # 檢查 URL 是否已經在連結語法中
            start_pos = match.start()
            if start_pos > 0:
                prev_char = line[start_pos - 1]
                if prev_char in ["[", "(", "<"]:
                    return url

            end_pos = match.end()
            if end_pos < len(line):
                next_char = line[end_pos]
                if next_char in ["]", ")", ">"]:
                    return url

            return f"<{url}>"

        return re.sub(url_pattern, replace_bare_url, line)

    def _fix_hr_style(self, content: str) -> str:
        """修復水平線樣式 (MD035)"""
        return content

    def _fix_no_emphasis_only(self, content: str) -> str:
        """修復僅強調 (MD036) - 檢測並報告問題"""
        lines = content.split("\n")
        issues = []

        for i, line in enumerate(lines):
            # 檢測只包含強調標記的行（不應該用作標題）
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("#"):
                # 檢查是否整行都是強調內容
                # 簡單的檢查：如果一行只包含 *或_ 包圍的文字，可能應該是標題
                if (
                    re.match(r"^\*.*\*$", line_stripped)
                    or re.match(r"^_.*_$", line_stripped)
                ) and len(line_stripped) < 100:
                    # 進一步檢查上下文：如果前後都是段落，這可能是誤用的強調
                    prev_line = lines[i - 1].strip() if i > 0 else ""
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

                    if (not prev_line or not prev_line.startswith("#")) and (
                        not next_line or not next_line.startswith("#")
                    ):
                        issues.append({"line": i + 1, "context": line_stripped})

        if issues:
            print("🔍 發現強調用作標題的問題 (MD036):")
            for issue in issues:
                print(f"  第{issue['line']}行: 強調標記可能應該是標題")
                print(f"    內容: {issue['context']}")
            print("  💡 建議: 考慮將強調轉換為適當級別的標題")
            print()

        return content

    def _fix_spaces_inside_emphasis(self, content: str) -> str:
        """修復強調內空格 (MD037)"""
        return content

    def _fix_spaces_inside_code_span(self, content: str) -> str:
        """修復程式碼跨度內空格 (MD038)"""
        return content

    def _fix_no_space_inside_link(self, content: str) -> str:
        """修復連結內無空格 (MD039)"""
        return content

    def _fix_first_line_header(self, content: str) -> str:
        """修復第一行標題 (MD041)"""
        lines = content.split("\n")
        if not lines:
            return content

        # 找到第一個非空行
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line:
                # 如果第一個非空行已經是標題，不需要修復
                if stripped_line.startswith("#"):
                    return content
                # 在第一個非空行前面添加 # 作為 H1 標題
                lines[i] = f"# {stripped_line}"
                break

        return "\n".join(lines)

    def _fix_no_empty_link(self, content: str) -> str:
        """修復空連結 (MD042)"""
        return content

    def _fix_required_headers(self, content: str) -> str:
        """修復必需標題結構 (MD043)"""
        return content

    def _fix_proper_names(self, content: str) -> str:
        """修復專有名詞大小寫 (MD044)"""
        return content

    def _fix_no_alt_text(self, content: str) -> str:
        """修復圖片無替代文字 (MD045)"""
        return content

    def _fix_code_block_style(self, content: str) -> str:
        """修復程式碼區塊樣式 (MD046)"""
        return content

    def _fix_code_fence_style(self, content: str) -> str:
        """修復程式碼圍欄樣式 (MD048)"""
        return content

    def _fix_emphasis_style(self, content: str) -> str:
        """修復強調樣式 (MD049)"""
        return content

    def _fix_strong_style(self, content: str) -> str:
        """修復強強調樣式 (MD050)"""
        return content

    def _fix_link_fragments(self, content: str) -> str:
        """修復連結片段 (MD051) - 檢測並報告無效鏈接片段"""
        lines = content.split("\n")
        headers = set()
        issues = []

        # 首先收集所有標題錨點
        for line in lines:
            header_info = self._extract_header_info(line)
            if header_info:
                level, title = header_info
                title = title.lower()
                # 移除標點符號並將空格轉為連字符
                anchor = re.sub(r"[^\w\s-]", "", title)
                anchor = re.sub(r"\s+", "-", anchor)
                headers.add(anchor)

        # 然後檢查所有鏈接
        for i, line in enumerate(lines):
            # 查找 [text](#anchor) 格式的鏈接
            link_matches = re.findall(r"\[([^\]]+)\]\(#([^)]+)\)", line)
            for text, anchor in link_matches:
                # 清理錨點格式進行比較
                clean_anchor = anchor.lower().strip("#")
                if clean_anchor and clean_anchor not in headers:
                    issues.append(
                        {
                            "line": i + 1,
                            "text": text,
                            "anchor": anchor,
                            "context": line.strip(),
                        }
                    )

        if issues:
            print("🔍 發現無效鏈接片段問題 (MD051):")
            for issue in issues:
                print(f"  第{issue['line']}行: 鏈接片段 '{issue['anchor']}' 無效")
                print(f"    連結文字: {issue['text']}")
                print(f"    內容: {issue['context']}")
            print("  💡 建議: 檢查鏈接片段是否對應到文檔中的有效標題")
            print()

        return content

    def _fix_reference_link(self, content: str) -> str:
        """修復參考連結 (MD052)"""
        return content

    def _fix_link_image_ref(self, content: str) -> str:
        """修復連結和圖片參考 (MD053)"""
        return content

    def _fix_table_pipe_style(self, content: str) -> str:
        """修復表格管道符號樣式 (MD055) - 確保管道符號前後有空格"""
        lines = content.split("\n")
        result_lines = []

        for line in lines:
            stripped = line.strip()

            # 檢查是否為表格行（以 | 開頭和結尾）
            if self._is_table_line(line) and stripped.endswith("|"):
                # 檢查是否為分隔符行（只包含 - 和 |）
                if (
                    stripped.startswith("|")
                    and stripped.endswith("|")
                    and re.match(r"^\|[\s\-\|]*\|$", stripped)
                ):
                    # 分隔符行，保持原樣
                    result_lines.append(line)
                else:
                    # 表頭或數據行，確保管道符號前後有空格
                    parts = stripped.split("|")
                    fixed_parts = []
                    for part in parts:
                        if part.strip():  # 非空部分
                            fixed_parts.append(f" {part.strip()} ")
                        else:  # 空部分（表格邊界）
                            fixed_parts.append("")
                    line = "|".join(fixed_parts)
                    result_lines.append(line)
            else:
                # 非表格行
                result_lines.append(line)

        return "\n".join(result_lines)

    def _detect_table_pipe_style(self, content: str) -> str:
        """檢測表格管道符號樣式問題 (MD055) - 輸出警告但不修改"""
        lines = content.split("\n")
        issues = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 檢查是否為表格數據行（以 | 開頭和結尾，且不是分隔符行）
            if (
                self._is_table_line(line)
                and stripped.endswith("|")
                and not (
                    stripped.startswith("|")
                    and stripped.endswith("|")
                    and re.match(r"^\|[\s\-\|]*\|$", stripped)
                )
            ):
                # 檢查管道符號前後是否有正確的空格
                # 查找缺少空格的管道符號
                if re.search(r"[^|\s]\|[^|\s]", stripped):
                    issues.append(
                        {
                            "line": i + 1,
                            "content": stripped,
                            "problem": "管道符號前後缺少空格",
                        }
                    )

        if issues:
            print("🔍 發現表格管道符號樣式問題 (MD055):")
            for issue in issues:
                print(f"  第{issue['line']}行: {issue['problem']}")
                print(f"    內容: {issue['content']}")
            print("  💡 建議: 表格中管道符號前後應各有一個空格")
            print()

        return content

    def _detect_table_multiline_cells(self, content: str) -> str:
        """檢測表格單元格跨越多行問題 (MD056) - 輸出警告但不修改"""
        lines = content.split("\n")
        issues = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 檢查是否為表格數據行（以 | 開頭，但可能沒有正確閉合）
            if (
                self._is_table_line(line)
                and "|" in stripped
                and not (
                    stripped.startswith("|")
                    and stripped.endswith("|")
                    and re.match(r"^\|[\s\-\|]*\|$", stripped)
                )
            ):
                # 如果這行沒有以 | 結束，可能是單元格內容未閉合
                if not stripped.endswith("|"):
                    issues.append(
                        {
                            "line": i + 1,
                            "content": stripped,
                            "problem": "表格行缺少右邊界管道符號",
                        }
                    )

                # 檢查下一行是否為空行或跨越多行的內容
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()

                    # 如果下一行是空行，且當前行沒有正確閉合
                    if not next_line and not stripped.endswith("|"):
                        issues.append(
                            {
                                "line": i + 2,  # 空行的行號
                                "content": "",
                                "problem": "表格單元格內容中包含空行",
                            }
                        )

                    # 如果下一行不以 | 開始但有內容，且當前行沒有正確閉合
                    elif (
                        next_line
                        and not next_line.startswith("|")
                        and not next_line.startswith("#")
                        and not stripped.endswith("|")
                    ):
                        issues.append(
                            {
                                "line": i + 2,
                                "content": next_line,
                                "problem": "表格單元格內容跨越多行",
                            }
                        )

        if issues:
            print("🔍 發現表格單元格跨越多行問題 (MD056):")
            for issue in issues:
                print(f"  第{issue['line']}行: {issue['problem']}")
                if issue["content"]:
                    print(f"    內容: {issue['content']}")
            print("  💡 建議: 表格單元格內容應在一行內，使用 <br> 標籤表示換行")
            print()

        return content

    def _detect_inline_html(self, content: str) -> str:
        """檢測內聯HTML問題 (MD033) - 輸出警告但不修改"""
        import re

        lines = content.split("\n")
        issues = []

        # HTML標籤的正則表達式
        html_tag_pattern = re.compile(r"<[^>]+>")

        for i, line in enumerate(lines):
            # 查找HTML標籤
            matches = html_tag_pattern.findall(line)
            if matches:
                for match in matches:
                    issues.append(
                        {
                            "line": i + 1,
                            "content": line.strip(),
                            "problem": f"發現內聯HTML標籤: {match}",
                        }
                    )

        if issues:
            print("🔍 發現內聯HTML問題 (MD033):")
            for issue in issues:
                print(f"  第{issue['line']}行: {issue['problem']}")
                print(f"    內容: {issue['content']}")
            print("  💡 建議: 避免在Markdown中使用內聯HTML標籤")
            print()

        return content

    def _detect_line_length(self, content: str) -> str:
        """檢測行長度問題 (MD013) - 輸出警告但不修改"""
        lines = content.split("\n")
        max_length = self.max_line_length
        issues = []

        for i, line in enumerate(lines):
            # 跳過程式碼區塊、標題、列表等不應換行的特殊行，但保留表格行檢測
            if (
                line.strip().startswith("```")
                or self._is_header_line(line)  # 標題
                or self._is_unordered_list_line(line)  # 無序列表
                or self._is_ordered_list_line(line)  # 有序列表
                or line.strip() == ""
            ):  # 空行
                continue

            # 檢查行長度（包括表格行）
            if len(line) > max_length:
                issues.append(
                    {
                        "line": i + 1,
                        "length": len(line),
                        "content": line[:80] + "..." if len(line) > 80 else line,
                    }
                )

        if issues:
            print(f"🔍 發現行長度問題 (MD013 - 超過 {max_length} 字符):")
            for issue in issues:
                print(f"  第{issue['line']}行: {issue['length']} 字符")
                print(f"    內容: {issue['content']}")
            print(f"  💡 建議: 將長行拆分為多行，每行不超過 {max_length} 字符")
            print()

        return content
