"""Projects router — CRUD with pagination, filtering, sorting."""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response

from app.auth import require_permission, require_role, Role, get_current_user
from app.auth.models import AuthUser
from app.auth.ownership import check_project_ownership
from app.auth.audit import audit_allow, audit_deny

from app.infrastructure.database.repositories.project_repo import PostgresProjectRepository, PostgresTeamMemberRepository
from app.application.project.services import ProjectService, TeamMemberService
from app.application.project.dto import ProjectDTO, TeamMemberDTO

router = APIRouter()


@router.get("", dependencies=[Depends(require_permission("project", "read"))])
async def list_projects(
    pagination: PaginationParams = Depends(),
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        repo = PostgresProjectRepository(db)
        service = ProjectService(repo)
        items, total = await service.list_projects(pagination.page, pagination.page_size)

        def _entity_to_dict(entity) -> dict:
            return {
                "id": str(entity.id),
                "projectId": entity.project_id,
                "category": entity.category,
                "name": entity.name, "projectName": entity.name,
                "type": entity.type,
                "startDate": entity.start_date, "goLiveDate": entity.go_live_date,
                "duration": entity.duration, "objectives": entity.objectives,
                "description": entity.description, "status": entity.status,
                "ownerId": entity.owner_id, "aiRelated": entity.ai_related,
                "comment": entity.comment,
                "pm": entity.pm, "pmName": entity.pm, "pmItcode": entity.pm_itcode,
                "dtLead": entity.dt_lead, "dtLeadName": entity.dt_lead, "dtLeadItcode": entity.dt_lead_itcode,
                "itLead": entity.it_lead, "itLeadName": entity.it_lead, "itLeadItcode": entity.it_lead_itcode,
                "createdAt": entity.created_at.isoformat() if entity.created_at else None,
                "updatedAt": entity.updated_at.isoformat() if entity.updated_at else None,
            }

        return paginated_response([_entity_to_dict(e) for e in items], total, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")


@router.get("/{project_id}", dependencies=[Depends(require_permission("project", "read"))])
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    try:
        repo = PostgresProjectRepository(db)
        entity = await repo.get_by_id(project_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "id": str(entity.id), "projectId": entity.project_id, "category": entity.category,
            "name": entity.name, "projectName": entity.name,
            "type": entity.type, "startDate": entity.start_date, "goLiveDate": entity.go_live_date,
            "duration": entity.duration, "objectives": entity.objectives, "description": entity.description,
            "status": entity.status, "ownerId": entity.owner_id, "aiRelated": entity.ai_related,
            "comment": entity.comment,
            "pm": entity.pm, "pmName": entity.pm, "pmItcode": entity.pm_itcode,
            "dtLead": entity.dt_lead, "dtLeadName": entity.dt_lead, "dtLeadItcode": entity.dt_lead_itcode,
            "itLead": entity.it_lead, "itLeadName": entity.it_lead, "itLeadItcode": entity.it_lead_itcode,
            "createdAt": entity.created_at.isoformat() if entity.created_at else None,
            "updatedAt": entity.updated_at.isoformat() if entity.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching project: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")


@router.post("", status_code=201, dependencies=[Depends(require_permission("project", "write"))])
async def create_project(body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        repo = PostgresProjectRepository(db)
        service = ProjectService(repo)
        dto = ProjectDTO(
            name=body.get("projectName") or "",
            description=body.get("objectives") or "",
            status=body.get("status") or "Active",
            owner_id=body.get("ownerId") or user.id,
            category=body.get("category") or "regular",
            type=body.get("type") or "",
            start_date=body.get("startDate") or "",
            go_live_date=body.get("goLiveDate") or "",
            duration=body.get("duration") or "",
            objectives=body.get("objectives") or "",
            ai_related=body.get("aiRelated") or "",
            comment=body.get("comment") or "",
            pm=body.get("pm") or "", pm_itcode=body.get("pmItcode") or "",
            dt_lead=body.get("dtLead") or "", dt_lead_itcode=body.get("dtLeadItcode") or "",
            it_lead=body.get("itLead") or "", it_lead_itcode=body.get("itLeadItcode") or "",
        )
        result = await service.create_project(dto)
        await db.commit()
        audit_allow(user=user, action="create", resource_type="project", resource_id=str(result.id))
        return {
            "id": str(result.id), "projectId": result.project_id, "category": result.category,
            "name": result.name, "projectName": result.name,
            "type": result.type, "startDate": result.start_date, "goLiveDate": result.go_live_date,
            "duration": result.duration, "objectives": result.objectives, "description": result.description,
            "status": result.status, "ownerId": result.owner_id, "aiRelated": result.ai_related,
            "comment": result.comment,
            "pm": result.pm, "pmName": result.pm, "pmItcode": result.pm_itcode,
            "dtLead": result.dt_lead, "dtLeadName": result.dt_lead, "dtLeadItcode": result.dt_lead_itcode,
            "itLead": result.it_lead, "itLeadName": result.it_lead, "itLeadItcode": result.it_lead_itcode,
            "createdAt": result.created_at.isoformat() if result.created_at else None,
            "updatedAt": result.updated_at.isoformat() if result.updated_at else None,
        }
    except Exception as e:
        await db.rollback()
        print(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.put("/{project_id}", dependencies=[Depends(require_permission("project", "write"))])
async def update_project(project_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        project_data = await check_project_ownership(user, project_id, db)
        db_id = project_data["id"]

        repo = PostgresProjectRepository(db)
        entity = await repo.get_by_id(str(db_id))
        if not entity:
            raise HTTPException(status_code=404, detail="Project not found")
        entity.name = body.get("projectName") or entity.name
        entity.description = body.get("objectives") or entity.description
        entity.status = body.get("status") or entity.status
        entity.category = body.get("category") or entity.category
        entity.type = body.get("type") or entity.type
        entity.start_date = body.get("startDate") or entity.start_date
        entity.go_live_date = body.get("goLiveDate") or entity.go_live_date
        entity.duration = body.get("duration") or entity.duration
        entity.objectives = body.get("objectives") or entity.objectives
        entity.ai_related = body.get("aiRelated") or entity.ai_related
        entity.comment = body.get("comment") or entity.comment
        entity.pm = body.get("pm") or entity.pm
        entity.pm_itcode = body.get("pmItcode") or entity.pm_itcode
        entity.dt_lead = body.get("dtLead") or entity.dt_lead
        entity.dt_lead_itcode = body.get("dtLeadItcode") or entity.dt_lead_itcode
        entity.it_lead = body.get("itLead") or entity.it_lead
        entity.it_lead_itcode = body.get("itLeadItcode") or entity.it_lead_itcode
        await repo.update(entity)
        await db.commit()
        audit_allow(user=user, action="update", resource_type="project", resource_id=project_id)
        return {
            "id": str(entity.id), "projectId": entity.project_id, "category": entity.category,
            "name": entity.name, "projectName": entity.name,
            "type": entity.type, "startDate": entity.start_date, "goLiveDate": entity.go_live_date,
            "duration": entity.duration, "objectives": entity.objectives, "description": entity.description,
            "status": entity.status, "ownerId": entity.owner_id, "aiRelated": entity.ai_related,
            "comment": entity.comment,
            "pm": entity.pm, "pmName": entity.pm, "pmItcode": entity.pm_itcode,
            "dtLead": entity.dt_lead, "dtLeadName": entity.dt_lead, "dtLeadItcode": entity.dt_lead_itcode,
            "itLead": entity.it_lead, "itLeadName": entity.it_lead, "itLeadItcode": entity.it_lead_itcode,
            "createdAt": entity.created_at.isoformat() if entity.created_at else None,
            "updatedAt": entity.updated_at.isoformat() if entity.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/{project_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        project_data = await check_project_ownership(user, project_id, db)
        repo = PostgresProjectRepository(db)
        await repo.delete(str(project_data["id"]))
        await db.commit()
        return JSONResponse(status_code=200, content={"message": f"Project {project_id} deleted successfully"})
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


# ── Application linking ───────────────────────────────────────────────

@router.post("/{project_id}/applications", status_code=201, dependencies=[Depends(require_permission("project", "write"))])
async def add_project_application(project_id: str, body: dict, db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user)):
    try:
        app_id = (body.get("appId") or "").strip()
        if not app_id:
            raise HTTPException(status_code=400, detail="appId is required")
        result = await db.execute(text("INSERT INTO eam.project_app (project_id, app_id, create_by, create_at) VALUES (:pid, :aid, :cb, NOW()) RETURNING *"), {"pid": project_id, "aid": app_id, "cb": user.id})
        await db.commit()
        return {"projectId": project_id, "appId": app_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/applications", dependencies=[Depends(require_permission("project", "read"))])
async def list_project_applications(project_id: str, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(text("SELECT * FROM eam.project_app WHERE project_id = :pid ORDER BY create_at DESC"), {"pid": project_id})
    return [dict(r) for r in rows.mappings().all()]


@router.get("/{project_id}/tasks", dependencies=[Depends(require_permission("project", "read"))])
async def list_project_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(text("SELECT * FROM eam.project_task WHERE project_id = :pid ORDER BY create_at DESC"), {"pid": project_id})
    return [dict(r) for r in rows.mappings().all()]


@router.delete("/{project_id}/applications/{app_id}", dependencies=[Depends(require_permission("project", "write"))])
async def delete_project_application(project_id: str, app_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM eam.project_app WHERE project_id = :pid AND app_id = :aid"), {"pid": project_id, "aid": app_id})
    await db.commit()
    return {"message": "deleted"}
