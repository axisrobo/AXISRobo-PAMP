"""AxisArch authorization roles — baseline RBAC + scoped business roles.

Role model:
    EA_Admin        — platform-wide unrestricted access (sourced from eam_bigea_team_members.ea_admin_status)
    Normal_User     — default for every authenticated user
    EA_Reviewer     — scoped: can complete reviews on assigned requests
    App_Owner       — scoped: can maintain owned BCM, tech stack, and lifecycle data
    Project_Owner   — scoped: can maintain owned project data

Request_Owner is a per-record ownership concept (not a session-wide role).
It is evaluated at the record level by checking eam_request.requester.
"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class Role(str, Enum):
    """AxisArch authorization roles — baseline RBAC + scoped business roles.

    Baseline roles:
        EA_ADMIN       — unrestricted (from eam_bigea_team_members.ea_admin_status)
        NORMAL_USER    — every authenticated user

    Scoped business roles (additive on top of Normal_User):
        EA_REVIEWER    — record-scoped review authority
        APP_OWNER      — record-scoped application data authority
        PROJECT_OWNER  — record-scoped project data authority
    """

    EA_ADMIN = "ea_admin"
    NORMAL_USER = "normal_user"
    EA_REVIEWER = "ea_reviewer"
    APP_OWNER = "app_owner"
    PROJECT_OWNER = "project_owner"


class AuthUser(BaseModel):
    """Authenticated user context injected into request.state.

    A user always has Normal_User baseline.  Additional roles are additive.
    """

    id: str              # itcode / preferred_username
    name: str
    email: str
    email_prefix: str    # normalized email prefix for ownership matching
    roles: list[Role]    # all resolved roles (baseline + scoped)
    permissions: list[str] = []  # cached flat list, e.g. ["ea_request:read", ...]

    # ── Convenience helpers ────────────────────────────────────────

    @property
    def is_admin(self) -> bool:
        return Role.EA_ADMIN in self.roles

    @property
    def is_reviewer(self) -> bool:
        return Role.EA_REVIEWER in self.roles

    @property
    def is_app_owner(self) -> bool:
        return Role.APP_OWNER in self.roles

    @property
    def is_project_owner(self) -> bool:
        return Role.PROJECT_OWNER in self.roles

    def has_role(self, role: Role) -> bool:
        return role in self.roles
