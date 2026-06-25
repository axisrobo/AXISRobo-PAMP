"""Record-level ownership and assignment checks.

These helpers are used by router endpoints to enforce record-scoped
authorization *after* the feature-level permission gate has passed.

Four categories of checks:
    1. Request ownership  — is the user the requester of this EA request?
    2. Reviewer assignment — is the user assigned as reviewer on this request?
    3. Application ownership — does the user own the application for BCM/lifecycle?
    4. Project ownership  — is the user the PM, DT Lead, or IT Lead of this project?
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser, Role

logger = logging.getLogger("eam.auth.ownership")


# ---------------------------------------------------------------------------
# 1. EA Review Request — requester ownership
# ---------------------------------------------------------------------------

async def check_request_owner(
    user: AuthUser,
    request_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Fetch an EA request by its business key and verify the user is the requester.

    *request_id* is the business key (e.g. "EA250001"), not the UUID PK.

    Request_Owner is determined by the ``requester`` field on the request,
    NOT the ``create_by`` field.

    Returns the request row as a dict on success.
    Raises 404 if the request doesn't exist.
    Raises 403 if the user is not the requester (and not EA_Admin).
    """
    result = await db.execute(
        text("SELECT * FROM eam.eam_request WHERE request_id = :rid"),
        {"rid": request_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="EA request not found")

    request_data = dict(row)

    from app.config import settings
    if not settings.EE_ENABLED:
        return request_data

    # EA_Admin bypasses ownership checks
    if user.is_admin:
        return request_data

    # Requester check (Request_Owner concept)
    if request_data.get("requester") != user.id:
        logger.warning(
            "Authz denied: user=%s tried to modify request=%s owned by requester=%s",
            user.id, request_id, request_data.get("requester"),
        )
        raise HTTPException(
            status_code=403,
            detail="You can only modify EA Review Requests where you are the requester",
        )

    return request_data


# Backwards-compatible alias
check_request_creator = check_request_owner


async def check_request_draft_status(
    request_data: dict[str, Any],
    operation: str = "submit",
) -> None:
    """Verify that the EA request is in draft status.

    Raises 403 if the request is not in draft status.
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return

    status = (request_data.get("status") or "").strip()
    if status.lower() != "draft":
        raise HTTPException(
            status_code=403,
            detail=f"Cannot {operation} a request that is not in Draft status (current: {status})",
        )


async def check_request_not_completed(
    request_data: dict[str, Any],
    operation: str = "upload",
) -> None:
    """Verify that the EA request is NOT in completed status.

    Used for upload operations (diagrams, attachments) where the
    Request_Owner can upload as long as the request is not completed.

    Raises 403 if the request is in completed status.
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return

    status = (request_data.get("status") or "").strip()
    if status.lower() == "completed":
        raise HTTPException(
            status_code=403,
            detail=f"Cannot {operation} on a request in Completed status",
        )


# ---------------------------------------------------------------------------
# 2. EA Review — reviewer assignment
# ---------------------------------------------------------------------------

async def check_reviewer_assignment(
    user: AuthUser,
    request_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Verify the user is assigned as reviewer on this request.

    *request_id* is the business key (e.g. "EA250001"), not the UUID PK.

    Returns the request row as a dict on success.
    Raises 404 if the request doesn't exist.
    Raises 403 if the user is not assigned as reviewer (and not EA_Admin).
    """
    result = await db.execute(
        text("SELECT * FROM eam.eam_request WHERE request_id = :rid"),
        {"rid": request_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="EA request not found")

    request_data = dict(row)

    from app.config import settings
    if not settings.EE_ENABLED:
        return request_data

    # EA_Admin bypasses
    if user.is_admin:
        return request_data

    # Check assign_reviewer array
    assign_reviewer = request_data.get("assign_reviewer") or []
    if isinstance(assign_reviewer, str):
        assign_reviewer = [assign_reviewer]

    # assign_reviewer stores itcodes; match against user.id (itcode)
    if user.id not in assign_reviewer:
        logger.warning(
            "Authz denied: reviewer=%s not assigned to request=%s (assigned=%s)",
            user.id, request_id, assign_reviewer,
        )
        raise HTTPException(
            status_code=403,
            detail="You are not assigned as reviewer for this request",
        )

    return request_data


# ---------------------------------------------------------------------------
# 3. Application ownership — for BCM, Tech Stack, and Lifecycle
# ---------------------------------------------------------------------------

async def check_app_ownership(
    user: AuthUser,
    app_id: str,
    db: AsyncSession,
) -> bool:
    """Verify the user owns the application.

    Returns True on success.
    Raises 403 if the user does not own the application (and not EA_Admin).
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return True

    # EA_Admin bypasses
    if user.is_admin:
        return True

    # Check cmdb_application ownership fields
    result = await db.execute(
        text(
            "SELECT 1 FROM eam.cmdb_application "
            "WHERE app_id = :app_id "
            "  AND (app_dt_owner = :uid OR app_operation_owner = :uid OR app_it_owner = :uid) "
            "LIMIT 1"
        ),
        {"app_id": app_id, "uid": user.id},
    )
    if result.scalar() is not None:
        return True

    # Check application_member by email prefix
    if user.email_prefix:
        result = await db.execute(
            text(
                "SELECT 1 FROM eam.application_member "
                "WHERE app_id = :app_id AND LOWER(itcode) = :prefix "
                "LIMIT 1"
            ),
            {"app_id": app_id, "prefix": user.email_prefix},
        )
        if result.scalar() is not None:
            return True

    logger.warning(
        "Authz denied: user=%s does not own app=%s",
        user.id, app_id,
    )
    raise HTTPException(
        status_code=403,
        detail=f"You do not have ownership of application {app_id}",
    )


# ---------------------------------------------------------------------------
# 4. Project ownership — for project mutations
# ---------------------------------------------------------------------------

async def check_project_ownership(
    user: AuthUser,
    project_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Verify the user is the PM, DT Lead, or IT Lead of this project.

    *project_id* is the business key (e.g. "P250001"), not the UUID PK.

    Returns the project row as a dict on success.
    Raises 404 if the project doesn't exist.
    Raises 403 if the user is not a project owner (and not EA_Admin/EA_Reviewer).
    """
    result2 = await db.execute(
        text("SELECT id, project_id, name, status, owner_id, pm_itcode, dt_lead_itcode, it_lead_itcode FROM eam.eam_project WHERE project_id = :pid OR id::text = :pid"),
        {"pid": project_id},
    )
    row2 = result2.mappings().first()
    if not row2:
        raise HTTPException(status_code=404, detail="Project not found")

    project_data = dict(row2)
    project_data.setdefault("pm_itcode", project_data.get("pm_itcode") or "")
    project_data.setdefault("dt_lead_itcode", project_data.get("dt_lead_itcode") or "")
    project_data.setdefault("it_lead_itcode", project_data.get("it_lead_itcode") or "")
    project_data["_source_table"] = "new"

    from app.config import settings
    if not settings.EE_ENABLED:
        return project_data

    # EA_Admin bypasses ownership checks
    if user.is_admin:
        return project_data

    # EA_Reviewer can change any project (no record-level scoping per matrix)
    if user.is_reviewer:
        return project_data

    # Project_Owner check: user must be PM, DT Lead, or IT Lead
    owner_fields = [
        project_data.get("pm_itcode"),
        project_data.get("dt_lead_itcode"),
        project_data.get("it_lead_itcode"),
    ]
    if user.id in owner_fields:
        return project_data

    logger.warning(
        "Authz denied: user=%s is not owner of project=%s (pm=%s, dt=%s, it=%s)",
        user.id, project_id,
        project_data.get("pm_itcode"),
        project_data.get("dt_lead_itcode"),
        project_data.get("it_lead_itcode"),
    )
    raise HTTPException(
        status_code=403,
        detail="You do not have ownership of this project",
    )


# ---------------------------------------------------------------------------
# 5. Cross-resource access — EA review sub-resources by project/request
# ---------------------------------------------------------------------------

async def check_request_access_by_project(
    user: AuthUser,
    project_id: str,
    db: AsyncSession,
) -> None:
    """Verify the user has write access to EA review sub-resources for a project.

    EA review sub-resources (actions, meetings, meeting decks, scope) are
    linked to EA requests via project_id.  Write access is granted if:
        - user is EA_Admin (always bypasses)
        - user is EA_Reviewer (can create/change meetings, actions, etc. on any project)
        - user created a request under this project

    Raises 403 if none of the above apply.
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return

    if user.is_admin:
        return

    # EA_Reviewer can create/change meetings, actions, meeting decks, and scope
    # on any project — the feature-level gate (meeting:write, action:write, etc.)
    # already limits them to the right operations.  Record-level assignment
    # checks are only used for completing reviews (check_reviewer_assignment).
    if user.is_reviewer:
        return

    # Check if user is the requester of any request under this project
    result = await db.execute(
        text(
            "SELECT 1 FROM eam.eam_request "
            "WHERE project_id = :pid AND requester = :uid "
            "LIMIT 1"
        ),
        {"pid": project_id, "uid": user.id},
    )
    if result.scalar() is not None:
        return

    logger.warning(
        "Authz denied: user=%s has no write access to project=%s resources",
        user.id, project_id,
    )
    raise HTTPException(
        status_code=403,
        detail="You do not have permission to modify resources under this project",
    )


async def check_request_access_by_request_id(
    user: AuthUser,
    request_id: str,
    db: AsyncSession,
) -> None:
    """Verify the user has write access to an EA review sub-resource
    linked to a specific request_id (business key like "EA250001").

    Write access is granted if:
        - user is EA_Admin
        - user is EA_Reviewer (can create/change meetings, actions, etc. on any request)
        - user is the requester of this request

    Raises 404 if the request doesn't exist.
    Raises 403 if none of the above apply.
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return

    if user.is_admin:
        return

    # EA_Reviewer can create/change meetings, actions, meeting decks, and scope
    # on any request — assignment checks are only for completing reviews.
    if user.is_reviewer:
        return

    result = await db.execute(
        text("SELECT requester FROM eam.eam_request WHERE request_id = :rid"),
        {"rid": request_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="EA request not found")

    # Requester check
    if row["requester"] == user.id:
        return

    logger.warning(
        "Authz denied: user=%s has no write access to request=%s",
        user.id, request_id,
    )
    raise HTTPException(
        status_code=403,
        detail="You do not have permission to modify resources for this request",
    )


async def check_reviewer_assigned_to_project(
    user: AuthUser,
    project_id: str,
    db: AsyncSession,
) -> None:
    """Verify that an EA_Reviewer is assigned to the request(s) under this project.

    EA_Admin always bypasses.  For EA_Reviewer, checks that the user's itcode
    appears in the ``assign_reviewer`` array of at least one request under the
    given project.

    Raises 403 if the reviewer is not assigned to any request under this project.
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return

    if user.is_admin:
        return

    result = await db.execute(
        text(
            "SELECT 1 FROM eam.eam_request "
            "WHERE project_id = :pid AND :uid = ANY(assign_reviewer) "
            "LIMIT 1"
        ),
        {"pid": project_id, "uid": user.id},
    )
    if result.scalar() is not None:
        return

    logger.warning(
        "Authz denied: reviewer=%s not assigned to any request under project=%s",
        user.id, project_id,
    )
    raise HTTPException(
        status_code=403,
        detail="You are not assigned as reviewer for this request",
    )


# ---------------------------------------------------------------------------
# 7. Application ownership — owned app_ids listing
# ---------------------------------------------------------------------------

async def get_owned_app_ids(user: AuthUser, db: AsyncSession) -> list[str]:
    """Return all app_ids that the user owns.

    Used for filtering queries to only show/allow the user's owned apps.
    Returns an empty list if the user owns no apps.
    For EA_Admin, returns an empty list (caller should skip filtering).
    In OSS mode, returns empty list (caller should skip filtering).
    """
    from app.config import settings
    if not settings.EE_ENABLED:
        return []

    if user.is_admin:
        return []  # admin sees all — caller should not filter

    app_ids: set[str] = set()

    # From cmdb_application owner fields
    result = await db.execute(
        text(
            "SELECT DISTINCT app_id FROM eam.cmdb_application "
            "WHERE app_dt_owner = :uid "
            "   OR app_operation_owner = :uid "
            "   OR app_it_owner = :uid"
        ),
        {"uid": user.id},
    )
    for row in result.fetchall():
        app_ids.add(row[0])

    # From application_member
    if user.email_prefix:
        result = await db.execute(
            text(
                "SELECT DISTINCT app_id FROM eam.application_member "
                "WHERE LOWER(itcode) = :prefix"
            ),
            {"prefix": user.email_prefix},
        )
        for row in result.fetchall():
            app_ids.add(row[0])

    return sorted(app_ids)
