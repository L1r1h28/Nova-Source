"""Nova 工具函數

提供通用的工具函數和裝飾器。
"""

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Tuple

from nova.core.logging import get_logger


def timer(func: Callable) -> Callable:
    """計時裝飾器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = get_logger(func.__module__)

        try:
            logger.debug(f"開始執行: {func.__name__}")
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"執行完成: {func.__name__}, 耗時: {elapsed:.4f} 秒")
            return result
        except Exception:
            elapsed = time.time() - start_time
            logger.error(f"執行失敗: {func.__name__}, 耗時: {elapsed:.4f} 秒")
            raise

    return wrapper


@contextmanager
def time_context(description: str = "操作"):
    """時間上下文管理器"""
    logger = get_logger()
    start_time = time.time()

    logger.debug(f"開始{description}")
    try:
        yield
        elapsed = time.time() - start_time
        logger.debug(f"{description}完成, 耗時: {elapsed:.4f} 秒")
    except Exception:
        elapsed = time.time() - start_time
        logger.error(f"{description}失敗, 耗時: {elapsed:.4f} 秒")
        raise
    finally:
        pass


def cache_result(ttl_seconds: int = 300):
    """結果快取裝飾器"""

    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Tuple[Any, float]] = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 創建快取鍵
            cache_key = str((args, tuple(sorted(kwargs.items()))))

            # 檢查快取
            if cache_key in cache:
                cached_result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl_seconds:
                    return cached_result

            # 執行函數並快取結果
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())

            # 清理過期快取
            current_time = time.time()
            expired_keys = [
                key
                for key, (_, timestamp) in cache.items()
                if current_time - timestamp >= ttl_seconds
            ]
            for key in expired_keys:
                del cache[key]

            return result

        return wrapper

    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重試裝飾器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"嘗試 {attempt + 1} 失敗, {current_delay:.1f} 秒後重試: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"重試 {max_attempts} 次後仍然失敗: {e}")

            # 如果到這裡，說明所有嘗試都失敗了
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError(
                    f"函數 {func.__name__} 在 {max_attempts} 次嘗試後失敗，但沒有捕獲到異常"
                )

        return wrapper

    return decorator


def validate_input(**validators):
    """輸入驗證裝飾器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 驗證位置參數
            arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]
            for i, arg in enumerate(args):
                if i < len(arg_names):
                    param_name = arg_names[i]
                    if param_name in validators:
                        validator = validators[param_name]
                        if not validator(arg):
                            raise ValueError(f"參數 {param_name} 驗證失敗: {arg}")

            # 驗證關鍵字參數
            for param_name, value in kwargs.items():
                if param_name in validators:
                    validator = validators[param_name]
                    if not validator(value):
                        raise ValueError(f"參數 {param_name} 驗證失敗: {value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def format_bytes(size: float) -> str:
    """格式化字節數為人類可讀格式"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def format_duration(seconds: float) -> str:
    """格式化持續時間為人類可讀格式"""
    if seconds < 1.0:
        return f"{seconds:.1f}秒"
    elif seconds < 60.0:
        return f"{seconds:.1f}秒"
    elif seconds < 3600.0:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds:.1f}秒"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}小時{remaining_minutes}分"


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """安全獲取屬性"""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def deep_merge_dicts(base: Dict, update: Dict) -> Dict:
    """深度合併字典"""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result
