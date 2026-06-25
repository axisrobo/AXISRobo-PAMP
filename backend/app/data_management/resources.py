"""Resources router — resource pool list + autocomplete search."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.utils.pagination import PaginationParams, paginated_response

from app.auth import require_permission, require_role, Role, get_current_user
from app.auth.models import AuthUser
from app.infrastructure.database.repositories.data_repo import PostgresResourceRepository

router = APIRouter()

# ── Mapping helpers ──────────────────────────────────────────────

SORT_FIELD_MAP: dict[str, str] = {
    "itcode": "itcode",
    "name": "name",
    "email": "email",
    "country": "country",
    "workerType": "worker_type",
    "tier1Org": "tier_1_org",
}

ALLOWED_SORT_FIELDS = set(SORT_FIELD_MAP.values())


def _map_resource(r) -> dict:
    """Convert a DB row to the camelCase API shape."""
    m = r._mapping if hasattr(r, "_mapping") else r
    return {
        "itcode": m["itcode"],
        "name": m["name"],
        "email": m["email"],
        "worker": m["worker"],
        "workerType": m["worker_type"],
        "country": m["country"],
        "location": m["location"],
        "tier1Org": m["tier_1_org"],
        "tier2Org": m["tier_2_org"],
        "tier3Org": m["tier_3_org"],
    }


# ── GET /api/resources/search — Quick autocomplete search ────────
# NOTE: This route MUST be defined before the parameterised GET /{id}
# style routes to avoid path conflicts. In Express the /search literal
# path is checked first because it is registered first; in FastAPI
# literal paths take precedence over path params at the same level, but
# we keep it first for clarity.

@router.get("/search")
async def search_resources(
    q: str = Query(""),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user: AuthUser = Depends(get_current_user),
):
    try:
        q = q.strip()
        if q:
            result = await db.execute(
                text("""
                    SELECT itcode, name, email
                    FROM eam.resource_pool
                    WHERE itcode ILIKE :q
                       OR name   ILIKE :q
                       OR email  ILIKE :q
                    ORDER BY name ASC
                    LIMIT :limit
                """),
                {"q": f"%{q}%", "limit": limit},
            )
        else:
            result = await db.execute(
                text("""
                    SELECT itcode, name, email
                    FROM eam.resource_pool
                    ORDER BY name ASC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
        try:
            repo = PostgresResourceRepository(db)
            items = await repo.list_by_type("resource_pool")
        except Exception:
            pass
        rows = result.mappings().all()

        return [
            {
                "key": r["itcode"],
                "value": f"{r['itcode']}-{r['name']}",
                "itcode": r["itcode"],
                "name": r["name"],
                "email": r["email"],
                "label": f"{r['name']} ({r['itcode']})",
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error searching resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to search resources")


# ── GET /api/resources — Paginated list with filters ─────────────

@router.get("", dependencies=[Depends(require_permission("resource", "read"))])
async def list_resources(
    pagination: PaginationParams = Depends(),
    itcode: str | None = Query(None),
    name: str | None = Query(None),
    country: str | None = Query(None),
    tier1Org: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions: list[str] = []
        params: dict = {}

        if itcode:
            conditions.append("itcode ILIKE :itcode")
            params["itcode"] = f"%{itcode}%"
        if name:
            conditions.append("name ILIKE :name")
            params["name"] = f"%{name}%"
        if country:
            conditions.append("country ILIKE :country")
            params["country"] = f"%{country}%"
        if tier1Org:
            conditions.append("tier_1_org ILIKE :tier1Org")
            params["tier1Org"] = f"%{tier1Org}%"

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Sort
        db_sort_field = SORT_FIELD_MAP.get(pagination.sort_field, pagination.sort_field) if pagination.sort_field else "name"
        if db_sort_field not in ALLOWED_SORT_FIELDS:
            db_sort_field = "name"
        sort_order = "DESC" if pagination.sort_order and pagination.sort_order.lower() == "desc" else "ASC"

        data_query = text(
            f"SELECT * FROM eam.resource_pool WHERE {where_clause} "
            f"ORDER BY {db_sort_field} {sort_order} "
            f"LIMIT :limit OFFSET :offset"
        )
        count_query = text(
            f"SELECT COUNT(*) FROM eam.resource_pool WHERE {where_clause}"
        )

        params["limit"] = pagination.page_size
        params["offset"] = pagination.offset

        result = await db.execute(data_query, params)
        rows = result.mappings().all()

        count_result = await db.execute(count_query, {k: v for k, v in params.items() if k not in ("limit", "offset")})
        total = count_result.scalar_one()

        try:
            repo = PostgresResourceRepository(db)
            items = await repo.list_by_type("resource_pool")
        except Exception:
            pass

        return paginated_response(
            [_map_resource(r) for r in rows],
            total,
            pagination.page,
            pagination.page_size,
        )
    except Exception as e:
        print(f"Error fetching resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch resources")
