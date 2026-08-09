"""Unit tests for Database Dumper drivers and methods."""

import pytest
from unittest.mock import patch, MagicMock
from lunardump.config.schema import DatabaseConfig
from lunardump.core.dumpers import get_dumper, PostgreSQLDumper, MySQLDumper, MongoDBDumper


def test_dumper_factory():
    pg_cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    assert isinstance(get_dumper(pg_cfg), PostgreSQLDumper)

    mysql_cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    assert isinstance(get_dumper(mysql_cfg), MySQLDumper)

    mongo_cfg = DatabaseConfig(type="mongo", name="db", user="usr")
    assert isinstance(get_dumper(mongo_cfg), MongoDBDumper)


def test_unsupported_dumper_type():
    with pytest.raises(ValueError):
        DatabaseConfig(type="oracle", name="db", user="usr")


# --- PostgreSQL Dumper Tests ---

@patch("shutil.which", return_value="/usr/bin/pg_dump")
def test_postgres_check_tool(mock_which):
    cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    dumper = PostgreSQLDumper(cfg)
    assert dumper.check_tool() is True


@patch("shutil.which", return_value=None)
def test_postgres_dump_tool_missing(mock_which):
    cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    dumper = PostgreSQLDumper(cfg)
    with pytest.raises(RuntimeError, match="pg_dump binary tool is not installed"):
        list(dumper.dump_stream())


@patch("lunardump.core.dumpers.postgres.run_process_stream")
@patch("shutil.which", return_value="/usr/bin/pg_dump")
def test_postgres_dump_stream(mock_which, mock_stream):
    mock_stream.return_value = iter([b"pg_dump payload"])
    cfg = DatabaseConfig(type="postgres", name="db", user="usr", password="secret_password")
    dumper = PostgreSQLDumper(cfg)
    chunks = list(dumper.dump_stream())
    assert chunks == [b"pg_dump payload"]


@patch("subprocess.Popen")
@patch("shutil.which", return_value="/usr/bin/pg_restore")
def test_postgres_restore_stream(mock_which, mock_popen):
    process_mock = MagicMock()
    process_mock.stdin = MagicMock()
    process_mock.communicate.return_value = (b"", b"")
    process_mock.returncode = 0
    mock_popen.return_value = process_mock

    cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    dumper = PostgreSQLDumper(cfg)
    dumper.restore_stream(iter([b"chunk1", b"chunk2"]))

    assert process_mock.stdin.write.call_count == 2


@patch("lunardump.core.dumpers.postgres.run_command")
@patch("shutil.which", return_value="/usr/bin/pg_isready")
def test_postgres_check_connection(mock_which, mock_cmd):
    mock_cmd.return_value = (0, "ready", "")
    cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    dumper = PostgreSQLDumper(cfg)
    assert dumper.check_connection() is True


# --- MySQL Dumper Tests ---

@patch("shutil.which", return_value="/usr/bin/mysqldump")
def test_mysql_check_tool(mock_which):
    cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    dumper = MySQLDumper(cfg)
    assert dumper.check_tool() is True


@patch("shutil.which", return_value=None)
def test_mysql_dump_tool_missing(mock_which):
    cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    dumper = MySQLDumper(cfg)
    with pytest.raises(RuntimeError, match="mysqldump binary tool is not installed"):
        list(dumper.dump_stream())


@patch("lunardump.core.dumpers.mysql.run_process_stream")
@patch("shutil.which", return_value="/usr/bin/mysqldump")
def test_mysql_dump_stream(mock_which, mock_stream):
    mock_stream.return_value = iter([b"mysql payload"])
    cfg = DatabaseConfig(type="mysql", name="db", user="usr", password="p")
    dumper = MySQLDumper(cfg)
    assert list(dumper.dump_stream()) == [b"mysql payload"]


@patch("subprocess.Popen")
@patch("shutil.which", return_value="/usr/bin/mysql")
def test_mysql_restore_stream(mock_which, mock_popen):
    process_mock = MagicMock()
    process_mock.stdin = MagicMock()
    process_mock.communicate.return_value = (b"", b"")
    process_mock.returncode = 0
    mock_popen.return_value = process_mock

    cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    dumper = MySQLDumper(cfg)
    dumper.restore_stream(iter([b"chunk1"]))
    assert process_mock.stdin.write.call_count == 1


@patch("lunardump.core.dumpers.mysql.run_command")
@patch("shutil.which", return_value="/usr/bin/mysqladmin")
def test_mysql_check_connection(mock_which, mock_cmd):
    mock_cmd.return_value = (0, "mysqld is alive", "")
    cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    dumper = MySQLDumper(cfg)
    assert dumper.check_connection() is True


# --- MongoDB Dumper Tests ---

@patch("shutil.which", return_value="/usr/bin/mongodump")
def test_mongo_check_tool(mock_which):
    cfg = DatabaseConfig(type="mongo", name="db", user="usr")
    dumper = MongoDBDumper(cfg)
    assert dumper.check_tool() is True


@patch("shutil.which", return_value=None)
def test_mongo_dump_tool_missing(mock_which):
    cfg = DatabaseConfig(type="mongo", name="db", user="usr")
    dumper = MongoDBDumper(cfg)
    with pytest.raises(RuntimeError, match="mongodump binary tool is not installed"):
        list(dumper.dump_stream())


@patch("lunardump.core.dumpers.mongo.run_process_stream")
@patch("shutil.which", return_value="/usr/bin/mongodump")
def test_mongo_dump_stream(mock_which, mock_stream):
    mock_stream.return_value = iter([b"mongo archive payload"])
    cfg = DatabaseConfig(type="mongo", name="db", user="usr", password="secret")
    dumper = MongoDBDumper(cfg)
    assert list(dumper.dump_stream()) == [b"mongo archive payload"]


@patch("subprocess.Popen")
@patch("shutil.which", return_value="/usr/bin/mongorestore")
def test_mongo_restore_stream(mock_which, mock_popen):
    process_mock = MagicMock()
    process_mock.stdin = MagicMock()
    process_mock.communicate.return_value = (b"", b"")
    process_mock.returncode = 0
    mock_popen.return_value = process_mock

    cfg = DatabaseConfig(type="mongo", name="db", user="usr", password="secret")
    dumper = MongoDBDumper(cfg)
    dumper.restore_stream(iter([b"chunk"]))
    assert process_mock.stdin.write.call_count == 1


@patch("lunardump.core.dumpers.mongo.run_command")
@patch("shutil.which", return_value="/usr/bin/mongosh")
def test_mongo_check_connection(mock_which, mock_cmd):
    mock_cmd.return_value = (0, "{ok: 1}", "")
    cfg = DatabaseConfig(type="mongo", name="db", user="usr")
    dumper = MongoDBDumper(cfg)
    assert dumper.check_connection() is True

    mock_cmd.side_effect = Exception("Conn Error")
    assert dumper.check_connection() is False


@patch("lunardump.core.dumpers.mysql.run_command")
@patch("shutil.which", return_value="/usr/bin/mysqladmin")
def test_mysql_check_connection_fail(mock_which, mock_cmd):
    mock_cmd.side_effect = Exception("Conn Error")
    cfg = DatabaseConfig(type="mysql", name="db", user="usr")
    dumper = MySQLDumper(cfg)
    assert dumper.check_connection() is False


@patch("lunardump.core.dumpers.postgres.run_command")
@patch("shutil.which", return_value="/usr/bin/pg_isready")
def test_postgres_check_connection_fail(mock_which, mock_cmd):
    mock_cmd.side_effect = Exception("Conn Error")
    cfg = DatabaseConfig(type="postgres", name="db", user="usr")
    dumper = PostgreSQLDumper(cfg)
    assert dumper.check_connection() is False
