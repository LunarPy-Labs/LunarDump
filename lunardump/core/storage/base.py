"""Abstract Base Class for Cloud Storage Drivers."""

from abc import ABC, abstractmethod
from typing import Generator, List
from lunardump.config.schema import StorageConfig


class BaseStorage(ABC):
    """Abstract base class for all storage target drivers."""

    def __init__(self, config: StorageConfig):
        self.config = config

    @abstractmethod
    def upload_stream(
        self, stream: Generator[bytes, None, None], remote_key: str
    ) -> str:
        """Upload input bytes stream to remote storage path.

        Args:
            stream: Generator yielding bytes chunks.
            remote_key: Target object key / file path in bucket.

        Returns:
            URL or identifier path of the uploaded storage object.
        """
        pass

    @abstractmethod
    def download_stream(self, remote_key: str) -> Generator[bytes, None, None]:
        """Download remote storage object as a byte stream.

        Args:
            remote_key: Remote object key in bucket.

        Yields:
            Bytes chunks.
        """
        pass

    @abstractmethod
    def clean_retention(self, days: int) -> List[str]:
        """Remove objects older than retention threshold.

        Args:
            days: Maximum age in days.

        Returns:
            List of deleted remote key names.
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test bucket access and write permission."""
        pass

    def check_connection(self) -> bool:
        """Alias for test_connection to maintain API consistency with Dumpers and Restorers."""
        return self.test_connection()

    def clean_expired_backups(self, days: int) -> List[str]:
        """Alias for clean_retention."""
        return self.clean_retention(days)

    def list_backups(self) -> List[dict]:
        """List backup files in storage target."""
        return []
