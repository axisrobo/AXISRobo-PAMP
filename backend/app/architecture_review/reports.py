"""Compatibility reports router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_permission
from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response


router = APIRouter()


@router.get("/lead-time", dependencies=[Depends(require_permission("report", "read"))])
async def lead_time_report(
    pagination: PaginationParams = Depends(),
    projectId: str | None = Query(None),
    status: str | None = Query(None),
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
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        data_result = await db.execute(
            text(
                f"SELECT * FROM eam.eam_architecture_review {where_clause} "
                "ORDER BY create_at DESC LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": pagination.page_size, "offset": pagination.offset},
        )
        rows = data_result.mappings().all()
        count_result = await db.execute(text(f"SELECT COUNT(*) FROM eam.eam_architecture_review {where_clause}"), params)
        mapped = []
        for row in rows:
            project_result = await db.execute(text("SELECT name as project_name FROM eam.eam_project WHERE project_id = :project_id OR id::text = :project_id"), {"project_id": row.get("project_id")})
            logs_result = await db.execute(
                text("SELECT action, create_at FROM eam.eam_process_log WHERE request_id = :request_id ORDER BY create_at ASC"),
                {"request_id": row.get("request_id")},
            )
            project = project_result.mappings().first() or {}
            logs = logs_result.mappings().all()
            submit_at = next((item.get("create_at") for item in logs if item.get("action") == "Submit"), None)
            complete_at = next((item.get("create_at") for item in logs if item.get("action") == "Completed"), None)
            mapped.append(
                {
                    "requestId": row.get("request_id"),
                    "projectId": row.get("project_id"),
                    "projectName": project.get("project_name"),
                    "status": row.get("status"),
                    "createdAt": row.get("create_at"),
                    "submittedAt": submit_at,
                    "completedAt": complete_at,
                }
            )
        return paginated_response(mapped, int(count_result.scalar() or 0), pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch lead time report") from exc