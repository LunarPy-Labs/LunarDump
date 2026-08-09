"""Unit tests for Storage drivers including S3, GCS, and Local storage."""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from lunardump.config.schema import StorageConfig
from lunardump.core.storage import get_storage, LocalStorage, S3Storage, GCSStorage


def test_storage_factory():
    local_cfg = StorageConfig(provider="local", bucket="/tmp/test", path="backups/")
    storage = get_storage(local_cfg)
    assert isinstance(storage, LocalStorage)

    s3_cfg = StorageConfig(provider="s3", bucket="my-bucket", path="backups/")
    with patch("boto3.client"):
        assert isinstance(get_storage(s3_cfg), S3Storage)

    gcs_cfg = StorageConfig(provider="gcs", bucket="my-gcs-bucket", path="backups/")
    with patch("google.cloud.storage.Client"):
        assert isinstance(get_storage(gcs_cfg), GCSStorage)


def test_unsupported_storage_provider():
    with pytest.raises(ValueError):
        StorageConfig(provider="azure", bucket="test")


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

        # Test retention cleanup
        deleted = storage.clean_retention(days=30)
        assert len(deleted) == 0


# --- S3 Storage Driver Tests ---

@patch("boto3.client")
def test_s3_storage_upload_and_download(mock_boto_client):
    s3_client_mock = MagicMock()
    mock_boto_client.return_value = s3_client_mock

    # Mock multipart upload
    s3_client_mock.create_multipart_upload.return_value = {"UploadId": "upload123"}
    s3_client_mock.upload_part.return_value = {"ETag": "etag123"}

    cfg = StorageConfig(provider="s3", bucket="my-bucket", path="daily/")
    storage = S3Storage(cfg)

    def data_stream():
        yield b"A" * (1024 * 1024)  # 1MB chunk

    with patch("lunardump.core.storage.s3.MIN_MULTIPART_SIZE", 512 * 1024):
        res_url = storage.upload_stream(data_stream(), "db.dump")
        assert res_url == "s3://my-bucket/daily/db.dump"
        assert s3_client_mock.complete_multipart_upload.called

    # Mock download stream
    body_mock = MagicMock()
    body_mock.read.side_effect = [b"chunk1", b""]
    s3_client_mock.get_object.return_value = {"Body": body_mock}

    downloaded = list(storage.download_stream("daily/db.dump"))
    assert downloaded == [b"chunk1"]

    # Mock retention cleanup
    paginator_mock = MagicMock()
    paginator_mock.paginate.return_value = [
        {
            "Contents": [
                {
                    "Key": "daily/old.dump",
                    "LastModified": datetime.now(timezone.utc) - timedelta(days=40),
                }
            ]
        }
    ]
    s3_client_mock.get_paginator.return_value = paginator_mock
    deleted = storage.clean_retention(days=30)
    assert deleted == ["daily/old.dump"]

    # Mock test connection
    s3_client_mock.head_bucket.return_value = {}
    assert storage.test_connection() is True


# --- GCS Storage Driver Tests ---

@patch("google.cloud.storage.Client")
def test_gcs_storage_upload_and_download(mock_gcs_client):
    client_instance = MagicMock()
    bucket_mock = MagicMock()
    blob_mock = MagicMock()

    mock_gcs_client.return_value = client_instance
    client_instance.bucket.return_value = bucket_mock
    bucket_mock.blob.return_value = blob_mock

    cfg = StorageConfig(provider="gcs", bucket="my-gcs-bucket", path="daily/")
    storage = GCSStorage(cfg)

    # Test upload stream
    blob_open_mock = MagicMock()
    blob_mock.open.return_value.__enter__.return_value = blob_open_mock
    res_url = storage.upload_stream(iter([b"gcs payload"]), "db.dump")
    assert res_url == "gs://my-gcs-bucket/daily/db.dump"

    # Test retention
    old_blob = MagicMock()
    old_blob.name = "daily/old_gcs.dump"
    old_blob.time_created = datetime.now(timezone.utc) - timedelta(days=45)
    client_instance.list_blobs.return_value = [old_blob]

    deleted = storage.clean_retention(days=30)
    assert deleted == ["daily/old_gcs.dump"]
    assert old_blob.delete.called

    # Test connection
    bucket_mock.exists.return_value = True
    assert storage.test_connection() is True

    # Test download_stream
    file_read_mock = MagicMock()
    file_read_mock.read.side_effect = [b"gcs download data", b""]
    blob_mock.open.return_value.__enter__.return_value = file_read_mock
    chunks = list(storage.download_stream("daily/db.dump"))
    assert b"".join(chunks) == b"gcs download data"

    # Test list_backups
    b1 = MagicMock()
    b1.name = "daily/backup1.sql.enc"
    b1.size = 1024
    b1.updated = datetime.now(timezone.utc)
    client_instance.list_blobs.return_value = [b1]
    files = storage.list_backups()
    assert len(files) == 1
    assert files[0]["key"] == "daily/backup1.sql.enc"
