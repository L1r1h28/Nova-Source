"""Nova 核心配置管理模組

提供統一的配置載入和管理功能。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
import json

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python < 3.11
    except ImportError:
        tomllib = None


@dataclass
class NovaConfig:
    """Nova 統一配置類"""

    # 基本配置
    project_root: Path = field(default_factory=lambda: Path.cwd())
    config_file: Optional[Path] = None

    # 監控配置
    monitoring: Dict[str, Any] = field(default_factory=dict)

    # 測試配置
    testing: Dict[str, Any] = field(default_factory=dict)

    # 審計配置
    auditing: Dict[str, Any] = field(default_factory=dict)

    # 插件配置
    plugins: Dict[str, Any] = field(default_factory=dict)

    # 日誌配置
    logging: Dict[str, Any] = field(default_factory=lambda: {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': None
    })

    def __post_init__(self):
        if self.config_file is None:
            # 自動查找配置文件
            possible_configs = [
                self.project_root / "pyproject.toml",
                self.project_root / "nova.toml",
                self.project_root / "nova.json",
                Path.home() / ".nova" / "config.toml",
                Path.home() / ".nova" / "config.json"
            ]

            for config_path in possible_configs:
                if config_path.exists():
                    self.config_file = config_path
                    break

    def load_config(self) -> 'NovaConfig':
        """載入配置文件"""
        if not self.config_file or not self.config_file.exists():
            return self

        try:
            if self.config_file.suffix == '.toml':
                return self._load_toml_config()
            elif self.config_file.suffix == '.json':
                return self._load_json_config()
            else:
                print(f"⚠️ 不支援的配置文件格式: {self.config_file.suffix}")
                return self
        except Exception as e:
            print(f"⚠️ 載入配置文件失敗: {e}")
            return self

    def _load_toml_config(self) -> 'NovaConfig':
        """載入 TOML 配置"""
        if tomllib is None:
            raise ImportError("需要安裝 tomli 或使用 Python 3.11+")

        if self.config_file is None:
            return self

        with open(self.config_file, 'rb') as f:
            data = tomllib.load(f)

        # 解析 nova 相關配置
        nova_config = data.get('tool', {}).get('nova', {})

        # 更新各模組配置
        if 'monitoring' in nova_config:
            self.monitoring.update(nova_config['monitoring'])
        if 'testing' in nova_config:
            self.testing.update(nova_config['testing'])
        if 'auditing' in nova_config:
            self.auditing.update(nova_config['auditing'])
        if 'plugins' in nova_config:
            self.plugins.update(nova_config['plugins'])
        if 'logging' in nova_config:
            self.logging.update(nova_config['logging'])

        return self

    def _load_json_config(self) -> 'NovaConfig':
        """載入 JSON 配置"""
        if self.config_file is None:
            return self

        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 更新各模組配置
        if 'monitoring' in data:
            self.monitoring.update(data['monitoring'])
        if 'testing' in data:
            self.testing.update(data['testing'])
        if 'auditing' in data:
            self.auditing.update(data['auditing'])
        if 'plugins' in data:
            self.plugins.update(data['plugins'])
        if 'logging' in data:
            self.logging.update(data['logging'])

        return self

    def get_monitoring_config(self) -> Dict[str, Any]:
        """獲取監控配置"""
        defaults = {
            'threshold_normal': 0.85,
            'threshold_critical': 0.95,
            'check_interval': 30,
            'gpu_monitoring': True,
            'continuous_mode': False
        }
        defaults.update(self.monitoring)
        return defaults

    def get_testing_config(self) -> Dict[str, Any]:
        """獲取測試配置"""
        defaults = {
            'iterations': 100,
            'output_dir': 'performance_results',
            'memory_profile': False,
            'system_info': False,
            'discord_notifications': False,
            'discord_webhook': os.environ.get('PING_DISCORD_WEBHOOK_URL')
        }
        defaults.update(self.testing)
        return defaults

    def get_auditing_config(self) -> Dict[str, Any]:
        """獲取審計配置"""
        defaults = {
            'exclude_dirs': ['__pycache__', 'build', 'dist', '.git'],
            'exclude_files': ['*.pyc', '*.pyo', '*.tmp'],
            'detailed_mode': False,
            'auto_fix': False
        }
        defaults.update(self.auditing)
        return defaults

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """獲取插件配置"""
        return self.plugins.get(plugin_name, {})

    def save_config(self, file_path: Optional[Path] = None) -> None:
        """保存配置到文件"""
        save_path = file_path or self.config_file or self.project_root / "nova.json"

        config_data = {
            'monitoring': self.monitoring,
            'testing': self.testing,
            'auditing': self.auditing,
            'plugins': self.plugins,
            'logging': self.logging
        }

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"✅ 配置已保存到: {save_path}")


# 全域配置實例
_config_instance: Optional[NovaConfig] = None


def get_config() -> NovaConfig:
    """獲取全域配置實例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = NovaConfig().load_config()
    return _config_instance


def reload_config() -> NovaConfig:
    """重新載入配置"""
    global _config_instance
    _config_instance = NovaConfig().load_config()
    return _config_instance