"""AxisArch Authentication & Authorization module.

Role model:
    EA_Admin        — unrestricted (from eam_bigea_team_members.ea_admin_status)
    Normal_User     — every authenticated user
    EA_Reviewer     — scoped: assigned review authority
    App_Owner       — scoped: owned application data authority
    Project_Owner   — scoped: owned project data authority
    Request_Owner   — per-record: resolved from eam_request.requester

Public API:
    Models:    AuthUser, Role
    RBAC:      check_permission
    Deps:      get_current_user, require_auth, require_role, require_permission
    Ownership: check_request_owner, check_request_creator (alias),
               check_request_draft_status, check_request_not_completed,
               check_reviewer_assignment, check_reviewer_assigned_to_project,
               check_app_ownership,
               check_project_ownership, get_owned_app_ids
    Resolver:  resolve_scoped_roles
    Audit:     audit_allow, audit_deny
"""

from app.auth.models import AuthUser, Role
from app.auth.rbac import check_permission
from app.auth.dependencies import get_current_user, require_auth, require_role, require_permission
from app.auth.ownership import (
    check_request_owner,
    check_request_creator,
    check_request_draft_status,
    check_request_not_completed,
    check_reviewer_assignment,
    check_reviewer_assigned_to_project,
    check_app_ownership,
    check_project_ownership,
    get_owned_app_ids,
    check_request_access_by_project,
    check_request_access_by_request_id,
)
from app.auth.role_resolver import resolve_scoped_roles
from app.auth.audit import audit_allow, audit_deny

__all__ = [
    # Models
    "AuthUser",
    "Role",
    # RBAC
    "check_permission",
    # Dependencies
    "get_current_user",
    "require_auth",
    "require_role",
    "require_permission",
    # Ownership checks
    "check_request_owner",
    "check_request_creator",  # backwards-compatible alias
    "check_request_draft_status",
    "check_request_not_completed",
    "check_reviewer_assignment",
    "check_reviewer_assigned_to_project",
    "check_app_ownership",
    "check_project_ownership",
    "get_owned_app_ids",
    "check_request_access_by_project",
    "check_request_access_by_request_id",
    # Role resolution
    "resolve_scoped_roles",
    # Audit
    "audit_allow",
    "audit_deny",
]
