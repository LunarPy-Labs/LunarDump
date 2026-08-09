"""Unit tests for DaemonScheduler runner."""

import pytest
from unittest.mock import MagicMock, patch
from lunardump.core.scheduler.runner import DaemonScheduler


def test_daemon_scheduler_single_run():
    callback = MagicMock()
    scheduler = DaemonScheduler("every-1s", run_callback=callback)

    with patch("time.sleep"):
        scheduler.start(once=True)

    callback.assert_called_once()
    assert scheduler.running is True
