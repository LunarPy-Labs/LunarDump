"""Unit tests for Process runner utilities and logging."""

import pytest
from unittest.mock import patch, MagicMock
from lunardump.core.utils.process import check_tool_installed, run_process_stream, run_command
from lunardump.core.utils.logger import setup_logger, logger


def test_check_tool_installed():
    assert check_tool_installed("ls") is True
    assert check_tool_installed("non_existent_binary_tool_xyz") is False


@patch("subprocess.Popen")
def test_run_process_stream_success(mock_popen):
    proc = MagicMock()
    proc.stdout.read.side_effect = [b"chunk1", b""]
    proc.poll.return_value = 0
    proc.communicate.return_value = (b"", b"")
    mock_popen.return_value = proc

    chunks = list(run_process_stream(["echo", "hi"]))
    assert chunks == [b"chunk1"]


@patch("subprocess.Popen")
def test_run_process_stream_failure(mock_popen):
    proc = MagicMock()
    proc.stdout.read.return_value = b""
    proc.poll.return_value = 1
    proc.communicate.return_value = (b"", b"Error output")
    mock_popen.return_value = proc

    with pytest.raises(RuntimeError, match="failed"):
        list(run_process_stream(["failing_cmd"]))


def test_run_command():
    code, stdout, stderr = run_command(["echo", "hello"])
    assert code == 0
    assert "hello" in stdout


def test_logger_setup():
    log = setup_logger("DEBUG")
    assert log.level == 10  # DEBUG level


def test_ensure_extended_path():
    from lunardump.core.utils.process import ensure_extended_path
    import os
    ensure_extended_path()
    assert os.environ.get("PATH") is not None
