"""AWS S3, MinIO, and Cloudflare R2 storage driver implementation."""

from datetime import datetime, timezone, timedelta
from typing import Generator, List
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from lunardump.core.storage.base import BaseStorage
from lunardump.core.utils.logger import logger

MIN_MULTIPART_SIZE = 5 * 1024 * 1024  # 5MB S3 minimum part size


class S3Storage(BaseStorage):
    """S3 storage driver supporting AWS S3, Cloudflare R2, and MinIO."""

    def __init__(self, config):
        super().__init__(config)
        client_kwargs = {}
        if self.config.region:
            client_kwargs["region_name"] = self.config.region
        if self.config.endpoint_url:
            client_kwargs["endpoint_url"] = self.config.endpoint_url

        # Fast retries configuration
        boto_config = Config(
            retries={"max_attempts": 5, "mode": "standard"},
            connect_timeout=10,
            read_timeout=30,
        )
        self.s3_client = boto3.client("s3", config=boto_config, **client_kwargs)

    def upload_stream(
        self, stream: Generator[bytes, None, None], remote_key: str
    ) -> str:
        full_key = f"{self.config.path.strip('/')}/{remote_key.lstrip('/')}".strip('/')

        try:
            mpu = self.s3_client.create_multipart_upload(
                Bucket=self.config.bucket, Key=full_key
            )
            upload_id = mpu["UploadId"]
        except (BotoCoreError, ClientError) as err:
            raise RuntimeError(f"Failed to initiate S3 multipart upload: {err}") from err

        parts = []
        part_number = 1
        buffer = bytearray()

        try:
            for chunk in stream:
                buffer.extend(chunk)
                while len(buffer) >= MIN_MULTIPART_SIZE:
                    part_data = bytes(buffer[:MIN_MULTIPART_SIZE])
                    del buffer[:MIN_MULTIPART_SIZE]

                    res = self.s3_client.upload_part(
                        Bucket=self.config.bucket,
                        Key=full_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=part_data,
                    )
                    parts.append({"PartNumber": part_number, "ETag": res["ETag"]})
                    part_number += 1

            # Upload remaining buffer
            if len(buffer) > 0 or part_number == 1:
                res = self.s3_client.upload_part(
                    Bucket=self.config.bucket,
                    Key=full_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=bytes(buffer),
                )
                parts.append({"PartNumber": part_number, "ETag": res["ETag"]})

            self.s3_client.complete_multipart_upload(
                Bucket=self.config.bucket,
                Key=full_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            logger.info(f"[green]Successfully uploaded to S3: s3://{self.config.bucket}/{full_key}[/green]")
            return f"s3://{self.config.bucket}/{full_key}"

        except Exception as err:
            # Abort upload on failure
            self.s3_client.abort_multipart_upload(
                Bucket=self.config.bucket, Key=full_key, UploadId=upload_id
            )
            raise RuntimeError(f"S3 Multipart upload failed for key '{full_key}': {err}") from err

    def download_stream(self, remote_key: str) -> Generator[bytes, None, None]:
        full_key = (
            remote_key
            if remote_key.startswith(self.config.path)
            else f"{self.config.path.strip('/')}/{remote_key.lstrip('/')}".strip('/')
        )
        try:
            response = self.s3_client.get_object(Bucket=self.config.bucket, Key=full_key)
            body = response["Body"]
            while chunk := body.read(64 * 1024):
                yield chunk
        except (BotoCoreError, ClientError) as err:
            raise RuntimeError(f"Failed to download object 's3://{self.config.bucket}/{full_key}': {err}") from err

    def clean_retention(self, days: int) -> List[str]:
        prefix = self.config.path.strip("/") + "/" if self.config.path else ""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_keys = []

        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.config.bucket, Prefix=prefix)

        for page in pages:
            if "Contents" not in page:
                continue
            for obj in page["Contents"]:
                last_modified = obj["LastModified"]
                if last_modified < cutoff_date:
                    key = obj["Key"]
                    self.s3_client.delete_object(Bucket=self.config.bucket, Key=key)
                    deleted_keys.append(key)
                    logger.info(f"Cleaned expired backup object: {key}")

        return deleted_keys

    def test_connection(self) -> bool:
        try:
            self.s3_client.head_bucket(Bucket=self.config.bucket)
            return True
        except Exception as err:
            logger.error(f"S3 connection test failed: {err}")
            return False
