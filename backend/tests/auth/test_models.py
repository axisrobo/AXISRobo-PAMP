"""Tests for AuthUser model properties and helpers."""
from app.auth.models import AuthUser, Role
from tests.conftest import make_user


class TestAuthUserProperties:
    """Test computed properties on AuthUser."""

    def test_is_admin_true(self):
        user = make_user(roles=[Role.EA_ADMIN])
        assert user.is_admin is True

    def test_is_admin_false_for_normal(self):
        user = make_user(roles=[Role.NORMAL_USER])
        assert user.is_admin is False

    def test_is_reviewer_true(self):
        user = make_user(roles=[Role.EA_REVIEWER])
        assert user.is_reviewer is True

    def test_is_reviewer_false_for_normal(self):
        user = make_user(roles=[Role.NORMAL_USER])
        assert user.is_reviewer is False

    def test_is_app_owner_true(self):
        user = make_user(roles=[Role.APP_OWNER])
        assert user.is_app_owner is True

    def test_is_app_owner_false_for_normal(self):
        user = make_user(roles=[Role.NORMAL_USER])
        assert user.is_app_owner is False

    def test_has_role(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_REVIEWER])
        assert user.has_role(Role.EA_REVIEWER) is True
        assert user.has_role(Role.NORMAL_USER) is True
        assert user.has_role(Role.EA_ADMIN) is False

    def test_email_prefix_computed(self):
        user = make_user(email="John.Doe@example.com")
        assert user.email_prefix == "john.doe"

    def test_is_project_owner_true(self):
        user = make_user(roles=[Role.PROJECT_OWNER])
        assert user.is_project_owner is True

    def test_is_project_owner_false_for_normal(self):
        user = make_user(roles=[Role.NORMAL_USER])
        assert user.is_project_owner is False

    def test_permissions_populated(self):
        user = make_user(roles=[Role.NORMAL_USER])
        assert "ea_request:read" in user.permissions
        assert "ea_request:write" in user.permissions

    def test_normal_user_includes_meeting_read(self):
        user = make_user(roles=[Role.NORMAL_USER])
        assert "meeting:read" in user.permissions
        assert "meeting_deck:read" in user.permissions
        assert "meeting:write" not in user.permissions

    def test_multi_role_user_has_merged_permissions(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.APP_OWNER])
        assert "bcm:write" in user.permissions
        assert "ea_request:write" in user.permissions
