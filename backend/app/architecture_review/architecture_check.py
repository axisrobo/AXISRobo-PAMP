"""Architecture Check Apps router — manually add apps to an AI check record."""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

logger = logging.getLogger("eam.routers.architecture_check")

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AddArchCheckAppRequest(BaseModel):
    aiCheckId: str
    appId: str
    appName: str
    idIsStandard: bool = False
    standardId: Optional[str] = None
    functions: Optional[List[str]] = None
    checkAppStatus: str
    remark: Optional[str] = None


class UpdateArchCheckAppRequest(BaseModel):
    appId: str
    appName: str
    idIsStandard: bool = False
    standardId: Optional[str] = None
    functions: Optional[List[str]] = None
    checkAppStatus: str
    remark: Optional[str] = None


class ConfirmArchCheckAppsRequest(BaseModel):
    checkAppUuids: List[str]


# ---------------------------------------------------------------------------
# POST / — Add an application entry to an architecture check record
# ---------------------------------------------------------------------------

@router.post("", status_code=201, dependencies=[Depends(require_permission("ea_request", "write"))])
async def add_arch_check_app(
    body: AddArchCheckAppRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Manually add an application to an architecture AI check record."""
    try:
        itcode = current_user.id

        # Convert functions list to PostgreSQL array literal  e.g. ['Patient'] → '{Patient}'
        functions_pg: Any = None
        if body.functions:
            escaped = [f.replace('"', '\\"') for f in body.functions]
            functions_pg = "{" + ",".join(escaped) + "}"

        await db.execute(
            text(
                """
                INSERT INTO eam.eam_arch_ai_check_app (
                    ai_check_id,
                    app_id,
                    id_is_standard,
                    standard_id,
                    app_name,
                    "functions",
                    check_app_status,
                    remark,
                    status,
                    status_changed_by,
                    status_changed_at,
                    create_at,
                    create_by,
                    update_at,
                    update_by,
                    "type"
                ) VALUES (
                    :ai_check_id,
                    :app_id,
                    :id_is_standard,
                    :standard_id,
                    :app_name,
                    :functions,
                    :check_app_status,
                    :remark,
                    :status,
                    :itcode,
                    now(),
                    now(),
                    :itcode,
                    now(),
                    :itcode,
                    :type
                )
                """
            ),
            {
                "ai_check_id": body.aiCheckId,
                "app_id": body.appId,
                "id_is_standard": body.idIsStandard,
                "standard_id": body.standardId,
                "app_name": body.appName,
                "functions": functions_pg,
                "check_app_status": body.checkAppStatus,
                "remark": body.remark,
                "status": "Waiting to Confirm",
                "itcode": itcode,
                "type": "mannual",
            },
        )
        await db.commit()
        return {"message": "Application added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to add arch check app")
        raise HTTPException(status_code=500, detail="Failed to add application") from e


# ---------------------------------------------------------------------------
# PUT /{check_app_uuid} — Update an application entry
# ---------------------------------------------------------------------------

@router.put("/{check_app_uuid}", dependencies=[Depends(require_permission("ea_request", "write"))])
async def update_arch_check_app(
    check_app_uuid: str,
    body: UpdateArchCheckAppRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Update an existing application entry in an architecture AI check record."""
    try:
        itcode = current_user.id

        functions_pg: Any = None
        if body.functions:
            escaped = [f.replace('"', '\\"') for f in body.functions]
            functions_pg = "{" + ",".join(escaped) + "}"

        await db.execute(
            text(
                """
                UPDATE eam.eam_arch_ai_check_app
                SET
                  app_id = :app_id,
                  id_is_standard = :id_is_standard,
                  standard_id = :standard_id,
                  app_name = :app_name,
                  "functions" = :functions,
                  check_app_status = :check_app_status,
                  remark = :remark,
                  update_at = now(),
                  update_by = :itcode
                WHERE id = :check_app_uuid
                """
            ),
            {
                "check_app_uuid": check_app_uuid,
                "app_id": body.appId,
                "id_is_standard": body.idIsStandard,
                "standard_id": body.standardId,
                "app_name": body.appName,
                "functions": functions_pg,
                "check_app_status": body.checkAppStatus,
                "remark": body.remark,
                "itcode": itcode,
            },
        )
        await db.commit()
        return {"message": "Application updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update arch check app")
        raise HTTPException(status_code=500, detail="Failed to update application") from e


# ---------------------------------------------------------------------------
# DELETE /{check_app_uuid} — Soft-delete an application entry
# ---------------------------------------------------------------------------

@router.delete("/{check_app_uuid}", dependencies=[Depends(require_permission("ea_request", "write"))])
async def delete_arch_check_app(
    check_app_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Soft-delete an application entry by setting status = 'Deleted'."""
    try:
        itcode = current_user.id
        await db.execute(
            text(
                """
                UPDATE eam.eam_arch_ai_check_app
                SET
                  status = 'Deleted',
                  status_changed_by = :itcode,
                  status_changed_at = now(),
                  update_at = now(),
                  update_by = :itcode
                WHERE id = :check_app_uuid
                """
            ),
            {"check_app_uuid": check_app_uuid, "itcode": itcode},
        )
        await db.commit()
        return {"message": "Application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to delete arch check app")
        raise HTTPException(status_code=500, detail="Failed to delete application") from e


# ---------------------------------------------------------------------------
# POST /confirm — Batch confirm application entries
# ---------------------------------------------------------------------------

@router.post("/confirm", dependencies=[Depends(require_permission("ea_request", "write"))])
async def confirm_arch_check_apps(
    body: ConfirmArchCheckAppsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Batch confirm application entries by setting status = 'Confirmed'."""
    if not body.checkAppUuids:
        raise HTTPException(status_code=400, detail="checkAppUuids must not be empty")
    try:
        itcode = current_user.id
        placeholders = ", ".join(f":uuid_{i}" for i in range(len(body.checkAppUuids)))
        params: dict = {"itcode": itcode}
        for i, uuid in enumerate(body.checkAppUuids):
            params[f"uuid_{i}"] = uuid

        await db.execute(
            text(
                f"""
                UPDATE eam.eam_arch_ai_check_app
                SET
                  status = 'Confirmed',
                  status_changed_by = :itcode,
                  status_changed_at = now(),
                  update_at = now(),
                  update_by = :itcode
                WHERE id IN ({placeholders})
                """
            ),
            params,
        )
        await db.commit()
        return {"message": "Applications confirmed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to confirm arch check apps")
        raise HTTPException(status_code=500, detail="Failed to confirm applications") from e


# ---------------------------------------------------------------------------
# GET / — List application entries for an architecture check record
# ---------------------------------------------------------------------------

@router.get("", dependencies=[Depends(require_permission("ea_request", "read"))])
async def list_arch_check_apps(
    aiCheckId: str,
    db: AsyncSession = Depends(get_db),
):
    """List all application entries for an architecture AI check record.

    aiCheckId is the UUID of eam_arch_ai_check.id (new style). Old records in
    eam_arch_ai_check_app store the numeric id from eam_arch_ai_check.result->>'id'
    as ai_check_id. We resolve both to cover the full dataset.
    """
    try:
        # Step 1: resolve the legacy numeric id stored by the external AI system.
        # eam_arch_ai_check.id is UUID; old eam_arch_ai_check_app rows store the
        # numeric string from result->>'id' instead of the UUID.
        numeric_id_row = await db.execute(
            text("SELECT result->>'id' AS nid FROM eam.eam_arch_ai_check WHERE id = CAST(:uuid AS uuid) LIMIT 1"),
            {"uuid": aiCheckId},
        )
        numeric_id: str | None = None
        row0 = numeric_id_row.fetchone()
        if row0:
            numeric_id = row0._mapping.get("nid")

        # Step 2: build WHERE clause with explicit OR params to avoid asyncpg
        # array-typing issues that occur with text() + ANY(:list).
        if numeric_id and numeric_id != aiCheckId:
            where_clause = "eaaca.ai_check_id = :uuid_id OR eaaca.ai_check_id = :numeric_id"
            params: dict = {"uuid_id": aiCheckId, "numeric_id": numeric_id}
        else:
            where_clause = "eaaca.ai_check_id = :uuid_id"
            params = {"uuid_id": aiCheckId}

        # Step 3: query the app list matching any of the candidate ids.
        sql = text(f"""
            SELECT
              eaaca.id AS "checkAppUuid",
              eaaca.ai_check_id AS "aiCheckId",
              eaaca.app_id AS "appId",
              COALESCE(ca.name, eaaca.app_name) AS "appName",
              eaaca.id_is_standard AS "idIsStandard",
              eaaca.standard_id AS "standardId",
              eaaca."functions",
              eaaca.check_app_status AS "checkAppStatus",
              eaaca.remark,
              eaaca.status_changed_by AS "statusChangedBy",
              rp_cb.name AS "statusChangedByName",
              eaaca.status_changed_at AS "statusChangedAt",
              eaaca.status AS "confirmStatus",
              ca.app_ownership AS "appOwnership",
              ca.owned_by AS "appSolutionOwner",
              rp_ob.name AS "appSolutionOwnerName",
              ca.app_dt_owner AS "appDtOwner",
              rp_do.name AS "appDtOwnerName",
              ca.portfolio_mgt AS "portfolioMgt",
              ca.app_solution_type AS "appSolutionType",
              substring(
                ca.app_classification
                FROM 3 FOR char_length(ca.app_classification) - 4
              ) AS "appClassification",
              ca.u_status AS "appStatus",
              ca.u_service_area AS "bizFunction"
            FROM
              eam.eam_arch_ai_check_app eaaca
              LEFT JOIN stamp.cmdb_application ca ON ca.app_id = eaaca.app_id
              LEFT JOIN eam.resource_pool rp_ob ON rp_ob.itcode = ca.owned_by
              LEFT JOIN eam.resource_pool rp_do ON rp_do.itcode = ca.app_dt_owner
              LEFT JOIN eam.resource_pool rp_cb ON rp_cb.itcode = eaaca.status_changed_by
            WHERE
              ({where_clause})
              AND eaaca.status <> 'Deleted'
            ORDER BY
              eaaca.update_at DESC
        """)
        result = await db.execute(sql, params)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.exception("Failed to list arch check apps")
        raise HTTPException(status_code=500, detail="Failed to fetch application list") from e
