"""User CRUD — admin only. Manages eam.local_users table."""
from __future__ import annotations

import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_role, get_current_user, Role
from app.auth.models import AuthUser
from app.config import settings

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    email: str = ""
    role: str = "requestor"


class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    password: str


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _assert_local_mode():
    if settings.AUTH_MODE != "local":
        raise HTTPException(status_code=400, detail="User management is only available in local auth mode")


def _validate_role(role: str):
    if role not in ("admin", "reviewer", "requestor"):
        raise HTTPException(status_code=400, detail="Role must be admin, reviewer, or requestor")


@router.get("", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def list_users(
    q: str = Query("", description="Search by username or name"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _assert_local_mode()

    where = ""
    params: dict = {}
    if q.strip():
        where = "WHERE username ILIKE :q OR name ILIKE :q"
        params["q"] = f"%{q.strip()}%"

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM eam.local_users {where}"), params
    )
    total = count_result.scalar()

    offset = (page - 1) * pageSize
    result = await db.execute(
        text(
            f"SELECT id::text, username, name, email, role, is_active, "
            f"created_at, updated_at FROM eam.local_users {where} "
            f"ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": pageSize, "offset": offset},
    )
    rows = result.mappings().all()

    return {
        "data": [
            {
                "id": r["id"],
                "username": r["username"],
                "name": r["name"],
                "email": r["email"],
                "role": r["role"],
                "isActive": r["is_active"],
                "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
                "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


@router.post("", status_code=201, dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def create_user(
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()
    _validate_role(body.role)

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await db.execute(
        text("SELECT 1 FROM eam.local_users WHERE username = :un"),
        {"un": body.username},
    )
    if existing.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO eam.local_users (id, username, password_hash, name, email, role) "
            "VALUES (:id, :un, :ph, :name, :email, :role)"
        ),
        {
            "id": user_id,
            "un": body.username,
            "ph": _hash_password(body.password),
            "name": body.name or body.username,
            "email": body.email or "",
            "role": body.role,
        },
    )
    await db.commit()

    return {
        "id": user_id,
        "username": body.username,
        "name": body.name or body.username,
        "email": body.email or "",
        "role": body.role,
    }


@router.put("/{user_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()

    existing = await db.execute(
        text("SELECT id FROM eam.local_users WHERE id = :id::uuid"),
        {"id": user_id},
    )
    if not existing.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        _validate_role(body.role)

    sets = []
    params: dict = {"id": user_id}
    if body.name is not None:
        sets.append("name = :name")
        params["name"] = body.name
    if body.email is not None:
        sets.append("email = :email")
        params["email"] = body.email
    if body.role is not None:
        sets.append("role = :role")
        params["role"] = body.role
    if body.is_active is not None:
        sets.append("is_active = :is_active")
        params["is_active"] = body.is_active

    if sets:
        sets.append("updated_at = NOW()")
        await db.execute(
            text(f"UPDATE eam.local_users SET {', '.join(sets)} WHERE id = :id::uuid"),
            params,
        )
        await db.commit()

    result = await db.execute(
        text("SELECT id::text, username, name, email, role, is_active FROM eam.local_users WHERE id = :id::uuid"),
        {"id": user_id},
    )
    row = result.mappings().first()
    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "isActive": row["is_active"],
    }


@router.delete("/{user_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()

    result = await db.execute(
        text("DELETE FROM eam.local_users WHERE id = :id::uuid"),
        {"id": user_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return {"message": "deleted"}


@router.put("/{user_id}/password", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    result = await db.execute(
        text("UPDATE eam.local_users SET password_hash = :ph, updated_at = NOW() WHERE id = :id::uuid"),
        {"ph": _hash_password(body.password), "id": user_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return {"message": "password updated"}
