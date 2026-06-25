"""FastAPI dependency injection functions for auth.

Usage in routers:
    from app.auth import require_auth, require_role, require_permission, Role

    # Any authenticated user
    @router.get("", dependencies=[Depends(require_auth)])

    # Specific role
    @router.post("", dependencies=[Depends(require_role(Role.EA_ADMIN))])

    # Resource + scope permission (feature-level gate)
    @router.put("/{id}", dependencies=[Depends(require_permission("ea_request", "write"))])
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, Request

from app.auth.models import AuthUser, Role
from app.auth.rbac import check_permission as _check_permission


# ---------------------------------------------------------------------------
# Core: get current user from request.state
# ---------------------------------------------------------------------------

import logging
logger = logging.getLogger("eam.auth.get_current_user")

async def get_current_user(request: Request) -> AuthUser:
    """Retrieve the authenticated user from request.state.

    Raises 401 if no user is present.
    """
    # Log key request information to help troubleshoot authentication issues
    safe_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("authorization", "cookie", "set-cookie", "x-api-key")
    }
    logger.debug(f" [auth] Path: {request.url.path} Method: {request.method} Headers: {safe_headers}")
    user: AuthUser | None = getattr(request.state, "user", None)
    if user is None:
        logger.warning(f" [auth] No authenticated user found for request from {request.client}")
        raise HTTPException(status_code=401, detail="Not authenticated")
    logger.debug(f" [auth] User: {getattr(user, 'id', None)} Roles: {getattr(user, 'roles', None)}")
    return user


# ---------------------------------------------------------------------------
# Convenience: require_auth (alias for get_current_user as dependency)
# ---------------------------------------------------------------------------

async def require_auth(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Dependency that simply requires authentication — any role allowed."""
    return user


# ---------------------------------------------------------------------------
# Role-based: require_role(*roles)
# ---------------------------------------------------------------------------

def require_role(*roles: Role) -> Callable:
    """Return a dependency that requires the user to have at least one of *roles*.

    Only enforced in EE mode.

    Usage:
        @router.delete("/{id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
    """

    async def _check(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        from app.config import settings
        if not settings.EE_ENABLED and settings.AUTH_MODE != "local":
            return user
        if not any(r in user.roles for r in roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient role. Required one of: {[r.value for r in roles]}, have: {[r.value for r in user.roles]}",
            )
        return user

    return _check


# ---------------------------------------------------------------------------
# Resource-based: require_permission(resource, scope)
# ---------------------------------------------------------------------------

def require_permission(resource: str, scope: str = "read") -> Callable:
    """Return a dependency that requires *scope* on *resource*.

    Full RBAC in EE mode, auth-only in OSS mode.

    Usage:
        @router.post("", dependencies=[Depends(require_permission("ea_request", "write"))])
    """

    async def _check(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        from app.config import settings
        if not settings.EE_ENABLED and settings.AUTH_MODE != "local":
            return user
        if not _check_permission(user.roles, resource, scope):
            raise HTTPException(
                status_code=403,
                detail=f"No permission: {resource}:{scope}",
            )
        return user

    return _check
