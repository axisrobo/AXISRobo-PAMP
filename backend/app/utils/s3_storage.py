"""S3-compatible object storage service.

Provides upload / download / delete helpers backed by boto3.
Uses the S3_* settings from app.config.
"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import settings
from app.infrastructure.storage.provider import StorageProvider

# Implements app.infrastructure.storage.provider.StorageProvider

logger = logging.getLogger("eam.utils.s3_storage")

# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=BotoConfig(
                s3={"addressing_style": "path"},
                signature_version="s3",          # Use v2 sig — avoids chunked transfer-encoding
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )
    return _client


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def make_key(relative_path: str) -> str:
    """Build a full S3 object key from a relative path.

    >>> make_key("3-20260316120000123.png")
    'pm/eam/app/3-20260316120000123.png'
    """
    prefix = settings.S3_PREFIX.rstrip("/")
    return f"{prefix}/{relative_path}"


def upload_file(key: str, data: bytes | BinaryIO, content_type: str = "application/octet-stream") -> str:
    """Upload *data* to S3 under *key*. Returns the key."""
    client = _get_client()
    if isinstance(data, (bytes, bytearray)):
        body = data
        length = len(data)
    else:
        body = data.read() if hasattr(data, 'read') else data
        length = len(body)
    client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=body,
        ContentType=content_type,
        ContentLength=length,
    )
    logger.info("S3 uploaded: %s/%s", settings.S3_BUCKET, key)
    return key


def download_file(key: str) -> bytes:
    """Download an object from S3. Raises ``FileNotFoundError`` if missing."""
    client = _get_client()
    try:
        resp = client.get_object(Bucket=settings.S3_BUCKET, Key=key)
        return resp["Body"].read()
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
            raise FileNotFoundError(f"S3 key not found: {key}") from exc
        raise


def delete_file(key: str) -> None:
    """Delete an object from S3 (no error if already gone)."""
    client = _get_client()
    try:
        client.delete_object(Bucket=settings.S3_BUCKET, Key=key)
        logger.info("S3 deleted: %s/%s", settings.S3_BUCKET, key)
    except ClientError:
        logger.warning("S3 delete failed for key %s", key, exc_info=True)


def file_exists(key: str) -> bool:
    """Check whether an S3 object exists."""
    client = _get_client()
    try:
        client.head_object(Bucket=settings.S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False


def presign_url(key: str, filename: str = "", expires_in: int = 300) -> str:
    """Generate a pre-signed GET URL for *key*.

    Sets ``ResponseContentDisposition`` so the browser downloads the file
    with the original filename rather than opening it inline.
    """
    client = _get_client()
    params: dict = {"Bucket": settings.S3_BUCKET, "Key": key}
    if filename:
        import urllib.parse
        encoded = urllib.parse.quote(filename)
        params["ResponseContentDisposition"] = f'attachment; filename="{encoded}"'
    url: str = client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
    )
    return url


# ---------------------------------------------------------------------------
# StorageProvider adapter
# ---------------------------------------------------------------------------

class S3Storage(StorageProvider):
    """Async StorageProvider adapter wrapping the sync boto3 helpers."""

    def __init__(self, _settings=None):
        self._settings = _settings

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        return upload_file(key, data, content_type)

    async def download(self, key: str) -> bytes:
        return download_file(key)

    async def delete(self, key: str) -> bool:
        try:
            delete_file(key)
            return True
        except Exception:
            return False

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        return presign_url(key, "", expires_in)
