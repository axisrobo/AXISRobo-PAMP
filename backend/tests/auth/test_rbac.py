"""Tests for the RBAC permission matrix and helpers.

Covers:
    - EA_Admin wildcard access
    - Normal_User restricted access (no meeting, schedule, cert, etc.)
    - EA_Reviewer scoped permissions (BCM write, no schedule, no delete)
    - App_Owner scoped permissions (BCM/tech_stack write)
    - Project_Owner scoped permissions (project write)
    - build_permission_list merging
"""
from app.auth.models import Role
from app.auth.rbac import check_permission, build_permission_list


# ── EA_Admin — unrestricted wildcard ──────────────────────────────


class TestEAAdminPermissions:
    """EA_Admin should have wildcard access to everything."""

    def test_admin_read_any_resource(self):
        assert check_permission([Role.EA_ADMIN], "ea_request", "read") is True

    def test_admin_write_any_resource(self):
        assert check_permission([Role.EA_ADMIN], "ea_request", "write") is True

    def test_admin_arbitrary_resource(self):
        assert check_permission([Role.EA_ADMIN], "nonexistent_resource", "write") is True

    def test_admin_arbitrary_scope(self):
        assert check_permission([Role.EA_ADMIN], "ea_request", "delete") is True

    def test_admin_team_member_write(self):
        assert check_permission([Role.EA_ADMIN], "team_member", "write") is True

    def test_admin_project_write(self):
        assert check_permission([Role.EA_ADMIN], "project", "write") is True

    def test_admin_certification(self):
        assert check_permission([Role.EA_ADMIN], "certification", "write") is True

    def test_admin_schedule(self):
        assert check_permission([Role.EA_ADMIN], "schedule", "write") is True

    def test_admin_tech_stack_master(self):
        assert check_permission([Role.EA_ADMIN], "tech_stack_master", "write") is True

    def test_admin_tech_stack_lifecycle(self):
        assert check_permission([Role.EA_ADMIN], "tech_stack_lifecycle", "write") is True


# ── Normal_User — restricted module access ───────────────────────


class TestNormalUserPermissions:
    """Normal_User has limited module access + own EA request maintenance."""

    # ── Allowed ──
    def test_can_read_ea_request(self):
        assert check_permission([Role.NORMAL_USER], "ea_request", "read") is True

    def test_can_write_ea_request(self):
        assert check_permission([Role.NORMAL_USER], "ea_request", "write") is True

    def test_can_read_action(self):
        assert check_permission([Role.NORMAL_USER], "action", "read") is True

    def test_can_write_action_comment(self):
        assert check_permission([Role.NORMAL_USER], "action_comment", "write") is True

    def test_can_read_project(self):
        assert check_permission([Role.NORMAL_USER], "project", "read") is True

    def test_can_write_project(self):
        """Normal_User can create projects; update is scoped to Project_Owner at record level."""
        assert check_permission([Role.NORMAL_USER], "project", "write") is True

    def test_can_read_bcm(self):
        assert check_permission([Role.NORMAL_USER], "bcm", "read") is True

    def test_can_read_tech_stack_master(self):
        assert check_permission([Role.NORMAL_USER], "tech_stack_master", "read") is True

    def test_can_read_tech_stack_lifecycle(self):
        assert check_permission([Role.NORMAL_USER], "tech_stack_lifecycle", "read") is True

    def test_can_read_cmdb(self):
        assert check_permission([Role.NORMAL_USER], "cmdb", "read") is True

    def test_can_read_biz_capability(self):
        assert check_permission([Role.NORMAL_USER], "biz_capability", "read") is True

    def test_can_read_master_data(self):
        assert check_permission([Role.NORMAL_USER], "master_data", "read") is True

    # ── Denied (no access to these modules) ──
    def test_can_read_meeting(self):
        """Normal_User can view Meetings (read-only)."""
        assert check_permission([Role.NORMAL_USER], "meeting", "read") is True

    def test_cannot_write_meeting(self):
        assert check_permission([Role.NORMAL_USER], "meeting", "write") is False

    def test_can_read_meeting_deck(self):
        """Normal_User can view Meeting Decks (read-only)."""
        assert check_permission([Role.NORMAL_USER], "meeting_deck", "read") is True

    def test_cannot_write_meeting_deck(self):
        assert check_permission([Role.NORMAL_USER], "meeting_deck", "write") is False

    def test_can_read_schedule(self):
        assert check_permission([Role.NORMAL_USER], "schedule", "read") is True

    def test_cannot_write_schedule(self):
        assert check_permission([Role.NORMAL_USER], "schedule", "write") is False

    def test_cannot_read_certification(self):
        assert check_permission([Role.NORMAL_USER], "certification", "read") is False

    def test_cannot_read_resource(self):
        assert check_permission([Role.NORMAL_USER], "resource", "read") is False

    def test_cannot_read_report(self):
        assert check_permission([Role.NORMAL_USER], "report", "read") is False

    def test_cannot_read_dashboard(self):
        assert check_permission([Role.NORMAL_USER], "dashboard", "read") is False

    def test_cannot_read_settings(self):
        assert check_permission([Role.NORMAL_USER], "settings", "read") is False

    def test_cannot_read_team_member(self):
        """Normal_User has NO team_member access (empty cell in matrix)."""
        assert check_permission([Role.NORMAL_USER], "team_member", "read") is False

    def test_cannot_write_team_member(self):
        assert check_permission([Role.NORMAL_USER], "team_member", "write") is False

    def test_cannot_write_bcm(self):
        assert check_permission([Role.NORMAL_USER], "bcm", "write") is False

    def test_cannot_write_tech_stack_master(self):
        assert check_permission([Role.NORMAL_USER], "tech_stack_master", "write") is False

    def test_cannot_write_tech_stack_lifecycle(self):
        assert check_permission([Role.NORMAL_USER], "tech_stack_lifecycle", "write") is False

    def test_cannot_write_action(self):
        """Normal_User can only add comments, not write full actions."""
        assert check_permission([Role.NORMAL_USER], "action", "write") is False

    def test_cannot_access_unknown_resource(self):
        assert check_permission([Role.NORMAL_USER], "nonexistent", "read") is False

    def test_can_execute_export(self):
        """Normal_User can export data."""
        assert check_permission([Role.NORMAL_USER], "export", "execute") is True


# ── EA_Reviewer — review-scoped access ────────────────────────────


class TestEAReviewerPermissions:
    """EA_Reviewer gets write on EA review resources + BCM + project, read on tech stack."""

    # ── Allowed ──
    def test_can_write_ea_request(self):
        assert check_permission([Role.EA_REVIEWER], "ea_request", "write") is True

    def test_can_write_meeting(self):
        assert check_permission([Role.EA_REVIEWER], "meeting", "write") is True

    def test_can_write_meeting_deck(self):
        assert check_permission([Role.EA_REVIEWER], "meeting_deck", "write") is True

    def test_can_write_action(self):
        assert check_permission([Role.EA_REVIEWER], "action", "write") is True

    def test_can_write_action_comment(self):
        assert check_permission([Role.EA_REVIEWER], "action_comment", "write") is True

    def test_can_write_scope(self):
        assert check_permission([Role.EA_REVIEWER], "scope", "write") is True

    def test_can_write_project(self):
        """EA_Reviewer can CRU projects (no delete; enforced at router)."""
        assert check_permission([Role.EA_REVIEWER], "project", "write") is True

    def test_can_write_bcm(self):
        """EA_Reviewer can CRU BCM (no delete; enforced at router)."""
        assert check_permission([Role.EA_REVIEWER], "bcm", "write") is True

    def test_can_execute_export(self):
        assert check_permission([Role.EA_REVIEWER], "export", "execute") is True

    def test_can_read_tech_stack_master(self):
        assert check_permission([Role.EA_REVIEWER], "tech_stack_master", "read") is True

    def test_can_read_tech_stack_lifecycle(self):
        assert check_permission([Role.EA_REVIEWER], "tech_stack_lifecycle", "read") is True

    def test_can_read_master_data(self):
        assert check_permission([Role.EA_REVIEWER], "master_data", "read") is True

    # ── Denied ──
    def test_can_read_schedule(self):
        """EA_Reviewer can read EA Calendar."""
        assert check_permission([Role.EA_REVIEWER], "schedule", "read") is True

    def test_cannot_write_schedule(self):
        assert check_permission([Role.EA_REVIEWER], "schedule", "write") is False

    def test_cannot_write_tech_stack_master(self):
        assert check_permission([Role.EA_REVIEWER], "tech_stack_master", "write") is False

    def test_cannot_write_tech_stack_lifecycle(self):
        assert check_permission([Role.EA_REVIEWER], "tech_stack_lifecycle", "write") is False

    def test_cannot_write_team_member(self):
        assert check_permission([Role.EA_REVIEWER], "team_member", "write") is False

    def test_cannot_read_certification(self):
        assert check_permission([Role.EA_REVIEWER], "certification", "read") is False

    def test_cannot_read_resource(self):
        assert check_permission([Role.EA_REVIEWER], "resource", "read") is False

    def test_cannot_read_report(self):
        assert check_permission([Role.EA_REVIEWER], "report", "read") is False

    def test_cannot_read_dashboard(self):
        assert check_permission([Role.EA_REVIEWER], "dashboard", "read") is False

    def test_cannot_read_settings(self):
        assert check_permission([Role.EA_REVIEWER], "settings", "read") is False


# ── App_Owner — application-scoped write ──────────────────────────


class TestAppOwnerPermissions:
    """App_Owner gets write on application/BCM/tech_stack, read on the rest."""

    # ── Allowed ──
    def test_can_write_application(self):
        assert check_permission([Role.APP_OWNER], "application", "write") is True

    def test_can_write_bcm(self):
        assert check_permission([Role.APP_OWNER], "bcm", "write") is True

    def test_can_write_tech_stack_master(self):
        assert check_permission([Role.APP_OWNER], "tech_stack_master", "write") is True

    def test_can_write_tech_stack_lifecycle(self):
        assert check_permission([Role.APP_OWNER], "tech_stack_lifecycle", "write") is True

    def test_can_write_ea_request(self):
        assert check_permission([Role.APP_OWNER], "ea_request", "write") is True

    def test_can_write_action_comment(self):
        assert check_permission([Role.APP_OWNER], "action_comment", "write") is True

    def test_can_write_project(self):
        assert check_permission([Role.APP_OWNER], "project", "write") is True

    def test_can_execute_export(self):
        assert check_permission([Role.APP_OWNER], "export", "execute") is True

    def test_can_read_cmdb(self):
        assert check_permission([Role.APP_OWNER], "cmdb", "read") is True

    # ── Denied ──
    def test_cannot_write_meeting(self):
        assert check_permission([Role.APP_OWNER], "meeting", "write") is False

    def test_can_read_meeting(self):
        """App_Owner can view Meetings (read-only)."""
        assert check_permission([Role.APP_OWNER], "meeting", "read") is True

    def test_cannot_write_schedule(self):
        assert check_permission([Role.APP_OWNER], "schedule", "write") is False

    def test_can_read_schedule(self):
        assert check_permission([Role.APP_OWNER], "schedule", "read") is True

    def test_cannot_write_team_member(self):
        assert check_permission([Role.APP_OWNER], "team_member", "write") is False

    def test_cannot_read_certification(self):
        assert check_permission([Role.APP_OWNER], "certification", "read") is False

    def test_cannot_read_resource(self):
        assert check_permission([Role.APP_OWNER], "resource", "read") is False

    def test_cannot_read_report(self):
        assert check_permission([Role.APP_OWNER], "report", "read") is False

    def test_cannot_read_settings(self):
        assert check_permission([Role.APP_OWNER], "settings", "read") is False

    def test_cannot_write_action(self):
        """App_Owner can only add comments, not full action write."""
        assert check_permission([Role.APP_OWNER], "action", "write") is False


# ── Project_Owner — project-scoped write ──────────────────────────


class TestProjectOwnerPermissions:
    """Project_Owner gets project write + same as Normal_User for everything else."""

    # ── Allowed ──
    def test_can_write_project(self):
        assert check_permission([Role.PROJECT_OWNER], "project", "write") is True

    def test_can_read_project(self):
        assert check_permission([Role.PROJECT_OWNER], "project", "read") is True

    def test_can_write_ea_request(self):
        assert check_permission([Role.PROJECT_OWNER], "ea_request", "write") is True

    def test_can_read_ea_request(self):
        assert check_permission([Role.PROJECT_OWNER], "ea_request", "read") is True

    def test_can_write_action_comment(self):
        assert check_permission([Role.PROJECT_OWNER], "action_comment", "write") is True

    def test_can_read_action(self):
        assert check_permission([Role.PROJECT_OWNER], "action", "read") is True

    def test_can_read_bcm(self):
        assert check_permission([Role.PROJECT_OWNER], "bcm", "read") is True

    def test_can_read_tech_stack_master(self):
        assert check_permission([Role.PROJECT_OWNER], "tech_stack_master", "read") is True

    def test_can_read_master_data(self):
        assert check_permission([Role.PROJECT_OWNER], "master_data", "read") is True

    # ── Denied ──
    def test_cannot_write_bcm(self):
        assert check_permission([Role.PROJECT_OWNER], "bcm", "write") is False

    def test_cannot_write_tech_stack_master(self):
        assert check_permission([Role.PROJECT_OWNER], "tech_stack_master", "write") is False

    def test_cannot_write_tech_stack_lifecycle(self):
        assert check_permission([Role.PROJECT_OWNER], "tech_stack_lifecycle", "write") is False

    def test_cannot_write_meeting(self):
        assert check_permission([Role.PROJECT_OWNER], "meeting", "write") is False

    def test_can_read_meeting(self):
        """Project_Owner can view Meetings (read-only)."""
        assert check_permission([Role.PROJECT_OWNER], "meeting", "read") is True

    def test_can_read_schedule(self):
        assert check_permission([Role.PROJECT_OWNER], "schedule", "read") is True

    def test_cannot_write_schedule(self):
        assert check_permission([Role.PROJECT_OWNER], "schedule", "write") is False

    def test_cannot_read_certification(self):
        assert check_permission([Role.PROJECT_OWNER], "certification", "read") is False

    def test_cannot_read_settings(self):
        assert check_permission([Role.PROJECT_OWNER], "settings", "read") is False

    def test_cannot_write_action(self):
        assert check_permission([Role.PROJECT_OWNER], "action", "write") is False

    def test_can_execute_export(self):
        """Project_Owner can export data."""
        assert check_permission([Role.PROJECT_OWNER], "export", "execute") is True


# ── Multi-role combinations ───────────────────────────────────────


class TestMultiRolePermissions:
    """When a user has multiple roles, permissions are additive."""

    def test_normal_plus_reviewer_can_write_meeting(self):
        roles = [Role.NORMAL_USER, Role.EA_REVIEWER]
        assert check_permission(roles, "meeting", "write") is True

    def test_normal_plus_app_owner_can_write_bcm(self):
        roles = [Role.NORMAL_USER, Role.APP_OWNER]
        assert check_permission(roles, "bcm", "write") is True

    def test_normal_plus_reviewer_can_write_bcm(self):
        """EA_Reviewer now HAS bcm:write."""
        roles = [Role.NORMAL_USER, Role.EA_REVIEWER]
        assert check_permission(roles, "bcm", "write") is True

    def test_normal_plus_project_owner_can_write_project(self):
        roles = [Role.NORMAL_USER, Role.PROJECT_OWNER]
        assert check_permission(roles, "project", "write") is True

    def test_reviewer_plus_app_owner_tech_stack_write(self):
        """Only App_Owner contributes tech_stack_master:write."""
        roles = [Role.EA_REVIEWER, Role.APP_OWNER]
        assert check_permission(roles, "tech_stack_master", "write") is True

    def test_all_roles_combined(self):
        all_roles = [Role.NORMAL_USER, Role.EA_REVIEWER, Role.APP_OWNER, Role.PROJECT_OWNER]
        assert check_permission(all_roles, "meeting", "write") is True
        assert check_permission(all_roles, "bcm", "write") is True
        assert check_permission(all_roles, "tech_stack_master", "write") is True
        assert check_permission(all_roles, "export", "execute") is True

    def test_empty_roles_deny_all(self):
        assert check_permission([], "ea_request", "read") is False


# ── build_permission_list ─────────────────────────────────────────


class TestBuildPermissionList:
    """build_permission_list should merge and de-duplicate permissions."""

    def test_admin_has_wildcard(self):
        perms = build_permission_list([Role.EA_ADMIN])
        assert "*:*" in perms

    def test_normal_user_includes_ea_request_rw(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert "ea_request:read" in perms
        assert "ea_request:write" in perms

    def test_normal_user_includes_action_comment_write(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert "action_comment:write" in perms

    def test_normal_user_includes_project_write(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert "project:write" in perms

    def test_normal_user_excludes_bcm_write(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert "bcm:write" not in perms

    def test_normal_user_includes_meeting_read(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert "meeting:read" in perms
        assert "meeting_deck:read" in perms
        assert "meeting:write" not in perms

    def test_normal_user_excludes_team_member(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert "team_member:read" not in perms

    def test_reviewer_includes_bcm_write(self):
        perms = build_permission_list([Role.EA_REVIEWER])
        assert "bcm:write" in perms

    def test_reviewer_includes_schedule_read(self):
        perms = build_permission_list([Role.EA_REVIEWER])
        assert "schedule:read" in perms
        assert "schedule:write" not in perms

    def test_app_owner_includes_tech_stack_master_write(self):
        perms = build_permission_list([Role.APP_OWNER])
        assert "tech_stack_master:write" in perms
        assert "tech_stack_lifecycle:write" in perms

    def test_project_owner_basic(self):
        perms = build_permission_list([Role.PROJECT_OWNER])
        assert "project:write" in perms
        assert "ea_request:read" in perms
        assert "bcm:write" not in perms

    def test_merged_roles_deduplicated(self):
        perms = build_permission_list([Role.NORMAL_USER, Role.EA_REVIEWER])
        # ea_request:read appears in both but should only be listed once
        assert perms.count("ea_request:read") == 1

    def test_merged_roles_union(self):
        perms = build_permission_list([Role.NORMAL_USER, Role.APP_OWNER])
        assert "bcm:write" in perms
        assert "ea_request:write" in perms

    def test_permissions_sorted(self):
        perms = build_permission_list([Role.NORMAL_USER])
        assert perms == sorted(perms)

    def test_empty_roles_returns_empty(self):
        perms = build_permission_list([])
        assert perms == []
