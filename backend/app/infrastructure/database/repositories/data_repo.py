from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.data_management.repository import MasterDataRepository, CertificationRepository, ResourceRepository
from app.domain.data_management.entities import MasterDataEntry, Certification, Resource

class PostgresMasterDataRepository(MasterDataRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[MasterDataEntry]:
        result = await self._session.execute(
            text("SELECT id, data_type, code, name, description, is_active, created_at FROM eam_master_data WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[MasterDataEntry], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_master_data"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, data_type, code, name, description, is_active, created_at FROM eam_master_data ORDER BY code LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        items = [self._to_entity(row) for row in result.fetchall()]
        return items, total

    async def search(self, query: str) -> list[MasterDataEntry]:
        result = await self._session.execute(
            text("SELECT id, data_type, code, name, description, is_active, created_at FROM eam_master_data WHERE name ILIKE :query OR code ILIKE :query ORDER BY code"),
            {"query": f"%{query}%"}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_by_type(self, data_type: str) -> list[MasterDataEntry]:
        result = await self._session.execute(
            text("SELECT id, data_type, code, name, description, is_active, created_at FROM eam_master_data WHERE data_type = :data_type ORDER BY code"),
            {"data_type": data_type}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: MasterDataEntry) -> MasterDataEntry:
        await self._session.execute(
            text("INSERT INTO eam_master_data (id, data_type, code, name, description, is_active, created_at) VALUES (:id, :data_type, :code, :name, :description, :is_active, :created_at)"),
            {"id": str(entity.id), "data_type": entity.data_type, "code": entity.code, "name": entity.name, "description": entity.description, "is_active": entity.is_active, "created_at": entity.created_at}
        )
        return entity

    async def update(self, entity: MasterDataEntry) -> MasterDataEntry:
        await self._session.execute(
            text("UPDATE eam_master_data SET name=:name, description=:description, is_active=:is_active WHERE id=:id"),
            {"id": str(entity.id), "name": entity.name, "description": entity.description, "is_active": entity.is_active}
        )
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("UPDATE eam_master_data SET is_active=false WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> MasterDataEntry:
        return MasterDataEntry(id=UUID(str(row[0])), data_type=str(row[1]), code=str(row[2]), name=str(row[3]), description=str(row[4] or ""), is_active=bool(row[5]), created_at=row[6])

class PostgresCertificationRepository(CertificationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Certification]:
        result = await self._session.execute(text("SELECT id, person_itcode, cert_type, cert_name, issue_date, expiry_date, status FROM eam_certifications WHERE id = :id"), {"id": id})
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Certification], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_certifications"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, person_itcode, cert_type, cert_name, issue_date, expiry_date, status FROM eam_certifications ORDER BY cert_name LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        return [self._to_entity(row) for row in result.fetchall()], total

    async def list_by_person(self, itcode: str) -> list[Certification]:
        result = await self._session.execute(
            text("SELECT id, person_itcode, cert_type, cert_name, issue_date, expiry_date, status FROM eam_certifications WHERE person_itcode = :itcode"),
            {"itcode": itcode}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_expiring_soon(self, days: int = 30) -> list[Certification]:
        result = await self._session.execute(
            text("SELECT id, person_itcode, cert_type, cert_name, issue_date, expiry_date, status FROM eam_certifications WHERE expiry_date <= CURRENT_DATE + :days AND status = 'active'"),
            {"days": days}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Certification) -> Certification:
        await self._session.execute(
            text("INSERT INTO eam_certifications (id, person_itcode, cert_type, cert_name, issue_date, expiry_date, status) VALUES (:id, :person_itcode, :cert_type, :cert_name, :issue_date, :expiry_date, :status)"),
            {"id": str(entity.id), "person_itcode": entity.person_itcode, "cert_type": entity.cert_type, "cert_name": entity.cert_name, "issue_date": entity.issue_date, "expiry_date": entity.expiry_date, "status": entity.status}
        )
        return entity

    async def update(self, entity: Certification) -> Certification:
        await self._session.execute(
            text("UPDATE eam_certifications SET cert_type=:cert_type, cert_name=:cert_name, issue_date=:issue_date, expiry_date=:expiry_date, status=:status WHERE id=:id"),
            {"id": str(entity.id), "cert_type": entity.cert_type, "cert_name": entity.cert_name, "issue_date": entity.issue_date, "expiry_date": entity.expiry_date, "status": entity.status}
        )
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("UPDATE eam_certifications SET status='inactive' WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> Certification:
        return Certification(id=UUID(str(row[0])), person_itcode=str(row[1]), cert_type=str(row[2]), cert_name=str(row[3]), issue_date=row[4], expiry_date=row[5], status=str(row[6]))

class PostgresResourceRepository(ResourceRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Resource]: return None
    async def list(self, page: int = 1, page_size: int = 20): return [], 0

    async def list_by_type(self, resource_type: str) -> list[Resource]:
        result = await self._session.execute(
            text("SELECT id, name, resource_type, description, is_available FROM eam_resources WHERE resource_type = :resource_type ORDER BY name"),
            {"resource_type": resource_type}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Resource) -> Resource:
        await self._session.execute(
            text("INSERT INTO eam_resources (id, name, resource_type, description, is_available) VALUES (:id, :name, :resource_type, :description, :is_available)"),
            {"id": str(entity.id), "name": entity.name, "resource_type": entity.resource_type, "description": entity.description, "is_available": entity.is_available}
        )
        return entity

    async def update(self, entity: Resource) -> Resource: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> Resource:
        return Resource(id=UUID(str(row[0])), name=str(row[1]), resource_type=str(row[2]), description=str(row[3] or ""), is_available=bool(row[4]))
