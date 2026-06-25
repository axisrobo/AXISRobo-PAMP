"""RBAC permission matrix — hybrid baseline + scoped authorization model.

Role hierarchy and capability matrix:
    EA_Admin       → unrestricted access (wildcard)
    Normal_User    → limited module access + own EA request maintenance
    EA_Reviewer    → Normal_User + review assigned requests + meetings/actions/BCM write
    App_Owner      → Normal_User + maintain owned BCM/tech-stack/lifecycle data
    Project_Owner  → Normal_User + maintain owned project data

Scoped business roles (EA_Reviewer, App_Owner, Project_Owner) are additive
on top of Normal_User.  The static matrix here defines *feature-level* access.
Record-level ownership and assignment checks are enforced separately
in the router layer and the ``ownership`` module.

Per-module access restrictions (empty = no access):
    - Meetings: EA_Admin + EA_Reviewer (read+write), Normal_User/App_Owner/Project_Owner (read-only)
    - EA Calendar: EA_Admin (full CRUD), all other roles (read-only)
    - Certification, Resources, Reports, Settings: EA_Admin only
    - Action comments: all authenticated users
    - BCM write: EA_Admin + EA_Reviewer + App_Owner
    - Tech Stack write: EA_Admin + App_Owner
    - Project write: EA_Admin + EA_Reviewer + Project_Owner
"""
from __future__ import annotations

from app.auth.models import Role


# ---------------------------------------------------------------------------
# Permission matrix
#
# Each role maps to { resource: [scopes] }.
# EA_Admin uses wildcard "*" for both resource and scope.
#
# Resources:
#   ea_request          — EA Review Request CRUD
#   meeting             — Meetings management
#   meeting_deck        — Meeting deck files
#   action              — Actions management
#   action_comment      — Action update comments (subset of action)
#   schedule            — EA Calendar
#   ea_review_log       — EA review process logs
#   scope               — Scope of change / checklist
#   project             — Projects management
#   application         — Application management (CMDB read, BCM list read)
#   bcm                 — Business Capability Mapping / App BC Mapping write
#   cmdb                — CMDB application master data
#   biz_capability       — Business Capability Master Data
#   tech_stack_master   — Technology Stack Version Master Data
#   tech_stack_lifecycle — Technology Stack Lifecycle Management
#   certification       — Certifications management
#   resource            — Resources (people lookup)
#   report              — Reports & analytics
#   dashboard           — Dashboard views
#   master_data         — Help files & reference data
#   settings            — Settings (audit log, email logs)
#   team_member         — Team members management
#   dict_option         — Dictionary options
#   export              — Data export
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[Role, dict[str, list[str]]] = {
    # ── EA_Admin — unrestricted ──────────────────────────────────
    Role.EA_ADMIN: {
        "*": ["*"],
    },

    # ── Normal_User — restricted module access + own EA requests ─
    # Modules with NO access:
    #   certification, resource, report, dashboard, settings,
    #   team_member, dict_option
    Role.NORMAL_USER: {
        # EA Review — create/maintain own requests (record-level enforcement)
        "ea_request": ["read", "write"],
        "ea_review_log": ["read"],
        "scope": ["read"],

        # Meetings — read only (no create/edit/delete)
        "meeting": ["read"],
        "meeting_deck": ["read"],

        # Actions — read + add comments only
        "action": ["read"],
        "action_comment": ["write"],

        # EA Calendar — read only
        "schedule": ["read"],

        # Projects — create + read; change scoped to Project_Owner at record level
        "project": ["read", "write"],

        # Application management — read only
        "application": ["read"],
        "bcm": ["read"],
        "cmdb": ["read"],
        "biz_capability": ["read"],

        # Technology Stack — read only
        "tech_stack_master": ["read"],
        "tech_stack_lifecycle": ["read"],

        # AVDM — submit questionnaires for own projects
        "avdm": ["read", "write"],

        # Export
        "export": ["execute"],

        # Help — read only
        "master_data": ["read"],
    },

    # ── EA_Reviewer — Normal_User + review + meetings/actions/BCM ─
    # Modules with NO access: certification,
    #   resource, report, dashboard, settings, team_member, dict_option
    Role.EA_REVIEWER: {
        # EA Review — full read + write (scoped to assigned at record level)
        "ea_request": ["read", "write"],
        "meeting": ["read", "write"],
        "meeting_deck": ["read", "write"],
        "action": ["read", "write"],
        "action_comment": ["write"],
        "ea_review_log": ["read", "write"],
        "scope": ["read", "write"],

        # EA Calendar — read only
        "schedule": ["read"],

        # Projects — create + read + change (no delete; handled at router)
        "project": ["read", "write"],

        # Application management — BCM write (no delete; handled at router)
        "application": ["read"],
        "bcm": ["read", "write"],
        "cmdb": ["read"],
        "biz_capability": ["read"],

        # Technology Stack — read only
        "tech_stack_master": ["read"],
        "tech_stack_lifecycle": ["read"],

        # AVDM — evaluate, review, confirm workflows
        "avdm": ["read", "write"],

        # Export
        "export": ["execute"],

        # Help — read only
        "master_data": ["read"],
    },

    # ── App_Owner — Normal_User + owned BCM/tech-stack/lifecycle ──
    # Modules with NO access:
    #   certification, resource, report, dashboard, settings,
    #   team_member, dict_option
    Role.APP_OWNER: {
        # EA Review — same as Normal_User (write own requests)
        "ea_request": ["read", "write"],
        "ea_review_log": ["read"],
        "scope": ["read"],

        # Meetings — read only (no create/edit/delete)
        "meeting": ["read"],
        "meeting_deck": ["read"],

        # Actions — read + add comments only
        "action": ["read"],
        "action_comment": ["write"],

        # EA Calendar — read only
        "schedule": ["read"],

        # Projects — create + read; change scoped to Project_Owner at record level
        "project": ["read", "write"],

        # Application management — read + write BCM (scoped to owned at record level)
        "application": ["read", "write"],
        "bcm": ["read", "write"],
        "cmdb": ["read"],
        "biz_capability": ["read"],

        # Technology Stack — read + write (scoped to owned at record level)
        "tech_stack_master": ["read", "write"],
        "tech_stack_lifecycle": ["read", "write"],

        # AVDM — read only
        "avdm": ["read"],

        # Export
        "export": ["execute"],

        # Help — read only
        "master_data": ["read"],
    },

    # ── Project_Owner — Normal_User + owned project maintenance ───
    # Only difference from Normal_User: project write is record-scoped
    # to owned projects.  The feature-level permission is the same as
    # Normal_User (project: [read, write]) — record-level enforcement
    # distinguishes Project_Owner from a plain Normal_User.
    Role.PROJECT_OWNER: {
        # EA Review — same as Normal_User
        "ea_request": ["read", "write"],
        "ea_review_log": ["read"],
        "scope": ["read"],

        # Meetings — read only (no create/edit/delete)
        "meeting": ["read"],
        "meeting_deck": ["read"],

        # Actions — read + add comments only
        "action": ["read"],
        "action_comment": ["write"],

        # EA Calendar — read only
        "schedule": ["read"],

        # Projects — create + read + write (scoped to owned at record level)
        "project": ["read", "write"],

        # Application management — read only
        "application": ["read"],
        "bcm": ["read"],
        "cmdb": ["read"],
        "biz_capability": ["read"],

        # Technology Stack — read only
        "tech_stack_master": ["read"],
        "tech_stack_lifecycle": ["read"],

        # AVDM — submit questionnaires for owned projects
        "avdm": ["read", "write"],

        # Export
        "export": ["execute"],

        # Help — read only
        "master_data": ["read"],
    },
}


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

def check_permission(roles: list[Role], resource: str, scope: str) -> bool:
    """Return True if any of *roles* is allowed *scope* on *resource*.

    This checks *feature-level* access only.  Record-level ownership and
    assignment checks must be performed separately.
    """
    for role in roles:
        perms = ROLE_PERMISSIONS.get(role, {})
        # Wildcard role (admin)
        if "*" in perms and ("*" in perms["*"] or scope in perms["*"]):
            return True
        allowed_scopes = perms.get(resource, [])
        if "*" in allowed_scopes or scope in allowed_scopes:
            return True
    return False


def build_permission_list(roles: list[Role]) -> list[str]:
    """Return a merged, de-duplicated flat list of permissions for *roles*.

    Example: ["ea_request:read", "ea_request:write", "meeting:read", ...]
    """
    result_set: set[str] = set()
    for role in roles:
        perms = ROLE_PERMISSIONS.get(role, {})
        for resource, scopes in perms.items():
            for scope in scopes:
                result_set.add(f"{resource}:{scope}")
    return sorted(result_set)
