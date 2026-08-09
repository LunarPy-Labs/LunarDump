"""Unit tests for LunarDump restorers and live migration pipeline."""

import pytest
from unittest.mock import MagicMock, patch
from lunardump.config.schema import DatabaseConfig
from lunardump.core.restorers import (
    get_restorer,
    PostgreSQLRestorer,
    MySQLRestorer,
    MongoRestorer,
)
from lunardump.core.migration import DatabaseMigrator


def test_get_restorer_factory():
    pg_cfg = DatabaseConfig(type="postgres", host="localhost", name="db1", user="postgres")
    assert isinstance(get_restorer(pg_cfg), PostgreSQLRestorer)

    mysql_cfg = DatabaseConfig(type="mysql", host="localhost", name="db2", user="root")
    assert isinstance(get_restorer(mysql_cfg), MySQLRestorer)

    mongo_cfg = DatabaseConfig(type="mongo", host="localhost", name="db3", user="admin")
    assert isinstance(get_restorer(mongo_cfg), MongoRestorer)


def test_unsupported_restorer():
    with pytest.raises(ValueError):
        invalid_cfg = DatabaseConfig(type="sqlite", name="test", user="user")
        get_restorer(invalid_cfg)


def test_postgres_restorer_checks_and_stream():
    cfg = DatabaseConfig(type="postgres", host="localhost", name="testdb", user="postgres", password="secretpassword")
    restorer = PostgreSQLRestorer(cfg)

    with patch("shutil.which", return_value="/usr/bin/psql"):
        assert restorer.check_tool() is True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.return_code = 0
            mock_run.return_value.returncode = 0
            assert restorer.check_connection() is True

        # Test restore_stream
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")

        with patch("subprocess.Popen", return_value=mock_proc):
            def sample_stream():
                yield b"CREATE TABLE t1 (id int);"

            assert restorer.restore_stream(sample_stream()) is True
            mock_proc.stdin.write.assert_called_with(b"CREATE TABLE t1 (id int);")


def test_postgres_restorer_failures():
    cfg = DatabaseConfig(type="postgres", host="localhost", name="testdb", user="postgres")
    restorer = PostgreSQLRestorer(cfg)

    with patch("shutil.which", return_value=None):
        assert restorer.check_tool() is False
        assert restorer.check_connection() is False
        with pytest.raises(RuntimeError, match="not installed"):
            restorer.restore_stream((chunk for chunk in [b"test"]))

    with patch("shutil.which", return_value="/usr/bin/psql"):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"syntax error near CREATE")

        with patch("subprocess.Popen", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="psql restore failed"):
                restorer.restore_stream((chunk for chunk in [b"invalid sql"]))


def test_mysql_restorer_checks_and_stream():
    cfg = DatabaseConfig(type="mysql", host="localhost", name="testdb", user="root", password="rootpassword")
    restorer = MySQLRestorer(cfg)

    with patch("shutil.which", side_effect=lambda x: "/usr/bin/mysql" if x == "mysql" else None):
        assert restorer.check_tool() is True
        assert restorer.get_binary() == "mysql"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            assert restorer.check_connection() is True

        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")

        with patch("subprocess.Popen", return_value=mock_proc):
            def sample_stream():
                yield b"CREATE TABLE users (id int);"

            assert restorer.restore_stream(sample_stream()) is True


def test_mysql_restorer_mariadb_fallback_and_failure():
    cfg = DatabaseConfig(type="mysql", host="localhost", name="testdb", user="root")
    restorer = MySQLRestorer(cfg)

    with patch("shutil.which", side_effect=lambda x: "/usr/bin/mariadb" if x == "mariadb" else None):
        assert restorer.check_tool() is True
        assert restorer.get_binary() == "mariadb"

    with patch("shutil.which", return_value=None):
        assert restorer.check_tool() is False
        with pytest.raises(RuntimeError, match="not installed"):
            restorer.restore_stream((chunk for chunk in [b"test"]))


def test_mongo_restorer_checks_and_stream():
    cfg = DatabaseConfig(type="mongo", host="localhost", name="testdb", user="admin", password="password")
    restorer = MongoRestorer(cfg)

    with patch("shutil.which", return_value="/usr/bin/mongorestore"):
        assert restorer.check_tool() is True
        assert restorer.check_connection() is True

        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")

        with patch("subprocess.Popen", return_value=mock_proc):
            def sample_stream():
                yield b"\x00\x00\x00\x00"

            assert restorer.restore_stream(sample_stream()) is True

    # Test URI connection
    cfg_uri = DatabaseConfig(type="mongo", name="testdb", user="admin", uri="mongodb://localhost:27017/testdb")
    restorer_uri = MongoRestorer(cfg_uri)
    with patch("shutil.which", return_value="/usr/bin/mongorestore"):
        assert restorer_uri.check_connection() is True
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")
        with patch("subprocess.Popen", return_value=mock_proc):
            assert restorer_uri.restore_stream((chunk for chunk in [b"bson"])) is True


def test_mysql_mongo_restorer_failures():
    mysql_cfg = DatabaseConfig(type="mysql", host="localhost", name="testdb", user="root")
    mysql_restorer = MySQLRestorer(mysql_cfg)

    with patch("shutil.which", return_value="/usr/bin/mysql"):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"mysql error")
        with patch("subprocess.Popen", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="mysql restore failed"):
                mysql_restorer.restore_stream((c for c in [b"invalid sql"]))

    mongo_cfg = DatabaseConfig(type="mongo", host="localhost", name="testdb", user="admin")
    mongo_restorer = MongoRestorer(mongo_cfg)
    with patch("shutil.which", return_value=None):
        assert mongo_restorer.check_tool() is False
        assert mongo_restorer.check_connection() is False
        with pytest.raises(RuntimeError, match="not installed"):
            mongo_restorer.restore_stream((c for c in [b"bson"]))

    with patch("shutil.which", return_value="/usr/bin/mongorestore"):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"mongorestore error")
        with patch("subprocess.Popen", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="mongorestore failed"):
                mongo_restorer.restore_stream((c for c in [b"bad bson"]))
