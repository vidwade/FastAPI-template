from __future__ import annotations

import io
from botocore.exceptions import BotoCoreError, ClientError
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
from fastapi import UploadFile

from app.core.config import settings


class StorageService:
    """Stores files either on S3 or on the local filesystem."""

    def __init__(self) -> None:
        self._s3_client: Optional[boto3.client] = None

    @property
    def s3_client(self):  # type: ignore[return-value]
        if self._s3_client is None:
            self._s3_client = boto3.client("s3")
        return self._s3_client

    async def save_profile_picture(self, user_id: int, file: UploadFile) -> str:
        suffix = Path(file.filename or "upload").suffix
        object_name = f"profile-pictures/{user_id}-{uuid4().hex}{suffix}"
        blob = await file.read()

        if settings.has_s3:
            try:
                data = io.BytesIO(blob)
                data.seek(0)
                self.s3_client.upload_fileobj(data, settings.s3_bucket_name, object_name)  # type: ignore[arg-type]
                base_url = settings.s3_base_url.rstrip("/") if settings.s3_base_url else ""
                return f"{base_url}/{object_name}"
            except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network dependent
                raise RuntimeError("Failed to upload file to S3") from exc

        return self._save_locally(object_name, blob)

    def _save_locally(self, object_name: str, blob: bytes) -> str:
        target_dir = settings.local_upload_dir / Path(object_name).parent
        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / Path(object_name).name
        destination.write_bytes(blob)
        return str(destination)


storage_service = StorageService()
