"""
Tests for Nova Source Markdown Formatter
"""

import os
import tempfile

import pytest

from nova.markdown.formatter import MarkdownFormatter


class TestMarkdownFormatter:
    """測試Markdown格式化器"""

    def setup_method(self):
        """測試前設置"""
        self.formatter = MarkdownFormatter()

    def test_fix_trailing_spaces(self):
        """測試修復行尾空格"""
        content = "這是測試行   \n另一行    \n"
        expected = "這是測試行\n另一行\n"
        result = self.formatter._fix_trailing_spaces(content)
        assert result == expected

    def test_fix_multiple_blanks(self):
        """測試修復多個連續空行"""
        content = "行1\n\n\n\n行2\n\n\n行3\n"
        expected = "行1\n\n行2\n\n行3\n"
        result = self.formatter._fix_multiple_blanks(content)
        assert result == expected

    def test_fix_blanks_around_headers(self):
        """測試修復標題周圍空行"""
        content = "前文\n# 標題1\n內容1\n## 標題2\n內容2\n"
        expected = "前文\n\n# 標題1\n\n內容1\n\n## 標題2\n\n內容2\n"
        result = self.formatter._fix_blanks_around_headers(content)
        assert result == expected

    def test_fix_blanks_around_lists(self):
        """測試修復清單周圍空行"""
        content = "前文\n- 項目1\n- 項目2\n後文\n"
        expected = "前文\n\n- 項目1\n- 項目2\n\n後文\n"
        result = self.formatter._fix_blanks_around_lists(content)
        assert result == expected

    def test_fix_file_end_newline(self):
        """測試確保檔案以換行符結束"""
        content = "最後一行"
        expected = "最後一行\n"
        result = self.formatter._fix_file_end_newline(content)
        assert result == expected

    def test_fix_no_space_after_hash(self):
        """測試修復井號後無空格"""
        content = "#標題1\n##標題2\n###標題3\n"
        expected = "# 標題1\n## 標題2\n### 標題3\n"
        result = self.formatter._fix_no_space_after_hash(content)
        assert result == expected

    def test_fix_multiple_spaces_after_hash(self):
        """測試修復井號後多個空格"""
        content = "#  標題1\n##   標題2\n"
        expected = "# 標題1\n## 標題2\n"
        result = self.formatter._fix_multiple_spaces_after_hash(content)
        assert result == expected

    def test_fix_header_start_left(self):
        """測試修復標題起始位置"""
        content = "  # 標題1\n    ## 標題2\n"
        expected = "# 標題1\n## 標題2\n"
        result = self.formatter._fix_header_start_left(content)
        assert result == expected

    def test_fix_hard_tabs(self):
        """測試修復硬製表符"""
        content = "行1\t繼續\n行2\t\t結束\n"
        expected = "行1    繼續\n行2        結束\n"
        result = self.formatter._fix_hard_tabs(content)
        assert result == expected

    def test_fix_first_line_header(self):
        """測試修復第一行標題 (MD041)"""
        # 第一行不是標題的情況
        content = "這是標題\n第二行內容\n"
        expected = "# 這是標題\n第二行內容\n"
        result = self.formatter._fix_first_line_header(content)
        assert result == expected

        # 第一行已經是標題的情況
        content = "# 這是標題\n第二行內容\n"
        expected = "# 這是標題\n第二行內容\n"
        result = self.formatter._fix_first_line_header(content)
        assert result == expected

        # 第一行是空行，第二行需要修復的情況
        content = "\n這是標題\n第三行內容\n"
        expected = "\n# 這是標題\n第三行內容\n"
        result = self.formatter._fix_first_line_header(content)
        assert result == expected

    def test_fix_bare_url(self):
        """測試修復裸URL (MD034)"""
        # 裸 URL 應該被包裝在 <>
        content = "請訪問 https://www.example.com 獲取更多資訊\n"
        expected = "請訪問 <https://www.example.com> 獲取更多資訊\n"
        result = self.formatter._fix_bare_url(content)
        assert result == expected

        # 已經在連結語法中的 URL 不應該被修改
        content = "請訪問 [連結](https://www.example.com) 獲取更多資訊\n"
        expected = "請訪問 [連結](https://www.example.com) 獲取更多資訊\n"
        result = self.formatter._fix_bare_url(content)
        assert result == expected

        # 已經在 <> 中的 URL 不應該被修改
        content = "請訪問 <https://www.example.com> 獲取更多資訊\n"
        expected = "請訪問 <https://www.example.com> 獲取更多資訊\n"
        result = self.formatter._fix_bare_url(content)
        assert result == expected

        # 多個 URL 的情況
        content = "請訪問 https://site1.com 和 https://site2.com\n"
        expected = "請訪問 <https://site1.com> 和 <https://site2.com>\n"
        result = self.formatter._fix_bare_url(content)
        assert result == expected

        # 跨行 URL 的情況
        content = "請訪問 <https://www.example.com/very/long/path/that/gets/wrapped->\nto/next/line> 獲取更多資訊\n"
        expected = "請訪問 <https://www.example.com/very/long/path/that/gets/wrapped-to/next/line> 獲取更多資訊\n"
        result = self.formatter._fix_bare_url(content)
        assert result == expected

        # 被自動換行的裸 URL 的情況
        content = "請訪問 https://economictimes.indiatimes.com/tech/artificial-intelligence/anthropic-\nunveils-claude-ai-agent-for-chrome-browser/articleshow/123546136.cms 獲取更多資訊\n"
        expected = "請訪問 <https://economictimes.indiatimes.com/tech/artificial-intelligence/anthropic-unveils-claude-ai-agent-for-chrome-browser/articleshow/123546136.cms> 獲取更多資訊\n"
        result = self.formatter._fix_bare_url(content)
        assert result == expected

    def test_fix_header_style(self):
        """測試修復標題樣式 (MD003)"""
        # ATX 樣式標題應該保持不變
        content = "# 這是標題\n\n## 次標題\n\n內容\n"
        expected = "# 這是標題\n\n## 次標題\n\n內容\n"
        result = self.formatter._fix_header_style(content)
        assert result == expected

        # Setext 樣式標題轉換為 ATX
        content = "這是標題\n=========\n\n次標題\n------\n\n內容\n"
        expected = "# 這是標題\n\n## 次標題\n\n內容\n"
        result = self.formatter._fix_header_style(content)
        assert result == expected

        # 混合樣式，預設轉換為 ATX
        content = "# 主要標題\n\n次要標題\n----\n\n### 三級標題\n"
        expected = "# 主要標題\n\n## 次要標題\n\n### 三級標題\n"
        result = self.formatter._fix_header_style(content)
        assert result == expected

    def test_detect_line_length(self):
        """測試檢測行長度"""
        # 創建一個長行（超過80字符）
        long_line = "這是一個非常長的句子，用來測試行長度檢測功能，希望這個句子能夠超過八十個字元以觸發檢測機制，讓我們繼續添加更多內容直到超過限制。這裡還要添加更多文字來確保長度足夠。"
        content = f"前文\n{long_line}\n後文\n"

        # 捕獲輸出
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            self.formatter._detect_line_length(content)

        output = f.getvalue()

        # 檢查是否檢測到了長行問題
        assert "發現行長度問題 (MD013" in output
        assert "超過 80 字符" in output

    def test_format_file(self):
        """測試格式化檔案"""
        content = "#標題\n\n\n行尾空格   \n\t製表符\n- 項目1\n- 項目2\n內容"

        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = self.formatter.format_file(temp_path)
            assert result is True

            with open(temp_path, encoding="utf-8") as f:
                formatted_content = f.read()

            # 檢查一些關鍵修復
            assert formatted_content.startswith("# 標題")  # MD018
            assert "\n\n\n" not in formatted_content  # MD012
            assert not formatted_content.endswith("   \n")  # MD009
            assert "\t" not in formatted_content  # MD010
            assert "\n\n- 項目1" in formatted_content  # MD032
            assert formatted_content.endswith("\n")  # MD047

        finally:
            os.unlink(temp_path)

    def test_format_directory(self):
        """測試格式化目錄"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 創建測試檔案
            file1_content = "#標題1\n\n\n行尾空格   \n"
            file2_content = "##標題2\n- 項目\n"

            file1_path = os.path.join(temp_dir, "test1.md")
            file2_path = os.path.join(temp_dir, "test2.md")

            with open(file1_path, "w", encoding="utf-8") as f:
                f.write(file1_content)
            with open(file2_path, "w", encoding="utf-8") as f:
                f.write(file2_content)

            # 格式化目錄
            stats = self.formatter.format_directory(temp_dir, recursive=False)

            assert stats["processed"] == 2
            assert stats["formatted"] >= 1  # 至少有一個檔案被格式化
            assert stats["errors"] == 0
            assert len(stats["files"]) == 2

    def test_detect_language(self):
        """測試程式碼語言檢測"""
        # Python
        python_lines = ["def hello():", "    print('Hello')"]
        assert self.formatter._detect_language(python_lines) == "python"

        # JavaScript
        js_lines = ["function hello() {", "    console.log('Hello');", "}"]
        assert self.formatter._detect_language(js_lines) == "javascript"

        # Shell
        shell_lines = ["#!/bin/bash", "apt-get update"]
        assert self.formatter._detect_language(shell_lines) == "bash"

        # SQL
        sql_lines = ["SELECT * FROM users", "WHERE id = 1"]
        assert self.formatter._detect_language(sql_lines) == "sql"

        # JSON
        json_lines = ['{ "name": "test" }']
        assert self.formatter._detect_language(json_lines) == "json"

        # Unknown
        unknown_lines = ["some random text"]
        assert self.formatter._detect_language(unknown_lines) is None

    def test_fix_ol_prefix(self):
        """測試有序列表編號修復"""
        content = """前文

1. 第一項
2. 第二項

新列表
6. 第六項
7. 第七項

結尾"""

        expected = """前文

1. 第一項
2. 第二項

新列表
1. 第六項
2. 第七項

結尾"""

        result = self.formatter._fix_ol_prefix(content)
        assert result == expected

    def test_fix_multiple_headers_same_content_detection(self):
        """測試重複標題檢測"""
        content = """# 第一章
內容1

# 第一章
內容2"""

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = self.formatter._fix_multiple_headers_same_content(content)

        output = f.getvalue()
        assert "發現重複標題問題 (MD024)" in output
        assert "重複標題 '第一章'" in output
        assert result == content  # 不應該修改內容


if __name__ == "__main__":
    pytest.main([__file__])
