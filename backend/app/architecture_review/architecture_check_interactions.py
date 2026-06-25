"""Architecture Check Interactions router — manually add interactions to an AI check record."""
from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

logger = logging.getLogger("eam.routers.architecture_check_interactions")

router = APIRouter()


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class AddArchCheckInteractionRequest(BaseModel):
    aiCheckId: str
    sourceAppId: str
    targetAppId: str
    interactionType: Optional[str] = None
    direction: Optional[str] = None
    sourceFunction: Optional[str] = None
    targetFunction: Optional[str] = None
    interfaceStatus: Optional[str] = None
    businessObject: Optional[str] = None
    remark: Optional[str] = None


# ---------------------------------------------------------------------------
# POST / — Add an interaction entry to an architecture check record
# ---------------------------------------------------------------------------


class ConfirmArchCheckInteractionsRequest(BaseModel):
    interactionUuids: List[str]


@router.post("/confirm", dependencies=[Depends(require_permission("ea_request", "write"))])
async def confirm_arch_check_interactions(
    body: ConfirmArchCheckInteractionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Confirm selected interaction entries."""
    try:
        itcode = current_user.id
        for uuid in body.interactionUuids:
            await db.execute(
                text(
                    """
                    UPDATE eam.eam_arch_ai_check_interaction
                    SET
                        status = 'Confirmed',
                        status_changed_by = :itcode,
                        status_changed_at = now(),
                        update_at = now(),
                        update_by = :itcode
                    WHERE id = :uuid
                    """
                ),
                {"uuid": uuid, "itcode": itcode},
            )
        await db.commit()
        return {"message": "Interactions confirmed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to confirm arch check interactions")
        raise HTTPException(status_code=500, detail="Failed to confirm interactions") from e


@router.post("", status_code=201, dependencies=[Depends(require_permission("ea_request", "write"))])
async def add_arch_check_interaction(
    body: AddArchCheckInteractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Manually add an interaction to an architecture AI check record."""
    try:
        itcode = current_user.id

        await db.execute(
            text(
                """
                INSERT INTO eam.eam_arch_ai_check_interaction (
                    ai_check_id,
                    source_app_id,
                    target_app_id,
                    interaction_type,
                    direction,
                    source_function,
                    target_function,
                    interface_status,
                    business_object,
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
                    :source_app_id,
                    :target_app_id,
                    :interaction_type,
                    :direction,
                    :source_function,
                    :target_function,
                    :interface_status,
                    :business_object,
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
                "source_app_id": body.sourceAppId,
                "target_app_id": body.targetAppId,
                "interaction_type": body.interactionType,
                "direction": body.direction,
                "source_function": body.sourceFunction,
                "target_function": body.targetFunction,
                "interface_status": body.interfaceStatus,
                "business_object": body.businessObject,
                "remark": body.remark,
                "status": "Waiting to Confirm",
                "itcode": itcode,
                "type": "mannual",
            },
        )
        await db.commit()
        return {"message": "Interaction added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to add arch check interaction")
        raise HTTPException(status_code=500, detail="Failed to add interaction") from e


# ---------------------------------------------------------------------------
# PUT /{interaction_uuid} — Update an interaction entry
# ---------------------------------------------------------------------------

class UpdateArchCheckInteractionRequest(BaseModel):
    sourceAppId: str
    targetAppId: str
    interactionType: Optional[str] = None
    direction: Optional[str] = None
    sourceFunction: Optional[str] = None
    targetFunction: Optional[str] = None
    interfaceStatus: Optional[str] = None
    businessObject: Optional[str] = None
    remark: Optional[str] = None


@router.put("/{interaction_uuid}", dependencies=[Depends(require_permission("ea_request", "write"))])
async def update_arch_check_interaction(
    interaction_uuid: str,
    body: UpdateArchCheckInteractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Update an existing interaction entry in an architecture AI check record."""
    try:
        itcode = current_user.id

        await db.execute(
            text(
                """
                UPDATE eam.eam_arch_ai_check_interaction
                SET
                    source_app_id = :source_app_id,
                    target_app_id = :target_app_id,
                    interaction_type = :interaction_type,
                    direction = :direction,
                    source_function = :source_function,
                    target_function = :target_function,
                    interface_status = :interface_status,
                    business_object = :business_object,
                    remark = :remark,
                    update_at = now(),
                    update_by = :itcode
                WHERE id = :interaction_uuid
                """
            ),
            {
                "interaction_uuid": interaction_uuid,
                "source_app_id": body.sourceAppId,
                "target_app_id": body.targetAppId,
                "interaction_type": body.interactionType,
                "direction": body.direction,
                "source_function": body.sourceFunction,
                "target_function": body.targetFunction,
                "interface_status": body.interfaceStatus,
                "business_object": body.businessObject,
                "remark": body.remark,
                "itcode": itcode,
            },
        )
        await db.commit()
        return {"message": "Interaction updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update arch check interaction")
        raise HTTPException(status_code=500, detail="Failed to update interaction") from e


# ---------------------------------------------------------------------------
# DELETE /{interaction_uuid} — Soft-delete an interaction entry
# ---------------------------------------------------------------------------

@router.delete("/{interaction_uuid}", dependencies=[Depends(require_permission("ea_request", "write"))])
async def delete_arch_check_interaction(
    interaction_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Soft-delete an interaction by setting status to 'Deleted'."""
    try:
        itcode = current_user.id

        await db.execute(
            text(
                """
                UPDATE eam.eam_arch_ai_check_interaction
                SET
                    status = 'Deleted',
                    status_changed_by = :itcode,
                    status_changed_at = now(),
                    update_at = now(),
                    update_by = :itcode
                WHERE id = :interaction_uuid
                """
            ),
            {"interaction_uuid": interaction_uuid, "itcode": itcode},
        )
        await db.commit()
        return {"message": "Interaction deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to delete arch check interaction")
        raise HTTPException(status_code=500, detail="Failed to delete interaction") from e


# ---------------------------------------------------------------------------
# GET / — List interaction entries for an architecture check record
# ---------------------------------------------------------------------------

@router.get("", dependencies=[Depends(require_permission("ea_request", "read"))])
async def list_arch_check_interactions(
    aiCheckId: str,
    db: AsyncSession = Depends(get_db),
):
    """List all interaction entries for an architecture AI check record.

    aiCheckId is the UUID of eam_arch_ai_check.id. Old records may store the
    numeric id from eam_arch_ai_check.result->>'id' as ai_check_id, so we
    resolve both to cover the full dataset.
    """
    try:
        # Resolve legacy numeric id (same pattern as arch-check-apps)
        numeric_id_row = await db.execute(
            text("SELECT result->>'id' AS nid FROM eam.eam_arch_ai_check WHERE id = CAST(:uuid AS uuid) LIMIT 1"),
            {"uuid": aiCheckId},
        )
        numeric_id: str | None = None
        row0 = numeric_id_row.fetchone()
        if row0:
            numeric_id = row0._mapping.get("nid")

        if numeric_id and numeric_id != aiCheckId:
            where_clause = "eaaci.ai_check_id = :uuid_id OR eaaci.ai_check_id = :numeric_id"
            params: dict = {"uuid_id": aiCheckId, "numeric_id": numeric_id}
        else:
            where_clause = "eaaci.ai_check_id = :uuid_id"
            params = {"uuid_id": aiCheckId}

        sql = text(f"""
            SELECT
                eaaci.id AS "checkAppUuid",
                eaaci.ai_check_id AS "aiCheckId",
                COALESCE(ca_s.app_id, eaaci.source_app_id) AS "sourceAppId",
                ca_s.name AS "sourceAppName",
                COALESCE(ca_t.app_id, eaaci.target_app_id) AS "targetAppId",
                ca_t.name AS "targetAppName",
                eaaci.interaction_type AS "interactionType",
                eaaci.direction,
                eaaci.source_function AS "sourceFunction",
                eaaci.target_function AS "targetFunction",
                eaaci.interface_status AS "interfaceStatus",
                replace(replace(eaaci.business_object, '[', ''), ']', '') AS "businessObject",
                eaaci.remark,
                eaaci.status_changed_by AS "statusChangedBy",
                rp_cb.name AS "statusChangedByName",
                eaaci.status_changed_at AS "statusChangedAt",
                eaaci.status AS "confirmStatus"
            FROM
                eam.eam_arch_ai_check_interaction eaaci
                LEFT JOIN stamp.cmdb_application ca_s ON (ca_s.app_id = eaaci.source_app_id OR ca_s.name = eaaci.source_app_id)
                LEFT JOIN stamp.cmdb_application ca_t ON (ca_t.app_id = eaaci.target_app_id OR ca_t.name = eaaci.target_app_id)
                LEFT JOIN eam.resource_pool rp_cb ON rp_cb.itcode = eaaci.status_changed_by
            WHERE
                ({where_clause})
                AND eaaci.status <> 'Deleted'
            ORDER BY
                eaaci.update_at DESC
        """)
        result = await db.execute(sql, params)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.exception("Failed to list arch check interactions")
        raise HTTPException(status_code=500, detail="Failed to fetch interaction list") from e
