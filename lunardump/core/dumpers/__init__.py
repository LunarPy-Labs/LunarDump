"""Dumpers package with factory method for database drivers."""

from typing import Type
from lunardump.config.schema import DatabaseConfig
from lunardump.core.dumpers.base import BaseDumper
from lunardump.core.dumpers.postgres import PostgreSQLDumper
from lunardump.core.dumpers.mysql import MySQLDumper
from lunardump.core.dumpers.mongo import MongoDBDumper


def get_dumper(config: DatabaseConfig) -> BaseDumper:
    """Factory function to get dumper instance based on database type.

    Args:
        config: DatabaseConfig instance.

    Returns:
        Concrete BaseDumper subclass.

    Raises:
        ValueError: If unsupported database type.
    """
    db_type = config.type.lower()
    if db_type == "postgres":
        return PostgreSQLDumper(config)
    elif db_type == "mysql":
        return MySQLDumper(config)
    elif db_type == "mongo":
        return MongoDBDumper(config)
    else:
        raise ValueError(f"Unsupported database type: {config.type}")


__all__ = [
    "BaseDumper",
    "PostgreSQLDumper",
    "MySQLDumper",
    "MongoDBDumper",
    "get_dumper",
]
