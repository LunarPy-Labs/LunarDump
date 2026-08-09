"""Integration unit tests for Typer CLI commands."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from lunardump.main import app
from lunardump.core.security import generate_key_hex, StreamCipher

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "LunarDump version" in result.stdout


def test_cli_keygen(tmp_path):
    # Test keygen stdout
    result = runner.invoke(app, ["keygen"])
    assert result.exit_code == 0
    assert "Generated 256-bit Encryption Key" in result.stdout

    # Test keygen to file
    out_file = tmp_path / "test.key"
    result = runner.invoke(app, ["keygen", "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "LunarDump" in result.stdout


def test_cli_run_dry_run(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
version: "1.0"
backup:
  name: "test-run"
  database:
    type: "postgres"
    host: "localhost"
    port: 5432
    name: "main_db"
    user: "postgres"
  security:
    encrypt: true
    key_env: "TEST_KEY"
  storage:
    provider: "local"
    bucket: "/tmp/backups"
    path: "daily/"
    retention_days: 7
""")
    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch.dict(os.environ, {"TEST_KEY": generate_key_hex()}):
        result = runner.invoke(app, ["run", "--config", str(config_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry-run mode completed successfully" in result.stdout


def test_cli_run_full_pipeline(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(f"""
version: "1.0"
backup:
  name: "test-run-pipeline"
  database:
    type: "postgres"
    host: "localhost"
    port: 5432
    name: "main_db"
    user: "postgres"
  security:
    encrypt: true
    key_env: "TEST_KEY"
  storage:
    provider: "local"
    bucket: "{tmp_path}"
    path: "daily/"
    retention_days: 7
""")
    key_hex = generate_key_hex()
    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.dump_stream", return_value=iter([b"pg data"])), \
         patch.dict(os.environ, {"TEST_KEY": key_hex}):
        result = runner.invoke(app, ["run", "--config", str(config_file)])
        assert result.exit_code == 0
        assert "Backup Completed Successfully" in result.stdout


def test_cli_restore(tmp_path):
    key = generate_key_hex()
    cipher = StreamCipher(key)

    original_text = b"CREATE TABLE users (id int);"
    encrypted_data = cipher.encrypt_bytes(original_text)

    enc_file = tmp_path / "backup.enc"
    enc_file.write_bytes(encrypted_data)

    out_file = tmp_path / "restored.sql"
    result = runner.invoke(app, ["restore", "--file", str(enc_file), "--key", key, "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.read_bytes() == original_text

    # Test restore --verify (PASSED)
    result_verify = runner.invoke(app, ["restore", "--file", str(enc_file), "--key", key, "--verify"])
    assert result_verify.exit_code == 0
    assert "PASSED (AES-256-GCM Authenticated)" in result_verify.stdout
    assert "SHA-256 Checksum" in result_verify.stdout

    # Test restore --verify (FAILED / Corrupted)
    corrupted_file = tmp_path / "corrupted.enc"
    corrupted_file.write_bytes(b"LUNARDUMP_V1\n1234567890123456bad_payload_data")
    result_bad = runner.invoke(app, ["restore", "--file", str(corrupted_file), "--key", key, "--verify"])
    assert result_bad.exit_code == 1
    assert "FAILED / CORRUPTED" in result_bad.stdout


def test_cli_db_dump(tmp_path):
    out_file = tmp_path / "dump.sql"
    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.dump_stream", return_value=iter([b"dump data"])):
        result = runner.invoke(app, ["db", "dump", "--type", "postgres", "--name", "mydb", "--output", str(out_file)])
        assert result.exit_code == 0
        assert out_file.read_bytes() == b"dump data"


def test_cli_config_check(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(f"""
version: "1.0"
backup:
  name: "test-check"
  database:
    type: "postgres"
    host: "localhost"
    port: 5432
    name: "main_db"
    user: "postgres"
  security:
    encrypt: true
    key_env: "TEST_KEY"
  storage:
    provider: "local"
    bucket: "{tmp_path}"
    path: "daily/"
    retention_days: 7
""")
    key_hex = generate_key_hex()
    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_connection", return_value=True), \
         patch.dict(os.environ, {"TEST_KEY": key_hex}):
        result = runner.invoke(app, ["config", "check", "--config", str(config_file)])
        assert result.exit_code == 0
        assert "VALID (Pydantic v2)" in result.stdout


def test_cli_migrate_dry_run():
    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.check_tool", return_value=True):
        result = runner.invoke(app, [
            "migrate",
            "--source-type", "postgres", "--source-name", "db_a",
            "--target-type", "postgres", "--target-name", "db_b",
            "--dry-run"
        ])
        assert result.exit_code == 0
        assert "Migration dry-run completed successfully" in result.stdout


def test_cli_restore_target_db(tmp_path):
    key = generate_key_hex()
    cipher = StreamCipher(key)

    original_text = b"CREATE TABLE users (id int);"
    encrypted_data = cipher.encrypt_bytes(original_text)

    enc_file = tmp_path / "backup.enc"
    enc_file.write_bytes(encrypted_data)

    with patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.check_tool", return_value=True), \
         patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.restore_stream", return_value=True):
        result = runner.invoke(app, [
            "restore",
            "--file", str(enc_file),
            "--key", key,
            "--target-db-type", "postgres",
            "--target-db-name", "dest_db",
            "--target-db-user", "postgres"
        ])
        assert result.exit_code == 0
        assert "Successfully decrypted and restored backup directly into target database" in result.stdout


def test_cli_migrate_full_pipeline():
    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.check_tool", return_value=True), \
         patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.dump_stream", return_value=iter([b"sql"])), \
         patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.restore_stream", return_value=True):
        result = runner.invoke(app, [
            "migrate",
            "--source-type", "postgres", "--source-name", "db_a",
            "--target-type", "postgres", "--target-name", "db_b"
        ])
        assert result.exit_code == 0
        assert "Database Migration Completed Successfully" in result.stdout


def test_cli_config_generate(tmp_path):
    cfg_file = tmp_path / "gen_config.yaml"
    mig_file = tmp_path / "gen_migration.yaml"
    env_file = tmp_path / "gen.env"

    result = runner.invoke(app, [
        "config", "generate",
        "--config", str(cfg_file),
        "--migrate", str(mig_file),
        "--env", str(env_file),
        "--db-type", "mysql",
        "--storage", "s3"
    ])
    assert result.exit_code == 0
    assert cfg_file.exists()
    assert mig_file.exists()
    assert env_file.exists()
    assert "production-mysql-backup" in cfg_file.read_text()
    assert "production-mysql-migration" in mig_file.read_text()
    assert "LUNARDUMP_ENCRYPTION_KEY=" in env_file.read_text()
    assert "GOOGLE_APPLICATION_CREDENTIALS=" in env_file.read_text()

    # Test overwrite warning without --force
    result_warn = runner.invoke(app, [
        "config", "generate",
        "--config", str(cfg_file),
        "--migrate", str(mig_file),
        "--env", str(env_file)
    ])
    assert result_warn.exit_code == 1

    # Test overwrite with --force
    result_force = runner.invoke(app, [
        "config", "generate",
        "--config", str(cfg_file),
        "--migrate", str(mig_file),
        "--env", str(env_file),
        "--force"
    ])
def test_cli_ui(monkeypatch):
    server_started = {}
    def mock_start_ui_server(host, port, open_browser):
        server_started["host"] = host
        server_started["port"] = port
        server_started["open_browser"] = open_browser

    monkeypatch.setattr("lunardump.ui.start_ui_server", mock_start_ui_server)
    result = runner.invoke(app, ["ui", "--host", "127.0.0.1", "--port", "8080", "--no-open"])
    assert result.exit_code == 0
    assert server_started["host"] == "127.0.0.1"
    assert server_started["port"] == 8080
    assert server_started["open_browser"] is False


def test_cli_migrate_yaml_config(tmp_path):
    mig_file = tmp_path / "migration.yaml"
    mig_file.write_text("""
version: "1.0"
backup:
  name: "test-yaml-migration"
  database:
    type: "postgres"
    host: "localhost"
    port: 5432
    name: "db_src"
    user: "user_a"
  target_database:
    type: "postgres"
    host: "localhost"
    port: 5432
    name: "db_tgt"
    user: "user_b"
""")

    with patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", return_value=True), \
         patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.check_tool", return_value=True), \
         patch("lunardump.core.dumpers.postgres.PostgreSQLDumper.dump_stream", return_value=iter([b"data"])), \
         patch("lunardump.core.restorers.postgres.PostgreSQLRestorer.restore_stream", return_value=True):
        result = runner.invoke(app, ["migrate", "--config", str(mig_file)])
        assert result.exit_code == 0
        assert "Database Migration Completed Successfully" in result.stdout


def test_cli_migrate_missing_args():
    result = runner.invoke(app, ["migrate"])
    assert result.exit_code != 0


def test_cli_run_config_not_found():
    result = runner.invoke(app, ["run", "--config", "nonexistent.yaml"])
    assert result.exit_code != 0


def test_cli_config_check_invalid(tmp_path):
    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text("invalid_yaml: [")
    result = runner.invoke(app, ["config", "check", "--config", str(bad_cfg)])
    assert result.exit_code == 1




