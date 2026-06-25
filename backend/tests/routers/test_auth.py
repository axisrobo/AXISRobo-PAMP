"""Tests for auth router — GET /api/auth/me and /api/auth/permissions."""
from __future__ import annotations

import pytest
from .conftest import make_client, reset_overrides, ADMIN_USER, FakeResult


class TestAuthMe:
    def setup_method(self):
        self.client = make_client()

    def teardown_method(self):
        reset_overrides()

    def test_me_returns_user_info(self):
        resp = self.client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["id"] == ADMIN_USER.id

    def test_me_contains_roles(self):
        resp = self.client.get("/api/auth/me")
        data = resp.json().get("data") or resp.json()
        assert "roles" in data
        assert "ea_admin" in data["roles"]

    def test_me_contains_permissions(self):
        resp = self.client.get("/api/auth/me")
        data = resp.json().get("data") or resp.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)

    def test_me_backward_compat_role_field(self):
        resp = self.client.get("/api/auth/me")
        data = resp.json().get("data") or resp.json()
        assert "role" in data
        assert data["role"] == "ea_admin"


class TestAuthPermissions:
    def setup_method(self):
        self.client = make_client()

    def teardown_method(self):
        reset_overrides()

    def test_permissions_returns_list(self):
        resp = self.client.get("/api/auth/permissions")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)
