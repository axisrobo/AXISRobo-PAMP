"""Meetings endpoint tests — Priority 2."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


MEETING_KEYS = ["id", "meetingNo", "title", "projectId", "status", "startTime", "endTime"]


@pytest.mark.readonly
@pytest.mark.priority2
class TestMeetingsList:
    def test_list_paginated(self, client):
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_pagination_params(self, client):
        resp = client.get("/api/meetings", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_item_keys(self, client):
        resp = client.get("/api/meetings", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No meetings")
        assert_has_keys(body["data"][0], MEETING_KEYS, "meeting")

    def test_filter_title(self, client):
        resp = client.get("/api/meetings", params={"title": "review"})
        assert resp.status_code == 200

    def test_filter_status(self, client):
        resp = client.get("/api/meetings", params={"status": "Scheduled"})
        assert resp.status_code == 200

    def test_filter_requestId(self, client):
        resp = client.get("/api/meetings", params={"requestId": "EA"})
        assert resp.status_code == 200

    def test_filter_projectId(self, client):
        sample = client.get("/api/meetings", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No meetings")
        pid = sample["data"][0].get("projectId", "")
        if not pid:
            pytest.skip("No projectId")
        resp = client.get("/api/meetings", params={"projectId": pid})
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_sort_by_startTime(self, client):
        resp = client.get("/api/meetings", params={
            "sortField": "startTime", "sortOrder": "desc"
        })
        assert resp.status_code == 200

    def test_empty_result(self, client):
        resp = client.get("/api/meetings", params={"projectId": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


@pytest.mark.readonly
@pytest.mark.priority2
class TestMeetingsDetail:
    def test_get_by_meetingNo(self, client):
        sample = client.get("/api/meetings", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No meetings")
        meeting_no = sample["data"][0]["meetingNo"]
        resp = client.get(f"/api/meetings/{meeting_no}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["meetingNo"] == meeting_no

    def test_get_not_found(self, client):
        resp = client.get("/api/meetings/999999")
        assert resp.status_code in (404, 500)
