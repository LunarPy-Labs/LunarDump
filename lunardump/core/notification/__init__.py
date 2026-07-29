"""Notification dispatcher package."""

from lunardump.config.schema import NotificationConfig
from lunardump.core.notification.telegram import TelegramNotifier
from lunardump.core.notification.slack import SlackNotifier
from lunardump.core.utils.logger import logger


def notify_event(
    config: NotificationConfig, message: str, status: str = "success"
) -> None:
    """Dispatch telemetry notification to configured channels.

    Args:
        config: NotificationConfig.
        message: Markdown message content.
        status: "success" or "failure".
    """
    if status == "success" and not config.on_success:
        return
    if status == "failure" and not config.on_failure:
        return

    for channel in config.channels:
        if channel.type == "telegram":
            notifier = TelegramNotifier(channel)
            notifier.send_message(message)
        elif channel.type == "slack":
            notifier = SlackNotifier(channel)
            notifier.send_message(message, status=status)
        else:
            logger.warning(f"Unknown notification channel type: {channel.type}")


__all__ = [
    "TelegramNotifier",
    "SlackNotifier",
    "notify_event",
]
