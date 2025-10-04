"""Nova 插件系統

提供可擴展的插件架構，支持動態載入和配置。
"""

import importlib
import inspect
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..core.config import get_config


class PluginBase(ABC):
    """插件基類"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.enabled = True

    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理插件資源"""
        pass

    def is_enabled(self) -> bool:
        """檢查插件是否啟用"""
        return self.enabled

    def get_config(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return self.config.get(key, default)


class NotificationPlugin(PluginBase):
    """通知插件基類"""

    @abstractmethod
    def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """發送通知"""
        pass


class MonitoringPlugin(PluginBase):
    """監控插件基類"""

    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """收集指標"""
        pass


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_types: Dict[str, Type[PluginBase]] = {}
        self.config = get_config()

    def register_plugin_type(
        self, plugin_type: str, base_class: Type[PluginBase]
    ) -> None:
        """註冊插件類型"""
        self.plugin_types[plugin_type] = base_class

    def load_plugins(self, plugin_type: str) -> None:
        """載入指定類型的插件"""
        if plugin_type not in self.plugin_types:
            raise ValueError(f"未知的插件類型: {plugin_type}")

        base_class = self.plugin_types[plugin_type]
        plugin_configs = self.config.get_plugin_config(plugin_type)

        # 從配置中載入插件
        for plugin_name, plugin_config in plugin_configs.items():
            if plugin_config.get("enabled", True):
                self._load_plugin(plugin_name, plugin_config, base_class)

        # 自動發現內建插件
        self._discover_builtin_plugins(plugin_type, base_class)

    def _load_plugin(
        self, name: str, config: Dict[str, Any], base_class: Type[PluginBase]
    ) -> None:
        """載入單個插件"""
        try:
            module_name = config.get("module")
            class_name = config.get("class", f"{name.capitalize()}Plugin")

            if module_name:
                # 從模組載入
                module = importlib.import_module(module_name)
                plugin_class = getattr(module, class_name)
            else:
                # 嘗試從內建插件載入
                plugin_class = self._find_builtin_plugin_class(name, base_class)

            if plugin_class and issubclass(plugin_class, base_class):
                plugin_instance = plugin_class(name, config)
                if plugin_instance.initialize():
                    self.plugins[name] = plugin_instance
                    print(f"✅ 插件載入成功: {name}")
                else:
                    print(f"❌ 插件初始化失敗: {name}")
            else:
                print(f"❌ 插件類無效: {name}")

        except Exception as e:
            print(f"❌ 載入插件失敗 {name}: {e}")

    def _find_builtin_plugin_class(
        self, name: str, base_class: Type[PluginBase]
    ) -> Optional[Type[PluginBase]]:
        """查找內建插件類"""
        # 從 plugins 目錄查找
        plugins_dir = Path(__file__).parent

        for _, module_name, _ in pkgutil.iter_modules([str(plugins_dir)]):
            try:
                module = importlib.import_module(f"nova.plugins.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, base_class)
                        and attr.__name__.lower().startswith(name.lower())
                    ):
                        return attr
            except ImportError:
                continue

        return None

    def _discover_builtin_plugins(
        self, plugin_type: str, base_class: Type[PluginBase]
    ) -> None:
        """自動發現內建插件"""
        plugins_dir = Path(__file__).parent / plugin_type

        if not plugins_dir.exists():
            return

        for py_file in plugins_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            module_name = f"nova.plugins.{plugin_type}.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, base_class)
                        and not attr_name.endswith("Plugin")
                    ):  # 避免載入基類
                        plugin_name = attr_name.lower().replace("plugin", "")
                        if plugin_name not in self.plugins:  # 避免重複載入
                            plugin_instance = attr(plugin_name)
                            if plugin_instance.initialize():
                                self.plugins[plugin_name] = plugin_instance
                                print(f"✅ 內建插件載入成功: {plugin_name}")

            except ImportError as e:
                print(f"⚠️ 無法載入插件模組 {module_name}: {e}")

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """獲取插件實例"""
        return self.plugins.get(name)

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """獲取指定類型的所有插件"""
        base_class = self.plugin_types.get(plugin_type)
        if not base_class:
            return []

        return [
            plugin for plugin in self.plugins.values() if isinstance(plugin, base_class)
        ]

    def enable_plugin(self, name: str) -> bool:
        """啟用插件"""
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enabled = True
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """停用插件"""
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enabled = False
            return True
        return False

    def cleanup_all(self) -> None:
        """清理所有插件"""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"⚠️ 清理插件失敗 {plugin.name}: {e}")

        self.plugins.clear()


# 全域插件管理器實例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """獲取全域插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
        # 註冊內建插件類型
        _plugin_manager.register_plugin_type("notifications", NotificationPlugin)
        _plugin_manager.register_plugin_type("monitoring", MonitoringPlugin)
    return _plugin_manager


def initialize_plugins() -> None:
    """初始化所有插件"""
    manager = get_plugin_manager()
    manager.load_plugins("notifications")
    manager.load_plugins("monitoring")


def cleanup_plugins() -> None:
    """清理所有插件"""
    manager = get_plugin_manager()
    manager.cleanup_all()
