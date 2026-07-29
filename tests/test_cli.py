"""Integration unit tests for Typer CLI commands."""

from typer.testing import CliRunner
from lunardump.main import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "LunarDump version" in result.stdout


def test_cli_keygen():
    result = runner.invoke(app, ["keygen"])
    assert result.exit_code == 0
    assert "Generated 256-bit Encryption Key" in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "LunarDump" in result.stdout
