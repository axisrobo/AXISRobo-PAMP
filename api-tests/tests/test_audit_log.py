"""Audit Log, Process Log, Email Log endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated


@pytest.mark.readonly
@pytest.mark.priority3
class TestAuditLog:
    def test_list_paginated(self, client):
        resp = client.get("/api/audit-log")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_filter_projectId(self, client):
        resp = client.get("/api/audit-log", params={"projectId": "P001"})
        assert resp.status_code == 200

    def test_filter_objectType(self, client):
        resp = client.get("/api/audit-log", params={"objectType": "project"})
        assert resp.status_code == 200

    def test_filter_createBy(self, client):
        resp = client.get("/api/audit-log", params={"createBy": "admin"})
        assert resp.status_code == 200

    def test_pagination_size(self, client):
        resp = client.get("/api/audit-log", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5


@pytest.mark.readonly
@pytest.mark.priority3
class TestProcessLogs:
    def test_list_returns_array(self, client):
        resp = client.get("/api/process-logs")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_filter_requestId(self, client):
        resp = client.get("/api/process-logs", params={"requestId": "EA250001"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.readonly
@pytest.mark.priority3
class TestEmailLogs:
    def test_action_email_logs(self, client):
        resp = client.get("/api/email-logs/actions")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_meeting_email_logs(self, client):
        resp = client.get("/api/email-logs/meetings")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)
