"""Unit tests for Storage drivers and local storage implementation."""

import tempfile
import pytest
from pathlib import Path
from lunardump.config.schema import StorageConfig
from lunardump.core.storage import get_storage, LocalStorage


def test_storage_factory():
    local_cfg = StorageConfig(provider="local", bucket="/tmp/test", path="backups/")
    storage = get_storage(local_cfg)
    assert isinstance(storage, LocalStorage)


def test_local_storage_upload_download_and_retention():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = StorageConfig(provider="local", bucket=tmp_dir, path="daily/", retention_days=1)
        storage = get_storage(cfg)

        assert storage.test_connection() is True

        def dummy_stream():
            yield b"Sample backup chunk 1\n"
            yield b"Sample backup chunk 2\n"

        target_file = "postgres_test_backup.dump"
        uploaded_path = storage.upload_stream(dummy_stream(), target_file)
        assert Path(uploaded_path).exists()

        downloaded_chunks = list(storage.download_stream(target_file))
        assert b"".join(downloaded_chunks) == b"Sample backup chunk 1\nSample backup chunk 2\n"

        # Test retention cleanup (0 deleted because file is brand new)
        deleted = storage.clean_retention(days=30)
        assert len(deleted) == 0
