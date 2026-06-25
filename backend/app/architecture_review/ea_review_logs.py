"""Compatibility EA review logs router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_permission
from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response


router = APIRouter()

SORT_FIELDS = {
    "createdAt": "create_at",
    "operator": "operator",
    "operation": "operation",
    "projectId": "project_id",
}


@router.get("", dependencies=[Depends(require_permission("ea_review_log", "read"))])
async def list_ea_review_logs(
    pagination: PaginationParams = Depends(),
    projectId: str | None = Query(None),
    operator: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions: list[str] = []
        params: dict[str, object] = {}
        if projectId:
            conditions.append("project_id = :project_id")
            params["project_id"] = projectId
        if operator:
            conditions.append("operator ILIKE :operator")
            params["operator"] = f"%{operator}%"
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sort_field = SORT_FIELDS.get(pagination.sort_field or "", "create_at")
        sort_order = "DESC" if (pagination.sort_order or "").lower() == "desc" else "ASC"
        count_result = await db.execute(text(f"SELECT COUNT(*) FROM eam.eam_review_log {where_clause}"), params)
        data_result = await db.execute(
            text(
                f"SELECT * FROM eam.eam_review_log {where_clause} "
                f"ORDER BY {sort_field} {sort_order} LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": pagination.page_size, "offset": pagination.offset},
        )
        return paginated_response(data_result.mappings().all(), int(count_result.scalar() or 0), pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch EA review logs") from exc