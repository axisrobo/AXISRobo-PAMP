"""Auth endpoint tests — /api/auth/*."""
import pytest


@pytest.mark.readonly
class TestAuthMe:
    """GET /api/auth/me."""

    def test_returns_user_info(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert "id" in body
        assert "name" in body
        assert "email" in body
        assert "role" in body
        assert "permissions" in body

    def test_dev_mode_returns_admin(self, client):
        """In dev mode (AUTH_DISABLED=True), default user is admin."""
        resp = client.get("/api/auth/me")
        body = resp.json()
        assert body["id"] == "dev_admin"
        assert body["role"] == "admin"
        assert isinstance(body["permissions"], list)
        assert len(body["permissions"]) > 0


@pytest.mark.readonly
class TestAuthPermissions:
    """GET /api/auth/permissions."""

    def test_returns_permissions(self, client):
        resp = client.get("/api/auth/permissions")
        assert resp.status_code == 200
        body = resp.json()
        assert "role" in body
        assert "permissions" in body
        assert isinstance(body["permissions"], list)

    def test_admin_has_wildcard(self, client):
        """Admin role should have wildcard permissions."""
        resp = client.get("/api/auth/permissions")
        body = resp.json()
        assert body["role"] == "admin"
        assert "*:*" in body["permissions"]
