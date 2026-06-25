from __future__ import annotations
from typing import Any

from app.domain.review.repository import ReviewRequestRepository
from app.application.review.dto import ReviewRequestDTO


class ReviewService:
    def __init__(self, repo: ReviewRequestRepository):
        self._repo = repo

    async def list_requests(self, page: int = 1, page_size: int = 20):
        return await self._repo.list(page, page_size)

    async def list_query(self, data_sql: str, params: dict[str, Any], count_sql: str) -> tuple[list[dict[str, Any]], int]:
        rows = await self._repo.execute_rows(data_sql, params)
        total = await self._repo.execute_scalar(count_sql, params) or 0
        return rows, int(total)

    async def execute_rows(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return await self._repo.execute_rows(sql, params)

    async def get_dashboard_stats(self):
        return await self._repo.get_dashboard_stats()

    async def create_request(self, dto: ReviewRequestDTO):
        from app.domain.review.entities import ReviewRequest
        entity = ReviewRequest(request_id=dto.request_id, title=dto.title, description=dto.description, submitter=dto.submitter, reviewer=dto.reviewer)
        return await self._repo.create(entity)
