"""Team members management router."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

router = APIRouter()

TEAM_MEMBER_SORT_FIELDS = {"itcode", "name", "email", "worker_type", "country", "location", "primary_skill", "job_role"}


def _map_member(row) -> dict:
    return {key: row[key] if hasattr(row, "_mapping") else row[i] if isinstance(row, (tuple, list)) else None for i, key in enumerate(["itcode", "name", "email", "worker", "worker_type", "country", "location", "primary_skill", "skill_level", "job_role", "track_focal", "manager_itcode", "manager_name", "email_option", "ea_admin_status", "tier_1_org", "tier_2_org"])}


def _row_to_dict(row) -> dict:
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return row


@router.get("", dependencies=[Depends(require_permission("team_member", "read"))])
async def list_team_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    itcode: str | None = None,
    name: str | None = None,
    workerType: str | None = None,
    country: str | None = None,
    sortField: str | None = None,
    sortOrder: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    where_clauses = []
    params: dict = {}

    if itcode:
        where_clauses.append("t.itcode ILIKE :itcode")
        params["itcode"] = f"%{itcode}%"
    if name:
        where_clauses.append("t.name ILIKE :name")
        params["name"] = f"%{name}%"
    if workerType:
        where_clauses.append("t.worker_type = :worker_type")
        params["worker_type"] = workerType
    if country:
        where_clauses.append("t.country = :country")
        params["country"] = country

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sort_field = "itcode"
    if sortField and sortField in TEAM_MEMBER_SORT_FIELDS:
        sort_field = sortField
    direction = "DESC" if sortOrder and sortOrder.upper() == "DESC" else "ASC"

    count_query = text(f"SELECT COUNT(*) FROM eam.eam_bigea_team_members t {where_sql}")
    count_result = await db.execute(count_query, params)
    total = count_result.scalar()

    offset = (page - 1) * page_size
    data_query = text(f"SELECT * FROM eam.eam_bigea_team_members t {where_sql} ORDER BY t.{sort_field} {direction} LIMIT :limit OFFSET :offset")
    params["limit"] = page_size
    params["offset"] = offset
    data_result = await db.execute(data_query, params)
    rows = data_result.mappings().all()

    return paginated_response(
        [_row_to_dict(r) for r in rows],
        total,
        page,
        page_size,
    )


@router.post("", status_code=201, dependencies=[Depends(require_permission("team_member", "write"))])
async def create_team_member(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    itcode = body.get("itcode")
    if not itcode:
        raise HTTPException(status_code=400, detail="itcode is required")

    try:
        result = await db.execute(
            text("INSERT INTO eam.eam_bigea_team_members (itcode, name, email, worker, worker_type, country, location, primary_skill, skill_level, job_role, track_focal, manager_itcode, manager_name, email_option, ea_admin_status, tier_1_org, tier_2_org) VALUES (:itcode, :name, :email, :worker, :worker_type, :country, :location, :primary_skill, :skill_level, :job_role, :track_focal, :manager_itcode, :manager_name, :email_option, :ea_admin_status, :tier_1_org, :tier_2_org) RETURNING *"),
            {
                "itcode": itcode,
                "name": body.get("name", ""),
                "email": body.get("email", ""),
                "worker": body.get("worker", body.get("worker_type", "")),
                "worker_type": body.get("worker_type", ""),
                "country": body.get("country", ""),
                "location": body.get("location", ""),
                "primary_skill": body.get("primary_skill", ""),
                "skill_level": body.get("skill_level", ""),
                "job_role": body.get("job_role", ""),
                "track_focal": body.get("track_focal"),
                "manager_itcode": body.get("manager_itcode"),
                "manager_name": body.get("manager_name"),
                "email_option": body.get("email_option"),
                "ea_admin_status": body.get("ea_admin_status"),
                "tier_1_org": body.get("tier_1_org", ""),
                "tier_2_org": body.get("tier_2_org", ""),
            },
        )
        row = result.mappings().first()
        await db.commit()
        return _row_to_dict(row)
    except Exception:
        await db.rollback()
        raise


@router.put("/{itcode}", dependencies=[Depends(require_permission("team_member", "write"))])
async def update_team_member(
    itcode: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    check = await db.execute(
        text("SELECT 1 FROM eam.eam_bigea_team_members WHERE itcode = :itcode LIMIT 1"),
        {"itcode": itcode},
    )
    if check.first() is None:
        raise HTTPException(status_code=404, detail="Team member not found")

    set_parts = []
    params = {"itcode": itcode}
    for field in ["name", "email", "worker", "worker_type", "country", "location", "primary_skill", "skill_level", "job_role", "track_focal", "manager_itcode", "manager_name", "email_option", "ea_admin_status", "tier_1_org", "tier_2_org"]:
        if field in body:
            set_parts.append(f"{field} = :{field}")
            params[field] = body[field]

    try:
        if set_parts:
            await db.execute(
                text(f"UPDATE eam.eam_bigea_team_members SET {', '.join(set_parts)} WHERE itcode = :itcode"),
                params,
            )

        result = await db.execute(
            text("SELECT * FROM eam.eam_bigea_team_members WHERE itcode = :itcode"),
            {"itcode": itcode},
        )
        row = result.mappings().first()
        await db.commit()
        return _row_to_dict(row)
    except Exception:
        await db.rollback()
        raise


@router.delete("/{itcode}", dependencies=[Depends(require_permission("team_member", "write"))])
async def delete_team_member(
    itcode: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    try:
        result = await db.execute(
            text("DELETE FROM eam.eam_bigea_team_members WHERE itcode = :itcode"),
            {"itcode": itcode},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Team member not found")
        await db.commit()
        return {"detail": "deleted"}
    except Exception:
        await db.rollback()
        raise
