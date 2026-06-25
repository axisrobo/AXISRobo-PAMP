"""Dashboard endpoint tests — Priority 3."""
import pytest


@pytest.mark.readonly
@pytest.mark.priority3
class TestDashboard:
    def test_stats_returns_expected_keys(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        body = resp.json()
        expected = [
            "totalProjects", "inProgress", "completed",
            "meetings", "actions", "pending",
            "scopeCheck", "scopeOfChange",
        ]
        for key in expected:
            assert key in body, f"Missing key: {key}"
            assert isinstance(body[key], int), f"{key} should be int, got {type(body[key])}"

    def test_stats_values_non_negative(self, client):
        body = client.get("/api/dashboard/stats").json()
        for key, val in body.items():
            if isinstance(val, int):
                assert val >= 0, f"{key} is negative: {val}"

    def test_home_stats_returns_expected_keys(self, client):
        resp = client.get("/api/dashboard/home-stats")
        assert resp.status_code == 200
        body = resp.json()
        expected = ["myProjects", "myRequests", "myActions", "requestQueue"]
        for key in expected:
            assert key in body, f"Missing key: {key}"
            assert isinstance(body[key], int)

    def test_home_stats_values_non_negative(self, client):
        body = client.get("/api/dashboard/home-stats").json()
        for key, val in body.items():
            if isinstance(val, int):
                assert val >= 0
