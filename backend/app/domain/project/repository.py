from abc import abstractmethod
from app.domain.base_repository import BaseRepository
from app.domain.project.entities import Project, TeamMember


class ProjectRepository(BaseRepository[Project]):
    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list[Project]: ...


class TeamMemberRepository(BaseRepository[TeamMember]):
    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[TeamMember]: ...
