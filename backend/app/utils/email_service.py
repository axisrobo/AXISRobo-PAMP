"""Email notification service — sends emails via BCT Message API.

Flow:
  1. Obtain a short-lived access token from BCT OIDC:
       POST {BCT_TOKEN_URL}/{BCT_APP_CODE}
       Header: sdk-private-key: <BCT_SDK_KEY>
  2. Send email via BCT Message Service:
       POST {BCT_MS_URL}/bct-message/api/v1.0/email/send
       Headers: sdk-access-token: <token>, sdk-app-code: <BCT_APP_CODE>
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("eam.email_service")

# ---------------------------------------------------------------------------
# Token cache — avoid fetching a new token for every email
# ---------------------------------------------------------------------------
_cached_token: str | None = None
_token_expires_at: float = 0.0  # Unix timestamp
_TOKEN_REFRESH_BUFFER = 60  # seconds before expiry to proactively refresh


def _parse_token_expiry(token: str) -> float:
    """Return the token's 'exp' claim as a Unix timestamp, or 0 on failure."""
    try:
        import base64 as _b64

        parts = token.split(".")
        if len(parts) != 3:
            return 0.0
        # Add padding so base64 doesn't complain
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(_b64.urlsafe_b64decode(padded))
        return float(payload.get("exp", 0))
    except Exception:
        return 0.0


async def _get_access_token() -> str:
    """Return a valid BCT access token, refreshing if necessary."""
    global _cached_token, _token_expires_at

    now = time.time()
    if _cached_token and _token_expires_at > now + _TOKEN_REFRESH_BUFFER:
        return _cached_token

    if not settings.BCT_SDK_KEY:
        raise RuntimeError("BCT_SDK_KEY is not configured")

    token_url = f"{settings.BCT_TOKEN_URL.rstrip('/')}/{settings.BCT_APP_CODE}"
    logger.debug("Fetching BCT access token from %s", token_url)

    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        resp = await client.post(
            token_url,
            headers={
                "Content-Type": "application/json",
                "sdk-private-key": settings.BCT_SDK_KEY,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Response shape: {"success": true, "data": {"token": "...", "expiration": "..."}, ...}
    # Also handle flat {"accessToken": "..."} or {"token": "..."} shapes.
    nested = data.get("data") or {}
    token: str = (
        nested.get("token")
        or nested.get("accessToken")
        or data.get("accessToken")
        or data.get("token")
        or ""
    )
    if not token:
        raise RuntimeError(f"No access token in BCT OIDC response: {data}")

    expiry = _parse_token_expiry(token)
    _cached_token = token
    _token_expires_at = expiry if expiry else now + 3600  # default 1 h if no exp claim
    logger.info("BCT access token refreshed (expires at %.0f)", _token_expires_at)
    return token


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_email(
    *,
    to: str,
    subject: str,
    payload: dict[str, Any],
    template_code: str,
    template_tag: str,
    cc: str | None = None,
    app_id: str | None = None,
) -> dict[str, Any]:
    """Send an email via the BCT Message API.

    Args:
        to: Semicolon-separated recipient emails
        subject: Email subject
        payload: Template payload data (will be JSON-serialised)
        template_code: Email template code
        template_tag: Email template tag
        cc: Optional semicolon-separated CC emails
        app_id: Application identifier (defaults to BCT_APP_CODE)

    Returns:
        API response data or error dict
    """
    if not settings.BCT_SDK_KEY:
        logger.warning("BCT_SDK_KEY not configured, skipping email send")
        return {"status": "skipped", "message": "BCT email service not configured"}

    effective_app_id = app_id or settings.BCT_APP_CODE

    body: dict[str, Any] = {
        "to": to,
        "payload": json.dumps(payload),
        "subject": subject,
        "appId": effective_app_id,
        "templateCode": template_code,
        "templateTag": template_tag,
    }
    if cc:
        body["cc"] = cc

    email_url = f"{settings.BCT_MS_URL.rstrip('/')}/bct-message/api/v1.0/email/send"

    try:
        access_token = await _get_access_token()

        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            response = await client.post(
                email_url,
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "sdk-access-token": access_token,
                    "sdk-app-code": effective_app_id,
                },
            )
            response.raise_for_status()
            logger.info("Email sent successfully: subject=%r to=%s", subject, to)
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            "Email API returned error %s: %s", e.response.status_code, e.response.text
        )
        return {"status": "error", "message": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return {"status": "error", "message": str(e)}


from app.infrastructure.email.provider import EmailProvider
from app.infrastructure.email.smtp_provider import SMTPEmailProvider


def create_email_provider() -> EmailProvider:
    if settings.EMAIL_SERVICE_URL:
        return SMTPEmailProvider()  # placeholder for BCT/enterprise provider
    return SMTPEmailProvider()
