"""Factory module for Database Restorers."""

from lunardump.config.schema import DatabaseConfig
from lunardump.core.restorers.base import BaseRestorer
from lunardump.core.restorers.postgres import PostgreSQLRestorer
from lunardump.core.restorers.mysql import MySQLRestorer
from lunardump.core.restorers.mongo import MongoRestorer


def get_restorer(db_config: DatabaseConfig) -> BaseRestorer:
    """Factory function to instantiate restorer for specified database engine."""
    db_type = db_config.type.lower()
    if db_type == "postgres":
        return PostgreSQLRestorer(db_config)
    elif db_type == "mysql":
        return MySQLRestorer(db_config)
    elif db_type == "mongo":
        return MongoRestorer(db_config)
    else:
        raise ValueError(f"Unsupported database engine type for restore: '{db_config.type}'")
