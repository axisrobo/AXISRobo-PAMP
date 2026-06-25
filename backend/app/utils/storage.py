"""Storage provider factory — selects S3 or DB storage based on config."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.storage.provider import StorageProvider


def get_storage_provider(db: AsyncSession | None = None) -> StorageProvider:
    if settings.S3_ENDPOINT:
        from app.utils.s3_storage import S3Storage
        return S3Storage()

    if db is None:
        raise RuntimeError("Database session is required when S3 is not configured")

    from app.infrastructure.storage.db import DatabaseStorage
    return DatabaseStorage(db)
