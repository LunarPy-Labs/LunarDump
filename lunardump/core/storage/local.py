"""Local filesystem storage driver implementation."""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Generator, List

from lunardump.core.storage.base import BaseStorage
from lunardump.core.utils.logger import logger


class LocalStorage(BaseStorage):
    """Local filesystem storage driver."""

    def __init__(self, config):
        super().__init__(config)
        self.base_dir = Path(self.config.bucket) / self.config.path.strip("/")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upload_stream(
        self, stream: Generator[bytes, None, None], remote_key: str
    ) -> str:
        target_path = self.base_dir / remote_key.lstrip("/")
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(target_path, "wb") as f:
                for chunk in stream:
                    f.write(chunk)
            logger.info(f"[green]Successfully saved backup to local storage: {target_path}[/green]")
            return str(target_path)
        except Exception as err:
            raise RuntimeError(f"Local file write failed for path '{target_path}': {err}") from err

    def download_stream(self, remote_key: str) -> Generator[bytes, None, None]:
        target_path = Path(remote_key) if os.path.isabs(remote_key) else self.base_dir / remote_key.lstrip("/")
        if not target_path.exists():
            raise FileNotFoundError(f"Local backup file not found: {target_path}")

        with open(target_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    def clean_retention(self, days: int) -> List[str]:
        cutoff_timestamp = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
        deleted_keys = []

        if not self.base_dir.exists():
            return deleted_keys

        for file_path in self.base_dir.glob("**/*"):
            if file_path.is_file():
                mtime = file_path.stat().st_mtime
                if mtime < cutoff_timestamp:
                    rel_key = str(file_path.relative_to(self.base_dir))
                    file_path.unlink()
                    deleted_keys.append(rel_key)
                    logger.info(f"Cleaned expired local backup file: {rel_key}")

        return deleted_keys

    def test_connection(self) -> bool:
        try:
            test_file = self.base_dir / ".health_check"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception as err:
            logger.error(f"Local storage health check failed: {err}")
            return False
