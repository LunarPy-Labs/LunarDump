"""Google Cloud Storage driver implementation."""

import os
from datetime import datetime, timezone, timedelta
from typing import Generator, List

from lunardump.core.storage.base import BaseStorage
from lunardump.core.utils.logger import logger

try:
    from google.cloud import storage as gcs_storage
    from google.api_core.exceptions import GoogleAPIError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class GCSStorage(BaseStorage):
    """Google Cloud Storage driver."""

    def __init__(self, config):
        super().__init__(config)
        if not GCS_AVAILABLE:
            raise RuntimeError(
                "google-cloud-storage package is not installed. Install it via `pip install google-cloud-storage` or `pip install lunardump[gcs]`"
            )
        self.client = gcs_storage.Client()
        self.bucket = self.client.bucket(self.config.bucket)

    def upload_stream(
        self, stream: Generator[bytes, None, None], remote_key: str
    ) -> str:
        full_key = f"{self.config.path.strip('/')}/{remote_key.lstrip('/')}".strip('/')
        blob = self.bucket.blob(full_key)

        try:
            # GCS chunked upload via blob open stream
            with blob.open("wb") as f:
                for chunk in stream:
                    f.write(chunk)
            logger.info(f"[green]Successfully uploaded to GCS: gs://{self.config.bucket}/{full_key}[/green]")
            return f"gs://{self.config.bucket}/{full_key}"
        except Exception as err:
            raise RuntimeError(f"GCS upload failed for blob '{full_key}': {err}") from err

    def download_stream(self, remote_key: str) -> Generator[bytes, None, None]:
        full_key = (
            remote_key
            if remote_key.startswith(self.config.path)
            else f"{self.config.path.strip('/')}/{remote_key.lstrip('/')}".strip('/')
        )
        blob = self.bucket.blob(full_key)
        try:
            with blob.open("rb") as f:
                while chunk := f.read(64 * 1024):
                    yield chunk
        except Exception as err:
            raise RuntimeError(f"Failed to download blob 'gs://{self.config.bucket}/{full_key}': {err}") from err

    def clean_retention(self, days: int) -> List[str]:
        prefix = self.config.path.strip("/") + "/" if self.config.path else ""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_keys = []

        blobs = self.client.list_blobs(self.config.bucket, prefix=prefix)
        for blob in blobs:
            if blob.time_created < cutoff_date:
                key = blob.name
                blob.delete()
                deleted_keys.append(key)
                logger.info(f"Cleaned expired GCS backup object: {key}")

        return deleted_keys

    def test_connection(self) -> bool:
        try:
            return self.bucket.exists()
        except Exception as err:
            logger.error(f"GCS connection test failed: {err}")
            return False
