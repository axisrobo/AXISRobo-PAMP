"""Authorization audit logging.

Records privileged and denied authorization decisions for auditability.
Events are written to the ``eam_audit_log`` database table (EE mode) and
logged via Python's logging module.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from app.auth.models import AuthUser
from app.database import AsyncSessionLocal

logger = logging.getLogger("eam.auth.audit")


async def _write_audit_log(
    *,
    user: AuthUser,
    action: str,
    resource_type: str,
    resource_id: str | None,
    decision: str,
    reason: str = "",
) -> None:
    """Write an audit event to the ``eam_audit_log`` table.

    Failures are silently caught so that a missing column or transient
    database issue does not affect the request.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    "INSERT INTO eam.eam_audit_log "
                    "(user_id, roles, resource, action, decision, reason) "
                    "VALUES (:user_id, :roles, :resource, :action, :decision, :reason)"
                ),
                {
                    "user_id": user.id,
                    "roles": [r.value for r in user.roles],
                    "resource": f"{resource_type}:{resource_id}" if resource_id else resource_type,
                    "action": action,
                    "decision": decision,
                    "reason": reason,
                },
            )
            await session.commit()
    except Exception:
        logger.error("Failed to write audit log entry", exc_info=True)


def audit_allow(
    *,
    user: AuthUser,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    scope_basis: str = "",
) -> None:
    """Record an allowed authorization decision."""
    from app.config import settings
    if not settings.EE_ENABLED:
        return
    logger.info(
        "AUTHZ_ALLOW user=%s roles=%s action=%s resource=%s id=%s basis=%s",
        user.id,
        [r.value for r in user.roles],
        action,
        resource_type,
        resource_id or "-",
        scope_basis or "baseline",
    )
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(
                _write_audit_log(
                    user=user,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    decision="allow",
                    reason=scope_basis or "baseline",
                )
            )
    except RuntimeError:
        pass


def audit_deny(
    *,
    user: AuthUser,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    reason: str = "",
) -> None:
    """Record a denied authorization decision."""
    from app.config import settings
    if not settings.EE_ENABLED:
        return
    logger.warning(
        "AUTHZ_DENY user=%s roles=%s action=%s resource=%s id=%s reason=%s",
        user.id,
        [r.value for r in user.roles],
        action,
        resource_type,
        resource_id or "-",
        reason,
    )
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(
                _write_audit_log(
                    user=user,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    decision="deny",
                    reason=reason,
                )
            )
    except RuntimeError:
        pass
