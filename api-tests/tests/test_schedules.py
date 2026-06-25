"""Schedules endpoint tests — Priority 2."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


@pytest.mark.readonly
@pytest.mark.priority2
class TestSchedulesList:
    def test_list_paginated(self, client):
        resp = client.get("/api/schedules")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_has_stats(self, client):
        resp = client.get("/api/schedules")
        body = resp.json()
        assert "stats" in body
        stats = body["stats"]
        for key in ["total", "available", "booked", "expired", "completed"]:
            assert key in stats, f"Missing stats key: {key}"

    def test_pagination_params(self, client):
        resp = client.get("/api/schedules", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_filter_status(self, client):
        resp = client.get("/api/schedules", params={"status": "Available"})
        assert resp.status_code == 200

    def test_filter_timeFrom(self, client):
        resp = client.get("/api/schedules", params={"timeFrom": "2024-01-01"})
        assert resp.status_code == 200

    def test_sort_by_startTime(self, client):
        resp = client.get("/api/schedules", params={
            "sortField": "startTime", "sortOrder": "desc"
        })
        assert resp.status_code == 200

    def test_empty_filter(self, client):
        resp = client.get("/api/schedules", params={"status": "NONEXISTENT"})
        body = resp.json()
        assert body["total"] == 0


@pytest.mark.write
@pytest.mark.priority2
class TestSchedulesCRUD:
    def test_create_and_delete(self, client):
        create_data = {
            "scheduleTitle": "__API_TEST_SCHEDULE__",
            "startTime": "2099-01-01T09:00:00.000Z",
            "endTime": "2099-01-01T10:00:00.000Z",
            "duration": 60,
            "owner": ["TESTUSER"],
            "remark": "API test schedule",
        }
        resp = client.post("/api/schedules", json=create_data)
        assert resp.status_code == 201
        created = resp.json()
        assert isinstance(created, list)
        assert len(created) >= 1

        # Delete (only Available status can be deleted)
        schedule_id = created[0]["id"]
        del_resp = client.delete(f"/api/schedules/{schedule_id}")
        assert del_resp.status_code == 200

    def test_create_with_recurrence(self, client):
        create_data = {
            "scheduleTitle": "__API_TEST_RECURRING__",
            "startTime": "2099-02-01T09:00:00.000Z",
            "endTime": "2099-02-01T10:00:00.000Z",
            "duration": 60,
            "recurrencePattern": "Weekly",
            "endAfter": 3,
            "owner": ["TESTUSER"],
        }
        resp = client.post("/api/schedules", json=create_data)
        assert resp.status_code == 201
        created = resp.json()
        assert isinstance(created, list)
        assert len(created) == 3  # 3 weekly occurrences

        # Cleanup
        for s in created:
            client.delete(f"/api/schedules/{s['id']}")
