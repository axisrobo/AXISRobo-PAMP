from __future__ import annotations
from typing import Any, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.review.repository import ReviewRequestRepository, MeetingRepository, ActionRepository, AttachmentRepository
from app.domain.review.entities import ReviewRequest, Meeting, Action, Attachment

class PostgresReviewRequestRepository(ReviewRequestRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def execute_rows(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = await self._session.execute(text(sql), params or {})
        return [dict(r._mapping) for r in result.fetchall()]

    async def execute_scalar(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        result = await self._session.execute(text(sql), params or {})
        return result.scalar()

    async def execute_fetchone(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        result = await self._session.execute(text(sql), params or {})
        row = result.fetchone()
        return dict(row._mapping) if row is not None else None

    async def get_by_id(self, id: str) -> Optional[ReviewRequest]:
        result = await self._session.execute(
            text("SELECT id, request_id, title, description, status, submitter, reviewer, submitted_at, reviewed_at, created_at FROM eam_request WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[ReviewRequest], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_request"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, request_id, title, description, status, submitter, reviewer, submitted_at, reviewed_at, created_at FROM eam_request ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        items = [self._to_entity(row) for row in result.fetchall()]
        return items, total

    async def list_by_submitter(self, submitter: str) -> list[ReviewRequest]:
        result = await self._session.execute(
            text("SELECT id, request_id, title, description, status, submitter, reviewer, submitted_at, reviewed_at, created_at FROM eam_request WHERE submitter = :submitter ORDER BY created_at DESC"),
            {"submitter": submitter}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_by_reviewer(self, reviewer: str) -> list[ReviewRequest]:
        result = await self._session.execute(
            text("SELECT id, request_id, title, description, status, submitter, reviewer, submitted_at, reviewed_at, created_at FROM eam_request WHERE reviewer = :reviewer ORDER BY created_at DESC"),
            {"reviewer": reviewer}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_by_status(self, status: str) -> list[ReviewRequest]:
        result = await self._session.execute(
            text("SELECT id, request_id, title, description, status, submitter, reviewer, submitted_at, reviewed_at, created_at FROM eam_request WHERE status = :status ORDER BY created_at DESC"),
            {"status": status}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def get_dashboard_stats(self) -> dict:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_request"))
        total = count_result.scalar()
        draft_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_request WHERE status = 'draft'"))
        return {"total": total, "draft": draft_result.scalar()}

    async def create(self, entity: ReviewRequest) -> ReviewRequest:
        await self._session.execute(
            text("INSERT INTO eam_request (id, request_id, title, description, status, submitter, reviewer, submitted_at, reviewed_at, created_at) VALUES (:id, :request_id, :title, :description, :status, :submitter, :reviewer, :submitted_at, :reviewed_at, :created_at)"),
            {"id": str(entity.id), "request_id": entity.request_id, "title": entity.title, "description": entity.description, "status": entity.status, "submitter": entity.submitter, "reviewer": entity.reviewer, "submitted_at": entity.submitted_at, "reviewed_at": entity.reviewed_at, "created_at": entity.created_at}
        )
        return entity

    async def update(self, entity: ReviewRequest) -> ReviewRequest:
        await self._session.execute(
            text("UPDATE eam_request SET title=:title, description=:description, status=:status, reviewer=:reviewer, reviewed_at=:reviewed_at WHERE id=:id"),
            {"id": str(entity.id), "title": entity.title, "description": entity.description, "status": entity.status, "reviewer": entity.reviewer, "reviewed_at": entity.reviewed_at}
        )
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("DELETE FROM eam_request WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> ReviewRequest:
        return ReviewRequest(id=UUID(str(row[0])), request_id=str(row[1]), title=str(row[2]), description=str(row[3] or ""), status=str(row[4]), submitter=str(row[5] or ""), reviewer=str(row[6] or ""), submitted_at=row[7], reviewed_at=row[8], created_at=row[9])

class PostgresMeetingRepository(MeetingRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def execute_rows(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = await self._session.execute(text(sql), params or {})
        return [dict(r._mapping) for r in result.fetchall()]

    async def execute_scalar(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        result = await self._session.execute(text(sql), params or {})
        return result.scalar()

    async def get_by_id(self, id: str) -> Optional[Meeting]: return None
    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Meeting], int]: return [], 0

    async def list_by_request(self, request_id: str) -> list[Meeting]:
        result = await self._session.execute(
            text("SELECT id, request_id, title, meeting_date, location, attendees, minutes, status FROM eam_meetings WHERE request_id = :request_id ORDER BY meeting_date DESC"),
            {"request_id": request_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Meeting) -> Meeting: return entity
    async def update(self, entity: Meeting) -> Meeting: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> Meeting:
        return Meeting(id=UUID(str(row[0])), request_id=str(row[1]), title=str(row[2]), meeting_date=row[3], location=str(row[4] or ""), attendees=str(row[5] or ""), minutes=str(row[6] or ""), status=str(row[7]))

class PostgresActionRepository(ActionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def execute_rows(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = await self._session.execute(text(sql), params or {})
        return [dict(r._mapping) for r in result.fetchall()]

    async def execute_scalar(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        result = await self._session.execute(text(sql), params or {})
        return result.scalar()

    async def execute_fetchone(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        result = await self._session.execute(text(sql), params or {})
        row = result.fetchone()
        return dict(row._mapping) if row is not None else None

    async def get_by_id(self, id: str) -> Optional[Action]: return None
    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Action], int]: return [], 0

    async def list_by_request(self, request_id: str) -> list[Action]:
        result = await self._session.execute(
            text("SELECT id, request_id, meeting_id, description, assignee, due_date, status FROM eam_actions WHERE request_id = :request_id ORDER BY due_date"),
            {"request_id": request_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def list_by_assignee(self, assignee: str) -> list[Action]:
        result = await self._session.execute(
            text("SELECT id, request_id, meeting_id, description, assignee, due_date, status FROM eam_actions WHERE assignee = :assignee ORDER BY due_date"),
            {"assignee": assignee}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Action) -> Action: return entity
    async def update(self, entity: Action) -> Action: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> Action:
        return Action(id=UUID(str(row[0])), request_id=str(row[1]), meeting_id=str(row[2] or ""), description=str(row[3]), assignee=str(row[4] or ""), due_date=row[5], status=str(row[6]))

class PostgresAttachmentRepository(AttachmentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Attachment]: return None
    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Attachment], int]: return [], 0

    async def list_by_request(self, request_id: str) -> list[Attachment]:
        result = await self._session.execute(
            text("SELECT id, request_id, filename, content_type, s3_key, size_bytes, uploaded_at FROM eam_request_attachment WHERE request_id = :request_id ORDER BY uploaded_at DESC"),
            {"request_id": request_id}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Attachment) -> Attachment: return entity
    async def update(self, entity: Attachment) -> Attachment: return entity
    async def delete(self, id: str) -> bool: return False

    @staticmethod
    def _to_entity(row) -> Attachment:
        return Attachment(id=UUID(str(row[0])), request_id=str(row[1]), filename=str(row[2]), content_type=str(row[3] or "application/octet-stream"), s3_key=str(row[4] or ""), size_bytes=int(row[5] or 0), uploaded_at=row[6])
