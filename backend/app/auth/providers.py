"""Authentication providers — Dev mode.

Role resolution:
    EA_Admin      — resolved from eam_bigea_team_members.ea_admin_status (via role_resolver)
    Normal_User   — every authenticated user (automatic)
    EA_Reviewer   — resolved from eam_bigea_team_members (via role_resolver)
    App_Owner     — resolved from cmdb_application / application_member (via role_resolver)
"""
from __future__ import annotations

import logging

from datetime import datetime, timedelta, timezone

from fastapi import Request

import bcrypt
import jwt
from sqlalchemy import text

from app.auth.models import AuthUser, Role
from app.auth.rbac import build_permission_list
from app.config import settings
from app.infrastructure.auth.provider import AuthProvider

logger = logging.getLogger("eam.auth")


def _email_prefix(email: str) -> str:
    """Extract the part before '@' from an email address, lowered."""
    return email.split("@")[0].lower() if email else ""


# ---------------------------------------------------------------------------
# Dev mode — no real token validation
# ---------------------------------------------------------------------------

class DevAuthProvider(AuthProvider):
    """Return a fixed dev user — used when AUTH_DISABLED=True.

    NOTE: In dev mode, EA_Admin is granted directly based on AUTH_DEV_ROLE
    without querying the database.  In production, EA_Admin is resolved
    from eam_bigea_team_members.ea_admin_status by the role_resolver.
    """

    def __init__(self, _settings=None):
        pass

    async def authenticate(self, request: Request) -> AuthUser | None:
        dev_role = settings.AUTH_DEV_ROLE.lower()
        roles: list[Role] = [Role.NORMAL_USER]

        if dev_role in ("admin", "ea_admin"):
            roles = [Role.EA_ADMIN, Role.NORMAL_USER]
        elif dev_role == "ea_reviewer":
            roles.append(Role.EA_REVIEWER)
        elif dev_role == "app_owner":
            roles.append(Role.APP_OWNER)

        email = f"{settings.AUTH_DEV_USER}@dev.local"
        return AuthUser(
            id=settings.AUTH_DEV_USER,
            name=settings.AUTH_DEV_USER,
            email=email,
            email_prefix=_email_prefix(email),
            roles=roles,
            permissions=build_permission_list(roles),
        )

    async def refresh_token(self, refresh_token: str) -> dict | None:
        return None


# ---------------------------------------------------------------------------
# Local auth — JWT tokens + bcrypt password verification
# ---------------------------------------------------------------------------

class LocalAuthProvider(AuthProvider):
    def __init__(self, _settings=None):
        pass

    def _create_token(self, user_id: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def authenticate(self, request: Request) -> AuthUser | None:
        from app.database import AsyncSessionLocal

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

        username = payload.get("sub")
        if not username:
            return None

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT username, name, email, role FROM eam.local_users "
                    "WHERE username = :un AND is_active = TRUE"
                ),
                {"un": username},
            )
            row = result.mappings().first()

        if not row:
            return None

        role_value = row["role"]
        if role_value == "admin":
            roles = [Role.EA_ADMIN, Role.NORMAL_USER]
        elif role_value == "reviewer":
            roles = [Role.NORMAL_USER, Role.EA_REVIEWER]
        else:
            roles = [Role.NORMAL_USER]

        return AuthUser(
            id=row["username"],
            name=row["name"] or row["username"],
            email=row["email"] or f"{row['username']}@local",
            email_prefix=row["username"].lower(),
            roles=roles,
            permissions=build_permission_list(roles),
        )

    async def refresh_token(self, refresh_token: str) -> dict | None:
        return None

    @staticmethod
    async def login(username: str, password: str) -> tuple[str, AuthUser] | None:
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT username, password_hash, name, email, role "
                    "FROM eam.local_users "
                    "WHERE username = :un AND is_active = TRUE"
                ),
                {"un": username},
            )
            row = result.mappings().first()

        if not row:
            return None

        if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            return None

        provider = LocalAuthProvider()
        token = provider._create_token(username, row["role"])

        role_value = row["role"]
        if role_value == "admin":
            roles = [Role.EA_ADMIN, Role.NORMAL_USER]
        elif role_value == "reviewer":
            roles = [Role.NORMAL_USER, Role.EA_REVIEWER]
        else:
            roles = [Role.NORMAL_USER]

        user = AuthUser(
            id=row["username"],
            name=row["name"] or row["username"],
            email=row["email"] or f"{row['username']}@local",
            email_prefix=row["username"].lower(),
            roles=roles,
            permissions=build_permission_list(roles),
        )
        return token, user


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_auth_provider() -> AuthProvider:
    """Return the configured auth provider based on AUTH_MODE setting."""
    if settings.AUTH_MODE == "dev" or settings.AUTH_DISABLED:
        return DevAuthProvider()
    if settings.AUTH_MODE == "local":
        return LocalAuthProvider()
    if settings.AUTH_MODE == "oidc":
        from app.ee.auth.keycloak_provider import KeycloakAuthProvider
        return KeycloakAuthProvider()
    logger.warning("Unknown AUTH_MODE=%s, falling back to DevAuthProvider", settings.AUTH_MODE)
    return DevAuthProvider()
