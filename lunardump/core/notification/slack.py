"""Slack Webhook notification driver implementation."""

import httpx
from lunardump.config.schema import NotificationChannelConfig
from lunardump.core.utils.logger import logger


class SlackNotifier:
    """Slack Webhook notification sender."""

    def __init__(self, config: NotificationChannelConfig):
        self.config = config
        self.webhook_url = self.config.webhook_url

    def send_message(self, message: str, status: str = "success") -> bool:
        """Send formatted webhook message to Slack."""
        if not self.webhook_url:
            logger.warning("Slack notification skipped: missing webhook URL.")
            return False

        color = "#36a64f" if status == "success" else "#ff0000"
        title = "🚀 Backup Successful" if status == "success" else "❌ Backup Failed"

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"LunarDump Telemetry - {title}",
                    "text": message,
                    "mrkdwn_in": ["text"],
                }
            ]
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as err:
            logger.error(f"Failed to send Slack notification: {err}")
            return False
