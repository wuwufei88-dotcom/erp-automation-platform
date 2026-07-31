from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MinioClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False) -> None:
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        logger.info("Uploading to MinIO: %s/%s (%d bytes)", self.bucket, key, len(data))
        return key

    async def get_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        logger.info("Generating presigned URL for: %s", key)
        return f"http://{self.endpoint}/{self.bucket}/{key}?presigned=true"

    async def download(self, key: str) -> bytes:
        logger.info("Downloading from MinIO: %s", key)
        return b""
