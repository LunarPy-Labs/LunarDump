"""Storage package with factory method for target storage providers."""

from lunardump.config.schema import StorageConfig
from lunardump.core.storage.base import BaseStorage
from lunardump.core.storage.s3 import S3Storage
from lunardump.core.storage.gcs import GCSStorage
from lunardump.core.storage.local import LocalStorage


def get_storage(config: StorageConfig) -> BaseStorage:
    """Factory function to instantiate storage provider.

    Args:
        config: StorageConfig instance.

    Returns:
        Concrete BaseStorage subclass.

    Raises:
        ValueError: If unsupported storage provider.
    """
    provider = config.provider.lower()
    if provider == "s3":
        return S3Storage(config)
    elif provider == "gcs":
        return GCSStorage(config)
    elif provider == "local":
        return LocalStorage(config)
    else:
        raise ValueError(f"Unsupported storage provider: {config.provider}")


__all__ = [
    "BaseStorage",
    "S3Storage",
    "GCSStorage",
    "LocalStorage",
    "get_storage",
]
