"""Scoped business role resolution from application data.

This module resolves EA_Admin, EA_Reviewer, App_Owner, and Project_Owner
roles by querying the database.  It is called during the auth middleware
pipeline *after* Keycloak authentication establishes user identity.

Sources:
    EA_Admin       ← eam.eam_bigea_team_members  (ea_admin_status = true)
    EA_Reviewer    ← eam.eam_bigea_team_members  (matched by itcode)
    App_Owner      ← eam.cmdb_application         (app_dt_owner, app_operation_owner, app_it_owner)
                   ← eam.application_member        (itcode = email prefix)
    Project_Owner  ← eam.project                   (pm_itcode, dt_lead_itcode, it_lead_itcode)
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser, Role
from app.auth.rbac import build_permission_list

logger = logging.getLogger("eam.auth.role_resolver")


async def resolve_scoped_roles(user: AuthUser, db: AsyncSession) -> AuthUser:
    """Resolve scoped business roles for *user* and return an updated copy.

    This adds EA_Admin, EA_Reviewer, App_Owner, and/or Project_Owner to
    the user's role list based on database lookups.  The user's
    permissions list is rebuilt after role resolution.

    This function is safe to call multiple times — it is idempotent.
    """
    new_roles = list(user.roles)  # copy

    # ── Resolve EA_Admin ─────────────────────────────────────────
    if Role.EA_ADMIN not in new_roles:
        is_admin = await _is_ea_admin(user.id, db)
        if is_admin:
            new_roles.insert(0, Role.EA_ADMIN)

    # ── Resolve EA_Reviewer ──────────────────────────────────────
    if Role.EA_REVIEWER not in new_roles:
        is_reviewer = await _is_team_member(user.id, db)
        if is_reviewer:
            new_roles.append(Role.EA_REVIEWER)

    # ── Resolve App_Owner ────────────────────────────────────────
    if Role.APP_OWNER not in new_roles:
        is_owner = await _is_app_owner(user.id, user.email_prefix, db)
        if is_owner:
            new_roles.append(Role.APP_OWNER)

    # ── Resolve Project_Owner ────────────────────────────────────
    if Role.PROJECT_OWNER not in new_roles:
        is_proj_owner = await _is_project_owner(user.id, db)
        if is_proj_owner:
            new_roles.append(Role.PROJECT_OWNER)

    # Rebuild if roles changed
    if len(new_roles) != len(user.roles):
        return user.model_copy(update={
            "roles": new_roles,
            "permissions": build_permission_list(new_roles),
        })

    return user


async def _is_ea_admin(itcode: str, db: AsyncSession) -> bool:
    """Return True if *itcode* has ea_admin_status set to true in eam_bigea_team_members."""
    result = await db.execute(
        text(
            "SELECT 1 FROM eam.eam_bigea_team_members "
            "WHERE itcode = :itcode AND ea_admin_status = true "
            "LIMIT 1"
        ),
        {"itcode": itcode},
    )
    return result.scalar() is not None


async def _is_team_member(itcode: str, db: AsyncSession) -> bool:
    """Return True if *itcode* exists in eam_bigea_team_members."""
    result = await db.execute(
        text("SELECT 1 FROM eam.eam_bigea_team_members WHERE itcode = :itcode LIMIT 1"),
        {"itcode": itcode},
    )
    return result.scalar() is not None


async def _is_app_owner(user_id: str, email_prefix: str, db: AsyncSession) -> bool:
    """Return True if *user_id* or *email_prefix* is an owner of any application.

    Ownership sources:
        - cmdb_application.app_dt_owner
        - cmdb_application.app_operation_owner
        - cmdb_application.app_it_owner
        - application_member.itcode (matched against email_prefix)
    """
    # Check cmdb_application ownership fields
    result = await db.execute(
        text(
            "SELECT 1 FROM eam.cmdb_application "
            "WHERE app_dt_owner = :uid "
            "   OR app_operation_owner = :uid "
            "   OR app_it_owner = :uid "
            "LIMIT 1"
        ),
        {"uid": user_id},
    )
    if result.scalar() is not None:
        return True

    # Check application_member by email prefix
    if email_prefix:
        result = await db.execute(
            text(
                "SELECT 1 FROM eam.application_member "
                "WHERE LOWER(itcode) = :prefix "
                "LIMIT 1"
            ),
            {"prefix": email_prefix},
        )
        if result.scalar() is not None:
            return True

    return False


async def _is_project_owner(user_id: str, db: AsyncSession) -> bool:
    """Return True if *user_id* is PM, DT Lead, or IT Lead on any project.

    Ownership sources:
        - project.pm_itcode
        - project.dt_lead_itcode
        - project.it_lead_itcode
    """
    result = await db.execute(
        text(
            "SELECT 1 FROM eam.eam_project "
            "WHERE pm_itcode = :uid "
            "   OR dt_lead_itcode = :uid "
            "   OR it_lead_itcode = :uid "
            "LIMIT 1"
        ),
        {"uid": user_id},
    )
    return result.scalar() is not None
