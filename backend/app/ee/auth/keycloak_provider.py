"""Keycloak Auth Provider — Enterprise Edition."""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from fastapi import Request

from app.auth.models import AuthUser, Role
from app.auth.rbac import build_permission_list
from app.config import settings
from app.infrastructure.auth.provider import AuthProvider

logger = logging.getLogger("eam.auth")

# ---------------------------------------------------------------------------
# Keycloak JWT — production mode
# ---------------------------------------------------------------------------

class KeycloakAuthProvider(AuthProvider):
    """Decode Keycloak JWT and extract user identity.

    Normal_User is granted to every authenticated user.
    EA_Admin and scoped business roles (EA_Reviewer, App_Owner) are
    resolved after authentication via the role_resolver module by
    querying the database.
    """

    def __init__(self, _settings=None):
        pass

    # Cache JWKS keys for 1 hour to avoid hitting Keycloak on every request
    _jwks_cache: dict[str, Any] = {}
    _jwks_cache_ts: float = 0
    _JWKS_TTL: int = 3600  # seconds

    async def authenticate(self, request: Request) -> AuthUser | None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return None

        try:
            jwks = await self._fetch_jwks()
            payload = self._decode_token(token, jwks)
        except Exception as exc:
            raise ValueError(f"Invalid token: {exc}") from exc

        username = payload.get("preferred_username", "")
        email = payload.get("email", "")
        name = payload.get("name", username)

        roles: list[Role] = [Role.NORMAL_USER]

        user = AuthUser(
            id=username,
            name=name,
            email=email,
            email_prefix=email.split("@")[0].lower() if email else "",
            roles=roles,
            permissions=build_permission_list(roles),
        )
        return user

    async def refresh_token(self, refresh_token: str) -> dict | None:
        token_url = (
            f"{settings.KEYCLOAK_SERVER_URL.rstrip('/')}"
            f"/realms/{settings.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/token"
        )
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.KEYCLOAK_CLIENT_ID,
        }
        try:
            async with httpx.AsyncClient(timeout=10, verify=False) as client:
                resp = await client.post(token_url, data=data)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("Token refresh failed: %s", exc)
            return None

    # -- helpers --

    async def _fetch_jwks(self) -> dict[str, Any]:
        now = time.monotonic()
        if self._jwks_cache and (now - self._jwks_cache_ts) < self._JWKS_TTL:
            return self._jwks_cache

        jwks_url = (
            f"{settings.KEYCLOAK_SERVER_URL.rstrip('/')}"
            f"/realms/{settings.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/certs"
        )
        logger.info("Fetching JWKS from %s", jwks_url)
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            jwks = resp.json()

        KeycloakAuthProvider._jwks_cache = jwks
        KeycloakAuthProvider._jwks_cache_ts = now
        return jwks

    def _decode_token(self, token: str, jwks: dict[str, Any]) -> dict:
        try:
            from jose import jwt as jose_jwt
        except ImportError:
            raise RuntimeError(
                "python-jose[cryptography] is required for Keycloak auth. "
                "Install it with: pip install python-jose[cryptography]"
            )

        unverified_header = jose_jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        rsa_key: dict = {}
        for key_data in jwks.get("keys", []):
            if key_data.get("kid") == kid:
                rsa_key = key_data
                break

        if not rsa_key:
            raise ValueError(f"No matching JWKS key found for kid={kid}")

        verify_aud = bool(settings.KEYCLOAK_CLIENT_ID)
        payload: dict = jose_jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.KEYCLOAK_ALGORITHMS],
            audience=settings.KEYCLOAK_CLIENT_ID if verify_aud else None,
            options={
                "verify_aud": verify_aud,
                "verify_exp": True,
                "verify_iat": True,
            },
        )
        return payload
