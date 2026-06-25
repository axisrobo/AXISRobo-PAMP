from abc import abstractmethod
from typing import Optional
from app.domain.base_repository import BaseRepository
from app.domain.review.entities import ReviewRequest, Meeting, Action, Attachment


class ReviewRequestRepository(BaseRepository[ReviewRequest]):
    @abstractmethod
    async def list_by_submitter(self, submitter: str) -> list[ReviewRequest]: ...
    @abstractmethod
    async def list_by_reviewer(self, reviewer: str) -> list[ReviewRequest]: ...
    @abstractmethod
    async def list_by_status(self, status: str) -> list[ReviewRequest]: ...
    @abstractmethod
    async def get_dashboard_stats(self) -> dict: ...


class MeetingRepository(BaseRepository[Meeting]):
    @abstractmethod
    async def list_by_request(self, request_id: str) -> list[Meeting]: ...


class ActionRepository(BaseRepository[Action]):
    @abstractmethod
    async def list_by_request(self, request_id: str) -> list[Action]: ...
    @abstractmethod
    async def list_by_assignee(self, assignee: str) -> list[Action]: ...


class AttachmentRepository(BaseRepository[Attachment]):
    @abstractmethod
    async def list_by_request(self, request_id: str) -> list[Attachment]: ...
