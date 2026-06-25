from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.project.repository import ProjectRepository, TeamMemberRepository
from app.domain.project.entities import Project, TeamMember

SEL = "id, project_id, name, description, status, owner_id, category, type, start_date, go_live_date, duration, objectives, ai_related, comment, pm, pm_itcode, dt_lead, dt_lead_itcode, it_lead, it_lead_itcode, created_at, updated_at"
INS = "INSERT INTO eam_project (id, project_id, name, description, status, owner_id, category, type, start_date, go_live_date, duration, objectives, ai_related, comment, pm, pm_itcode, dt_lead, dt_lead_itcode, it_lead, it_lead_itcode, created_at, updated_at) VALUES (:id, :pid, :name, :description, :status, :owner_id, :category, :type, :start_date, :go_live_date, :duration, :objectives, :ai_related, :comment, :pm, :pm_itcode, :dt_lead, :dt_lead_itcode, :it_lead, :it_lead_itcode, :created_at, :updated_at)"
UPD = "UPDATE eam_project SET name=:name, description=:description, status=:status, owner_id=:owner_id, category=:category, type=:type, start_date=:start_date, go_live_date=:go_live_date, duration=:duration, objectives=:objectives, ai_related=:ai_related, comment=:comment, pm=:pm, pm_itcode=:pm_itcode, dt_lead=:dt_lead, dt_lead_itcode=:dt_lead_itcode, it_lead=:it_lead, it_lead_itcode=:it_lead_itcode, updated_at=NOW() WHERE id=:id"

def _parse_date(v: str | None) -> date | None:
    if not v or not v.strip():
        return None
    try:
        return date.fromisoformat(v.strip())
    except ValueError:
        return None

def _params(entity: Project) -> dict:
    return {"id": str(entity.id), "pid": entity.project_id, "name": entity.name, "description": entity.description, "status": entity.status, "owner_id": entity.owner_id, "category": entity.category, "type": entity.type, "start_date": _parse_date(entity.start_date), "go_live_date": _parse_date(entity.go_live_date), "duration": entity.duration or None, "objectives": entity.objectives, "ai_related": entity.ai_related, "comment": entity.comment, "pm": entity.pm, "pm_itcode": entity.pm_itcode, "dt_lead": entity.dt_lead, "dt_lead_itcode": entity.dt_lead_itcode, "it_lead": entity.it_lead, "it_lead_itcode": entity.it_lead_itcode, "created_at": entity.created_at, "updated_at": entity.updated_at}


class PostgresProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Project]:
        result = await self._session.execute(text(f"SELECT {SEL} FROM eam_project WHERE id::text = :id OR project_id = :id"), {"id": id})
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Project], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_project"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(text(f"SELECT {SEL} FROM eam_project ORDER BY created_at DESC LIMIT :limit OFFSET :offset"), {"limit": page_size, "offset": offset})
        items = [self._to_entity(row) for row in result.fetchall()]
        return items, total

    async def list_by_owner(self, owner_id: str) -> list[Project]:
        result = await self._session.execute(text(f"SELECT {SEL} FROM eam_project WHERE owner_id = :owner_id ORDER BY created_at DESC"), {"owner_id": owner_id})
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Project) -> Project:
        await self._session.execute(text(INS), _params(entity))
        return entity

    async def update(self, entity: Project) -> Project:
        await self._session.execute(text(UPD), _params(entity))
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("DELETE FROM eam_project WHERE id::text = :id OR project_id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> Project:
        return Project(id=UUID(str(row[0])), project_id=str(row[1] or ""), name=str(row[2]), description=str(row[3] or ""), status=str(row[4]), owner_id=str(row[5] or ""), category=str(row[6] or "") or "regular", type=str(row[7] or ""), start_date=str(row[8] or "") if row[8] else "", go_live_date=str(row[9] or "") if row[9] else "", duration=str(row[10] or "") if row[10] else "", objectives=str(row[11] or ""), ai_related=str(row[12] or ""), comment=str(row[13] or ""), pm=str(row[14] or ""), pm_itcode=str(row[15] or ""), dt_lead=str(row[16] or ""), dt_lead_itcode=str(row[17] or ""), it_lead=str(row[18] or ""), it_lead_itcode=str(row[19] or ""), created_at=row[20], updated_at=row[21])


class PostgresTeamMemberRepository(TeamMemberRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[TeamMember]:
        result = await self._session.execute(text("SELECT id, project_id, user_itcode, role FROM eam_team_member WHERE id = :id"), {"id": id})
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[TeamMember], int]:
        offset = (page - 1) * page_size
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_team_member"))
        total = count_result.scalar()
        result = await self._session.execute(text("SELECT id, project_id, user_itcode, role FROM eam_team_member ORDER BY user_itcode LIMIT :limit OFFSET :offset"), {"limit": page_size, "offset": offset})
        return [self._to_entity(row) for row in result.fetchall()], total

    async def list_by_project(self, project_id: str) -> list[TeamMember]:
        result = await self._session.execute(text("SELECT id, project_id, user_itcode, role FROM eam_team_member WHERE project_id = :project_id"), {"project_id": project_id})
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: TeamMember) -> TeamMember:
        await self._session.execute(text("INSERT INTO eam_team_member (id, project_id, user_itcode, role) VALUES (:id, :project_id, :user_itcode, :role)"), {"id": str(entity.id), "project_id": entity.project_id, "user_itcode": entity.user_itcode, "role": entity.role})
        return entity

    async def update(self, entity: TeamMember) -> TeamMember:
        await self._session.execute(text("UPDATE eam_team_member SET role=:role WHERE id=:id"), {"id": str(entity.id), "role": entity.role})
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("DELETE FROM eam_team_member WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> TeamMember:
        return TeamMember(id=UUID(str(row[0])), project_id=str(row[1]), user_itcode=str(row[2]), role=str(row[3]))
