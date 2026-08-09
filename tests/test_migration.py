"""Unit tests for DatabaseMigrator live migration pipeline."""

import pytest
from unittest.mock import MagicMock, patch
from lunardump.config.schema import DatabaseConfig
from lunardump.core.migration import DatabaseMigrator


def test_migrator_prerequisites():
    src_cfg = DatabaseConfig(type="postgres", host="srv-a", name="prod", user="postgres")
    dst_cfg = DatabaseConfig(type="postgres", host="srv-b", name="prod_replica", user="postgres")

    migrator = DatabaseMigrator(src_cfg, dst_cfg)

    with patch.object(migrator.source_dumper, "check_tool", return_value=True):
        with patch.object(migrator.target_restorer, "check_tool", return_value=True):
            assert migrator.check_prerequisites() is True

    with patch.object(migrator.source_dumper, "check_tool", return_value=False):
        with pytest.raises(RuntimeError, match="Source database tool"):
            migrator.check_prerequisites()

    with patch.object(migrator.source_dumper, "check_tool", return_value=True):
        with patch.object(migrator.target_restorer, "check_tool", return_value=False):
            with pytest.raises(RuntimeError, match="Target database tool"):
                migrator.check_prerequisites()


def test_migrator_execute_migration():
    src_cfg = DatabaseConfig(type="postgres", host="srv-a", name="prod", user="postgres")
    dst_cfg = DatabaseConfig(type="postgres", host="srv-b", name="prod_replica", user="postgres")

    migrator = DatabaseMigrator(src_cfg, dst_cfg)

    def dummy_stream():
        yield b"CREATE TABLE users (id int);"

    with patch.object(migrator.source_dumper, "check_tool", return_value=True):
        with patch.object(migrator.target_restorer, "check_tool", return_value=True):
            with patch.object(migrator.source_dumper, "dump_stream", return_value=dummy_stream()):
                with patch.object(migrator.target_restorer, "restore_stream", return_value=True):
                    assert migrator.execute_migration() is True
