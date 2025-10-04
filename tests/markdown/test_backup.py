"""
測試 Markdown 備份管理器
"""

import shutil
import tempfile
from pathlib import Path

from nova.markdown.backup import MarkdownBackupManager


class TestMarkdownBackupManager:
    """測試 MarkdownBackupManager 類別"""

    def setup_method(self):
        """設定測試環境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_manager = MarkdownBackupManager(str(self.temp_dir / "backups"))

        # 創建測試 markdown 檔案
        self.test_md_dir = self.temp_dir / "test_markdown"
        self.test_md_dir.mkdir()

        # 創建測試檔案
        self.test_file1 = self.test_md_dir / "test1.md"
        self.test_file1.write_text("# Test File 1\n\nThis is a test file.")

        self.test_file2 = self.test_md_dir / "test2.md"
        self.test_file2.write_text("# Test File 2\n\nThis is another test file.")

    def teardown_method(self):
        """清理測試環境"""
        shutil.rmtree(self.temp_dir)

    def test_create_backup_single_file(self):
        """測試備份單個檔案"""
        result = self.backup_manager.create_backup(str(self.test_file1))

        assert result["total_files"] == 1
        assert result["backed_up_files"] == 1
        assert result["errors"] == 0
        assert len(result["files"]) == 1

        # 檢查備份檔案是否存在
        backup_name = result["backup_name"]
        backup_dir = self.backup_manager.backup_root / backup_name
        assert backup_dir.exists()

        backup_file = backup_dir / self.test_file1.name
        assert backup_file.exists()
        assert backup_file.read_text() == self.test_file1.read_text()

    def test_create_backup_directory(self):
        """測試備份整個目錄"""
        result = self.backup_manager.create_backup(str(self.test_md_dir))

        assert result["total_files"] == 2
        assert result["backed_up_files"] == 2
        assert result["errors"] == 0
        assert len(result["files"]) == 2

        # 檢查備份檔案是否存在
        backup_name = result["backup_name"]
        backup_dir = self.backup_manager.backup_root / backup_name
        assert backup_dir.exists()

        for original_file in [self.test_file1, self.test_file2]:
            backup_file = backup_dir / original_file.name
            assert backup_file.exists()
            assert backup_file.read_text() == original_file.read_text()

    def test_list_backups(self):
        """測試列出備份"""
        # 創建多個備份
        self.backup_manager.create_backup(str(self.test_file1), "backup_1")
        self.backup_manager.create_backup(str(self.test_file2), "backup_2")

        backups = self.backup_manager.list_backups()

        assert len(backups) == 2
        # 應該按時間戳排序，最新的在前面
        assert backups[0]["name"] == "backup_2"
        assert backups[1]["name"] == "backup_1"

    def test_restore_backup(self):
        """測試恢復備份"""
        # 創建備份
        backup_result = self.backup_manager.create_backup(str(self.test_md_dir))
        backup_name = backup_result["backup_name"]

        # 刪除原始檔案
        self.test_file1.unlink()
        self.test_file2.unlink()

        # 恢復備份
        restore_dir = self.temp_dir / "restore"
        restore_result = self.backup_manager.restore_backup(
            backup_name, str(restore_dir)
        )

        assert restore_result["restored_files"] == 2
        assert restore_result["errors"] == 0

        # 檢查檔案是否恢復
        restored_file1 = restore_dir / self.test_file1.name
        restored_file2 = restore_dir / self.test_file2.name

        assert restored_file1.exists()
        assert restored_file2.exists()
        assert restored_file1.read_text() == "# Test File 1\n\nThis is a test file."
        assert (
            restored_file2.read_text() == "# Test File 2\n\nThis is another test file."
        )

    def test_incremental_backup(self):
        """測試增量備份"""
        # 第一次備份
        result1 = self.backup_manager.create_backup(
            str(self.test_file1), incremental=True
        )
        assert result1["backed_up_files"] == 1

        # 第二次備份（檔案未改變）
        result2 = self.backup_manager.create_backup(
            str(self.test_file1), incremental=True
        )
        assert result2["skipped_files"] == 1
        assert result2["backed_up_files"] == 0

        # 修改檔案後備份
        self.test_file1.write_text("# Test File 1\n\nThis is a modified test file.")
        result3 = self.backup_manager.create_backup(
            str(self.test_file1), incremental=True
        )
        assert result3["backed_up_files"] == 1
        assert result3["skipped_files"] == 0

    def test_cleanup_old_backups(self):
        """測試清理舊備份"""
        # 創建多個備份
        for i in range(5):
            self.backup_manager.create_backup(str(self.test_file1), f"backup_{i}")

        # 清理，只保留最新的 2 個，設定保留期限為 0 天來強制刪除
        result = self.backup_manager.cleanup_old_backups(keep_days=0, keep_count=2)

        assert result["removed_backups"] == 3  # 應該刪除 3 個舊備份

        backups = self.backup_manager.list_backups()
        assert len(backups) == 2
