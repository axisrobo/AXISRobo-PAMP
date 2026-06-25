from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.add.repository import ConcernRepository
from app.domain.add.entities import Concern

class PostgresConcernRepository(ConcernRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Concern]:
        result = await self._session.execute(
            text("SELECT id, concern_key, concern_name, layer, description, is_active FROM eam.avdm_pact_concern WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Concern], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam.avdm_pact_concern"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, concern_key, concern_name, layer, description, is_active FROM eam.avdm_pact_concern ORDER BY layer, concern_key LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        items = [self._to_entity(row) for row in result.fetchall()]
        return items, total

    async def list_by_category(self, category: str) -> list[Concern]:
        result = await self._session.execute(
            text("SELECT id, concern_key, concern_name, layer, description, is_active FROM eam.avdm_pact_concern WHERE layer = :category ORDER BY concern_key"),
            {"category": category}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Concern) -> Concern:
        await self._session.execute(
            text("INSERT INTO eam.avdm_pact_concern (concern_key, concern_name, layer, description, risk_tags, is_active, create_by, update_by) VALUES (:ck, :cn, :layer, :desc, '[]'::jsonb, TRUE, 'system', 'system')"),
            {"ck": entity.code, "cn": entity.name, "layer": entity.category, "desc": entity.description}
        )
        return entity

    async def update(self, entity: Concern) -> Concern:
        await self._session.execute(
            text("UPDATE eam.avdm_pact_concern SET concern_name=:cn, layer=:layer, description=:desc, update_at=NOW() WHERE id=:id"),
            {"id": str(entity.id), "cn": entity.name, "layer": entity.category, "desc": entity.description}
        )
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("DELETE FROM eam.avdm_pact_concern WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> Concern:
        return Concern(
            id=UUID(str(row[0])),
            code=str(row[1] or ""),
            name=str(row[2] or ""),
            category=str(row[3] or ""),
            description=str(row[4] or ""),
            severity="medium",
            likelihood="medium",
            classification="recommended"
        )
