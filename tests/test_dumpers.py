"""Unit tests for Database Dumper drivers."""

import pytest
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
