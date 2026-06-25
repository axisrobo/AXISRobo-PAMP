from __future__ import annotations
from typing import Any, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.application.repository import ApplicationRepository, BCMappingRepository, BizCapabilityRepository
from app.domain.application.entities import Application, BCMapping, BizCapability
from app.utils.filters import multi_value_condition, multi_value_int_condition

class PostgresApplicationRepository(ApplicationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Application]:
        result = await self._session.execute(text("SELECT id, app_id, app_name, description, owner, status, created_at FROM eam_project_app WHERE id = :id"), {"id": id})
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Application], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_project_app"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, app_id, app_name, description, owner, status, created_at FROM eam_project_app ORDER BY app_name LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        items = [self._to_entity(row) for row in result.fetchall()]
        return items, total

    async def list_by_app_id(self, app_id: str) -> list[Application]:
        result = await self._session.execute(
            text("SELECT id, app_id, app_name, description, owner, status, created_at FROM eam_project_app WHERE app_id = :app_id"),
            {"app_id": app_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_applications_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        appId: str | None = None,
        name: str | None = None,
        projectId: str | None = None,
        sort_field: str = "app_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if appId:
            conditions.append("app_id ILIKE :p_appId")
            params["p_appId"] = f"%{appId}%"
        if name:
            conditions.append("app_name ILIKE :p_name")
            params["p_name"] = f"%{name}%"
        if projectId:
            conditions.append("project_id = :p_projectId")
            params["p_projectId"] = projectId

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        order_dir = "ASC" if sort_order == "asc" else "DESC"
        offset = (page - 1) * page_size

        count_result = await self._session.execute(
            text(f"SELECT COUNT(*) as total FROM eam.project_app {where_clause}"),
            params,
        )
        total = int(count_result.scalar() or 0)

        params["p_limit"] = page_size
        params["p_offset"] = offset

        data_result = await self._session.execute(
            text(
                f"SELECT * FROM eam.project_app {where_clause} "
                f"ORDER BY {sort_field} {order_dir} "
                f"LIMIT :p_limit OFFSET :p_offset"
            ),
            params,
        )
        rows = data_result.mappings().all()
        return rows, total

    async def list_cmdb_applications_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        appId: str | None = None,
        name: str | None = None,
        sort_field: str = "app_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if appId:
            conditions.append("app_id ILIKE :p_appId")
            params["p_appId"] = f"%{appId}%"
        if name:
            conditions.append("name ILIKE :p_name")
            params["p_name"] = f"%{name}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        order_dir = "ASC" if sort_order == "asc" else "DESC"
        offset = (page - 1) * page_size

        count_result = await self._session.execute(
            text(f"SELECT COUNT(*) as total FROM eam.cmdb_application {where_clause}"),
            params,
        )
        total = int(count_result.scalar() or 0)

        params["p_limit"] = page_size
        params["p_offset"] = offset

        data_result = await self._session.execute(
            text(
                f"SELECT app_id, name, owned_by, app_dt_owner, u_status "
                f"FROM eam.cmdb_application {where_clause} "
                f"ORDER BY {sort_field} {order_dir} "
                f"LIMIT :p_limit OFFSET :p_offset"
            ),
            params,
        )
        rows = data_result.mappings().all()
        return rows, total

    async def list_bcm_versions(self) -> list[str]:
        result = await self._session.execute(
            text("SELECT DISTINCT data_version FROM eam.bcpf_master_data ORDER BY data_version DESC")
        )
        return [r[0] for r in result.fetchall()]

    async def list_cmdb_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        appId: str | None = None,
        name: str | None = None,
        q: str | None = None,
        status: str | None = None,
        ownerTower: str | None = None,
        ownedBy: str | None = None,
        portfolio: str | None = None,
        classification: str | None = None,
        solutionType: str | None = None,
        serviceArea: str | None = None,
        ownership: str | None = None,
        appFullName: str | None = None,
        sort_field: str = "app_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if appId:
            conditions.append("app_id ILIKE :p_appId")
            params["p_appId"] = f"%{appId}%"
        if name:
            conditions.append("(name ILIKE :p_name OR app_full_name ILIKE :p_name)")
            params["p_name"] = f"%{name}%"
        if q:
            conditions.append("(app_id ILIKE :p_q OR name ILIKE :p_q OR app_full_name ILIKE :p_q)")
            params["p_q"] = f"%{q}%"
        if status:
            conditions.append(multi_value_condition("u_status", "p_status", status, params))
        if ownerTower:
            conditions.append("app_owner_tower ILIKE :p_ownerTower")
            params["p_ownerTower"] = f"%{ownerTower}%"
        if ownedBy:
            conditions.append("owned_by ILIKE :p_ownedBy")
            params["p_ownedBy"] = f"%{ownedBy}%"
        if portfolio:
            conditions.append(multi_value_condition("portfolio_mgt", "p_portfolio", portfolio, params))
        if classification:
            conditions.append(multi_value_condition("app_classification", "p_classification", classification, params))
        if solutionType:
            conditions.append(multi_value_condition("app_solution_type", "p_solutionType", solutionType, params))
        if serviceArea:
            conditions.append(multi_value_condition("u_service_area", "p_serviceArea", serviceArea, params))
        if ownership:
            conditions.append(multi_value_condition("app_ownership", "p_ownership", ownership, params))
        if appFullName:
            conditions.append("app_full_name ILIKE :p_appFullName")
            params["p_appFullName"] = f"%{appFullName}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        direction = "DESC" if sort_order == "desc" else "ASC"
        order_by = f"ORDER BY (COALESCE({sort_field},'') = '') ASC, {sort_field} {direction} NULLS LAST"
        offset = (page - 1) * page_size

        count_result = await self._session.execute(
            text(f"SELECT count(*) as count FROM eam.cmdb_application {where_clause}"),
            params,
        )
        total = int(count_result.scalar() or 0)

        params["p_limit"] = page_size
        params["p_offset"] = offset

        data_result = await self._session.execute(
            text(
                f"SELECT * FROM eam.cmdb_application {where_clause} "
                f"{order_by} LIMIT :p_limit OFFSET :p_offset"
            ),
            params,
        )
        rows = data_result.mappings().all()
        return rows, total

    async def create(self, entity: Application) -> Application:
        await self._session.execute(
            text("INSERT INTO eam_project_app (id, app_id, app_name, description, owner, status, created_at) VALUES (:id, :app_id, :app_name, :description, :owner, :status, :created_at)"),
            {"id": str(entity.id), "app_id": entity.app_id, "app_name": entity.app_name, "description": entity.description, "owner": entity.owner, "status": entity.status, "created_at": entity.created_at}
        )
        return entity

    async def update(self, entity: Application) -> Application:
        await self._session.execute(
            text("UPDATE eam_project_app SET app_name=:app_name, description=:description, owner=:owner, status=:status WHERE id=:id"),
            {"id": str(entity.id), "app_name": entity.app_name, "description": entity.description, "owner": entity.owner, "status": entity.status}
        )
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("DELETE FROM eam_project_app WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> Application:
        return Application(id=UUID(str(row[0])), app_id=str(row[1]), app_name=str(row[2]), description=str(row[3] or ""), owner=str(row[4] or ""), status=str(row[5]), created_at=row[6])

class PostgresBCMappingRepository(BCMappingRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[BCMapping]: return None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[BCMapping], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_biz_cap_map"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, application_id, capability_id, capability_name, mapping_level FROM eam_biz_cap_map ORDER BY capability_name LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        return [self._to_entity(row) for row in result.fetchall()], total

    async def list_by_application(self, application_id: str) -> list[BCMapping]:
        result = await self._session.execute(
            text("SELECT id, application_id, capability_id, capability_name, mapping_level FROM eam_biz_cap_map WHERE application_id = :app_id"),
            {"app_id": application_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_by_capability(self, capability_id: str) -> list[BCMapping]:
        result = await self._session.execute(
            text("SELECT id, application_id, capability_id, capability_name, mapping_level FROM eam_biz_cap_map WHERE capability_id = :cid"),
            {"cid": capability_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: BCMapping) -> BCMapping:
        await self._session.execute(
            text("INSERT INTO eam_biz_cap_map (id, application_id, capability_id, capability_name, mapping_level) VALUES (:id, :application_id, :capability_id, :capability_name, :mapping_level)"),
            {"id": str(entity.id), "application_id": entity.application_id, "capability_id": entity.capability_id, "capability_name": entity.capability_name, "mapping_level": entity.mapping_level}
        )
        return entity

    async def update(self, entity: BCMapping) -> BCMapping: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> BCMapping:
        return BCMapping(id=UUID(str(row[0])), application_id=str(row[1]), capability_id=str(row[2]), capability_name=str(row[3] or ""), mapping_level=str(row[4] or "supports"))

class PostgresBizCapabilityRepository(BizCapabilityRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[BizCapability]: return None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[BizCapability], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_bcpf_master_data"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, code, name, parent_code, level, description FROM eam_bcpf_master_data ORDER BY code LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        return [self._to_entity(row) for row in result.fetchall()], total

    async def list_by_parent(self, parent_code: str | None) -> list[BizCapability]:
        if parent_code:
            result = await self._session.execute(text("SELECT id, code, name, parent_code, level, description FROM eam_bcpf_master_data WHERE parent_code = :pc ORDER BY code"), {"pc": parent_code})
        else:
            result = await self._session.execute(text("SELECT id, code, name, parent_code, level, description FROM eam_bcpf_master_data WHERE parent_code IS NULL ORDER BY code"))
        return [self._to_entity(row) for row in result.fetchall()]

    async def get_tree(self) -> list[dict]: return []

    async def list_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        version: str | None = None,
        domainL1: str | None = None,
        subDomainL2: str | None = None,
        capabilityGroupL3: str | None = None,
        level: str | None = None,
        sort_field: str = "bc_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if version:
            conditions.append("data_version = :version")
            params["version"] = version
        if domainL1:
            conditions.append("lv1_domain = :domainL1")
            params["domainL1"] = domainL1
        if subDomainL2:
            conditions.append("lv2_sub_domain = :subDomainL2")
            params["subDomainL2"] = subDomainL2
        if capabilityGroupL3:
            conditions.append("lv3_capability_group = :capabilityGroupL3")
            params["capabilityGroupL3"] = capabilityGroupL3
        if level:
            conditions.append(multi_value_int_condition("level", "level", level, params))

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        order_dir = "ASC" if (not sort_order) or sort_order.lower() == "asc" else "DESC"
        offset = (page - 1) * page_size

        params["limit"] = page_size
        params["offset"] = offset

        data_result = await self._session.execute(
            text(
                f"SELECT * FROM eam.bcpf_master_data WHERE {where_clause} "
                f"ORDER BY {sort_field} {order_dir} "
                f"LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        rows = data_result.mappings().all()

        count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
        count_result = await self._session.execute(
            text(f"SELECT COUNT(*) FROM eam.bcpf_master_data WHERE {where_clause}"),
            count_params,
        )
        total = int(count_result.scalar() or 0)

        return rows, total

    async def create(self, entity: BizCapability) -> BizCapability: return entity
    async def update(self, entity: BizCapability) -> BizCapability: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> BizCapability:
        return BizCapability(id=UUID(str(row[0])), code=str(row[1]), name=str(row[2]), parent_code=str(row[3]) if row[3] else None, level=int(row[4] or 1), description=str(row[5] or ""))
