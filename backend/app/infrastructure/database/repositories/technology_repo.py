from __future__ import annotations
from typing import Any, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.technology.repository import TechStackRepository, LifecycleLogRepository
from app.domain.technology.entities import TechStackItem, LifecycleLog
from app.utils.filters import multi_value_condition

class PostgresTechStackRepository(TechStackRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[TechStackItem]:
        result = await self._session.execute(text("SELECT id, name, category, version, status, eol_date, security_advice, created_at FROM eam_tech_key_stack_item WHERE id = :id"), {"id": id})
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[TechStackItem], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_tech_key_stack_item WHERE status != 'Deleted'"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, name, category, version, status, eol_date, security_advice, created_at FROM eam_tech_key_stack_item WHERE status != 'Deleted' ORDER BY name LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        return [self._to_entity(row) for row in result.fetchall()], total

    async def list_by_category(self, category: str) -> list[TechStackItem]:
        result = await self._session.execute(
            text("SELECT id, name, category, version, status, eol_date, security_advice, created_at FROM eam_tech_key_stack_item WHERE category = :category AND status != 'Deleted' ORDER BY name"),
            {"category": category}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def check_compliance(self, item_id: str) -> dict:
        item = await self.get_by_id(item_id)
        return {"compliant": True, "item": item.name if item else "unknown"}

    async def soft_delete(self, id: str) -> bool:
        result = await self._session.execute(text("UPDATE eam_tech_key_stack_item SET status='Deleted' WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    async def list_master_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        subCategory: str | None = None,
        component: str | None = None,
        componentPackage: str | None = None,
        eaAdvice: str | None = None,
        status: str | None = None,
        sort_field: str = "master_no",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        conditions: list[str] = []
        params: dict[str, Any] = {}
        if category:
            conditions.append(multi_value_condition("category", "category", category, params))
        if subCategory:
            conditions.append(multi_value_condition("sub_category", "sub_category", subCategory, params))
        if component:
            conditions.append("component ILIKE :component")
            params["component"] = f"%{component}%"
        if componentPackage:
            conditions.append("component_package ILIKE :component_package")
            params["component_package"] = f"%{componentPackage}%"
        if eaAdvice:
            conditions.append(multi_value_condition("ea_advice", "ea_advice", eaAdvice, params))
        if status:
            conditions.append(multi_value_condition("status", "status", status, params))
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        order_dir = "DESC" if sort_order == "desc" else "ASC"
        offset = (page - 1) * page_size

        total_result = await self._session.execute(
            text(f"SELECT COUNT(*) AS total FROM eam.tech_stack_master_data {where_clause}"),
            params,
        )
        total = int(total_result.scalar() or 0)

        params["limit"] = page_size
        params["offset"] = offset
        data_result = await self._session.execute(
            text(
                f"SELECT * FROM eam.tech_stack_master_data {where_clause} "
                f"ORDER BY {sort_field} {order_dir} NULLS LAST LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        rows = [dict(r._mapping) for r in data_result.fetchall()]
        return rows, total

    async def create(self, entity: TechStackItem) -> TechStackItem:
        await self._session.execute(
            text("INSERT INTO eam_tech_key_stack_item (id, name, category, version, status, eol_date, security_advice, created_at) VALUES (:id, :name, :category, :version, :status, :eol_date, :security_advice, :created_at)"),
            {"id": str(entity.id), "name": entity.name, "category": entity.category, "version": entity.version, "status": entity.status, "eol_date": entity.eol_date, "security_advice": entity.security_advice, "created_at": entity.created_at}
        )
        return entity

    async def update(self, entity: TechStackItem) -> TechStackItem:
        await self._session.execute(
            text("UPDATE eam_tech_key_stack_item SET name=:name, category=:category, version=:version, status=:status, eol_date=:eol_date, security_advice=:security_advice WHERE id=:id"),
            {"id": str(entity.id), "name": entity.name, "category": entity.category, "version": entity.version, "status": entity.status, "eol_date": entity.eol_date, "security_advice": entity.security_advice}
        )
        return entity

    async def delete(self, id: str) -> bool:
        return await self.soft_delete(id)

    @staticmethod
    def _to_entity(row) -> TechStackItem:
        return TechStackItem(id=UUID(str(row[0])), name=str(row[1]), category=str(row[2]), version=str(row[3] or ""), status=str(row[4]), eol_date=row[5], security_advice=str(row[6] or ""), created_at=row[7])

class PostgresLifecycleLogRepository(LifecycleLogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[LifecycleLog]: return None
    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[LifecycleLog], int]: return [], 0
    async def list_by_item(self, item_id: str) -> list[LifecycleLog]:
        result = await self._session.execute(
            text("SELECT id, item_id, action, previous_status, new_status, changed_by, changed_at FROM eam_tech_stack_operate_log WHERE item_id = :item_id ORDER BY changed_at DESC"),
            {"item_id": item_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: LifecycleLog) -> LifecycleLog: return entity
    async def update(self, entity: LifecycleLog) -> LifecycleLog: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> LifecycleLog:
        return LifecycleLog(id=UUID(str(row[0])), item_id=str(row[1]), action=str(row[2]), previous_status=str(row[3] or ""), new_status=str(row[4] or ""), changed_by=str(row[5] or ""), changed_at=row[6])
