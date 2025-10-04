"""
Markdown Backup Module for Nova Source

Provides comprehensive backup and restore functionality for markdown files.
Supports incremental backups, timestamp versioning, and automated cleanup.
"""

import hashlib
import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MarkdownBackupManager:
    """Markdown檔案備份管理器"""

    def __init__(self, backup_root: str = "./backups"):
        """
        初始化備份管理器

        Args:
            backup_root: 備份根目錄
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.backup_root / "backup_manifest.json"
        self._load_manifest()

    def _load_manifest(self):
        """載入備份清單"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, encoding="utf-8") as f:
                    self.manifest = json.load(f)
            except Exception as e:
                logger.warning(f"載入備份清單失敗: {e}")
                self.manifest = {}
        else:
            self.manifest = {}

    def _save_manifest(self):
        """儲存備份清單"""
        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"儲存備份清單失敗: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """計算檔案雜湊值"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"計算檔案雜湊失敗 {file_path}: {e}")
            return ""

    def _get_timestamp(self) -> str:
        """獲取當前時間戳"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_backup(
        self,
        source_path: str,
        backup_name: Optional[str] = None,
        incremental: bool = True,
    ) -> Dict[str, Any]:
        """
        創建備份

        Args:
            source_path: 來源檔案或目錄路徑
            backup_name: 備份名稱（可選）
            incremental: 是否增量備份

        Returns:
            備份結果統計
        """
        source_path_obj = Path(source_path)
        if not source_path_obj.exists():
            raise FileNotFoundError(f"來源路徑不存在: {source_path_obj}")

        # 生成備份名稱
        if backup_name is None:
            timestamp = self._get_timestamp()
            backup_name = f"backup_{timestamp}"

        backup_dir = self.backup_root / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        stats = {
            "backup_name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "source_path": str(source_path_obj),
            "total_files": 0,
            "backed_up_files": 0,
            "skipped_files": 0,
            "errors": 0,
            "files": [],
        }

        try:
            if source_path_obj.is_file():
                # 備份單個檔案
                result = self._backup_single_file(
                    source_path_obj, backup_dir, incremental
                )
                stats.update(result)
            else:
                # 備份目錄
                result = self._backup_directory(
                    source_path_obj, backup_dir, incremental
                )
                stats.update(result)

            # 更新清單
            self.manifest[backup_name] = {
                "timestamp": stats["timestamp"],
                "source_path": stats["source_path"],
                "stats": stats,
                "incremental": incremental,
            }
            self._save_manifest()

            logger.info(f"備份完成: {backup_name}")
            return stats

        except Exception as e:
            logger.error(f"備份失敗: {e}")
            stats["errors"] += 1
            return stats

    def _backup_single_file(
        self, source_file: Path, backup_dir: Path, incremental: bool
    ) -> Dict[str, Any]:
        """備份單個檔案"""
        stats = {
            "total_files": 1,
            "backed_up_files": 0,
            "skipped_files": 0,
            "errors": 0,
            "files": [],
        }

        try:
            # 檢查是否需要備份
            if incremental:
                current_hash = self._calculate_file_hash(str(source_file))
                last_backup = self._get_last_backup_info(str(source_file))

                if last_backup and last_backup.get("hash") == current_hash:
                    stats["skipped_files"] = 1
                    stats["files"].append(
                        {
                            "path": str(source_file),
                            "status": "skipped",
                            "reason": "unchanged",
                        }
                    )
                    return stats

            # 複製檔案
            backup_file = backup_dir / source_file.name
            shutil.copy2(source_file, backup_file)

            # 記錄檔案資訊
            file_info = {
                "path": str(source_file),
                "backup_path": str(backup_file),
                "size": source_file.stat().st_size,
                "hash": self._calculate_file_hash(str(source_file)),
                "status": "backed_up",
            }

            stats["backed_up_files"] = 1
            stats["files"].append(file_info)

        except Exception as e:
            logger.error(f"備份檔案失敗 {source_file}: {e}")
            stats["errors"] = 1
            stats["files"].append(
                {"path": str(source_file), "status": "error", "error": str(e)}
            )

        return stats

    def _is_file_unchanged(self, source_file: Path, backup_dir: Path) -> bool:
        """
        檢查檔案是否未改變

        Args:
            source_file: 來源檔案路徑
            backup_dir: 備份目錄

        Returns:
            如果檔案未改變則返回 True
        """
        try:
            # 計算檔案雜湊
            current_hash = self._calculate_file_hash(str(source_file))

            # 檢查最後備份中的雜湊
            last_backup = self._get_last_backup_info(str(source_file))
            if last_backup and last_backup.get("hash") == current_hash:
                return True

            return False

        except Exception as e:
            logger.warning(f"檢查檔案變化失敗 {source_file}: {e}")
            return False

    def _backup_directory(
        self, source_dir: Path, backup_dir: Path, incremental: bool
    ) -> Dict[str, Any]:
        """備份整個目錄"""
        stats = {
            "total_files": 0,
            "backed_up_files": 0,
            "skipped_files": 0,
            "errors": 0,
            "files": [],
        }

        # 遍歷所有markdown檔案
        for md_file in source_dir.rglob("*.md"):
            stats["total_files"] += 1

            try:
                # 計算相對路徑以保持目錄結構
                relative_path = md_file.relative_to(source_dir)
                backup_file = backup_dir / relative_path

                # 確保備份目錄存在
                backup_file.parent.mkdir(parents=True, exist_ok=True)

                # 檢查是否需要備份
                if incremental:
                    current_hash = self._calculate_file_hash(str(md_file))
                    last_backup = self._get_last_backup_info(str(md_file))

                    if last_backup and last_backup.get("hash") == current_hash:
                        stats["skipped_files"] += 1
                        stats["files"].append(
                            {
                                "path": str(md_file),
                                "status": "skipped",
                                "reason": "unchanged",
                            }
                        )
                        continue

                # 複製檔案
                shutil.copy2(md_file, backup_file)

                # 記錄檔案資訊
                file_info = {
                    "path": str(md_file),
                    "backup_path": str(backup_file),
                    "size": md_file.stat().st_size,
                    "hash": self._calculate_file_hash(str(md_file)),
                    "status": "backed_up",
                }

                stats["backed_up_files"] += 1
                stats["files"].append(file_info)

            except Exception as e:
                logger.error(f"備份檔案失敗 {md_file}: {e}")
                stats["errors"] += 1
                stats["files"].append(
                    {"path": str(md_file), "status": "error", "error": str(e)}
                )

        return stats

    def _get_last_backup_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """獲取檔案最後備份資訊"""
        for _backup_name, backup_info in reversed(self.manifest.items()):
            for file_info in backup_info.get("stats", {}).get("files", []):
                if file_info.get("path") == file_path:
                    return file_info
        return None

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有備份"""
        backups = []
        for backup_name, info in self.manifest.items():
            backups.append(
                {
                    "name": backup_name,
                    "timestamp": info.get("timestamp"),
                    "source_path": info.get("source_path"),
                    "incremental": info.get("incremental", False),
                    "stats": info.get("stats", {}),
                }
            )

        # 按時間戳排序
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups

    def restore_backup(
        self, backup_name: str, restore_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        恢復備份

        Args:
            backup_name: 備份名稱
            restore_path: 恢復目標路徑（可選）

        Returns:
            恢復結果統計
        """
        if backup_name not in self.manifest:
            raise ValueError(f"備份不存在: {backup_name}")

        backup_info = self.manifest[backup_name]
        backup_dir = self.backup_root / backup_name

        if not backup_dir.exists():
            raise FileNotFoundError(f"備份目錄不存在: {backup_dir}")

        # 確定恢復路徑
        if restore_path is None:
            source_path = backup_info.get("source_path")
            if source_path is None:
                raise ValueError(f"備份 {backup_name} 沒有來源路徑資訊")
            restore_path = str(source_path)

        restore_path_obj = Path(restore_path)
        stats = {
            "backup_name": backup_name,
            "restore_path": str(restore_path_obj),
            "restored_files": 0,
            "errors": 0,
            "files": [],
        }

        try:
            # 遍歷備份檔案
            for root, _dirs, files in os.walk(backup_dir):
                for file in files:
                    backup_file = Path(root) / file

                    try:
                        # 計算相對路徑
                        relative_path = backup_file.relative_to(backup_dir)
                        target_file = restore_path / relative_path

                        # 確保目標目錄存在
                        target_file.parent.mkdir(parents=True, exist_ok=True)

                        # 複製檔案
                        shutil.copy2(backup_file, target_file)

                        stats["restored_files"] += 1
                        stats["files"].append(
                            {
                                "backup_path": str(backup_file),
                                "restore_path": str(target_file),
                                "status": "restored",
                            }
                        )

                    except Exception as e:
                        logger.error(f"恢復檔案失敗 {backup_file}: {e}")
                        stats["errors"] += 1
                        stats["files"].append(
                            {
                                "backup_path": str(backup_file),
                                "status": "error",
                                "error": str(e),
                            }
                        )

            logger.info(f"恢復完成: {backup_name} -> {restore_path}")
            return stats

        except Exception as e:
            logger.error(f"恢復失敗: {e}")
            stats["errors"] += 1
            return stats

    def cleanup_old_backups(
        self, keep_days: int = 30, keep_count: int = 10
    ) -> Dict[str, Any]:
        """
        清理舊備份

        Args:
            keep_days: 保留天數
            keep_count: 最少保留數量

        Returns:
            清理結果統計
        """
        stats = {"removed_backups": 0, "freed_space": 0, "errors": 0}

        try:
            # 獲取所有備份
            backups = self.list_backups()

            if len(backups) <= keep_count:
                logger.info(
                    f"備份數量 ({len(backups)}) 小於等於保留數量 ({keep_count})，跳過清理"
                )
                return stats

            # 計算保留期限
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            # 識別要刪除的備份
            to_remove = []
            for backup in backups[keep_count:]:  # 保留最新的 keep_count 個
                backup_date = datetime.fromisoformat(backup["timestamp"])
                if backup_date < cutoff_date:
                    to_remove.append(backup)

            # 刪除舊備份
            for backup in to_remove:
                try:
                    backup_dir = self.backup_root / backup["name"]
                    if backup_dir.exists():
                        # 計算目錄大小
                        total_size = sum(
                            f.stat().st_size
                            for f in backup_dir.rglob("*")
                            if f.is_file()
                        )

                        # 刪除目錄
                        shutil.rmtree(backup_dir)

                        # 從清單中移除
                        if backup["name"] in self.manifest:
                            del self.manifest[backup["name"]]

                        stats["removed_backups"] += 1
                        stats["freed_space"] += total_size

                        logger.info(
                            f"刪除舊備份: {backup['name']} ({total_size} bytes)"
                        )

                except Exception as e:
                    logger.error(f"刪除備份失敗 {backup['name']}: {e}")
                    stats["errors"] += 1

            # 儲存更新後的清單
            self._save_manifest()

            logger.info(
                f"清理完成: 刪除 {stats['removed_backups']} 個備份，釋放 {stats['freed_space']} bytes"
            )
            return stats

        except Exception as e:
            logger.error(f"清理失敗: {e}")
            stats["errors"] += 1
            return stats

    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """獲取備份詳細資訊"""
        return self.manifest.get(backup_name)

    def compare_backups(self, backup1: str, backup2: str) -> Dict[str, Any]:
        """比較兩個備份的差異"""
        if backup1 not in self.manifest or backup2 not in self.manifest:
            raise ValueError("備份不存在")

        info1 = self.manifest[backup1]
        info2 = self.manifest[backup2]

        # 建立檔案映射
        files1 = {
            f["path"]: f
            for f in info1.get("stats", {}).get("files", [])
            if f["status"] == "backed_up"
        }
        files2 = {
            f["path"]: f
            for f in info2.get("stats", {}).get("files", [])
            if f["status"] == "backed_up"
        }

        comparison = {
            "backup1": backup1,
            "backup2": backup2,
            "added": [],
            "removed": [],
            "modified": [],
            "unchanged": [],
        }

        # 找出新增和修改的檔案
        for path, info2 in files2.items():
            if path not in files1:
                comparison["added"].append({"path": path, "info": info2})
            elif files1[path]["hash"] != info2["hash"]:
                comparison["modified"].append(
                    {
                        "path": path,
                        "old_hash": files1[path]["hash"],
                        "new_hash": info2["hash"],
                    }
                )
            else:
                comparison["unchanged"].append({"path": path, "info": info2})

        # 找出刪除的檔案
        for path, info1 in files1.items():
            if path not in files2:
                comparison["removed"].append({"path": path, "info": info1})

        return comparison
