"""Technology stack management router.

Supports both the legacy `/api/tech-stack` compatibility surface used by the
existing router tests and the `/api/technology-stack` endpoints consumed by the
current frontend.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_permission
from app.auth.models import AuthUser
from app.auth.ownership import check_app_ownership
from app.database import get_db
from app.utils.filters import multi_value_condition
from app.utils.pagination import PaginationParams, paginated_response

from app.infrastructure.database.repositories.technology_repo import PostgresTechStackRepository
from app.application.technology.services import TechStackService


router = APIRouter()

MASTER_SORT_FIELDS = {
    "masterNo": "master_no",
    "category": "category",
    "sourceType": "source_type",
    "source": "source",
    "subCategory": "sub_category",
    "component": "component",
    "componentPackage": "component_package",
    "version": "version",
    "eaAdvice": "ea_advice",
    "standard": "standard",
    "status": "status",
    "eolDate": "eol_date",
}

LIFECYCLE_SORT_FIELDS = {
    "applicationId": "tsa.app_id",
    "applicationName": "ca.name",
    "applicationOwner": "ca.owned_by",
    "applicationOwnership": "ca.app_ownership",
    "applicationClassification": "ca.app_classification",
    "lifecycleStatus": "tsa.status",
}


def _mapping(row: Any) -> dict[str, Any]:
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


def _fetchone_mapping(result: Any) -> dict[str, Any] | None:
    row = result.fetchone()
    if row is None:
        return None
    return _mapping(row)


def _deleted(result: Any) -> bool:
    if getattr(result, "rowcount", 0):
        return True
    mappings = getattr(result, "mappings", None)
    if callable(mappings):
        return mappings().first() is not None
    return False


def _map_master(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id") or row.get("record_id") or row.get("stack_id"),
        "recordId": row.get("record_id") or row.get("stack_id") or row.get("id"),
        "masterNo": row.get("master_no"),
        "category": row.get("category") or "",
        "subCategory": row.get("sub_category") or "",
        "sourceType": row.get("source_type") or "",
        "source": row.get("source") or "",
        "component": row.get("component") or row.get("product_name") or "",
        "componentPackage": row.get("component_package") or "",
        "version": row.get("version") or "",
        "majorVersion": row.get("major_version"),
        "minorVersion": row.get("minor_version"),
        "patchVersion": row.get("patch_version"),
        "eaAdvice": row.get("ea_advice") or "",
        "securityAdvice": row.get("security_advice") or row.get("security_serverity") or "",
        "securityServerity": row.get("security_serverity") or row.get("security_advice") or "",
        "status": row.get("status") or row.get("lifecycle_status") or "",
        "standard": row.get("standard") or "",
        "eolDate": row.get("eol_date"),
        "eolIntervalTime": row.get("eol_interval_time") or "",
        "maintainabilityRiskLevel": row.get("maintainability_risk_level") or "",
        "securityRiskLevel": row.get("security_risk_level") or "",
        "cvssV3Score": row.get("cvss_v3_score"),
        "remark": row.get("remark") or row.get("description") or "",
    }


def _map_lifecycle(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id") or row.get("app_id"),
        "appId": row.get("app_id") or row.get("application_id") or "",
        "applicationId": row.get("app_id") or row.get("application_id") or "",
        "applicationName": row.get("name") or row.get("app_name") or "",
        "applicationOwnership": row.get("app_ownership") or "",
        "applicationClassification": row.get("app_classification") or "",
        "functionValueChain": row.get("u_service_area") or row.get("service_area") or "",
        "applicationOwner": row.get("owned_by") or row.get("app_it_owner") or "",
        "lifecycleStatus": row.get("status") or row.get("lifecycle_status") or "",
    }


def _map_cmdb_lookup(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "appId": row.get("app_id") or row.get("objectId") or "",
        "applicationName": row.get("name") or row.get("objectName") or "",
        "appFullName": row.get("app_full_name") or row.get("name") or row.get("objectName") or "",
        "applicationStatus": row.get("u_status") or row.get("status") or "",
        "applicationOwnership": row.get("app_ownership") or "",
        "applicationClassification": row.get("app_classification") or "",
        "functionValueChain": row.get("u_service_area") or "",
        "applicationItOwner": row.get("app_it_owner") or "",
        "portfolioManagement": row.get("portfolio_mgt") or "",
        "applicationSolutionType": row.get("app_solution_type") or "",
    }


def _map_catalog(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id") or row.get("item_id") or row.get("stack_id"),
        "itemId": row.get("item_id") or row.get("stack_id") or row.get("id"),
        "appId": row.get("app_id") or "",
        "category": row.get("category") or "",
        "subCategory": row.get("sub_category") or "",
        "component": row.get("component") or row.get("product_name") or "",
        "componentPackage": row.get("component_package") or "",
        "version": row.get("version") or "",
        "majorVersion": row.get("major_version"),
        "minorVersion": row.get("minor_version"),
        "patchVersion": row.get("patch_version"),
        "useStatus": row.get("use_status") or "",
        "eaAdvice": row.get("ea_advice") or "",
        "securityAdvice": row.get("security_advice") or "",
        "statusComments": row.get("status_comments") or "",
        "remark": row.get("remark") or row.get("usage_purpose") or "",
        "standard": row.get("standard") or "",
        "eolDate": row.get("eol_date"),
        "eolIntervalTime": row.get("eol_interval_time") or "",
        "maintainabilityRiskLevel": row.get("maintainability_risk_level") or "",
        "securityRiskLevel": row.get("security_risk_level") or "",
        "cvssV3Score": row.get("cvss_v3_score"),
        "masterNo": row.get("master_no"),
    }


def _map_team_member(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id") or row.get("member_id") or row.get("itcode"),
        "memberId": row.get("member_id") or row.get("id") or row.get("itcode"),
        "appId": row.get("app_id") or "",
        "itcode": row.get("itcode") or row.get("user_id") or "",
        "userId": row.get("itcode") or row.get("user_id") or "",
        "name": row.get("name") or row.get("user_name") or "",
        "userName": row.get("name") or row.get("user_name") or "",
        "managerItcode": row.get("manager_itcode") or "",
        "role": row.get("role") or "Member",
    }


@router.get("", dependencies=[Depends(require_permission("tech_stack_master", "read"))])
async def list_technology_stack(
    pagination: PaginationParams = Depends(),
    category: str | None = Query(None),
    subCategory: str | None = Query(None),
    component: str | None = Query(None),
    componentPackage: str | None = Query(None),
    eaAdvice: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        repo = PostgresTechStackRepository(db)
        service = TechStackService(repo)

        sort_field = MASTER_SORT_FIELDS.get(pagination.sort_field or "", "master_no")
        sort_order = "DESC" if (pagination.sort_order or "").lower() == "desc" else "ASC"

        rows, total = await service.list_master_items(
            page=pagination.page,
            page_size=pagination.page_size,
            category=category,
            subCategory=subCategory,
            component=component,
            componentPackage=componentPackage,
            eaAdvice=eaAdvice,
            status=status,
            sort_field=sort_field,
            sort_order=sort_order,
        )

        return paginated_response([_map_master(row) for row in rows], total, pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack") from exc


@router.get("/categories", dependencies=[Depends(require_permission("tech_stack_master", "read"))])
async def list_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text(
                "SELECT DISTINCT category, sub_category FROM eam.tech_stack_master_data "
                "ORDER BY category, sub_category"
            )
        )
        categories: list[dict[str, str]] = []
        sub_categories: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in result.mappings().all():
            category = row.get("category")
            sub_category = row.get("sub_category")
            if category and category not in seen:
                categories.append({"label": category, "value": category})
                seen.add(category)
            if category and sub_category:
                sub_categories.append({"category": category, "label": sub_category, "value": sub_category})
        return {"categories": categories, "subCategories": sub_categories}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack categories") from exc


@router.get("/master-options", dependencies=[Depends(require_permission("tech_stack_master", "read"))])
async def list_master_options(
    category: str | None = Query(None),
    subCategory: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions: list[str] = []
        params: dict[str, Any] = {}
        if category:
            conditions.append("category = :category")
            params["category"] = category
        if subCategory:
            conditions.append("sub_category = :sub_category")
            params["sub_category"] = subCategory
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        result = await db.execute(
            text(
                "SELECT component, component_package FROM eam.tech_stack_master_data "
                f"{where_clause} ORDER BY component, component_package"
            ),
            params,
        )
        components: list[dict[str, str]] = []
        component_packages: list[dict[str, str]] = []
        component_packages_by_component: dict[str, list[str]] = defaultdict(list)
        seen_components: set[str] = set()
        seen_packages: set[str] = set()
        for row in result.mappings().all():
            component = row.get("component")
            package_name = row.get("component_package")
            if component and component not in seen_components:
                components.append({"label": component, "value": component})
                seen_components.add(component)
            if component and package_name:
                component_packages_by_component[component].append(package_name)
            if package_name and package_name not in seen_packages:
                component_packages.append({"label": package_name, "value": package_name})
                seen_packages.add(package_name)
        return {
            "components": components,
            "componentPackages": component_packages,
            "componentPackagesByComponent": dict(component_packages_by_component),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack options") from exc


@router.get("/lifecycle", dependencies=[Depends(require_permission("tech_stack_lifecycle", "read"))])
async def list_lifecycle(
    pagination: PaginationParams = Depends(),
    applicationId: str | None = Query(None),
    applicationName: str | None = Query(None),
    applicationOwner: str | None = Query(None),
    lifecycleStatus: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions = ["1=1"]
        params: dict[str, Any] = {}
        if applicationId:
            conditions.append("tsa.app_id ILIKE :application_id")
            params["application_id"] = f"%{applicationId}%"
        if applicationName:
            conditions.append("ca.name ILIKE :application_name")
            params["application_name"] = f"%{applicationName}%"
        if applicationOwner:
            conditions.append("COALESCE(ca.owned_by, ca.app_it_owner) ILIKE :application_owner")
            params["application_owner"] = f"%{applicationOwner}%"
        if lifecycleStatus:
            conditions.append(multi_value_condition("tsa.status", "lifecycle_status", lifecycleStatus, params))
        where_clause = " AND ".join(conditions)
        sort_field = LIFECYCLE_SORT_FIELDS.get(pagination.sort_field or "", "tsa.app_id")
        sort_order = "DESC" if (pagination.sort_order or "").lower() == "desc" else "ASC"
        base_query = (
            " FROM eam.tech_stack_app tsa "
            "LEFT JOIN eam.cmdb_application ca ON ca.app_id = tsa.app_id "
            f"WHERE {where_clause}"
        )
        total_result = await db.execute(text(f"SELECT COUNT(*) {base_query}"), params)
        params["limit"] = pagination.page_size
        params["offset"] = pagination.offset
        data_result = await db.execute(
            text(
                "SELECT tsa.id, tsa.app_id, tsa.status, ca.name, ca.app_ownership, ca.app_classification, "
                "ca.u_service_area, ca.owned_by, ca.app_it_owner "
                f"{base_query} ORDER BY {sort_field} {sort_order} NULLS LAST LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        rows = [_map_lifecycle(row) for row in data_result.mappings().all()]
        return paginated_response(rows, int(total_result.scalar() or 0), pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch lifecycle records") from exc


@router.get("/resource-pool", dependencies=[Depends(require_permission("tech_stack_lifecycle", "read"))])
async def list_resource_pool(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    itcode: str | None = Query(None),
    name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions = ["1=1"]
        params: dict[str, Any] = {}
        if itcode:
            conditions.append("itcode ILIKE :itcode")
            params["itcode"] = f"%{itcode}%"
        if name:
            conditions.append("name ILIKE :name")
            params["name"] = f"%{name}%"
        where_clause = " AND ".join(conditions)
        total_result = await db.execute(text(f"SELECT COUNT(*) FROM eam.resource_pool WHERE {where_clause}"), params)
        params["limit"] = pageSize
        params["offset"] = (page - 1) * pageSize
        data_result = await db.execute(
            text(
                f"SELECT itcode, name, worker_type, manager_itcode FROM eam.resource_pool "
                f"WHERE {where_clause} ORDER BY name ASC LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        items = [
            {
                "itcode": row.get("itcode"),
                "name": row.get("name"),
                "workerType": row.get("worker_type"),
                "managerItcode": row.get("manager_itcode"),
            }
            for row in data_result.mappings().all()
        ]
        return {"items": items, "total": int(total_result.scalar() or 0), "page": page, "pageSize": pageSize}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch resource pool") from exc


@router.get("/cmdb-lookup", dependencies=[Depends(require_permission("cmdb", "read"))])
async def list_cmdb_lookup(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    appId: str | None = Query(None),
    appName: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions = ["1=1"]
        params: dict[str, Any] = {}
        if appId:
            conditions.append("app_id ILIKE :app_id")
            params["app_id"] = f"%{appId}%"
        if appName:
            conditions.append("(name ILIKE :app_name OR app_full_name ILIKE :app_name)")
            params["app_name"] = f"%{appName}%"
        where_clause = " AND ".join(conditions)
        total_result = await db.execute(text(f"SELECT COUNT(*) FROM eam.cmdb_application WHERE {where_clause}"), params)
        params["limit"] = pageSize
        params["offset"] = (page - 1) * pageSize
        data_result = await db.execute(
            text(
                f"SELECT * FROM eam.cmdb_application WHERE {where_clause} "
                "ORDER BY app_id ASC LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        return {
            "items": [_map_cmdb_lookup(row) for row in data_result.mappings().all()],
            "total": int(total_result.scalar() or 0),
            "page": page,
            "pageSize": pageSize,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch CMDB applications") from exc


@router.get("/{record_id}", dependencies=[Depends(require_permission("tech_stack_master", "read"))])
async def get_technology_stack(record_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text(
                "SELECT * FROM eam.tech_stack_master_data "
                "WHERE CAST(id AS text) = :record_id OR component = :record_id OR component_package = :record_id LIMIT 1"
            ),
            {"record_id": record_id},
        )
        row = _fetchone_mapping(result)
        if not row:
            raise HTTPException(status_code=404, detail="Technology stack item not found")
        return _map_master(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack item") from exc


@router.post("", status_code=201, dependencies=[Depends(require_permission("tech_stack_master", "write"))])
async def create_technology_stack(body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        result = await db.execute(
            text(
                """
                INSERT INTO eam.tech_stack_master_data (
                    id, category, sub_category, source_type, source, component,
                    component_package, version, ea_advice, security_advice, status,
                    standard, major_version, minor_version, patch_version, remark,
                    create_by, create_at, update_by, update_at
                ) VALUES (
                    gen_random_uuid(), :category, :sub_category, :source_type, :source, :component,
                    :component_package, :version, :ea_advice, :security_advice, :status,
                    :standard, :major_version, :minor_version, :patch_version, :remark,
                    :operator, NOW(), :operator, NOW()
                ) RETURNING *
                """
            ),
            {
                "category": body.get("category"),
                "sub_category": body.get("subCategory"),
                "source_type": body.get("sourceType"),
                "source": body.get("source"),
                "component": body.get("component") or body.get("productName"),
                "component_package": body.get("componentPackage"),
                "version": body.get("version"),
                "ea_advice": body.get("eaAdvice"),
                "security_advice": body.get("securityAdvice"),
                "status": body.get("status") or body.get("lifecycleStatus"),
                "standard": body.get("standard"),
                "major_version": body.get("majorVersion"),
                "minor_version": body.get("minorVersion"),
                "patch_version": body.get("patchVersion"),
                "remark": body.get("remark") or body.get("description"),
                "operator": user.id,
            },
        )
        await db.commit()
        row = _fetchone_mapping(result)
        return _map_master(row or body)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create technology stack item") from exc


@router.put("/{record_id}", dependencies=[Depends(require_permission("tech_stack_master", "write"))])
async def update_technology_stack(record_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        existing = await db.execute(
            text(
                "SELECT * FROM eam.tech_stack_master_data "
                "WHERE CAST(id AS text) = :record_id OR component = :record_id OR component_package = :record_id LIMIT 1"
            ),
            {"record_id": record_id},
        )
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Technology stack item not found")
        result = await db.execute(
            text(
                """
                UPDATE eam.tech_stack_master_data
                SET category = COALESCE(:category, category),
                    sub_category = COALESCE(:sub_category, sub_category),
                    source_type = COALESCE(:source_type, source_type),
                    source = COALESCE(:source, source),
                    component = COALESCE(:component, component),
                    component_package = COALESCE(:component_package, component_package),
                    version = COALESCE(:version, version),
                    ea_advice = COALESCE(:ea_advice, ea_advice),
                    security_advice = COALESCE(:security_advice, security_advice),
                    status = COALESCE(:status, status),
                    standard = COALESCE(:standard, standard),
                    remark = COALESCE(:remark, remark),
                    update_by = :operator,
                    update_at = NOW()
                WHERE CAST(id AS text) = :record_id OR component = :record_id OR component_package = :record_id
                RETURNING *
                """
            ),
            {
                "record_id": record_id,
                "category": body.get("category"),
                "sub_category": body.get("subCategory"),
                "source_type": body.get("sourceType"),
                "source": body.get("source"),
                "component": body.get("component"),
                "component_package": body.get("componentPackage"),
                "version": body.get("version"),
                "ea_advice": body.get("eaAdvice"),
                "security_advice": body.get("securityAdvice"),
                "status": body.get("status") or body.get("lifecycleStatus"),
                "standard": body.get("standard"),
                "remark": body.get("remark") or body.get("description"),
                "operator": user.id,
            },
        )
        await db.commit()
        row = _fetchone_mapping(result)
        return _map_master(row or body)
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update technology stack item") from exc


@router.delete("/{record_id}", dependencies=[Depends(require_permission("tech_stack_master", "write"))])
async def delete_technology_stack(record_id: str, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(
            text(
                "SELECT id FROM eam.tech_stack_master_data "
                "WHERE CAST(id AS text) = :record_id OR component = :record_id OR component_package = :record_id LIMIT 1"
            ),
            {"record_id": record_id},
        )
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Technology stack item not found")
        result = await db.execute(
            text(
                "DELETE FROM eam.tech_stack_master_data "
                "WHERE CAST(id AS text) = :record_id OR component = :record_id OR component_package = :record_id"
            ),
            {"record_id": record_id},
        )
        if not _deleted(result):
            raise HTTPException(status_code=404, detail="Technology stack item not found")
        await db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete technology stack item") from exc


@router.post("/apps", status_code=201, dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def create_tech_stack_app(body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        result = await db.execute(
            text(
                """
                INSERT INTO eam.tech_stack_app (id, app_id, status, create_by, create_at, update_by, update_at)
                VALUES (gen_random_uuid(), :app_id, :status, :operator, NOW(), :operator, NOW())
                RETURNING *
                """
            ),
            {"app_id": body.get("appId"), "status": body.get("status") or "Active", "operator": user.id},
        )
        await db.commit()
        row = _fetchone_mapping(result)
        return _map_lifecycle(row or {"app_id": body.get("appId")})
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to register technology stack application") from exc


@router.get("/apps/{app_id}", dependencies=[Depends(require_permission("tech_stack_lifecycle", "read"))])
async def get_tech_stack_app(app_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text(
                "SELECT tsa.id, tsa.app_id, tsa.status, ca.name, ca.app_ownership, ca.app_classification, "
                "ca.u_service_area, ca.owned_by, ca.app_it_owner "
                "FROM eam.tech_stack_app tsa "
                "LEFT JOIN eam.cmdb_application ca ON ca.app_id = tsa.app_id "
                "WHERE tsa.app_id = :app_id LIMIT 1"
            ),
            {"app_id": app_id},
        )
        row = _fetchone_mapping(result)
        if not row:
            raise HTTPException(status_code=404, detail="Technology stack application not found")
        return _map_lifecycle(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack application") from exc


@router.delete("/apps/{app_id}", dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def delete_tech_stack_app(app_id: str, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        result = await db.execute(text("DELETE FROM eam.tech_stack_app WHERE app_id = :app_id"), {"app_id": app_id})
        if not _deleted(result):
            raise HTTPException(status_code=404, detail="Technology stack application not found")
        await db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete technology stack application") from exc


@router.get("/apps/{app_id}/catalog", dependencies=[Depends(require_permission("tech_stack_lifecycle", "read"))])
async def list_catalog(
    app_id: str,
    pagination: PaginationParams = Depends(),
    category: str | None = Query(None),
    subCategory: str | None = Query(None),
    component: str | None = Query(None),
    useStatus: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions = ["app_id = :app_id"]
        params: dict[str, Any] = {"app_id": app_id}
        if category:
            conditions.append(multi_value_condition("category", "category", category, params))
        if subCategory:
            conditions.append(multi_value_condition("sub_category", "sub_category", subCategory, params))
        if component:
            conditions.append("component ILIKE :component")
            params["component"] = f"%{component}%"
        if useStatus:
            conditions.append(multi_value_condition("use_status", "use_status", useStatus, params))
        where_clause = " AND ".join(conditions)
        total_result = await db.execute(text(f"SELECT COUNT(*) FROM eam.tech_key_stack_item WHERE {where_clause}"), params)
        params["limit"] = pagination.page_size
        params["offset"] = pagination.offset
        data_result = await db.execute(
            text(
                f"SELECT * FROM eam.tech_key_stack_item WHERE {where_clause} "
                "ORDER BY component, component_package, major_version, minor_version LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        rows = [_map_catalog(row) for row in data_result.mappings().all()]
        return paginated_response(rows, int(total_result.scalar() or 0), pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack catalog") from exc


@router.post("/apps/{app_id}/catalog", status_code=201, dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def create_catalog(app_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        result = await db.execute(
            text(
                """
                INSERT INTO eam.tech_key_stack_item (
                    id, app_id, category, sub_category, component, component_package,
                    major_version, minor_version, patch_version, use_status,
                    ea_advice, security_advice, status_comments, remark,
                    create_by, create_at, update_by, update_at
                ) VALUES (
                    gen_random_uuid(), :app_id, :category, :sub_category, :component, :component_package,
                    :major_version, :minor_version, :patch_version, :use_status,
                    :ea_advice, :security_advice, :status_comments, :remark,
                    :operator, NOW(), :operator, NOW()
                ) RETURNING *
                """
            ),
            {
                "app_id": app_id,
                "category": body.get("category") or body.get("recordId"),
                "sub_category": body.get("subCategory"),
                "component": body.get("component"),
                "component_package": body.get("componentPackage"),
                "major_version": body.get("majorVersion") or 0,
                "minor_version": body.get("minorVersion") or 0,
                "patch_version": body.get("patchVersion"),
                "use_status": body.get("useStatus"),
                "ea_advice": body.get("eaAdvice"),
                "security_advice": body.get("securityAdvice"),
                "status_comments": body.get("statusComments"),
                "remark": body.get("remark") or body.get("usagePurpose"),
                "operator": user.id,
            },
        )
        await db.commit()
        row = _fetchone_mapping(result)
        return _map_catalog(row or {"app_id": app_id, **body})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create technology stack catalog item") from exc


@router.put("/apps/{app_id}/catalog/{item_id}", dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def update_catalog(app_id: str, item_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        existing = await db.execute(
            text(
                "SELECT * FROM eam.tech_key_stack_item "
                "WHERE app_id = :app_id AND (stack_id = :item_id OR CAST(id AS text) = :item_id) LIMIT 1"
            ),
            {"app_id": app_id, "item_id": item_id},
        )
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Technology stack catalog item not found")
        result = await db.execute(
            text(
                """
                UPDATE eam.tech_key_stack_item
                SET category = COALESCE(:category, category),
                    sub_category = COALESCE(:sub_category, sub_category),
                    component = COALESCE(:component, component),
                    component_package = COALESCE(:component_package, component_package),
                    use_status = COALESCE(:use_status, use_status),
                    ea_advice = COALESCE(:ea_advice, ea_advice),
                    security_advice = COALESCE(:security_advice, security_advice),
                    status_comments = COALESCE(:status_comments, status_comments),
                    remark = COALESCE(:remark, remark),
                    update_by = :operator,
                    update_at = NOW()
                WHERE app_id = :app_id AND (stack_id = :item_id OR CAST(id AS text) = :item_id)
                RETURNING *
                """
            ),
            {
                "app_id": app_id,
                "item_id": item_id,
                "category": body.get("category"),
                "sub_category": body.get("subCategory"),
                "component": body.get("component"),
                "component_package": body.get("componentPackage"),
                "use_status": body.get("useStatus"),
                "ea_advice": body.get("eaAdvice"),
                "security_advice": body.get("securityAdvice"),
                "status_comments": body.get("statusComments"),
                "remark": body.get("remark") or body.get("usagePurpose"),
                "operator": user.id,
            },
        )
        await db.commit()
        row = _fetchone_mapping(result)
        return _map_catalog(row or {"app_id": app_id, **body})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update technology stack catalog item") from exc


@router.delete("/apps/{app_id}/catalog/{item_id}", dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def delete_catalog(app_id: str, item_id: str, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        result = await db.execute(
            text(
                "DELETE FROM eam.tech_key_stack_item "
                "WHERE app_id = :app_id AND (stack_id = :item_id OR CAST(id AS text) = :item_id)"
            ),
            {"app_id": app_id, "item_id": item_id},
        )
        if not _deleted(result):
            raise HTTPException(status_code=404, detail="Technology stack catalog item not found")
        await db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete technology stack catalog item") from exc


@router.get("/apps/{app_id}/team-members", dependencies=[Depends(require_permission("tech_stack_lifecycle", "read"))])
async def list_team_members(app_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text(
                "SELECT am.id, am.app_id, am.itcode, rp.name, rp.manager_itcode "
                "FROM eam.application_member am "
                "LEFT JOIN eam.resource_pool rp ON rp.itcode = am.itcode "
                "WHERE am.app_id = :app_id ORDER BY am.create_at DESC"
            ),
            {"app_id": app_id},
        )
        return [_map_team_member(row) for row in result.mappings().all()]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack team members") from exc


@router.post("/apps/{app_id}/team-members", status_code=201, dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def add_team_members(app_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        itcodes = body.get("itcodes") or ([body.get("userId")] if body.get("userId") else [])
        if not itcodes:
            raise HTTPException(status_code=400, detail="itcodes is required")
        created: list[dict[str, Any]] = []
        for itcode in itcodes:
            result = await db.execute(
                text(
                    "INSERT INTO eam.application_member (id, app_id, itcode, create_at) "
                    "VALUES (gen_random_uuid(), :app_id, :itcode, NOW()) RETURNING *"
                ),
                {"app_id": app_id, "itcode": itcode},
            )
            row = _fetchone_mapping(result)
            if row:
                created.append(_map_team_member(row))
        await db.commit()
        return created[0] if len(created) == 1 else created
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add technology stack team members") from exc


@router.delete("/apps/{app_id}/team-members/{member_id}", status_code=204, dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def delete_team_member(app_id: str, member_id: str, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        result = await db.execute(
            text(
                "DELETE FROM eam.application_member "
                "WHERE app_id = :app_id AND (CAST(id AS text) = :member_id OR itcode = :member_id)"
            ),
            {"app_id": app_id, "member_id": member_id},
        )
        if not _deleted(result):
            raise HTTPException(status_code=404, detail="Technology stack team member not found")
        await db.commit()
        return None
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove technology stack team member") from exc


@router.get("/apps/{app_id}/operate-log", dependencies=[Depends(require_permission("tech_stack_lifecycle", "read"))])
async def list_operate_log(app_id: str, pagination: PaginationParams = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        total_result = await db.execute(
            text("SELECT COUNT(*) FROM eam.tech_stack_operate_log WHERE app_id = :app_id"),
            {"app_id": app_id},
        )
        data_result = await db.execute(
            text(
                "SELECT * FROM eam.tech_stack_operate_log WHERE app_id = :app_id "
                "ORDER BY create_at DESC LIMIT :limit OFFSET :offset"
            ),
            {"app_id": app_id, "limit": pagination.page_size, "offset": pagination.offset},
        )
        rows = [
            {
                "id": row.get("id"),
                "appId": row.get("app_id"),
                "stackId": row.get("stack_id"),
                "field": row.get("field") or row.get("action"),
                "oldValue": row.get("old_value"),
                "newValue": row.get("new_value"),
                "operator": row.get("create_by") or row.get("operator"),
                "operateTime": row.get("create_at") or row.get("operate_time"),
            }
            for row in data_result.mappings().all()
        ]
        return paginated_response(rows, int(total_result.scalar() or 0), pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch technology stack operate log") from exc


@router.post("/apps/{app_id}/checking", status_code=201, dependencies=[Depends(require_permission("tech_stack_lifecycle", "write"))])
async def run_checking(app_id: str, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_app_ownership(user, app_id, db)
        await db.execute(
            text(
                "INSERT INTO eam.tech_key_stack_auto_checking_log "
                "(id, update_time, last_update_time, old_content, new_content, app_id, create_by) "
                "VALUES (gen_random_uuid(), NOW(), NOW(), '{}'::jsonb, '{}'::jsonb, :app_id, :operator)"
            ),
            {"app_id": app_id, "operator": user.id},
        )
        await db.commit()
        return {"message": "Checking completed", "alreadyUpToDate": False}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to run technology stack checking") from exc
