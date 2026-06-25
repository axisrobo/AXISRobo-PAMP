"""Tests for record-level ownership and assignment checks.

Covers:
    - Request_Owner checks (via requester field)
    - Draft-only submit behavior
    - Draft-only delete behavior
    - Request not-completed check (for uploads)
    - Assigned reviewer authorization
    - Application owner authorization through owner fields
    - Application owner authorization through application_member.itcode
    - Project ownership authorization
    - Cross-resource access checks
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth.models import Role
from app.auth.ownership import (
    check_request_owner,
    check_request_creator,
    check_request_draft_status,
    check_request_not_completed,
    check_reviewer_assignment,
    check_app_ownership,
    check_project_ownership,
    check_request_access_by_project,
    check_request_access_by_request_id,
    get_owned_app_ids,
)
from tests.conftest import make_user, make_mock_db, MockResult


# ═══════════════════════════════════════════════════════════════════
# Request_Owner checks (via requester field)
# ═══════════════════════════════════════════════════════════════════


class TestCheckRequestOwner:
    """Request_Owner is determined by the requester field, NOT create_by."""

    async def test_requester_can_access_own_request(self, normal_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "someone_else",
                "status": "Draft",
            }]),
        ])
        result = await check_request_owner(normal_user, "EA250001", db)
        assert result["request_id"] == "EA250001"
        assert result["requester"] == "user01"

    async def test_non_requester_gets_403(self, normal_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "someone_else",
                "create_by": "user01",  # create_by matches but requester doesn't
                "status": "Draft",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_request_owner(normal_user, "EA250001", db)
        assert exc_info.value.status_code == 403
        assert "requester" in exc_info.value.detail.lower()

    async def test_nonexistent_request_gets_404(self, normal_user):
        db = make_mock_db([MockResult(rows=[])])
        with pytest.raises(HTTPException) as exc_info:
            await check_request_owner(normal_user, "EA999999", db)
        assert exc_info.value.status_code == 404

    async def test_admin_bypasses_requester_check(self, admin_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "someone_else",
                "create_by": "someone_else",
                "status": "Draft",
            }]),
        ])
        result = await check_request_owner(admin_user, "EA250001", db)
        assert result["request_id"] == "EA250001"

    async def test_other_normal_user_denied(self, other_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "status": "Draft",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_request_owner(other_user, "EA250001", db)
        assert exc_info.value.status_code == 403

    async def test_backwards_compatible_alias(self, normal_user):
        """check_request_creator is an alias for check_request_owner."""
        assert check_request_creator is check_request_owner


# ═══════════════════════════════════════════════════════════════════
# Draft-only submit behavior
# ═══════════════════════════════════════════════════════════════════


class TestCheckRequestDraftStatusSubmit:
    """Submit should only be allowed on requests in 'Draft' status."""

    async def test_draft_status_allows_submit(self):
        request_data = {"status": "Draft", "request_id": "EA250001"}
        # Should not raise
        await check_request_draft_status(request_data, operation="submit")

    async def test_draft_status_case_insensitive(self):
        request_data = {"status": "draft", "request_id": "EA250001"}
        await check_request_draft_status(request_data, operation="submit")

    async def test_draft_status_with_whitespace(self):
        request_data = {"status": "  Draft  ", "request_id": "EA250001"}
        # strip() is called on status
        await check_request_draft_status(request_data, operation="submit")

    async def test_submitted_status_blocks_submit(self):
        request_data = {"status": "Submitted", "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="submit")
        assert exc_info.value.status_code == 403
        assert "not in Draft status" in exc_info.value.detail

    async def test_completed_status_blocks_submit(self):
        request_data = {"status": "Completed", "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="submit")
        assert exc_info.value.status_code == 403

    async def test_empty_status_blocks_submit(self):
        request_data = {"status": "", "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="submit")
        assert exc_info.value.status_code == 403

    async def test_none_status_blocks_submit(self):
        request_data = {"status": None, "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="submit")
        assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# Draft-only delete behavior
# ═══════════════════════════════════════════════════════════════════


class TestCheckRequestDraftStatusDelete:
    """Delete should only be allowed on requests in 'Draft' status."""

    async def test_draft_status_allows_delete(self):
        request_data = {"status": "Draft", "request_id": "EA250001"}
        await check_request_draft_status(request_data, operation="delete")

    async def test_in_review_status_blocks_delete(self):
        request_data = {"status": "In Review", "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="delete")
        assert exc_info.value.status_code == 403
        assert "delete" in exc_info.value.detail.lower()

    async def test_approved_status_blocks_delete(self):
        request_data = {"status": "Approved", "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="delete")
        assert exc_info.value.status_code == 403

    async def test_error_message_includes_current_status(self):
        request_data = {"status": "Completed", "request_id": "EA250001"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_draft_status(request_data, operation="delete")
        assert "Completed" in exc_info.value.detail


# ═══════════════════════════════════════════════════════════════════
# Request not-completed check (for uploads)
# ═══════════════════════════════════════════════════════════════════


class TestCheckRequestNotCompleted:
    """Upload should be blocked when request is in Completed status."""

    async def test_draft_allows_upload(self):
        request_data = {"status": "Draft"}
        await check_request_not_completed(request_data, operation="upload")

    async def test_in_review_allows_upload(self):
        request_data = {"status": "In Review"}
        await check_request_not_completed(request_data, operation="upload")

    async def test_submitted_allows_upload(self):
        request_data = {"status": "Submitted"}
        await check_request_not_completed(request_data, operation="upload")

    async def test_completed_blocks_upload(self):
        request_data = {"status": "Completed"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_not_completed(request_data, operation="upload")
        assert exc_info.value.status_code == 403
        assert "Completed" in exc_info.value.detail

    async def test_completed_case_insensitive(self):
        request_data = {"status": "completed"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_not_completed(request_data, operation="upload")
        assert exc_info.value.status_code == 403

    async def test_completed_with_whitespace(self):
        request_data = {"status": "  Completed  "}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_not_completed(request_data, operation="upload")
        assert exc_info.value.status_code == 403

    async def test_none_status_allows_upload(self):
        """None status is not 'completed', so upload is allowed."""
        request_data = {"status": None}
        await check_request_not_completed(request_data, operation="upload")

    async def test_empty_status_allows_upload(self):
        """Empty status is not 'completed', so upload is allowed."""
        request_data = {"status": ""}
        await check_request_not_completed(request_data, operation="upload")

    async def test_custom_operation_in_message(self):
        request_data = {"status": "Completed"}
        with pytest.raises(HTTPException) as exc_info:
            await check_request_not_completed(request_data, operation="modify attachment")
        assert "modify attachment" in exc_info.value.detail


# ═══════════════════════════════════════════════════════════════════
# Assigned reviewer authorization
# ═══════════════════════════════════════════════════════════════════


class TestCheckReviewerAssignment:
    """Reviewer actions should only be allowed for assigned reviewers."""

    async def test_assigned_reviewer_allowed(self, reviewer_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": ["reviewer01"],
                "status": "In Review",
            }]),
        ])
        result = await check_reviewer_assignment(reviewer_user, "EA250001", db)
        assert result["request_id"] == "EA250001"

    async def test_unassigned_reviewer_denied(self, reviewer_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": ["other_reviewer"],
                "status": "In Review",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_reviewer_assignment(reviewer_user, "EA250001", db)
        assert exc_info.value.status_code == 403
        assert "not assigned" in exc_info.value.detail.lower()

    async def test_empty_reviewer_list_denied(self, reviewer_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": [],
                "status": "In Review",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_reviewer_assignment(reviewer_user, "EA250001", db)
        assert exc_info.value.status_code == 403

    async def test_null_reviewer_list_denied(self, reviewer_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": None,
                "status": "In Review",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_reviewer_assignment(reviewer_user, "EA250001", db)
        assert exc_info.value.status_code == 403

    async def test_reviewer_in_multi_reviewer_list(self, reviewer_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": ["other01", "reviewer01", "other02"],
                "status": "In Review",
            }]),
        ])
        result = await check_reviewer_assignment(reviewer_user, "EA250001", db)
        assert result["request_id"] == "EA250001"

    async def test_admin_bypasses_reviewer_check(self, admin_user):
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": ["other_reviewer"],
                "status": "In Review",
            }]),
        ])
        result = await check_reviewer_assignment(admin_user, "EA250001", db)
        assert result["request_id"] == "EA250001"

    async def test_nonexistent_request_gets_404(self, reviewer_user):
        db = make_mock_db([MockResult(rows=[])])
        with pytest.raises(HTTPException) as exc_info:
            await check_reviewer_assignment(reviewer_user, "EA999999", db)
        assert exc_info.value.status_code == 404

    async def test_string_reviewer_field_handled(self, reviewer_user):
        """assign_reviewer might be a string instead of a list in some DB rows."""
        db = make_mock_db([
            MockResult(rows=[{
                "request_id": "EA250001",
                "requester": "user01",
                "create_by": "user01",
                "assign_reviewer": "reviewer01",
                "status": "In Review",
            }]),
        ])
        result = await check_reviewer_assignment(reviewer_user, "EA250001", db)
        assert result["request_id"] == "EA250001"


# ═══════════════════════════════════════════════════════════════════
# Application owner authorization — owner fields
# ═══════════════════════════════════════════════════════════════════


class TestCheckAppOwnershipViaOwnerFields:
    """App_Owner should be authorized via cmdb_application owner fields."""

    async def test_dt_owner_allowed(self, app_owner_user):
        """User matches app_dt_owner field."""
        db = make_mock_db([
            MockResult(scalar_value=1),  # cmdb_application match
        ])
        result = await check_app_ownership(app_owner_user, "APP001", db)
        assert result is True

    async def test_operation_owner_allowed(self, app_owner_user):
        """User matches app_operation_owner field."""
        db = make_mock_db([
            MockResult(scalar_value=1),
        ])
        result = await check_app_ownership(app_owner_user, "APP001", db)
        assert result is True

    async def test_it_owner_allowed(self, app_owner_user):
        """User matches app_it_owner field."""
        db = make_mock_db([
            MockResult(scalar_value=1),
        ])
        result = await check_app_ownership(app_owner_user, "APP001", db)
        assert result is True

    async def test_non_owner_denied(self, app_owner_user):
        """User does not match any owner field and is not in application_member."""
        db = make_mock_db([
            MockResult(scalar_value=None),   # cmdb_application — no match
            MockResult(scalar_value=None),   # application_member — no match
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_app_ownership(app_owner_user, "APP001", db)
        assert exc_info.value.status_code == 403
        assert "ownership" in exc_info.value.detail.lower()

    async def test_admin_bypasses_ownership(self, admin_user):
        """EA_Admin should bypass all ownership checks."""
        db = make_mock_db([])  # no DB calls needed
        result = await check_app_ownership(admin_user, "APP001", db)
        assert result is True

    async def test_normal_user_without_app_owner_role_denied(self, normal_user):
        """Normal_User without App_Owner role should be denied even if they
        happen to match an owner field — but in practice the RBAC gate
        would block them first. This tests the ownership function directly."""
        db = make_mock_db([
            MockResult(scalar_value=None),  # cmdb_application — no match
            MockResult(scalar_value=None),  # application_member — no match
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_app_ownership(normal_user, "APP001", db)
        assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# Application owner authorization — application_member.itcode
# ═══════════════════════════════════════════════════════════════════


class TestCheckAppOwnershipViaApplicationMember:
    """App_Owner should be authorized via application_member.itcode match."""

    async def test_member_itcode_match_allowed(self, app_owner_user):
        """User's email_prefix matches application_member.itcode."""
        db = make_mock_db([
            MockResult(scalar_value=None),   # cmdb_application — no match
            MockResult(scalar_value=1),      # application_member — match!
        ])
        result = await check_app_ownership(app_owner_user, "APP002", db)
        assert result is True

    async def test_member_itcode_no_match_denied(self, app_owner_user):
        """Neither cmdb owner fields nor application_member match."""
        db = make_mock_db([
            MockResult(scalar_value=None),   # cmdb_application — no match
            MockResult(scalar_value=None),   # application_member — no match
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_app_ownership(app_owner_user, "APP002", db)
        assert exc_info.value.status_code == 403

    async def test_cmdb_match_takes_priority(self, app_owner_user):
        """If cmdb_application matches, application_member is not checked."""
        db = make_mock_db([
            MockResult(scalar_value=1),  # cmdb_application — match!
            # application_member query should NOT be reached
        ])
        result = await check_app_ownership(app_owner_user, "APP003", db)
        assert result is True

    async def test_empty_email_prefix_skips_member_check(self):
        """User with empty email_prefix should skip application_member check."""
        user = make_user(
            user_id="noemail",
            email="",
            roles=[Role.APP_OWNER],
        )
        db = make_mock_db([
            MockResult(scalar_value=None),  # cmdb_application — no match
            # application_member should NOT be queried (email_prefix is empty)
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_app_ownership(user, "APP004", db)
        assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# Project ownership authorization
# ═══════════════════════════════════════════════════════════════════


class TestCheckProjectOwnership:
    """Project_Owner is determined by pm_itcode, dt_lead_itcode, or it_lead_itcode."""

    async def test_pm_can_access_project(self, normal_user):
        db = make_mock_db([
            MockResult(rows=[{
                "project_id": "P250001",
                "pm_itcode": "user01",
                "dt_lead_itcode": "other1",
                "it_lead_itcode": "other2",
            }]),
        ])
        result = await check_project_ownership(normal_user, "P250001", db)
        assert result["project_id"] == "P250001"

    async def test_dt_lead_can_access_project(self, normal_user):
        db = make_mock_db([
            MockResult(rows=[{
                "project_id": "P250001",
                "pm_itcode": "other1",
                "dt_lead_itcode": "user01",
                "it_lead_itcode": "other2",
            }]),
        ])
        result = await check_project_ownership(normal_user, "P250001", db)
        assert result["project_id"] == "P250001"

    async def test_it_lead_can_access_project(self, normal_user):
        db = make_mock_db([
            MockResult(rows=[{
                "project_id": "P250001",
                "pm_itcode": "other1",
                "dt_lead_itcode": "other2",
                "it_lead_itcode": "user01",
            }]),
        ])
        result = await check_project_ownership(normal_user, "P250001", db)
        assert result["project_id"] == "P250001"

    async def test_non_owner_denied(self, other_user):
        db = make_mock_db([
            MockResult(rows=[{
                "project_id": "P250001",
                "pm_itcode": "user01",
                "dt_lead_itcode": "user02",
                "it_lead_itcode": "user03",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_project_ownership(other_user, "P250001", db)
        assert exc_info.value.status_code == 403
        assert "ownership" in exc_info.value.detail.lower()

    async def test_admin_bypasses_ownership(self, admin_user):
        db = make_mock_db([
            MockResult(rows=[{
                "project_id": "P250001",
                "pm_itcode": "someone",
                "dt_lead_itcode": "someone",
                "it_lead_itcode": "someone",
            }]),
        ])
        result = await check_project_ownership(admin_user, "P250001", db)
        assert result["project_id"] == "P250001"

    async def test_reviewer_bypasses_ownership(self, reviewer_user):
        """EA_Reviewer can modify any project (no record-level scoping per matrix)."""
        db = make_mock_db([
            MockResult(rows=[{
                "project_id": "P250001",
                "pm_itcode": "someone",
                "dt_lead_itcode": "someone",
                "it_lead_itcode": "someone",
            }]),
        ])
        result = await check_project_ownership(reviewer_user, "P250001", db)
        assert result["project_id"] == "P250001"

    async def test_nonexistent_project_gets_404(self, normal_user):
        db = make_mock_db([MockResult(rows=[])])
        with pytest.raises(HTTPException) as exc_info:
            await check_project_ownership(normal_user, "P999999", db)
        assert exc_info.value.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# get_owned_app_ids
# ═══════════════════════════════════════════════════════════════════


class TestGetOwnedAppIds:
    """get_owned_app_ids should return all apps the user owns."""

    async def test_admin_returns_empty(self, admin_user):
        """Admin gets empty list — caller should skip filtering."""
        db = make_mock_db([])
        result = await get_owned_app_ids(admin_user, db)
        assert result == []

    async def test_owner_gets_cmdb_apps(self, app_owner_user):
        db = make_mock_db([
            MockResult(rows=[{"app_id": "APP001"}, {"app_id": "APP002"}]),  # cmdb
            MockResult(rows=[]),  # application_member
        ])
        result = await get_owned_app_ids(app_owner_user, db)
        assert result == ["APP001", "APP002"]

    async def test_owner_gets_member_apps(self, app_owner_user):
        db = make_mock_db([
            MockResult(rows=[]),  # cmdb — none
            MockResult(rows=[{"app_id": "APP003"}]),  # application_member
        ])
        result = await get_owned_app_ids(app_owner_user, db)
        assert result == ["APP003"]

    async def test_owner_gets_merged_deduped_apps(self, app_owner_user):
        db = make_mock_db([
            MockResult(rows=[{"app_id": "APP001"}, {"app_id": "APP002"}]),
            MockResult(rows=[{"app_id": "APP002"}, {"app_id": "APP003"}]),
        ])
        result = await get_owned_app_ids(app_owner_user, db)
        assert result == ["APP001", "APP002", "APP003"]

    async def test_no_ownership_returns_empty(self, app_owner_user):
        db = make_mock_db([
            MockResult(rows=[]),
            MockResult(rows=[]),
        ])
        result = await get_owned_app_ids(app_owner_user, db)
        assert result == []


# ═══════════════════════════════════════════════════════════════════
# check_request_access_by_project
# ═══════════════════════════════════════════════════════════════════


class TestCheckRequestAccessByProject:
    """Write access to EA review sub-resources by project_id."""

    async def test_admin_bypasses(self, admin_user):
        db = make_mock_db([])
        await check_request_access_by_project(admin_user, "PROJ001", db)

    async def test_reviewer_bypasses(self, reviewer_user):
        """EA_Reviewer can access any project's sub-resources without assignment."""
        db = make_mock_db([])
        await check_request_access_by_project(reviewer_user, "PROJ001", db)

    async def test_requester_allowed(self, normal_user):
        """User who is the requester of a request in this project gets access."""
        db = make_mock_db([
            MockResult(scalar_value=1),  # user is requester of a request in this project
        ])
        await check_request_access_by_project(normal_user, "PROJ001", db)

    async def test_unrelated_user_denied(self, other_user):
        db = make_mock_db([
            MockResult(scalar_value=None),  # not requester of any request in project
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_request_access_by_project(other_user, "PROJ001", db)
        assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# check_request_access_by_request_id
# ═══════════════════════════════════════════════════════════════════


class TestCheckRequestAccessByRequestId:
    """Write access to EA review sub-resources by request business key."""

    async def test_admin_bypasses(self, admin_user):
        db = make_mock_db([])
        await check_request_access_by_request_id(admin_user, "EA250001", db)

    async def test_reviewer_bypasses(self, reviewer_user):
        """EA_Reviewer can access any request's sub-resources without assignment."""
        db = make_mock_db([])
        await check_request_access_by_request_id(reviewer_user, "EA250001", db)

    async def test_requester_allowed(self, normal_user):
        """User who is the requester gets access."""
        db = make_mock_db([
            MockResult(rows=[{
                "requester": "user01",
            }]),
        ])
        await check_request_access_by_request_id(normal_user, "EA250001", db)

    async def test_nonexistent_request_gets_404(self, normal_user):
        db = make_mock_db([MockResult(rows=[])])
        with pytest.raises(HTTPException) as exc_info:
            await check_request_access_by_request_id(normal_user, "EA999999", db)
        assert exc_info.value.status_code == 404

    async def test_unrelated_user_denied(self, other_user):
        db = make_mock_db([
            MockResult(rows=[{
                "requester": "user01",
            }]),
        ])
        with pytest.raises(HTTPException) as exc_info:
            await check_request_access_by_request_id(other_user, "EA250001", db)
        assert exc_info.value.status_code == 403
