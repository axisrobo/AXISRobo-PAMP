from app.domain.project.repository import ProjectRepository, TeamMemberRepository
from app.application.project.dto import ProjectDTO, TeamMemberDTO

class ProjectService:
    def __init__(self, repo: ProjectRepository):
        self._repo = repo

    async def list_projects(self, page: int = 1, page_size: int = 20):
        return await self._repo.list(page, page_size)

    async def create_project(self, dto: ProjectDTO):
        from app.domain.project.entities import Project
        entity = Project(name=dto.name, description=dto.description, status=dto.status, owner_id=dto.owner_id,
                         project_id=_generate_project_id())
        return await self._repo.create(entity)


def _generate_project_id() -> str:
    import random
    from datetime import datetime, timezone
    year = datetime.now(timezone.utc).strftime("%Y")
    seq = random.randint(1, 9999)
    return f"{year}-{seq:04d}"

class TeamMemberService:
    def __init__(self, repo: TeamMemberRepository):
        self._repo = repo

    async def list_by_project(self, project_id: str):
        return await self._repo.list_by_project(project_id)

    async def add_member(self, dto: TeamMemberDTO):
        from app.domain.project.entities import TeamMember
        entity = TeamMember(project_id=dto.project_id, user_itcode=dto.user_itcode, role=dto.role)
        return await self._repo.create(entity)
