"""CMDB Applications router — ported from cmdb.ts."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response
from app.utils.filters import multi_value_condition

from app.auth import require_permission, require_role, Role
from app.ee.cmdb.sync import sync_cmdb_applications
from fastapi import BackgroundTasks

from app.infrastructure.database.repositories.application_repo import PostgresApplicationRepository
from app.application.application.services import ApplicationService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_pg_array(v: Any) -> str:
    """Strip PostgreSQL array literal braces, e.g. '{"Business Application"}' -> 'Business Application'."""
    if not v:
        return ""
    s = str(v)
    if s.startswith("{") and s.endswith("}"):
        return s[1:-1].replace('"', "")
    return s


def _map_row(r: dict) -> dict:
    return {
        "appId": r.get("app_id") or "",
        "name": r.get("name") or "",
        "appFullName": r.get("app_full_name") or "",
        "shortDescription": r.get("short_description") or "",
        "status": r.get("u_status") or "",
        "appOwnership": r.get("app_ownership") or "",
        "ownedBy": r.get("owned_by") or "",
        "appSolutionOwner": r.get("owned_by") or "",
        "appItOwner": r.get("app_it_owner") or "",
        "appDtOwner": r.get("app_dt_owner") or "",
        "appOperationOwner": r.get("app_operation_owner") or "",
        "appOwnerTower": r.get("app_owner_tower") or "",
        "appOwnerDomain": r.get("app_owner_domain") or "",
        "appOperationOwnerTower": r.get("app_operation_owner_tower") or "",
        "appOperationOwnerDomain": r.get("app_operation_owner_domain") or "",
        "portfolioMgt": r.get("portfolio_mgt") or "",
        "appClassification": r.get("app_classification") or "",
        "appSolutionType": r.get("app_solution_type") or "",
        "serviceArea": r.get("u_service_area") or "",
        "patchLevel": r.get("patch_level") or "",
        "updateAt": r.get("update_at"),
        "decommissionedAt": r.get("decommissioned_at"),
    }


# Sort column whitelist (uses sortKey/sortDir instead of sortField/sortOrder)
SORT_COLUMNS: dict[str, str] = {
    "appId": "app_id",
    "name": "name",
    "appFullName": "app_full_name",
    "status": "u_status",
    "appOwnerTower": "app_owner_tower",
    "ownedBy": "owned_by",
    "portfolioMgt": "portfolio_mgt",
    "appClassification": "app_classification",
}


# ---------------------------------------------------------------------------
# GET / — paginated list with search & sort
# ---------------------------------------------------------------------------

@router.get("", dependencies=[Depends(require_permission("cmdb", "read"))])
async def list_cmdb(
    pag: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    appId: str | None = Query(None),
    name: str | None = Query(None),
    q: str | None = Query(None),
    status: str | None = Query(None),
    ownerTower: str | None = Query(None),
    ownedBy: str | None = Query(None),
    portfolio: str | None = Query(None),
    classification: str | None = Query(None),
    solutionType: str | None = Query(None),
    serviceArea: str | None = Query(None),
    ownership: str | None = Query(None),
    appFullName: str | None = Query(None),
    sortKey: str | None = Query(None),
    sortDir: str | None = Query(None),
):
    try:
        repo = PostgresApplicationRepository(db)
        service = ApplicationService(repo)

        # Sort — uses sortKey/sortDir (not sortField/sortOrder)
        db_col = SORT_COLUMNS.get(sortKey or "", "app_id")
        direction = "DESC" if sortDir == "desc" else "ASC"

        rows, total = await service.list_cmdb_filtered(
            page=pag.page,
            page_size=pag.page_size,
            appId=appId,
            name=name,
            q=q,
            status=status,
            ownerTower=ownerTower,
            ownedBy=ownedBy,
            portfolio=portfolio,
            classification=classification,
            solutionType=solutionType,
            serviceArea=serviceArea,
            ownership=ownership,
            appFullName=appFullName,
            sort_field=db_col,
            sort_order=sortDir or "asc",
        )

        return paginated_response([_map_row(r) for r in rows], total, pag.page, pag.page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch CMDB applications") from e


# ---------------------------------------------------------------------------
# GET /{app_id} — single record detail
# ---------------------------------------------------------------------------

@router.get("/{app_id}", dependencies=[Depends(require_permission("cmdb", "read"))])
async def get_cmdb_detail(app_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text("SELECT * FROM eam.cmdb_application WHERE app_id = :p_appId LIMIT 1"),
            {"p_appId": app_id},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        return _map_row(dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch application detail") from e


# ---------------------------------------------------------------------------
# POST /sync — manual trigger sync
# ---------------------------------------------------------------------------

@router.post("/sync", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def trigger_cmdb_sync(background_tasks: BackgroundTasks):
    """Manually trigger the CMDB synchronization process in the background."""
    background_tasks.add_task(sync_cmdb_applications)
    return {"message": "Sync started in background"}
