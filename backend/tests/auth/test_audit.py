"""Tests for audit logging functions.

Verifies that audit_allow and audit_deny produce the expected log records
with the correct level, message format, and parameters.
"""
import logging

from app.auth.models import AuthUser, Role
from app.auth.audit import audit_allow, audit_deny
from tests.conftest import make_user


class TestAuditAllow:
    """audit_allow should emit INFO-level AUTHZ_ALLOW log entries."""

    def test_logs_at_info_level(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.INFO, logger="eam.auth.audit"):
            audit_allow(
                user=user,
                action="create",
                resource_type="ea_request",
                resource_id="EA250001",
            )
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_log_contains_allow_marker(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.INFO, logger="eam.auth.audit"):
            audit_allow(
                user=user,
                action="create",
                resource_type="ea_request",
            )
        assert "AUTHZ_ALLOW" in caplog.records[0].message

    def test_log_contains_user_id(self, caplog):
        user = make_user(user_id="alice", roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.INFO, logger="eam.auth.audit"):
            audit_allow(
                user=user,
                action="update",
                resource_type="ea_request",
                resource_id="EA250002",
            )
        assert "alice" in caplog.records[0].message

    def test_log_contains_action_and_resource(self, caplog):
        user = make_user(roles=[Role.EA_ADMIN])
        with caplog.at_level(logging.INFO, logger="eam.auth.audit"):
            audit_allow(
                user=user,
                action="delete",
                resource_type="bcm",
                resource_id="BCM-123",
                scope_basis="app_owner",
            )
        record = caplog.records[0].message
        assert "delete" in record
        assert "bcm" in record
        assert "BCM-123" in record
        assert "app_owner" in record

    def test_default_scope_basis_is_baseline(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.INFO, logger="eam.auth.audit"):
            audit_allow(
                user=user,
                action="create",
                resource_type="ea_request",
            )
        assert "baseline" in caplog.records[0].message

    def test_default_resource_id_is_dash(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.INFO, logger="eam.auth.audit"):
            audit_allow(
                user=user,
                action="create",
                resource_type="ea_request",
            )
        # resource_id defaults to "-" when None
        assert " - " in caplog.records[0].message or "=-" in caplog.records[0].message


class TestAuditDeny:
    """audit_deny should emit WARNING-level AUTHZ_DENY log entries."""

    def test_logs_at_warning_level(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.WARNING, logger="eam.auth.audit"):
            audit_deny(
                user=user,
                action="delete",
                resource_type="ea_request",
                resource_id="EA250003",
                reason="not_creator",
            )
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.WARNING

    def test_log_contains_deny_marker(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.WARNING, logger="eam.auth.audit"):
            audit_deny(
                user=user,
                action="update",
                resource_type="ea_request",
            )
        assert "AUTHZ_DENY" in caplog.records[0].message

    def test_log_contains_reason(self, caplog):
        user = make_user(user_id="mallory", roles=[Role.NORMAL_USER])
        with caplog.at_level(logging.WARNING, logger="eam.auth.audit"):
            audit_deny(
                user=user,
                action="delete",
                resource_type="ea_request",
                resource_id="EA250099",
                reason="not_creator",
            )
        record = caplog.records[0].message
        assert "mallory" in record
        assert "not_creator" in record
        assert "EA250099" in record

    def test_log_contains_roles(self, caplog):
        user = make_user(roles=[Role.NORMAL_USER, Role.APP_OWNER])
        with caplog.at_level(logging.WARNING, logger="eam.auth.audit"):
            audit_deny(
                user=user,
                action="write",
                resource_type="bcm",
            )
        record = caplog.records[0].message
        assert "normal_user" in record
        assert "app_owner" in record
