"""Database-backed storage provider implementing StorageProvider."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.storage.provider import StorageProvider


class DatabaseStorage(StorageProvider):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        await self._session.execute(
            text(
                "INSERT INTO eam.eam_file_storage (key, data, content_type) "
                "VALUES (:key, :data, :ct) "
                "ON CONFLICT (key) DO UPDATE SET data = :data, content_type = :ct"
            ),
            {"key": key, "data": data, "ct": content_type},
        )
        return key

    async def download(self, key: str) -> bytes:
        result = await self._session.execute(
            text("SELECT data FROM eam.eam_file_storage WHERE key = :key"),
            {"key": key},
        )
        row = result.fetchone()
        if not row:
            raise FileNotFoundError(f"File not found in database: {key}")
        return bytes(row[0])

    async def delete(self, key: str) -> bool:
        result = await self._session.execute(
            text("DELETE FROM eam.eam_file_storage WHERE key = :key"),
            {"key": key},
        )
        return result.rowcount > 0

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        return f"/api/files/{key}"
