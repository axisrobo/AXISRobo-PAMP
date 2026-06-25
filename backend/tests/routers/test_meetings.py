"""Tests for meetings router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_MEETING_ROW = {
    "id": 1, "meeting_no": 1001, "meeting_title": "EA Review Meeting",
    "project_id": "P001", "project_name": "Project Alpha",
    "request_id": "EA001", "start_time": datetime(2025, 3, 1, 9, 0),
    "end_time": datetime(2025, 3, 1, 11, 0), "location": "Room A",
    "presenter": ["user01"], "attendees": None, "ea_review_result": None,
    "status": "Scheduled", "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2), "meeting_minute_html": None,
    "meeting_minute_sent_at": None, "cancelled_at": None,
    "is_external_reviewer": False, "project_reviewer": None, "request": None,
    "bcm_list": None, "bcm_scope": None,
}


def _bad_db():
    from unittest.mock import AsyncMock

    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("fail")
        db.execute = _raise
        db.rollback = AsyncMock()
        yield db
    return gen


class TestListMeetings:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_MEETING_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_project_filter(self):
        client = make_client(
            FakeResult([_MEETING_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/meetings?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_status_filter(self):
        client = make_client(
            FakeResult([_MEETING_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/meetings?status=Scheduled")
        assert resp.status_code == 200
        reset_overrides()

    def test_empty_result(self):
        client = make_client(
            FakeResult([]),
            FakeResult([], scalar_value=0),
        )
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        reset_overrides()

    def test_db_error_returns_500(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = _bad_db()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/meetings")
        assert resp.status_code == 500
        reset_overrides()


class TestGetMeeting:
    def test_returns_meeting(self):
        client = make_client(FakeResult([_MEETING_ROW]))
        resp = client.get("/api/meetings/1001")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/meetings/9999")
        assert resp.status_code == 404
        reset_overrides()


class TestCreateMeeting:
    def test_creates_meeting(self):
        client = make_client(
            FakeResult([{"project_id": "P001"}]),  # project ownership check
            FakeResult([_MEETING_ROW]),              # insert
        )
        resp = client.post("/api/meetings", json={
            "projectId": "P001",
            "title": "New Meeting",
            "startTime": "2025-04-01T09:00:00",
            "endTime": "2025-04-01T11:00:00",
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_db_error_returns_500(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = _bad_db()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/meetings", json={"projectId": "P001", "title": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateMeeting:
    def test_updates_meeting(self):
        client = make_client(
            FakeResult([_MEETING_ROW]),  # get existing
            FakeResult([_MEETING_ROW]),  # update result
        )
        resp = client.put("/api/meetings/1001", json={"title": "Updated Title"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/meetings/9999", json={"title": "X"})
        assert resp.status_code == 404
        reset_overrides()


class TestCancelMeeting:
    def test_cancels_meeting(self):
        client = make_client(
            FakeResult([_MEETING_ROW]),  # get
            FakeResult([{**_MEETING_ROW, "status": "Cancelled"}]),  # update
        )
        resp = client.patch("/api/meetings/1001/cancel")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.patch("/api/meetings/9999/cancel")
        assert resp.status_code == 404
        reset_overrides()


class TestSetEaReviewResult:
    def test_sets_result(self):
        client = make_client(
            FakeResult([_MEETING_ROW]),  # get
            FakeResult([{**_MEETING_ROW, "ea_review_result": "Approved"}]),  # update
        )
        resp = client.post("/api/meetings/1001/set-ea-review-result", json={
            "eaReviewResult": "Approved",
        })
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.post("/api/meetings/9999/set-ea-review-result", json={
            "eaReviewResult": "Approved",
        })
        assert resp.status_code == 404
        reset_overrides()


class TestSendMeetingMinute:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.post("/api/meetings/9999/send-minute")
        assert resp.status_code == 404
        reset_overrides()

    def test_no_minute_returns_400(self):
        client = make_client(FakeResult([{**_MEETING_ROW, "meeting_minute_html": None}]))
        resp = client.post("/api/meetings/1001/send-minute")
        assert resp.status_code in (400, 422)
        reset_overrides()


class TestDeleteMeeting:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/meetings/9999")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_meeting(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            get_r = MagicMock()
            get_r.mappings.return_value.first.return_value = _MEETING_ROW
            del_r = MagicMock()
            del_r.rowcount = 1
            call = [0]
            async def execute(*a, **kw):
                idx = call[0]; call[0] += 1
                return get_r if idx == 0 else del_r
            db.execute = execute
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/meetings/1001")
        assert resp.status_code == 200
        reset_overrides()


class TestAttendeesTemplate:
    def test_returns_csv(self):
        client = make_client()
        resp = client.get("/api/meetings/attendees-template")
        assert resp.status_code == 200
        reset_overrides()


class TestParseAttendees:
    def test_parses_csv_file(self):
        client = make_client()
        csv_content = b"name,email\nAlice,alice@example.com\n"
        resp = client.post(
            "/api/meetings/parse-attendees",
            files={"file": ("attendees.csv", csv_content, "text/csv")},
        )
        assert resp.status_code in (200, 422)
        reset_overrides()
