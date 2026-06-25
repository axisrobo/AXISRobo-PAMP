"""Tests for actions router."""
from __future__ import annotations

from datetime import date, datetime
from .conftest import make_client, reset_overrides, FakeResult


_ACTION_ROW = {
    "id": 1, "action_no": 1, "action_title": "Fix Issue",
    "project_id": "P001", "meeting_id": None,
    "priority": "High", "due_date": date(2025, 3, 31),
    "close_date": None, "start_date": date(2025, 1, 1),
    "open_date": date(2025, 1, 1), "assignee": "user01",
    "assignee_name": "Alice", "action_description": "Fix something",
    "status": "Open", "type": "Action",
    "requested_by": "user02", "requested_by_name": "Bob",
    "action_updates": None, "applicable_domain": "EA",
    "create_at": datetime(2025, 1, 1), "update_at": datetime(2025, 1, 2),
    "create_by": "admin", "request_id": "EA001",
}
_COMMENT_ROW = {
    "id": "uuid-1", "object_type": "action", "object_id": "1",
    "content": "Comment", "create_by": "user01",
    "create_by_name": "Alice", "create_at": datetime(2025, 1, 5),
}
_AUDIT_ROW = {
    "id": 1, "object_type": "action", "object_id": "1",
    "field": "status", "old_value": "Open", "new_value": "Closed",
    "create_by": "admin", "create_time": datetime(2025, 1, 10), "project_id": "P001",
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


class TestListActions:
    def test_returns_paginated(self):
        # list endpoint needs: data, count, open_count, validation_count, closed_count
        client = make_client(
            FakeResult([]),              # data (empty → no enrichment queries)
            FakeResult([], scalar_value=0),  # count
            FakeResult([], scalar_value=0),  # open
            FakeResult([], scalar_value=0),  # in validation
            FakeResult([], scalar_value=0),  # closed
        )
        resp = client.get("/api/actions")
        assert resp.status_code == 200
        reset_overrides()

    def test_project_filter(self):
        client = make_client(
            FakeResult([]),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
        )
        resp = client.get("/api/actions?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_status_filter(self):
        client = make_client(
            FakeResult([]),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
        )
        resp = client.get("/api/actions?status=Open")
        assert resp.status_code == 200
        reset_overrides()

    def test_request_id_filter(self):
        client = make_client(
            FakeResult([]),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
            FakeResult([], scalar_value=0),
        )
        resp = client.get("/api/actions?requestId=EA001")
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
        resp = client.get("/api/actions")
        assert resp.status_code == 500
        reset_overrides()


class TestGetAction:
    def test_returns_action(self):
        # get_action needs: action row, project row, request row (project_id="P001")
        client = make_client(
            FakeResult([_ACTION_ROW]),
            FakeResult([{"project_name": "Alpha"}]),
            FakeResult([{"request_id": "EA001"}]),
        )
        resp = client.get("/api/actions/1")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/actions/999")
        assert resp.status_code == 404
        reset_overrides()


class TestActionComments:
    def test_list_comments(self):
        # First call gets action row, second call gets comments
        client = make_client(FakeResult([_ACTION_ROW]), FakeResult([_COMMENT_ROW]))
        resp = client.get("/api/actions/1/comments")
        assert resp.status_code == 200
        reset_overrides()

    def test_list_comments_action_not_found(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/actions/999/comments")
        assert resp.status_code == 404
        reset_overrides()

    def test_add_comment(self):
        # First call: get action; second call: insert comment; no extra ownership call since admin
        client = make_client(FakeResult([_ACTION_ROW]), FakeResult([_COMMENT_ROW]))
        resp = client.post("/api/actions/1/comments", json={"content": "New comment"})
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_add_comment_action_not_found(self):
        client = make_client(FakeResult([]))
        resp = client.post("/api/actions/999/comments", json={"content": "X"})
        assert resp.status_code == 404
        reset_overrides()


class TestActionAuditLogs:
    def test_list_audit_logs(self):
        # audit-logs needs: action row (get), data rows, count
        client = make_client(
            FakeResult([_ACTION_ROW]),         # action lookup
            FakeResult([_AUDIT_ROW]),          # audit data
            FakeResult([], scalar_value=1),    # total count
        )
        resp = client.get("/api/actions/1/audit-logs")
        assert resp.status_code == 200
        reset_overrides()

    def test_action_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/actions/9999/audit-logs")
        assert resp.status_code == 404
        reset_overrides()


class TestCreateAction:
    def test_creates_action(self):
        # Admin bypasses ownership check; just needs the insert result
        client = make_client(
            FakeResult([_ACTION_ROW]),  # insert result
        )
        resp = client.post("/api/actions", json={
            "projectId": "P001",
            "actionTitle": "New Action",
            "priority": "High",
            "type": "Action",
            "requestedBy": "user01",
            "requestedByName": "Alice",
            "applicableDomain": "EA",
            "actionDescription": "Fix something",
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_missing_required_fields_returns_400(self):
        client = make_client()
        resp = client.post("/api/actions", json={"projectId": "P001"})
        assert resp.status_code == 400
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
        resp = client.post("/api/actions", json={
            "projectId": "P001", "actionTitle": "T", "priority": "High",
            "type": "Action", "requestedBy": "u", "requestedByName": "N",
            "applicableDomain": "EA", "actionDescription": "x",
        })
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateAction:
    def test_updates_action(self):
        client = make_client(
            FakeResult([_ACTION_ROW]),  # get action
            FakeResult([_ACTION_ROW]),  # update
        )
        resp = client.put("/api/actions/1", json={"status": "Closed"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/actions/999", json={"status": "Closed"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteAction:
    def test_deletes_action(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            get_result = MagicMock()
            get_result.mappings.return_value.first.return_value = {"project_id": "P001", **_ACTION_ROW}
            del_result = MagicMock()
            del_result.rowcount = 1
            call = [0]
            async def execute(*a, **kw):
                idx = call[0]; call[0] += 1
                return get_result if idx == 0 else del_result
            db.execute = execute
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/actions/1")
        assert resp.status_code == 200
        reset_overrides()
