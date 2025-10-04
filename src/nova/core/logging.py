"""Nova 日誌系統

提供統一的日誌配置和處理。
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional

from .config import get_config


class NovaLogger:
    """Nova 日誌管理器"""

    def __init__(self):
        self.config = get_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._initialized = False

    def initialize(self) -> None:
        """初始化日誌系統"""
        if self._initialized:
            return

        log_config = self.config.logging

        # 設定根日誌器
        root_logger = logging.getLogger('nova')
        root_logger.setLevel(getattr(logging, log_config['level'].upper(), logging.INFO))

        # 清除現有處理器
        root_logger.handlers.clear()

        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(log_config['format'])
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 檔案處理器（如果指定）
        if log_config.get('file'):
            log_file = Path(log_config['file'])
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_formatter = logging.Formatter(log_config['format'])
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        self._initialized = True

    def get_logger(self, name: str) -> logging.Logger:
        """獲取指定名稱的日誌器"""
        if not self._initialized:
            self.initialize()

        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(f'nova.{name}')

        return self.loggers[name]

    def set_level(self, level: str) -> None:
        """設定日誌等級"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger('nova').setLevel(log_level)

    def enable_file_logging(self, file_path: Path) -> None:
        """啟用檔案日誌"""
        root_logger = logging.getLogger('nova')

        # 檢查是否已經有檔案處理器
        for handler in root_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                return  # 已經存在

        # 添加檔案處理器
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )

        formatter = logging.Formatter(self.config.logging['format'])
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# 全域日誌器實例
_logger_instance: Optional[NovaLogger] = None


def get_logger(name: str = 'main') -> logging.Logger:
    """獲取日誌器"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = NovaLogger()
    return _logger_instance.get_logger(name)


def initialize_logging() -> None:
    """初始化日誌系統"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = NovaLogger()
    _logger_instance.initialize()


# 便捷函數
def debug(message: str, *args, **kwargs) -> None:
    """調試日誌"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs) -> None:
    """資訊日誌"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs) -> None:
    """警告日誌"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs) -> None:
    """錯誤日誌"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs) -> None:
    """嚴重錯誤日誌"""
    get_logger().critical(message, *args, **kwargs)