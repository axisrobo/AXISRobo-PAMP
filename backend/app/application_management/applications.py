"""Applications router — ported from applications.ts."""
from __future__ import annotations

import logging
from typing import Any

import io
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response

from app.auth import require_permission, require_role, Role, get_current_user
from app.auth.models import AuthUser
from app.auth.ownership import check_app_ownership
from app.auth.audit import audit_allow, audit_deny

from app.infrastructure.database.repositories.application_repo import PostgresApplicationRepository
from app.application.application.services import ApplicationService

logger = logging.getLogger("eam.routers.applications")

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _map_app(r: dict) -> dict:
    return {
        "id": r.get("id"),
        "appId": r.get("app_id"),
        "projectId": r.get("project_id"),
        "appName": r.get("app_name"),
        "appFullName": r.get("app_full_name"),
        "appItOwner": r.get("app_it_owner"),
        "currentState": r.get("current_state"),
        "appTechIdInCmdb": r.get("app_tech_id_in_cmdb"),
        "appDescription": r.get("app_description"),
        "businessFunction": r.get("business_function"),
        "createdBy": r.get("create_by"),
        "createdAt": r.get("create_at"),
    }


# Sort field whitelist
APP_SORT_FIELDS: dict[str, str] = {
    "appId": "app_id",
    "name": "app_name",
}


# ---------------------------------------------------------------------------
# GET /cmdb — paginated list of applications from CMDB
# ---------------------------------------------------------------------------

@router.get("/cmdb", dependencies=[Depends(require_permission("application", "read"))])
async def list_cmdb_applications(
    pag: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    appId: str | None = Query(None),
    name: str | None = Query(None),
):
    try:
        repo = PostgresApplicationRepository(db)
        service = ApplicationService(repo)

        db_sort = "app_id"
        sort_order = pag.sort_order or "asc"

        rows, total = await service.list_cmdb_applications_filtered(
            page=pag.page,
            page_size=pag.page_size,
            appId=appId,
            name=name,
            sort_field=db_sort,
            sort_order=sort_order,
        )

        mapped = [
            {
                "appId": r.get("app_id"),
                "appName": r.get("name"),
                "appSolutionOwner": r.get("owned_by"),
                "appDtOwner": r.get("app_dt_owner"),
                "status": r.get("u_status"),
            }
            for r in rows
        ]

        return paginated_response(mapped, total, pag.page, pag.page_size)
    except Exception as e:
        logger.exception("Failed to fetch CMDB applications")
        raise HTTPException(status_code=500, detail="Failed to fetch CMDB applications") from e


# ---------------------------------------------------------------------------
# GET / — paginated list of applications
# ---------------------------------------------------------------------------

@router.get("", dependencies=[Depends(require_permission("application", "read"))])
async def list_applications(
    pag: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    appId: str | None = Query(None),
    name: str | None = Query(None),
    projectId: str | None = Query(None),
):
    try:
        repo = PostgresApplicationRepository(db)
        service = ApplicationService(repo)

        db_sort = APP_SORT_FIELDS.get(pag.sort_field or "", "app_id")
        sort_order = pag.sort_order or "asc"

        rows, total = await service.list_applications_filtered(
            page=pag.page,
            page_size=pag.page_size,
            appId=appId,
            name=name,
            projectId=projectId,
            sort_field=db_sort,
            sort_order=sort_order,
        )

        return paginated_response([_map_app(r) for r in rows], total, pag.page, pag.page_size)
    except Exception as e:
        logger.exception("Failed to fetch applications")
        raise HTTPException(status_code=500, detail="Failed to fetch applications") from e


# ---------------------------------------------------------------------------
# GET /bcm/versions — List distinct BizCapability data versions
# MUST be before /bcm to avoid ambiguity and before /bcm/{subpath}
# ---------------------------------------------------------------------------

@router.get("/bcm/versions", dependencies=[Depends(require_permission("application", "read"))])
async def bcm_versions(db: AsyncSession = Depends(get_db)):
    try:
        repo = PostgresApplicationRepository(db)
        service = ApplicationService(repo)
        return await service.list_bcm_versions()
    except Exception as e:
        logger.exception("Failed to fetch versions")
        raise HTTPException(status_code=500, detail="Failed to fetch versions") from e


# ---------------------------------------------------------------------------
# GET /bcm/bc-tree — Business Capability Master Data for cascader/search
# ---------------------------------------------------------------------------

@router.get("/bcm/bc-tree", dependencies=[Depends(require_permission("application", "read"))])
async def bcm_bc_tree(
    db: AsyncSession = Depends(get_db),
    version: str | None = Query(None),
    q: str | None = Query(None),
):
    try:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if version:
            conditions.append("data_version = :p_version")
            params["p_version"] = version
        if q:
            conditions.append(
                "(bc_id ILIKE :p_q OR bc_name ILIKE :p_q "
                "OR lv1_domain ILIKE :p_q OR lv2_sub_domain ILIKE :p_q "
                "OR lv3_capability_group ILIKE :p_q)"
            )
            params["p_q"] = f"%{q}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        result = await db.execute(
            text(
                f"SELECT id, bc_id, bc_name, lv1_domain, lv2_sub_domain, "
                f"lv3_capability_group, data_version, level "
                f"FROM eam.bcpf_master_data {where_clause} "
                f"ORDER BY bc_id ASC LIMIT 500"
            ),
            params,
        )
        rows = [dict(r._mapping) for r in result.fetchall()]
        return [
            {
                "id": int(r["id"]) if r.get("id") is not None else None,
                "bcId": r.get("bc_id"),
                "bcName": r.get("bc_name"),
                "domainL1": r.get("lv1_domain"),
                "subDomainL2": r.get("lv2_sub_domain"),
                "capGroupL3": r.get("lv3_capability_group"),
                "version": r.get("data_version"),
                "level": r.get("level"),
            }
            for r in rows
        ]
    except Exception as e:
        logger.exception("Failed to fetch BC tree data")
        raise HTTPException(status_code=500, detail="Failed to fetch BC tree data") from e


# ---------------------------------------------------------------------------
# GET /bcm/filter-options — Filter options for BCM search
# ---------------------------------------------------------------------------

@router.get("/bcm/filter-options", dependencies=[Depends(require_permission("application", "read"))])
async def bcm_filter_options(
    db: AsyncSession = Depends(get_db),
    version: str | None = Query(None),
    domainL1: str | None = Query(None),
    subDomainL2: str | None = Query(None),
):
    try:
        # 1. Distinct Versions
        v_res = await db.execute(text("SELECT DISTINCT data_version FROM eam.bcpf_master_data WHERE data_version IS NOT NULL ORDER BY data_version DESC"))
        versions = [r[0] for r in v_res.fetchall()]

        # 2. Distinct Application Classifications
        c_res = await db.execute(text("SELECT DISTINCT app_classification FROM eam.cmdb_application WHERE app_classification IS NOT NULL AND app_classification <> '' ORDER BY app_classification ASC"))
        classifications = [r[0] for r in c_res.fetchall()]

        # 3. Distinct Functions (Value Chain)
        f_res = await db.execute(text("SELECT DISTINCT business_function FROM eam.project_app WHERE business_function IS NOT NULL AND business_function <> '' ORDER BY business_function ASC"))
        functions = [r[0] for r in f_res.fetchall()]

        # 4. Cascading BizCapability options
        base_cond = []
        base_params = {}
        if version:
            base_cond.append("data_version = :v")
            base_params["v"] = version
        
        # Domain L1
        l1_sql = "SELECT DISTINCT lv1_domain FROM eam.bcpf_master_data WHERE lv1_domain IS NOT NULL"
        if base_cond:
            l1_sql += " AND " + " AND ".join(base_cond)
        l1_sql += " ORDER BY lv1_domain ASC"
        l1_res = await db.execute(text(l1_sql), base_params)
        domains = [r[0] for r in l1_res.fetchall()]

        # Sub Domain L2
        l2_cond = list(base_cond)
        l2_params = dict(base_params)
        if domainL1:
            l2_cond.append("lv1_domain = :l1")
            l2_params["l1"] = domainL1
        
        l2_sql = "SELECT DISTINCT lv2_sub_domain FROM eam.bcpf_master_data WHERE lv2_sub_domain IS NOT NULL"
        if l2_cond:
            l2_sql += " AND " + " AND ".join(l2_cond)
        l2_sql += " ORDER BY lv2_sub_domain ASC"
        l2_res = await db.execute(text(l2_sql), l2_params)
        sub_domains = [r[0] for r in l2_res.fetchall()]

        # Capability Group L3
        l3_cond = list(l2_cond)
        l3_params = dict(l2_params)
        if subDomainL2:
            l3_cond.append("lv2_sub_domain = :l2")
            l3_params["l2"] = subDomainL2
        
        l3_sql = "SELECT DISTINCT lv3_capability_group FROM eam.bcpf_master_data WHERE lv3_capability_group IS NOT NULL"
        if l3_cond:
            l3_sql += " AND " + " AND ".join(l3_cond)
        l3_sql += " ORDER BY lv3_capability_group ASC"
        l3_res = await db.execute(text(l3_sql), l3_params)
        cap_groups = [r[0] for r in l3_res.fetchall()]

        return {
            "versions": versions,
            "classifications": classifications,
            "functions": functions,
            "domains": domains,
            "subDomains": sub_domains,
            "capabilityGroups": cap_groups,
        }
    except Exception as e:
        logger.exception("Failed to fetch BCM filter options")
        raise HTTPException(status_code=500, detail="Failed to fetch BCM filter options") from e


# ---------------------------------------------------------------------------
# GET /bcm — Business Capability Mapping list (paginated)
# ---------------------------------------------------------------------------

@router.get("/bcm", dependencies=[Depends(require_permission("application", "read"))])
async def bcm_list(
    pag: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    appId: str | None = Query(None),
    name: str | None = Query(None),
    domainL1: str | None = Query(None),
    subDomainL2: str | None = Query(None),
    appDtOwner: str | None = Query(None),
    status: str | None = Query(None),
    bcName: str | None = Query(None),
    version: str | None = Query(None),
    appClassification: str | None = Query(None),
    businessFunction: str | None = Query(None),
    capGroupL3: str | None = Query(None),
    appSolutionOwner: str | None = Query(None),
    portfolioMgt: str | None = Query(None),
    sortKey: str | None = Query(None),
    sortDir: str | None = Query('asc'),
):
    try:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if appId:
            conditions.append("b.app_id ILIKE :p_appId")
            params["p_appId"] = f"%{appId}%"
        if name:
            conditions.append("COALESCE(NULLIF(a.app_name,''), c.name, '') ILIKE :p_name")
            params["p_name"] = f"%{name}%"
        if domainL1:
            conditions.append("m.lv1_domain = :p_domainL1")
            params["p_domainL1"] = domainL1
        if subDomainL2:
            conditions.append("m.lv2_sub_domain = :p_subDomainL2")
            params["p_subDomainL2"] = subDomainL2
        if capGroupL3:
            conditions.append("m.lv3_capability_group = :p_capGroupL3")
            params["p_capGroupL3"] = capGroupL3
        if bcName:
            conditions.append("m.bc_name ILIKE :p_bcName")
            params["p_bcName"] = f"%{bcName}%"
        if version:
            conditions.append("m.data_version = :p_version")
            params["p_version"] = version
        if appClassification:
            conditions.append("c.app_classification = :p_appClassification")
            params["p_appClassification"] = appClassification
        if businessFunction:
            conditions.append("a.business_function = :p_businessFunction")
            params["p_businessFunction"] = businessFunction
        if appSolutionOwner:
            conditions.append("c.owned_by ILIKE :p_appSolutionOwner")
            params["p_appSolutionOwner"] = f"%{appSolutionOwner}%"
        if portfolioMgt:
            conditions.append("c.portfolio_mgt = :p_portfolioMgt")
            params["p_portfolioMgt"] = portfolioMgt

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Mapping of frontend sort keys to database columns
        sort_mapping = {
            "appId": "b.app_id",
            "appName": "app_name",
            "appOwnership": "app_ownership",
            "appClassification": "app_classification",
            "businessFunction": "business_function",
            "portfolioMgt": "portfolio_mgt",
            "appSolutionOwner": "app_solution_owner",
            "appDtOwner": "app_dt_owner",
            "status": "current_state",
            "domainL1": "m.lv1_domain",
            "subDomainL2": "m.lv2_sub_domain",
            "capGroupL3": "m.lv3_capability_group",
            "bcId": "m.bc_id",
            "bcName": "m.bc_name",
            "bcNameCn": "m.bc_name_cn",
            "level": "m.level",
            "alias": "m.alias",
            "bcDescription": "m.bc_description",
            "bizGroup": "m.biz_group",
            "geo": "m.geo",
            "version": "m.data_version",
            "createdAt": "b.create_at",
            "createdBy": "b.create_by",
        }
        
        db_sort_col = sort_mapping.get(sortKey or "", "b.app_id")
        db_sort_dir = "ASC" if sortDir == "asc" else "DESC"
        order_clause = f"ORDER BY {db_sort_col} {db_sort_dir}, m.bc_id ASC"

        app_joins = (
            "LEFT JOIN eam.project_app a ON b.app_id = a.app_id "
            "LEFT JOIN eam.cmdb_application c ON b.app_id = c.app_id"
        )

        count_result = await db.execute(
            text(
                f"SELECT count(*) as count FROM eam.biz_cap_map b "
                f"LEFT JOIN eam.bcpf_master_data m ON b.data_version = m.data_version AND b.bc_id = m.bc_id "
                f"{app_joins} {where_clause}"
            ),
            params,
        )
        total = int(count_result.scalar() or 0)

        params["p_limit"] = pag.page_size
        params["p_offset"] = pag.offset

        data_result = await db.execute(
            text(
                f"SELECT b.id, b.app_id, "
                f"COALESCE(NULLIF(a.app_name,''), c.name, '') as app_name, "
                f"COALESCE(NULLIF(a.app_it_owner,''), c.app_it_owner, '') as app_it_owner, "
                f"COALESCE(c.u_status, '') as current_state, "
                f"COALESCE(c.app_ownership, '') as app_ownership, "
                f"COALESCE(c.portfolio_mgt, '') as portfolio_mgt, "
                f"COALESCE(c.app_solution_type, '') as app_solution_type, "
                f"COALESCE(c.app_classification, '') as app_classification, "
                f"COALESCE(a.business_function, '') as business_function, "
                f"COALESCE(c.app_full_name, '') as app_full_name, "
                f"COALESCE(c.owned_by, '') as app_solution_owner, "
                f"COALESCE(c.app_dt_owner, '') as app_dt_owner, "
                f"COALESCE(c.app_operation_owner, '') as app_operation_owner, "
                f"COALESCE(NULLIF(a.app_description,''), c.short_description, '') as app_description, "
                f"m.bc_id, m.bc_name, m.bc_name_cn, m.lv1_domain, m.lv2_sub_domain, "
                f"m.lv3_capability_group, m.data_version, m.level, m.alias, m.bc_description, m.biz_group, m.geo, "
                f"TO_CHAR(b.create_at, 'YYYY-MM-DD HH24:MI:SS') as created_at, "
                f"b.create_by as created_by "
                f"FROM eam.biz_cap_map b "
                f"LEFT JOIN eam.bcpf_master_data m ON b.data_version = m.data_version AND b.bc_id = m.bc_id "
                f"{app_joins} {where_clause} "
                f"{order_clause} "
                f"LIMIT :p_limit OFFSET :p_offset"
            ),
            params,
        )
        rows = [dict(r._mapping) for r in data_result.fetchall()]

        mapped = [
            {
                "id": r.get("id"),
                "appId": r.get("app_id"),
                "appName": r.get("app_name") or "",
                "appFullName": r.get("app_full_name") or "",
                "appItOwner": r.get("app_it_owner") or "",
                "status": r.get("current_state") or "",
                "appOwnership": r.get("app_ownership") or "",
                "appSolutionOwner": r.get("app_solution_owner") or "",
                "ownedBy": r.get("app_solution_owner") or "",
                "portfolioMgt": r.get("portfolio_mgt") or "",
                "appSolutionType": r.get("app_solution_type") or "",
                "appClassification": r.get("app_classification") or "",
                "businessFunction": r.get("business_function") or "",
                "appOwnerTower": r.get("app_owner_tower") or "",
                "appOwnerDomain": r.get("app_owner_domain") or "",
                "appDtOwner": r.get("app_dt_owner") or "",
                "appOperationOwner": r.get("app_operation_owner") or "",
                "appDescription": r.get("app_description") or "",
                "bcId": r.get("bc_id"),
                "bcName": r.get("bc_name"),
                "bcNameCn": r.get("bc_name_cn") or "",
                "domainL1": r.get("lv1_domain"),
                "subDomainL2": r.get("lv2_sub_domain"),
                "capGroupL3": r.get("lv3_capability_group"),
                "version": r.get("data_version"),
                "level": r.get("level"),
                "alias": r.get("alias") or "",
                "bcDescription": r.get("bc_description") or "",
                "bizGroup": r.get("biz_group") or "",
                "geo": r.get("geo") or "",
                "createdAt": r.get("created_at"),
                "createdBy": r.get("created_by") or "",
            }
            for r in rows
        ]

        return paginated_response(mapped, total, pag.page, pag.page_size)
    except Exception as e:
        logger.exception("Failed to fetch BCM data")
        raise HTTPException(status_code=500, detail="Failed to fetch BCM data") from e


# ---------------------------------------------------------------------------
# GET /bcm/export — Export Business Capability Mapping to Excel
# ---------------------------------------------------------------------------

@router.get("/bcm/export", dependencies=[Depends(require_permission("application", "read"))])
async def bcm_export(
    db: AsyncSession = Depends(get_db),
    appId: str | None = Query(None),
    name: str | None = Query(None),
    domainL1: str | None = Query(None),
    subDomainL2: str | None = Query(None),
    appDtOwner: str | None = Query(None),
    status: str | None = Query(None),
    bcName: str | None = Query(None),
    version: str | None = Query(None),
    appClassification: str | None = Query(None),
    businessFunction: str | None = Query(None),
    capGroupL3: str | None = Query(None),
    appSolutionOwner: str | None = Query(None),
    sortKey: str | None = Query(None),
    sortDir: str | None = Query('asc'),
):
    try:
        import openpyxl
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="Excel export requires openpyxl") from exc

    try:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if appId:
            conditions.append("b.app_id ILIKE :p_appId")
            params["p_appId"] = f"%{appId}%"
        if name:
            conditions.append("COALESCE(NULLIF(a.app_name,''), c.name, '') ILIKE :p_name")
            params["p_name"] = f"%{name}%"
        if domainL1:
            conditions.append("m.lv1_domain = :p_domainL1")
            params["p_domainL1"] = domainL1
        if subDomainL2:
            conditions.append("m.lv2_sub_domain = :p_subDomainL2")
            params["p_subDomainL2"] = subDomainL2
        if capGroupL3:
            conditions.append("m.lv3_capability_group = :p_capGroupL3")
            params["p_capGroupL3"] = capGroupL3
        if bcName:
            conditions.append("m.bc_name ILIKE :p_bcName")
            params["p_bcName"] = f"%{bcName}%"
        if version:
            conditions.append("m.data_version = :p_version")
            params["p_version"] = version
        if appClassification:
            conditions.append("c.app_classification = :p_appClassification")
            params["p_appClassification"] = appClassification
        if businessFunction:
            conditions.append("a.business_function = :p_businessFunction")
            params["p_businessFunction"] = businessFunction
        if appSolutionOwner:
            conditions.append("c.owned_by ILIKE :p_appSolutionOwner")
            params["p_appSolutionOwner"] = f"%{appSolutionOwner}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sort_mapping = {
            "appId": "b.app_id",
            "appName": "app_name",
            "appClassification": "app_classification",
            "businessFunction": "business_function",
            "appSolutionOwner": "app_solution_owner",
            "appDtOwner": "app_dt_owner",
            "status": "current_state",
            "domainL1": "m.lv1_domain",
            "subDomainL2": "m.lv2_sub_domain",
            "capGroupL3": "m.lv3_capability_group",
            "bcId": "m.bc_id",
            "bcName": "m.bc_name",
            "version": "m.data_version",
            "createdAt": "b.create_at",
            "createdBy": "b.create_by",
        }
        
        db_sort_col = sort_mapping.get(sortKey or "", "b.app_id")
        db_sort_dir = "ASC" if sortDir == "asc" else "DESC"
        order_clause = f"ORDER BY {db_sort_col} {db_sort_dir}, m.bc_id ASC"

        app_joins = (
            "LEFT JOIN eam.project_app a ON b.app_id = a.app_id "
            "LEFT JOIN eam.cmdb_application c ON b.app_id = c.app_id"
        )

        data_result = await db.execute(
            text(
                f"SELECT b.app_id, "
                f"COALESCE(NULLIF(a.app_name,''), c.name, '') as app_name, "
                f"COALESCE(c.app_full_name, '') as app_full_name, "
                f"COALESCE(NULLIF(a.app_it_owner,''), c.app_it_owner, '') as app_it_owner, "
                f"COALESCE(c.u_status, '') as current_state, "
                f"COALESCE(c.app_ownership, '') as app_ownership, "
                f"COALESCE(c.owned_by, '') as app_solution_owner, "
                f"COALESCE(c.portfolio_mgt, '') as portfolio_mgt, "
                f"COALESCE(c.app_solution_type, '') as app_solution_type, "
                f"COALESCE(c.app_classification, '') as app_classification, "
                f"COALESCE(a.business_function, '') as business_function, "
                f"COALESCE(c.app_dt_owner, '') as app_dt_owner, "
                f"COALESCE(c.app_operation_owner, '') as app_operation_owner, "
                f"COALESCE(NULLIF(a.app_description,''), c.short_description, '') as app_description, "
                f"m.lv1_domain, m.lv2_sub_domain, m.lv3_capability_group, "
                f"m.bc_id, m.bc_name, m.bc_name_cn, m.level, m.alias, m.bc_description, m.biz_group, m.geo, "
                f"m.data_version, "
                f"TO_CHAR(b.create_at, 'YYYY-MM-DD HH24:MI:SS') as created_at, "
                f"b.create_by as created_by "
                f"FROM eam.biz_cap_map b "
                f"LEFT JOIN eam.bcpf_master_data m ON b.data_version = m.data_version AND b.bc_id = m.bc_id "
                f"{app_joins} {where_clause} "
                f"{order_clause}"
            ),
            params,
        )
        rows = data_result.mappings().all()

        wb = openpyxl.Workbook()
        ws = wb.active
        if ws is None:
            ws = wb.create_sheet("BCM Export")
        else:
            ws.title = "BCM Export"
        
        headers = [
            "Application ID", "Application Name", "Application Full Name", "Application IT Owner", 
            "Status", "Application Ownership", "Application Solution Owner", "Portfolio Mgt", 
            "Application Solution Type", "Application Classification", "Business Function", 
            "Application DT Owner", "Application Operation Owner", "Application Description",
            "Domain (L1)", "Sub Domain (L2)", "Capability Group (L3)", "BC ID", "BC Name", 
            "BC Name (CN)", "Level", "Alias", "BC Description", "Biz Group", "Geo", 
            "Version", "Created At", "Created By"
        ]
        ws.append(headers)

        for r in rows:
            ws.append([
                r["app_id"], r["app_name"], r["app_full_name"], r["app_it_owner"],
                r["current_state"], r["app_ownership"], r["app_solution_owner"], r["portfolio_mgt"],
                r["app_solution_type"], r["app_classification"], r["business_function"],
                r["app_dt_owner"], r["app_operation_owner"], r["app_description"],
                r["lv1_domain"], r["lv2_sub_domain"], r["lv3_capability_group"],
                r["bc_id"], r["bc_name"], r["bc_name_cn"], r["level"], r["alias"], 
                r["bc_description"], r["biz_group"], r["geo"],
                r["data_version"], r["created_at"], r["created_by"]
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"BCM_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.exception("Failed to export BCM data")
        raise HTTPException(status_code=500, detail="Failed to export BCM data") from e


# ---------------------------------------------------------------------------
# POST /bcm — Create a Business Capability Mapping record
# ---------------------------------------------------------------------------

@router.post("/bcm", status_code=201, dependencies=[Depends(require_permission("bcm", "write"))])
async def bcm_create(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):

    try:
        app_id = body.get("appId")
        biz_capability_master_ids = body.get("bizCapabilityIds")

        # Backward compatibility: older clients post a single bcId/version pair
        # rather than an explicit bizCapabilityIds list.
        if not biz_capability_master_ids and body.get("bcId"):
            biz_capability_master_ids = [{
                "bizCapabilityId": body.get("bizCapabilityId") or body.get("bcId"),
                "bcId": body.get("bcId"),
                "version": body.get("version"),
            }]

        if not app_id or not biz_capability_master_ids or not isinstance(biz_capability_master_ids, list):
            raise HTTPException(status_code=400, detail="appId and bizCapabilityIds (list) are required")

        # ── Authorization: record-level ownership check ────────────
        await check_app_ownership(user, app_id, db)

        inserted_ids = []
        for item in biz_capability_master_ids:
            # Supports array of objects, compatible with legacy format
            if isinstance(item, dict):
                biz_capability_id = item.get("bizCapabilityId")
                data_version = item.get("version")
                bc_id = item.get("bcId")
            else:
                biz_capability_id = item
                data_version = body.get("version")
                bc_id = body.get("bcId")
            result = await db.execute(
                text("""
                    INSERT INTO eam.biz_cap_map (app_id, bcpf_master_id, data_version, bc_id, create_by)
                    VALUES (:app_id, :biz_capability_master_id, :data_version, :bc_id, :create_by)
                    RETURNING id
                """),
                {
                    "app_id": app_id,
                    "biz_capability_master_id": biz_capability_id,
                    "data_version": data_version,
                    "bc_id": bc_id,
                    "create_by": user.id,
                },
            )
            row = result.mappings().first()
            if row:
                inserted_ids.append(row["id"])
                audit_allow(
                    user=user,
                    action="create",
                    resource_type="bcm",
                    resource_id=str(row["id"]),
                    scope_basis=f"app={app_id}",
                )

        await db.commit()

        return {
            "success": True,
            "appId": app_id,
            "count": len(inserted_ids),
            "ids": inserted_ids
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to create BCM record")
        raise HTTPException(status_code=500, detail="Failed to create BCM record") from e


# ---------------------------------------------------------------------------
# PUT /bcm/{bcm_id} — Update a Business Capability Mapping record
# ---------------------------------------------------------------------------

@router.put("/bcm/{bcm_id}", dependencies=[Depends(require_permission("bcm", "write"))])
async def bcm_update(
    bcm_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    try:
        # Fetch existing record to resolve app ownership
        existing = await db.execute(
            text("SELECT id, app_id, bcpf_master_id FROM eam.biz_cap_map WHERE id = :id"),
            {"id": bcm_id},
        )
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="BCM record not found")

        # ── Authorization: record-level ownership check ────────────
        await check_app_ownership(user, row["app_id"], db)

        # Build dynamic SET clause
        set_parts: list[str] = []
        params: dict[str, Any] = {"db_id": bcm_id}

        if "bizCapabilityId" in body:
            set_parts.append("bcpf_master_id = :u_biz_capability_master_id")
            params["u_biz_capability_master_id"] = body["bizCapabilityId"]
        if "appId" in body:
            # If changing to a different app, check ownership of the new app too
            new_app_id = body["appId"]
            if new_app_id != row["app_id"]:
                await check_app_ownership(user, new_app_id, db)
            set_parts.append("app_id = :u_app_id")
            params["u_app_id"] = new_app_id

        if not set_parts:
            return {
                "id": row["id"],
                "appId": row["app_id"],
                "bizCapabilityId": row["bcpf_master_id"],
            }

        set_clause = ", ".join(set_parts)

        result = await db.execute(
            text(f"UPDATE eam.biz_cap_map SET {set_clause} WHERE id = :db_id RETURNING id, app_id, bcpf_master_id"),
            params,
        )
        updated = result.mappings().first()
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated record")
        await db.commit()

        audit_allow(
            user=user,
            action="update",
            resource_type="bcm",
            resource_id=bcm_id,
            scope_basis=f"app={row['app_id']}",
        )

        return {
            "id": updated["id"],
            "appId": updated["app_id"],
            "bizCapabilityId": updated["bcpf_master_id"],
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update BCM record")
        raise HTTPException(status_code=500, detail="Failed to update BCM record") from e


# ---------------------------------------------------------------------------
# DELETE /bcm/{bcm_id} — Delete a Business Capability Mapping record
# ---------------------------------------------------------------------------

@router.delete("/bcm/{bcm_id}", dependencies=[Depends(require_permission("bcm", "write"))])
async def bcm_delete(
    bcm_id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    try:
        # ── EA_Reviewer cannot delete BCM records (CRU only) ───────
        if not user.is_admin and Role.EA_REVIEWER in user.roles:
            raise HTTPException(status_code=403, detail="EA Reviewers cannot delete BCM records")

        # Fetch existing record to resolve app ownership
        existing = await db.execute(
            text("SELECT id, app_id FROM eam.biz_cap_map WHERE id = :id"),
            {"id": bcm_id},
        )
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="BCM record not found")

        # ── Authorization: record-level ownership check ────────────
        await check_app_ownership(user, row["app_id"], db)

        await db.execute(
            text("DELETE FROM eam.biz_cap_map WHERE id = :id"),
            {"id": bcm_id},
        )
        await db.commit()

        audit_allow(
            user=user,
            action="delete",
            resource_type="bcm",
            resource_id=bcm_id,
            scope_basis=f"app={row['app_id']}",
        )

        return {"message": "BCM record deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to delete BCM record")
        raise HTTPException(status_code=500, detail="Failed to delete BCM record") from e
