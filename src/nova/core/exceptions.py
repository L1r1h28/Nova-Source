"""Nova 自定義異常

定義 Nova 框架使用的自定義異常類。
"""


class NovaError(Exception):
    """Nova 基礎異常類"""
    pass


class ConfigError(NovaError):
    """配置相關錯誤"""
    pass


class PluginError(NovaError):
    """插件相關錯誤"""
    pass


class MonitoringError(NovaError):
    """監控相關錯誤"""
    pass


class TestingError(NovaError):
    """測試相關錯誤"""
    pass


class AuditingError(NovaError):
    """審計相關錯誤"""
    pass


class NotificationError(NovaError):
    """通知相關錯誤"""
    pass


class ValidationError(NovaError):
    """驗證錯誤"""
    pass


def handle_exception(exc: Exception, logger=None, re_raise: bool = True) -> None:
    """統一異常處理函數"""
    if logger:
        logger.error(f"發生異常: {type(exc).__name__}: {exc}")
        import traceback
        logger.debug(f"異常詳情:\n{traceback.format_exc()}")

    if re_raise:
        raise exc


def safe_execute(func, *args, logger=None, **kwargs):
    """安全執行函數，捕獲並處理異常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, logger, re_raise=False)
        return None