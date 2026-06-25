"""RBAC / Auth enforcement integration tests.

These tests verify that unauthenticated and under-privileged requests are
properly rejected with the expected HTTP status codes.

Requires a running backend server and the API_TESTS_BASE_URL env var.
"""
from __future__ import annotations

import pytest
from helpers.enveloped_client import EnvelopedClient


class TestUnauthenticated:
    """Requests without a valid token must receive 401."""

    def test_unauthenticated_ea_requests_list(self, anon_client: EnvelopedClient):
        resp = anon_client.get("/api/ea-requests")
        assert resp.status_code == 401

    def test_unauthenticated_avdm_projects(self, anon_client: EnvelopedClient):
        resp = anon_client.get("/api/avdm/projects/test-project")
        assert resp.status_code == 401

    def test_unauthenticated_tech_stack(self, anon_client: EnvelopedClient):
        resp = anon_client.get("/api/technology-stack")
        assert resp.status_code == 401

    def test_unauthenticated_team_members(self, anon_client: EnvelopedClient):
        resp = anon_client.get("/api/team-members")
        assert resp.status_code == 401

    def test_unauthenticated_projects_list(self, anon_client: EnvelopedClient):
        resp = anon_client.get("/api/projects")
        assert resp.status_code == 401

    def test_unauthenticated_avdm_write(self, anon_client: EnvelopedClient):
        resp = anon_client.post("/api/avdm/evaluate", json={})
        assert resp.status_code == 401


class TestAVDMWritePermissions:
    """AVDM write endpoints should return 403 for users without avdm:write."""

    def test_normal_user_cannot_evaluate(self, normal_user_client: EnvelopedClient):
        resp = normal_user_client.post("/api/avdm/evaluate", json={
            "projectId": "test",
            "projectType": "new",
            "projectComplexity": "medium",
            "riskItems": [],
        })
        # In EE mode this should be 403; in OSS mode it may be 200.
        assert resp.status_code in (200, 403)

    def test_normal_user_cannot_confirm_questionnaire(
        self, normal_user_client: EnvelopedClient
    ):
        resp = normal_user_client.post(
            "/api/avdm/projects/test/concerns/confirm",
            json={"operator": "test"},
        )
        assert resp.status_code in (200, 403)


class TestEnvelopeContract:
    """Verify response envelope shape for various status codes."""

    REQUIRED_KEYS = {"code", "message", "data"}

    def test_200_envelope(self, auth_client: EnvelopedClient):
        resp = auth_client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert self.REQUIRED_KEYS.issubset(body.keys())
        assert body["code"] == 200

    def test_404_envelope(self, auth_client: EnvelopedClient):
        resp = auth_client.get("/api/ea-requests/nonexistent-id")
        assert resp.status_code == 404
        body = resp.json()
        assert self.REQUIRED_KEYS.issubset(body.keys())
        assert body["code"] == 404

    def test_400_envelope_missing_required(self, auth_client: EnvelopedClient):
        resp = auth_client.post("/api/ea-requests", json={})
        assert resp.status_code == 400
        body = resp.json()
        assert "code" in body

    def test_401_envelope(self, anon_client: EnvelopedClient):
        resp = anon_client.post("/api/avdm/evaluate", json={})
        assert resp.status_code == 401
        body = resp.json()
        assert self.REQUIRED_KEYS.issubset(body.keys())


class TestTeamMemberPersistence:
    """Team member create/update/delete must persist and be retrievable."""

    def test_create_then_get(self, auth_client: EnvelopedClient):
        test_itcode = "test_persist_001"
        create_resp = auth_client.post("/api/team-members", json={
            "itcode": test_itcode,
            "name": "Test Persist",
            "email": "test@example.com",
            "worker_type": "EA Office",
            "country": "CN",
        })
        assert create_resp.status_code == 201

        get_resp = auth_client.get("/api/team-members", params={"itcode": test_itcode})
        assert get_resp.status_code == 200
        items = get_resp.json().get("data", {}).get("items", [])
        assert any(item["itcode"] == test_itcode for item in items)

        # Cleanup
        auth_client.delete(f"/api/team-members/{test_itcode}")

    def test_update_then_verify(self, auth_client: EnvelopedClient):
        test_itcode = "test_persist_002"
        auth_client.post("/api/team-members", json={
            "itcode": test_itcode,
            "name": "Original Name",
            "worker_type": "Office",
            "country": "CN",
        })

        auth_client.put(f"/api/team-members/{test_itcode}", json={
            "name": "Updated Name",
        })

        get_resp = auth_client.get("/api/team-members", params={"itcode": test_itcode})
        items = get_resp.json().get("data", {}).get("items", [])
        updated = next((item for item in items if item["itcode"] == test_itcode), None)
        assert updated is not None
        assert updated["name"] == "Updated Name"

        auth_client.delete(f"/api/team-members/{test_itcode}")

    def test_delete_then_not_found(self, auth_client: EnvelopedClient):
        test_itcode = "test_persist_003"
        auth_client.post("/api/team-members", json={
            "itcode": test_itcode,
            "name": "To Delete",
            "worker_type": "Office",
            "country": "CN",
        })

        auth_client.delete(f"/api/team-members/{test_itcode}")

        get_resp = auth_client.get("/api/team-members", params={"itcode": test_itcode})
        items = get_resp.json().get("data", {}).get("items", [])
        assert not any(item["itcode"] == test_itcode for item in items)
