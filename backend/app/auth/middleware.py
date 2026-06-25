"""FastAPI authentication middleware.

Pipeline:
    1. Skip public paths (health, docs)
    2. Authenticate via Keycloak (or dev provider) — establishes user identity
    3. Resolve all database-sourced roles (EA_Admin, EA_Reviewer, App_Owner, Project_Owner)
    4. Store AuthUser on request.state.user
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.auth.providers import get_auth_provider
from app.auth.role_resolver import resolve_scoped_roles
from app.database import AsyncSessionLocal
from app.utils.response_envelope import envelope_response

logger = logging.getLogger("eam.auth")

# Paths that never require authentication
PUBLIC_PATHS: set[str] = {
    "/api/health",
    "/api/health/check",
    "/api/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Path prefixes that never require authentication
PUBLIC_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
)


def _is_public(path: str) -> bool:
    """Return True if the request path is on the public whitelist."""
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


class AuthMiddleware(BaseHTTPMiddleware):
    """Extract user identity from request and inject into request.state.user.

    After authentication, resolves database-sourced roles (EA_Admin,
    EA_Reviewer, App_Owner, Project_Owner) by querying the database.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Always set user to None initially
        request.state.user = None

        # Skip auth for public paths
        if _is_public(request.url.path):
            return await call_next(request)

        provider = get_auth_provider()
        try:
            user = await provider.authenticate(request)

            # Resolve database-sourced roles (EA_Admin, EA_Reviewer, App_Owner, etc.)
            if user is not None:
                try:
                    async with AsyncSessionLocal() as db:
                        user = await resolve_scoped_roles(user, db)
                except Exception as exc:
                    # Role resolution failure should not block the request —
                    # the user still has baseline roles.
                    logger.warning(
                        "Role resolution failed for %s: %s",
                        user.id, exc,
                    )

            request.state.user = user
        except ValueError as exc:
            # Invalid token
            logger.warning("Auth failed for %s %s: %s", request.method, request.url.path, exc)
            return envelope_response(status_code=401, message=str(exc), data=None)
        except Exception as exc:
            logger.error("Unexpected auth error: %s", exc, exc_info=True)
            return envelope_response(status_code=500, message="Authentication error", data=None)

        return await call_next(request)
