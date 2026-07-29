"""Telegram Bot notification driver implementation."""

import os
import httpx
from lunardump.config.schema import NotificationChannelConfig
from lunardump.core.utils.logger import logger


class TelegramNotifier:
    """Telegram Bot notification sender."""

    def __init__(self, config: NotificationChannelConfig):
        self.config = config
        self.bot_token = (
            os.getenv(self.config.bot_token_env) if self.config.bot_token_env else None
        )
        self.chat_id = self.config.chat_id

    def send_message(self, message: str) -> bool:
        """Send Markdown formatted text message to Telegram channel/chat."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram notification skipped: missing bot token or chat ID.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as err:
            logger.error(f"Failed to send Telegram notification: {err}")
            return False
