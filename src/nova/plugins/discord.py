# nova/plugins/discord.py
"""
Discord 通知插件
基於原有的 discord_notifier.py 實現
"""

import logging
import os
import time
from typing import Any, Dict, Optional

import requests

from . import NotificationPlugin


class DiscordNotificationPlugin(NotificationPlugin):
    """Discord 通知插件"""

    def __init__(self, name: str = "discord", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.logger = logging.getLogger(f"nova.plugins.{name}")
        webhook_url = self.config.get('webhook_url') or os.environ.get("PING_DISCORD_WEBHOOK_URL")

        if not webhook_url:
            raise ValueError("Discord webhook URL 必須通過環境變數 PING_DISCORD_WEBHOOK_URL 或配置 webhook_url 設置")

        self.webhook_url: str = webhook_url

        # 預設值與圖示 URL
        self.defaults = {
            'general': {
                'username': "系統通知",
                'title': "📢 系統通知",
                'color': 3447003,  # Discord 藍色
                'avatar': "https://cdn-icons-png.flaticon.com/512/7005/7005115.png"
            },
            'success': {
                'username': "任務進度",
                'title': "✅ 任務進度報告",
                'color': 5814783,  # Discord 綠色
                'avatar': "https://cdn-icons-png.flaticon.com/512/190/190411.png"
            },
            'error': {
                'username': "🚨 系統錯誤",
                'title': "🚨 程式錯誤警報",
                'color': 15548997,  # Discord 紅色
                'avatar': "https://cdn-icons-png.flaticon.com/512/190/190406.png"
            }
        }

        # 自動判斷模式的關鍵字
        self.error_keywords = {"錯誤", "失敗", "異常", "Error", "Failed", "Exception", "timeout", "逾時", "崩潰"}
        self.success_keywords = {"成功", "完成", "已完成", "Success", "Done", "Completed", "ok", "OK"}

    def _auto_detect_mode(self, message: str) -> str:
        """自動判斷通知模式"""
        message_lower = message.lower()

        # 檢查錯誤關鍵字
        if any(keyword in message_lower for keyword in self.error_keywords):
            return 'error'

        # 檢查成功關鍵字
        if any(keyword in message_lower for keyword in self.success_keywords):
            return 'success'

        return 'general'

    def _extract_auto_title(self, message: str, max_length: int = 50) -> str:
        """自動提取標題"""
        # 查找第一個句子結尾
        ending_punctuations = ['。', '！', '？', '.', '!', '?']

        for punct in ending_punctuations:
            if punct in message:
                title = message.split(punct)[0] + punct
                if len(title) <= max_length:
                    return title

        # 如果沒有找到標點，使用前N個字符
        return message[:max_length] + "..." if len(message) > max_length else message

    def send_notification(self, title: Optional[str] = None, message: str = "",
                         mode: Optional[str] = None, **kwargs) -> bool:
        """發送 Discord 通知"""
        try:
            # 自動判斷模式
            if mode is None:
                mode = self._auto_detect_mode(message)

            # 獲取模式設定
            mode_config = self.defaults.get(mode, self.defaults['general'])

            # 自動提取標題
            if title is None:
                title = self._extract_auto_title(message)

            # 構建 payload
            payload = {
                "username": mode_config['username'],
                "avatar_url": mode_config['avatar'],
                "embeds": [{
                    "title": title,
                    "description": message,
                    "color": mode_config['color'],
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
                }]
            }

            # 發送請求
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 204:
                self.logger.info(f"✅ Discord 通知發送成功 (模式: {mode})")
                return True
            else:
                self.logger.error(f"❌ Discord 通知發送失敗: HTTP {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Discord 通知異常: {e}")
            return False

    def send_success(self, title: str, message: str) -> bool:
        """發送成功通知"""
        return self.send_notification(title, message, mode='success')

    def send_error(self, title: str, message: str) -> bool:
        """發送錯誤通知"""
        return self.send_notification(title, message, mode='error')

    def initialize(self) -> bool:
        """初始化插件"""
        try:
            # 檢查 webhook URL
            if not self.webhook_url:
                self.logger.error("Discord webhook URL 未設置")
                return False

            self.logger.info("Discord 插件初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"Discord 插件初始化失敗: {e}")
            return False

    def cleanup(self) -> None:
        """清理插件資源"""
        self.logger.info("Discord 插件清理完成")
