"""Unit tests for configuration loader and schema validation."""

import os
import tempfile
import pytest
from lunardump.config import load_config, LunarDumpConfig, DatabaseConfig, SecurityConfig, StorageConfig


def test_database_config_default_ports():
    pg_cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    assert pg_cfg.port == 5432

    mysql_cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    assert mysql_cfg.port == 3306

    mongo_cfg = DatabaseConfig(type="mongo", name="db", user="usr")
    assert mongo_cfg.port == 27017


def test_security_config_env_resolution(monkeypatch):
    monkeypatch.setenv("TEST_KEY_ENV", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    sec_cfg = SecurityConfig(key_env="TEST_KEY_ENV")
    assert sec_cfg.key == "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def test_load_valid_config():
    yaml_content = """
version: "1.0"
backup:
  name: "test-job"
  database:
    type: "postgres"
    host: "127.0.0.1"
    port: 5432
    name: "test_db"
    user: "postgres"
  security:
    encrypt: true
    algorithm: "aes-256-gcm"
  storage:
    provider: "local"
    bucket: "/tmp/lunardump_backups"
    path: "backups/"
    retention_days: 7
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f_path = f.name

    try:
        config = load_config(f_path)
        assert isinstance(config, LunarDumpConfig)
        assert config.backup.name == "test-job"
        assert config.backup.database.type == "postgres"
        assert config.backup.storage.provider == "local"
        assert config.backup.storage.retention_days == 7
    finally:
        os.unlink(f_path)


def test_load_non_existent_config():
    with pytest.raises(FileNotFoundError):
        load_config("/path/to/non_existent_config.yaml")
