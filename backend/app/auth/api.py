"""Auth router — user info & permissions API.

Endpoints:
    GET /api/auth/me          — current user info + role + permissions
    GET /api/auth/permissions — flat permission list for frontend UI gating
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.models import AuthUser

router = APIRouter()


@router.get("/me")
async def auth_me(user: AuthUser = Depends(get_current_user)):
    """Return the current authenticated user's profile and permissions.

    Returns ``roles`` (list) for the new multi-role model and ``role``
    (string, highest-precedence role) for backward compatibility with
    the frontend until it is fully migrated.
    """
    # Highest-precedence role for backward compat: admin > scoped > normal
    primary_role = user.roles[0].value if user.roles else "normal_user"
    for r in user.roles:
        if r.value == "ea_admin":
            primary_role = r.value
            break

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "roles": [r.value for r in user.roles],
        "role": primary_role,  # backward compat
        "permissions": user.permissions,
    }


@router.get("/permissions")
async def auth_permissions(user: AuthUser = Depends(get_current_user)):
    """Return the flat permission list for the current user.

    Used by the frontend PermissionGate component to show/hide UI elements.
    Response shape: { "roles": [...], "role": "...", "permissions": [...] }
    """
    primary_role = user.roles[0].value if user.roles else "normal_user"
    for r in user.roles:
        if r.value == "ea_admin":
            primary_role = r.value
            break

    return {
        "roles": [r.value for r in user.roles],
        "role": primary_role,  # backward compat
        "permissions": user.permissions,
    }


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def auth_login(body: LoginRequest):
    """Authenticate with local username/password. Returns a JWT access token."""
    from app.config import settings
    if settings.AUTH_MODE != "local":
        raise HTTPException(status_code=400, detail="Login is only available in local auth mode")

    from app.auth.providers import LocalAuthProvider
    result = await LocalAuthProvider.login(body.username, body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token, user = result
    primary_role = "ea_admin" if user.is_admin else (
        "ea_reviewer" if user.is_reviewer else "normal_user"
    )
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.id,
            "name": user.name,
            "email": user.email,
            "role": primary_role,
            "roles": [r.value for r in user.roles],
            "permissions": user.permissions,
        },
    }
