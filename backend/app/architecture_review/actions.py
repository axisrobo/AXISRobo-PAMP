"""Compatibility actions router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_permission
from app.auth.models import AuthUser
from app.auth.ownership import check_project_ownership
from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response
from app.infrastructure.database.repositories.review_repo import PostgresActionRepository


router = APIRouter()

SORT_FIELDS = {
    "createdAt": "create_at",
    "dueDate": "due_date",
    "priority": "priority",
    "status": "status",
}


def _map_action(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "actionNo": row.get("action_no"),
        "actionTitle": row.get("action_title") or "",
        "projectId": row.get("project_id") or "",
        "meetingId": row.get("meeting_id"),
        "priority": row.get("priority") or "",
        "dueDate": row.get("due_date"),
        "closeDate": row.get("close_date"),
        "startDate": row.get("start_date"),
        "openDate": row.get("open_date"),
        "assignee": row.get("assignee") or "",
        "assigneeName": row.get("assignee_name") or "",
        "actionDescription": row.get("action_description") or "",
        "status": row.get("status") or "",
        "type": row.get("type") or "",
        "requestedBy": row.get("requested_by") or "",
        "requestedByName": row.get("requested_by_name") or "",
        "actionUpdates": row.get("action_updates"),
        "applicableDomain": row.get("applicable_domain") or "",
        "createdAt": row.get("create_at"),
        "updatedAt": row.get("update_at"),
        "createdBy": row.get("create_by") or "",
        "requestId": row.get("request_id"),
    }


@router.get("", dependencies=[Depends(require_permission("action", "read"))])
async def list_actions(
    pagination: PaginationParams = Depends(),
    projectId: str | None = Query(None),
    status: str | None = Query(None),
    requestId: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions: list[str] = []
        params: dict[str, object] = {}
        if projectId:
            conditions.append("project_id = :project_id")
            params["project_id"] = projectId
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if requestId:
            conditions.append("request_id = :request_id")
            params["request_id"] = requestId
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sort_field = SORT_FIELDS.get(pagination.sort_field or "", "create_at")
        sort_order = "DESC" if (pagination.sort_order or "").lower() == "desc" else "ASC"
        params["limit"] = pagination.page_size
        params["offset"] = pagination.offset

        repo = PostgresActionRepository(db)
        data_sql = (
            f"SELECT * FROM eam.eam_actions {where_clause} "
            f"ORDER BY {sort_field} {sort_order} LIMIT :limit OFFSET :offset"
        )
        count_sql = f"SELECT COUNT(*) FROM eam.eam_actions {where_clause}"
        count_params = {k: v for k, v in params.items() if k not in {"limit", "offset"}}

        rows = await repo.execute_rows(data_sql, params)
        count_result = await repo.execute_scalar(count_sql, count_params) or 0
        open_result = await repo.execute_scalar(count_sql, count_params) or 0
        validation_result = await repo.execute_scalar(count_sql, count_params) or 0
        closed_result = await repo.execute_scalar(count_sql, count_params) or 0

        payload = paginated_response(
            [_map_action(row) for row in rows],
            int(count_result),
            pagination.page,
            pagination.page_size,
        )
        payload["summary"] = {
            "open": int(open_result),
            "inValidation": int(validation_result),
            "closed": int(closed_result),
        }
        return payload
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch actions") from exc


@router.get("/{action_id}", dependencies=[Depends(require_permission("action", "read"))])
async def get_action(action_id: str, db: AsyncSession = Depends(get_db)):
    try:
        action_result = await db.execute(text("SELECT * FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        action = action_result.mappings().first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        project_result = await db.execute(text("SELECT name as project_name FROM eam.eam_project WHERE project_id = :project_id OR id::text = :project_id"), {"project_id": action.get("project_id")})
        request_result = await db.execute(text("SELECT request_id FROM eam.eam_architecture_review WHERE project_id = :project_id LIMIT 1"), {"project_id": action.get("project_id")})
        payload = _map_action(action)
        payload["projectName"] = (project_result.mappings().first() or {}).get("project_name")
        payload["requestId"] = payload.get("requestId") or (request_result.mappings().first() or {}).get("request_id")
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch action") from exc


@router.get("/{action_id}/comments", dependencies=[Depends(require_permission("action", "read"))])
async def list_action_comments(action_id: str, db: AsyncSession = Depends(get_db)):
    try:
        action_result = await db.execute(text("SELECT id FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        if not action_result.mappings().first():
            raise HTTPException(status_code=404, detail="Action not found")
        comments_result = await db.execute(
            text("SELECT * FROM eam.comments WHERE object_type = 'action' AND object_id = :object_id ORDER BY create_at DESC"),
            {"object_id": action_id},
        )
        return [dict(row) for row in comments_result.mappings().all()]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch action comments") from exc


@router.post("/{action_id}/comments", status_code=201, dependencies=[Depends(require_permission("action", "write"))])
async def add_action_comment(action_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        action_result = await db.execute(text("SELECT * FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        action = action_result.mappings().first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        if action.get("project_id"):
            await check_project_ownership(user, action.get("project_id"), db)
        result = await db.execute(
            text(
                "INSERT INTO eam.comments (id, object_type, object_id, content, create_by, create_at) "
                "VALUES (gen_random_uuid(), 'action', :object_id, :content, :create_by, NOW()) RETURNING *"
            ),
            {"object_id": action_id, "content": body.get("content"), "create_by": user.id},
        )
        await db.commit()
        return dict((result.mappings().first() or {}))
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add action comment") from exc


@router.get("/{action_id}/audit-logs", dependencies=[Depends(require_permission("action", "read"))])
async def list_action_audit_logs(action_id: str, pagination: PaginationParams = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        action_result = await db.execute(text("SELECT id FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        if not action_result.mappings().first():
            raise HTTPException(status_code=404, detail="Action not found")
        data_result = await db.execute(
            text(
                "SELECT * FROM eam.audit_log WHERE object_type = 'action' AND object_id = :object_id "
                "ORDER BY create_time DESC LIMIT :limit OFFSET :offset"
            ),
            {"object_id": action_id, "limit": pagination.page_size, "offset": pagination.offset},
        )
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM eam.audit_log WHERE object_type = 'action' AND object_id = :object_id"),
            {"object_id": action_id},
        )
        return paginated_response(data_result.mappings().all(), int(count_result.scalar() or 0), pagination.page, pagination.page_size)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch action audit logs") from exc


@router.post("", status_code=201, dependencies=[Depends(require_permission("action", "write"))])
async def create_action(body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    required_fields = [
        "projectId", "actionTitle", "priority", "type", "requestedBy",
        "requestedByName", "applicableDomain", "actionDescription",
    ]
    if any(not body.get(field) for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing required fields")
    try:
        await check_project_ownership(user, body.get("projectId"), db)
        result = await db.execute(
            text(
                """
                INSERT INTO eam.eam_actions (
                    project_id, action_title, priority, type, requested_by, requested_by_name,
                    applicable_domain, action_description, create_by, create_at
                ) VALUES (
                    :project_id, :action_title, :priority, :type, :requested_by, :requested_by_name,
                    :applicable_domain, :action_description, :create_by, NOW()
                ) RETURNING *
                """
            ),
            {
                "project_id": body.get("projectId"),
                "action_title": body.get("actionTitle"),
                "priority": body.get("priority"),
                "type": body.get("type"),
                "requested_by": body.get("requestedBy"),
                "requested_by_name": body.get("requestedByName"),
                "applicable_domain": body.get("applicableDomain"),
                "action_description": body.get("actionDescription"),
                "create_by": user.id,
            },
        )
        await db.commit()
        return _map_action(result.mappings().first() or {})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create action") from exc


@router.put("/{action_id}", dependencies=[Depends(require_permission("action", "write"))])
async def update_action(action_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Action not found")
        if row.get("project_id"):
            await check_project_ownership(user, row.get("project_id"), db)
        result = await db.execute(
            text(
                """
                UPDATE eam.eam_actions
                SET status = COALESCE(:status, status),
                    update_at = NOW()
                WHERE id = :id
                RETURNING *
                """
            ),
            {"id": action_id, "status": body.get("status")},
        )
        await db.commit()
        return _map_action(result.mappings().first() or {})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update action") from exc


@router.delete("/{action_id}", dependencies=[Depends(require_permission("action", "write"))])
async def delete_action(action_id: str, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Action not found")
        if row.get("project_id"):
            await check_project_ownership(user, row.get("project_id"), db)
        result = await db.execute(text("DELETE FROM eam.eam_actions WHERE id = :id"), {"id": action_id})
        if not getattr(result, "rowcount", 0):
            raise HTTPException(status_code=404, detail="Action not found")
        await db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete action") from exc