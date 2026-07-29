"""Abstract Base Class for Database Dumpers."""

from abc import ABC, abstractmethod
from typing import Generator
from lunardump.config.schema import DatabaseConfig


class BaseDumper(ABC):
    """Abstract base class for all database dumper plugins."""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    @abstractmethod
    def check_tool(self) -> bool:
        """Check if required binary CLI tool (e.g. pg_dump) is installed."""
        pass

    @abstractmethod
    def dump_stream(self) -> Generator[bytes, None, None]:
        """Stream database dump output as bytes chunks."""
        pass

    @abstractmethod
    def restore_stream(self, stream: Generator[bytes, None, None]) -> None:
        """Restore database from input bytes stream."""
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """Test connectivity to the target database."""
        pass
