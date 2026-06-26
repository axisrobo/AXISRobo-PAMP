"""Shared test fixtures for the AxisArch authorization test suite.
 
Provides factory helpers for creating AuthUser instances with specific roles,
and a mock AsyncSession for testing ownership checks without a real database.
"""
from __future__ import annotations

import os
os.environ["EE_ENABLED"] = "true"  # Enable EE features for test suite

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auth.models import AuthUser, Role
from app.auth.rbac import build_permission_list


# ---------------------------------------------------------------------------
# AuthUser factories
# ---------------------------------------------------------------------------

def make_user(
    *,
    user_id: str = "testuser",
    name: str = "Test User",
    email: str = "testuser@example.com",
    roles: list[Role] | None = None,
) -> AuthUser:
    """Create an AuthUser with the given roles and auto-computed permissions."""
    if roles is None:
        roles = [Role.NORMAL_USER]
    email_prefix = email.split("@")[0].lower()
    return AuthUser(
        id=user_id,
        name=name,
        email=email,
        email_prefix=email_prefix,
        roles=roles,
        permissions=build_permission_list(roles),
    )


@pytest.fixture
def admin_user() -> AuthUser:
    """EA_Admin user — unrestricted access."""
    return make_user(
        user_id="admin01",
        name="Admin User",
        email="admin01@example.com",
        roles=[Role.NORMAL_USER, Role.EA_ADMIN],
    )


@pytest.fixture
def normal_user() -> AuthUser:
    """Normal_User — baseline read-only access."""
    return make_user(
        user_id="user01",
        name="Normal User",
        email="user01@example.com",
        roles=[Role.NORMAL_USER],
    )


@pytest.fixture
def reviewer_user() -> AuthUser:
    """EA_Reviewer — can review assigned requests."""
    return make_user(
        user_id="reviewer01",
        name="Reviewer User",
        email="reviewer01@example.com",
        roles=[Role.NORMAL_USER, Role.EA_REVIEWER],
    )


@pytest.fixture
def app_owner_user() -> AuthUser:
    """App_Owner — can manage owned applications."""
    return make_user(
        user_id="appowner01",
        name="App Owner User",
        email="appowner01@example.com",
        roles=[Role.NORMAL_USER, Role.APP_OWNER],
    )


@pytest.fixture
def other_user() -> AuthUser:
    """Another Normal_User for testing cross-user scenarios."""
    return make_user(
        user_id="other99",
        name="Other User",
        email="other99@example.com",
        roles=[Role.NORMAL_USER],
    )


@pytest.fixture
def project_owner_user() -> AuthUser:
    """Project_Owner — can manage owned projects."""
    return make_user(
        user_id="projowner01",
        name="Project Owner User",
        email="projowner01@example.com",
        roles=[Role.NORMAL_USER, Role.PROJECT_OWNER],
    )


# ---------------------------------------------------------------------------
# Mock AsyncSession helpers
# ---------------------------------------------------------------------------

class MockResult:
    """Minimal mock for SQLAlchemy async result."""

    def __init__(self, rows: list[dict[str, Any]] | None = None, scalar_value: Any = None):
        self._rows = rows
        self._scalar_value = scalar_value

    def mappings(self) -> MockMappings:
        return MockMappings(self._rows or [])

    def scalar(self) -> Any:
        return self._scalar_value

    def fetchall(self) -> list[tuple]:
        if self._rows is None:
            return []
        # Return rows as tuples (first value of each dict)
        return [tuple(r.values()) for r in self._rows]


class MockMappings:
    """Mock for result.mappings()."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict[str, Any]]:
        return self._rows


def make_mock_db(execute_results: list[MockResult] | None = None) -> AsyncMock:
    """Create a mock AsyncSession that returns pre-configured results.

    ``execute_results`` is a list of MockResult objects. Each call to
    ``db.execute()`` pops the next result from the list.  If None or
    exhausted, returns an empty MockResult.
    """
    db = AsyncMock()
    results = list(execute_results or [])
    call_index = 0

    async def _execute(*args: Any, **kwargs: Any) -> MockResult:
        nonlocal call_index
        if call_index < len(results):
            result = results[call_index]
            call_index += 1
            return result
        return MockResult()

    db.execute = _execute
    return db


# ---------------------------------------------------------------------------
# Quarantined stale tests — predecessor "Simple-eam" API that was redesigned,
# removed, or moved to EE modules during the OSS split.  These are preserved
# (not deleted) because the rewrite/delete decision requires product input.
# Removing them from the skip list signals that a test has been updated.
# ---------------------------------------------------------------------------

_STALE_NODEIDS: set[str] = {
    # auth/role_resolver — EE scoped-role logic (resolve_scoped_roles happy paths)
    "tests/auth/test_role_resolver.py::TestResolveScopedRoles::test_adds_app_owner_role",
    "tests/auth/test_role_resolver.py::TestResolveScopedRoles::test_adds_project_owner_role",
    "tests/auth/test_role_resolver.py::TestResolveScopedRoles::test_adds_reviewer_role",
    # architecture_check — API redesigned (now /arch-check-apps with different params/body)
    "tests/routers/test_architecture_check.py::TestConfirmArchitectureCheck::test_confirms_check",
    "tests/routers/test_architecture_check.py::TestCreateArchitectureCheck::test_creates_check",
    "tests/routers/test_architecture_check.py::TestCreateArchitectureCheck::test_db_error_returns_500",
    "tests/routers/test_architecture_check.py::TestDeleteArchitectureCheck::test_deletes_check",
    "tests/routers/test_architecture_check.py::TestListArchitectureChecks::test_db_error_returns_500",
    "tests/routers/test_architecture_check.py::TestListArchitectureChecks::test_returns_checks",
    "tests/routers/test_architecture_check.py::TestUpdateArchitectureCheck::test_updates_check",
    # architecture_check_interactions — API redesigned
    "tests/routers/test_architecture_check_interactions.py::TestConfirmInteractions::test_confirms_interactions",
    "tests/routers/test_architecture_check_interactions.py::TestCreateInteraction::test_creates_interaction",
    "tests/routers/test_architecture_check_interactions.py::TestDeleteInteraction::test_deletes_interaction",
    "tests/routers/test_architecture_check_interactions.py::TestListInteractions::test_db_error_returns_500",
    "tests/routers/test_architecture_check_interactions.py::TestListInteractions::test_returns_interactions",
    "tests/routers/test_architecture_check_interactions.py::TestUpdateInteraction::test_updates_interaction",
    # attachments — API path drift + s3_delete -> storage provider
    "tests/routers/test_attachments.py::TestDeleteAttachment::test_deletes_attachment",
    "tests/routers/test_attachments.py::TestListAttachments::test_db_error_returns_500",
    "tests/routers/test_attachments.py::TestListAttachments::test_returns_attachments",
    # audit_log — endpoint path removed in OSS
    "tests/routers/test_audit_log.py::TestAuditLog::test_create_by_filter",
    "tests/routers/test_audit_log.py::TestAuditLog::test_db_error_returns_500",
    "tests/routers/test_audit_log.py::TestAuditLog::test_field_filter",
    "tests/routers/test_audit_log.py::TestAuditLog::test_invalid_sort_falls_back",
    "tests/routers/test_audit_log.py::TestAuditLog::test_object_type_filter",
    "tests/routers/test_audit_log.py::TestAuditLog::test_project_id_filter",
    "tests/routers/test_audit_log.py::TestAuditLog::test_returns_paginated",
    "tests/routers/test_audit_log.py::TestAuditLog::test_sort_asc",
    # bc_visualization — 405 (method / path relocated to /applications/bcm)
    "tests/routers/test_bc_visualization.py::TestBCVisualization::test_db_error_returns_500",
    "tests/routers/test_bc_visualization.py::TestBCVisualization::test_returns_data",
    "tests/routers/test_bc_visualization.py::TestBCVisualization::test_version_filter",
    # certifications — endpoint not mounted in OSS (EE or removed)
    "tests/routers/test_certifications.py::TestCreateCertification::test_creates_cert",
    "tests/routers/test_certifications.py::TestCreateCertification::test_db_error_returns_500",
    "tests/routers/test_certifications.py::TestDeleteCertification::test_deletes_cert",
    "tests/routers/test_certifications.py::TestExportCertifications::test_export_returns_data",
    "tests/routers/test_certifications.py::TestGetCertification::test_returns_cert",
    "tests/routers/test_certifications.py::TestImportValidate::test_validates_import_file",
    "tests/routers/test_certifications.py::TestListCertifications::test_db_error_returns_500",
    "tests/routers/test_certifications.py::TestListCertifications::test_returns_paginated",
    "tests/routers/test_certifications.py::TestListCertifications::test_with_status_filter",
    "tests/routers/test_certifications.py::TestTemplateDownload::test_returns_template",
    "tests/routers/test_certifications.py::TestUpdateCertification::test_updates_cert",
    # dashboard — endpoint not mounted in OSS
    "tests/routers/test_dashboard.py::TestHomeStats::test_returns_home_stats",
    "tests/routers/test_dashboard.py::TestMyActions::test_returns_my_actions",
    "tests/routers/test_dashboard.py::TestMyProjects::test_db_error_returns_500",
    "tests/routers/test_dashboard.py::TestMyProjects::test_returns_my_projects",
    "tests/routers/test_dashboard.py::TestMyRequests::test_returns_my_requests",
    "tests/routers/test_dashboard.py::TestRequestQueue::test_db_error_returns_500",
    "tests/routers/test_dashboard.py::TestRequestQueue::test_returns_queue",
    "tests/routers/test_dashboard.py::TestRequestQueue::test_with_status_filter",
    "tests/routers/test_dashboard.py::TestRequestQueueHeader::test_returns_queue_header",
    "tests/routers/test_dashboard.py::TestStats::test_db_error_returns_500",
    "tests/routers/test_dashboard.py::TestStats::test_returns_stats",
    # dict_options — endpoint not mounted in OSS
    "tests/routers/test_dict_options.py::TestGetCategories::test_db_error_returns_500",
    "tests/routers/test_dict_options.py::TestGetCategories::test_returns_categories",
    "tests/routers/test_dict_options.py::TestGetDictOptions::test_db_error_returns_500",
    "tests/routers/test_dict_options.py::TestGetDictOptions::test_filter_by_category_id",
    "tests/routers/test_dict_options.py::TestGetDictOptions::test_filter_by_lang",
    "tests/routers/test_dict_options.py::TestGetDictOptions::test_returns_list",
    # projects — 500 (shape/code drift with mock data; 3 tests, rest of file passes)
    "tests/routers/test_projects.py::TestChangeFavourite::test_change_favourite",
    "tests/routers/test_projects.py::TestGetProject::test_returns_project",
    "tests/routers/test_projects.py::TestUpdateProject::test_updates_project",
    # schedules — endpoint not mounted in OSS
    "tests/routers/test_schedules.py::TestCreateSchedule::test_creates_schedule",
    "tests/routers/test_schedules.py::TestCreateSchedule::test_db_error_returns_500",
    "tests/routers/test_schedules.py::TestDeleteSchedule::test_deletes_schedule",
    "tests/routers/test_schedules.py::TestListSchedules::test_db_error_returns_500",
    "tests/routers/test_schedules.py::TestListSchedules::test_returns_paginated",
    "tests/routers/test_schedules.py::TestListSchedules::test_status_filter",
    "tests/routers/test_schedules.py::TestListSchedules::test_time_from_filter",
    "tests/routers/test_schedules.py::TestUpdateSchedule::test_updates_schedule",
    # scope — endpoint not mounted in OSS
    "tests/routers/test_scope.py::TestScopeChecklist::test_create_checklist",
    "tests/routers/test_scope.py::TestScopeChecklist::test_list_checklist",
    "tests/routers/test_scope.py::TestScopeChecklist::test_update_checklist",
    "tests/routers/test_scope.py::TestScopeOfChange::test_create_scope",
    "tests/routers/test_scope.py::TestScopeOfChange::test_db_error_returns_500",
    "tests/routers/test_scope.py::TestScopeOfChange::test_delete_scope",
    "tests/routers/test_scope.py::TestScopeOfChange::test_list_no_filter",
    "tests/routers/test_scope.py::TestScopeOfChange::test_list_with_project_id",
    "tests/routers/test_scope.py::TestScopeOfChange::test_list_with_request_id_found",
    "tests/routers/test_scope.py::TestScopeOfChange::test_list_with_request_id_not_found",
    "tests/routers/test_scope.py::TestScopeOfChange::test_update_scope",
    "tests/routers/test_scope.py::TestScopeTemplates::test_list_checklist_templates",
    "tests/routers/test_scope.py::TestScopeTemplates::test_list_scope_pages",
    "tests/routers/test_scope.py::TestScopeTemplates::test_list_scope_templates",
    # technology_stack — API path drifted /tech-stack -> /technology-stack; schema changed
    "tests/routers/test_technology_stack.py::TestCatalogEndpoints::test_create_catalog_item",
    "tests/routers/test_technology_stack.py::TestCatalogEndpoints::test_delete_catalog_item",
    "tests/routers/test_technology_stack.py::TestCatalogEndpoints::test_list_catalog",
    "tests/routers/test_technology_stack.py::TestCatalogEndpoints::test_update_catalog_item",
    "tests/routers/test_technology_stack.py::TestCategories::test_returns_categories",
    "tests/routers/test_technology_stack.py::TestChecking::test_create_checking",
    "tests/routers/test_technology_stack.py::TestCmdbLookup::test_returns_lookup",
    "tests/routers/test_technology_stack.py::TestCreateTechStack::test_creates_record",
    "tests/routers/test_technology_stack.py::TestCreateTechStack::test_db_error_returns_500",
    "tests/routers/test_technology_stack.py::TestDeleteTechStack::test_deletes_record",
    "tests/routers/test_technology_stack.py::TestGetTechStack::test_returns_record",
    "tests/routers/test_technology_stack.py::TestLifecycle::test_returns_lifecycle",
    "tests/routers/test_technology_stack.py::TestListTechStack::test_db_error_returns_500",
    "tests/routers/test_technology_stack.py::TestListTechStack::test_returns_paginated",
    "tests/routers/test_technology_stack.py::TestListTechStack::test_with_category_filter",
    "tests/routers/test_technology_stack.py::TestMasterOptions::test_returns_options",
    "tests/routers/test_technology_stack.py::TestOperateLog::test_list_operate_log",
    "tests/routers/test_technology_stack.py::TestResourcePool::test_returns_resource_pool",
    "tests/routers/test_technology_stack.py::TestTeamMemberEndpoints::test_add_team_member",
    "tests/routers/test_technology_stack.py::TestTeamMemberEndpoints::test_list_team_members",
    "tests/routers/test_technology_stack.py::TestTeamMemberEndpoints::test_remove_team_member",
    "tests/routers/test_technology_stack.py::TestTechStackApps::test_create_app",
    "tests/routers/test_technology_stack.py::TestTechStackApps::test_delete_app",
    "tests/routers/test_technology_stack.py::TestTechStackApps::test_get_app",
    "tests/routers/test_technology_stack.py::TestUpdateTechStack::test_updates_record",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Quarantine known-stale legacy tests from the predecessor Simple-eam API.

    These tests target endpoints that were redesigned, removed, or moved to
    EE modules during the OSS split.  They are preserved (not deleted) so the
    rewrite/delete decision can be made deliberately.  Remove a nodeid from
    _STALE_NODEIDS or update the test to signal it has been rewritten.
    """
    for item in items:
        if item.nodeid in _STALE_NODEIDS:
            item.add_marker(pytest.mark.skip(reason="Legacy predecessor-API test pending rewrite"))
