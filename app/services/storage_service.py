from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings
from app.core.exceptions import ResourceNotFoundError, S3OperationError
from app.utils.files import copy_file_with_timestamp


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class S3ObjectInfo:
    key: str
    last_modified: datetime
    size: int


class LocalStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def store_raw_file(self, source_path: Path) -> Path:
        if not source_path.exists():
            raise ResourceNotFoundError(f"Raw input file not found: {source_path}")
        destination = copy_file_with_timestamp(source_path, self.settings.raw_data_dir)
        logger.info("Stored raw file locally at %s", destination)
        return destination


class S3StorageService:
    """Minimal S3 adapter for ingestion and mirroring."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.validate_s3_settings()
        self.bucket_name = self.settings.s3_bucket_name
        endpoint_url = getattr(self.settings, "s3_endpoint_url", "") or None
        use_path_style = bool(getattr(self.settings, "s3_use_path_style", False))
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
            region_name=self.settings.aws_default_region,
            endpoint_url=endpoint_url,
            config=Config(s3={"addressing_style": "path" if use_path_style else "auto"}),
        )

    def upload_file(self, source_path: Path, key: str | None = None) -> str:
        self._validate_bucket_config()
        if not source_path.exists():
            raise ResourceNotFoundError(f"Local file not found for S3 upload: {source_path}")
        object_key = key or source_path.name
        try:
            self.client.upload_file(str(source_path), self.bucket_name, object_key)
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Failed to upload %s to S3 bucket %s.", source_path, self.bucket_name)
            raise S3OperationError(f"Failed to upload file to s3://{self.bucket_name}/{object_key}") from exc
        logger.info("Uploaded %s to s3://%s/%s", source_path, self.bucket_name, object_key)
        return object_key

    def list_files(self, prefix: str | None = None) -> list[S3ObjectInfo]:
        self._validate_bucket_config()
        object_prefix = prefix if prefix is not None else self.settings.s3_bucket_prefix
        paginator = self.client.get_paginator("list_objects_v2")

        try:
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=object_prefix)
            objects: list[S3ObjectInfo] = []
            for page in pages:
                for entry in page.get("Contents", []):
                    key = entry["Key"]
                    if key.endswith("/"):
                        continue
                    objects.append(
                        S3ObjectInfo(
                            key=key,
                            last_modified=entry["LastModified"],
                            size=int(entry.get("Size", 0)),
                        )
                    )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Failed to list S3 objects from bucket %s prefix %s.", self.bucket_name, object_prefix)
            raise S3OperationError(f"Failed to list files from s3://{self.bucket_name}/{object_prefix}") from exc

        logger.info("Listed %s file(s) from s3://%s/%s", len(objects), self.bucket_name, object_prefix)
        return sorted(objects, key=lambda item: item.last_modified, reverse=True)

    def get_latest_file(self, prefix: str | None = None) -> S3ObjectInfo:
        files = self.list_files(prefix=prefix)
        if not files:
            resolved_prefix = prefix if prefix is not None else self.settings.s3_bucket_prefix
            raise ResourceNotFoundError(f"No S3 files found in s3://{self.bucket_name}/{resolved_prefix}")
        return files[0]

    def download_file(self, key: str, destination_dir: Path) -> Path:
        self._validate_bucket_config()
        destination_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(key).name or "downloaded_file"
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        destination = destination_dir / f"{timestamp}_{filename}"

        try:
            self.client.download_file(self.bucket_name, key, str(destination))
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Failed to download s3://%s/%s", self.bucket_name, key)
            raise S3OperationError(f"Failed to download s3://{self.bucket_name}/{key}") from exc

        logger.info("Downloaded s3://%s/%s to %s", self.bucket_name, key, destination)
        return destination

    def verify_bucket_access(self) -> None:
        self._validate_bucket_config()
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Failed to access S3 bucket %s.", self.bucket_name)
            raise S3OperationError(
                f"Unable to access s3://{self.bucket_name}. "
                "Check AWS credentials, region, and bucket permissions."
            ) from exc
        logger.info("Verified access to s3://%s", self.bucket_name)

    def _validate_bucket_config(self) -> None:
        if not self.bucket_name:
            raise S3OperationError("S3 bucket name is not configured. Set S3_BUCKET_NAME in the environment.")


class RawFileStorageService:
    """Persists raw input locally or stores it durably in S3-compatible storage."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_storage = LocalStorageService()
        self._s3_storage: S3StorageService | None = None

    @property
    def s3_storage(self) -> S3StorageService:
        if self._s3_storage is None:
            self._s3_storage = S3StorageService()
        return self._s3_storage

    def store_raw_file(self, source_path: Path) -> tuple[str, Path]:
        if self.settings.raw_storage_mode == "s3":
            timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            object_key = f"raw/{timestamp}_{source_path.name}"
            self.s3_storage.upload_file(source_path, key=object_key)
            return f"s3://{self.s3_storage.bucket_name}/{object_key}", source_path

        local_path = self.local_storage.store_raw_file(source_path)
        return str(local_path), local_path

    def fetch_s3_file_to_raw(self, *, s3_key: str | None = None, s3_prefix: str | None = None) -> tuple[str, Path]:
        if s3_key is None:
            latest_file = self.s3_storage.get_latest_file(prefix=s3_prefix)
            s3_key = latest_file.key

        local_path = self.s3_storage.download_file(s3_key, self.settings.raw_data_dir)
        source_uri = f"s3://{self.s3_storage.bucket_name}/{s3_key}"
        return source_uri, local_path
