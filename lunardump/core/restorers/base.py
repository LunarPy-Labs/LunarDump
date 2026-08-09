"""Abstract base class for database restorers."""

import abc
import subprocess
from typing import Generator, Optional
from lunardump.config.schema import DatabaseConfig


class BaseRestorer(abc.ABC):
    """Abstract Base Class for Database Restorer implementations."""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    @abc.abstractmethod
    def check_tool(self) -> bool:
        """Check if native restorer CLI tool is installed in PATH."""
        pass

    @abc.abstractmethod
    def check_connection(self) -> bool:
        """Check connection to target database."""
        pass

    @abc.abstractmethod
    def restore_stream(self, stream: Generator[bytes, None, None]) -> bool:
        """Restore database payload by streaming stdin bytes directly into restorer process.

        Args:
            stream: Generator yielding raw plaintext bytes (SQL or BSON archive).

        Returns:
            bool: True if restore completed with exit code 0.
        """
        pass
