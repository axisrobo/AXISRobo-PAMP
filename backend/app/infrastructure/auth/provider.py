from abc import ABC, abstractmethod

from fastapi import Request

from app.auth.models import AuthUser


class AuthProvider(ABC):
    """Base class for authentication providers."""

    @abstractmethod
    async def authenticate(self, request: Request) -> AuthUser | None:
        """Extract and validate user identity from *request*.

        Returns ``AuthUser`` on success, ``None`` if no credentials are present.
        Raises ``ValueError`` with a human-readable message on invalid credentials.
        """

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict | None:
        """Exchange a refresh token for a new access token.

        Returns a dict with new token data on success, ``None`` if not supported.
        """
