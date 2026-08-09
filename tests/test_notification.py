"""Unit tests for Webhook Notification channels."""

from unittest.mock import patch, MagicMock
from lunardump.config.schema import NotificationConfig, NotificationChannelConfig
from lunardump.core.notification import TelegramNotifier, SlackNotifier, notify_event


def test_telegram_notifier(monkeypatch):
    monkeypatch.setenv("TEST_TG_TOKEN", "123456:ABC-DEF")
    cfg = NotificationChannelConfig(
        type="telegram", bot_token_env="TEST_TG_TOKEN", chat_id="-100123"
    )
    notifier = TelegramNotifier(cfg)
    assert notifier.bot_token == "123456:ABC-DEF"

    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = notifier.send_message("Test message")
        assert res is True
        assert mock_post.called


def test_slack_notifier(monkeypatch):
    monkeypatch.setenv("TEST_SLACK_URL", "https://hooks.slack.com/services/test")
    cfg = NotificationChannelConfig(
        type="slack", webhook_url_env="TEST_SLACK_URL"
    )
    notifier = SlackNotifier(cfg)
    assert notifier.webhook_url == "https://hooks.slack.com/services/test"

    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = notifier.send_message("Slack test", status="success")
        assert res is True
        assert mock_post.called


def test_telegram_slack_failure(monkeypatch):
    tg_cfg = NotificationChannelConfig(type="telegram", bot_token="123", chat_id="456")
    tg_notifier = TelegramNotifier(tg_cfg)

    slack_cfg = NotificationChannelConfig(type="slack", webhook_url="https://hooks.slack.com/test")
    slack_notifier = SlackNotifier(slack_cfg)

    with patch("httpx.Client.post", side_effect=Exception("HTTP Error")):
        assert tg_notifier.send_message("Fail msg") is False
        assert slack_notifier.send_message("Fail msg") is False


def test_notify_event_dispatch():
    config = NotificationConfig(
        on_success=True,
        on_failure=True,
        channels=[
            NotificationChannelConfig(type="telegram", bot_token="123", chat_id="456"),
            NotificationChannelConfig(type="slack", webhook_url="https://hooks.slack.com/test"),
        ],
    )

    with patch.object(TelegramNotifier, "send_message") as mock_tg, patch.object(
        SlackNotifier, "send_message"
    ) as mock_slack:
        notify_event(config, "Backup completed", status="success")
        assert mock_tg.called
        assert mock_slack.called

    # Test notify_event with None or on_success disabled
    config_disabled = NotificationConfig(on_success=False, on_failure=True, channels=[])
    notify_event(None, "No config")
    notify_event(config_disabled, "Success skip", status="success")
