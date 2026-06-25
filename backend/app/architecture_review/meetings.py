"""Compatibility meetings router."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_permission
from app.auth.models import AuthUser
from app.auth.ownership import check_project_ownership
from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response
from app.infrastructure.database.repositories.review_repo import PostgresMeetingRepository


router = APIRouter()


def _map_meeting(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "meetingNo": row.get("meeting_no"),
        "meetingTitle": row.get("meeting_title"),
        "projectId": row.get("project_id"),
        "projectName": row.get("project_name"),
        "requestId": row.get("request_id"),
        "startTime": row.get("start_time"),
        "endTime": row.get("end_time"),
        "location": row.get("location"),
        "presenter": row.get("presenter"),
        "attendees": row.get("attendees"),
        "eaReviewResult": row.get("ea_review_result"),
        "status": row.get("status"),
        "meetingMinuteHtml": row.get("meeting_minute_html"),
        "meetingMinuteSentAt": row.get("meeting_minute_sent_at"),
    }


@router.get("", dependencies=[Depends(require_permission("meeting", "read"))])
async def list_meetings(
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
        repo = PostgresMeetingRepository(db)
        data_sql = (
            f"SELECT * FROM eam.eam_meeting {where_clause} "
            "ORDER BY start_time DESC LIMIT :limit OFFSET :offset"
        )
        count_sql = f"SELECT COUNT(*) FROM eam.eam_meeting {where_clause}"
        data_params = {**params, "limit": pagination.page_size, "offset": pagination.offset}
        rows = await repo.execute_rows(data_sql, data_params)
        total = await repo.execute_scalar(count_sql, params) or 0
        return paginated_response([_map_meeting(row) for row in rows], int(total), pagination.page, pagination.page_size)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch meetings") from exc


@router.get("/attendees-template", dependencies=[Depends(require_permission("meeting", "read"))])
async def attendees_template():
    buffer = io.BytesIO(b"name,email\n")
    return StreamingResponse(buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=attendees-template.csv"})


@router.post("/parse-attendees", dependencies=[Depends(require_permission("meeting", "write"))])
async def parse_attendees(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid CSV encoding") from exc
    reader = csv.DictReader(io.StringIO(text_content))
    return {"data": [row for row in reader]}


@router.get("/{meeting_no}", dependencies=[Depends(require_permission("meeting", "read"))])
async def get_meeting(meeting_no: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return _map_meeting(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch meeting") from exc


@router.post("", status_code=201, dependencies=[Depends(require_permission("meeting", "write"))])
async def create_meeting(body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        await check_project_ownership(user, body.get("projectId"), db)
        result = await db.execute(
            text(
                """
                INSERT INTO eam.eam_meeting (project_id, meeting_title, start_time, end_time, create_by, create_at)
                VALUES (:project_id, :meeting_title, :start_time, :end_time, :create_by, NOW())
                RETURNING *
                """
            ),
            {
                "project_id": body.get("projectId"),
                "meeting_title": body.get("title"),
                "start_time": body.get("startTime"),
                "end_time": body.get("endTime"),
                "create_by": user.id,
            },
        )
        await db.commit()
        return _map_meeting(result.mappings().first() or {})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create meeting") from exc


@router.put("/{meeting_no}", dependencies=[Depends(require_permission("meeting", "write"))])
async def update_meeting(meeting_no: str, body: dict, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Meeting not found")
        result = await db.execute(
            text(
                "UPDATE eam.eam_meeting SET meeting_title = COALESCE(:meeting_title, meeting_title), update_at = NOW() "
                "WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no RETURNING *"
            ),
            {"meeting_no": meeting_no, "meeting_title": body.get("title")},
        )
        await db.commit()
        return _map_meeting(result.mappings().first() or {})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update meeting") from exc


@router.patch("/{meeting_no}/cancel", dependencies=[Depends(require_permission("meeting", "write"))])
async def cancel_meeting(meeting_no: str, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Meeting not found")
        result = await db.execute(
            text(
                "UPDATE eam.eam_meeting SET status = 'Cancelled', cancelled_at = NOW() "
                "WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no RETURNING *"
            ),
            {"meeting_no": meeting_no},
        )
        await db.commit()
        return _map_meeting(result.mappings().first() or {})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel meeting") from exc


@router.post("/{meeting_no}/set-ea-review-result", dependencies=[Depends(require_permission("meeting", "write"))])
async def set_ea_review_result(meeting_no: str, body: dict, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Meeting not found")
        result = await db.execute(
            text(
                "UPDATE eam.eam_meeting SET ea_review_result = :result, update_at = NOW() "
                "WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no RETURNING *"
            ),
            {"meeting_no": meeting_no, "result": body.get("eaReviewResult")},
        )
        await db.commit()
        return _map_meeting(result.mappings().first() or {})
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to set EA review result") from exc


@router.post("/{meeting_no}/send-minute", dependencies=[Depends(require_permission("meeting", "write"))])
async def send_meeting_minute(meeting_no: str, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if not row.get("meeting_minute_html"):
            raise HTTPException(status_code=400, detail="Meeting minute is empty")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to send meeting minute") from exc


@router.delete("/{meeting_no}", dependencies=[Depends(require_permission("meeting", "write"))])
async def delete_meeting(meeting_no: str, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(text("SELECT * FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Meeting not found")
        result = await db.execute(text("DELETE FROM eam.eam_meeting WHERE meeting_no = :meeting_no OR CAST(id AS text) = :meeting_no"), {"meeting_no": meeting_no})
        if not getattr(result, "rowcount", 0):
            raise HTTPException(status_code=404, detail="Meeting not found")
        await db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete meeting") from exc


@router.get("/{meeting_no}/decks", dependencies=[Depends(require_permission("meeting_deck", "read"))])
async def list_meeting_decks(meeting_no: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM eam.eam_meeting_deck WHERE meeting_id = :meeting_id OR CAST(meeting_id AS text) = :meeting_id"), {"meeting_id": meeting_no})
        return {"data": result.mappings().all()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch meeting decks") from exc


@router.post("/{meeting_no}/decks", status_code=201, dependencies=[Depends(require_permission("meeting_deck", "write"))])
async def create_meeting_deck(meeting_no: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        result = await db.execute(
            text(
                "INSERT INTO eam.eam_meeting_deck (deck_id, meeting_id, deck_name, created_by, created_at) "
                "VALUES (gen_random_uuid(), :meeting_id, :deck_name, :created_by, NOW()) RETURNING *"
            ),
            {"meeting_id": meeting_no, "deck_name": body.get("deckName"), "created_by": user.id},
        )
        await db.commit()
        return dict(result.mappings().first() or {})
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create meeting deck") from exc


@router.delete("/{meeting_no}/decks/{deck_id}", dependencies=[Depends(require_permission("meeting_deck", "write"))])
async def delete_meeting_deck(meeting_no: str, deck_id: str, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(
            text("SELECT * FROM eam.eam_meeting_deck WHERE (meeting_id = :meeting_id OR CAST(meeting_id AS text) = :meeting_id) AND deck_id = :deck_id"),
            {"meeting_id": meeting_no, "deck_id": deck_id},
        )
        if not existing.mappings().first():
            raise HTTPException(status_code=404, detail="Meeting deck not found")
        result = await db.execute(
            text("DELETE FROM eam.eam_meeting_deck WHERE (meeting_id = :meeting_id OR CAST(meeting_id AS text) = :meeting_id) AND deck_id = :deck_id"),
            {"meeting_id": meeting_no, "deck_id": deck_id},
        )
        if not getattr(result, "rowcount", 0):
            raise HTTPException(status_code=404, detail="Meeting deck not found")
        await db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete meeting deck") from exc