"""Tests for EA request attachments router."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from .conftest import make_client, reset_overrides, FakeResult


_ATTACHMENT_ROW = {
    "id": 1, "attachment_id": "ATT001", "request_id": "EA001",
    "file_name": "design.pdf", "file_type": "application/pdf",
    "biz_type": "App_Arch", "s3_key": "attachments/EA001/design.pdf",
    "file_size": 1024, "uploaded_by": "user01", "uploader_name": "Alice",
    "uploaded_at": datetime(2025, 1, 5), "ai_check_status": None,
    "ai_check_result": None,
}
_REQUEST_ROW = {
    "request_id": "EA001", "status": "Draft",
}


def _bad_db():
    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("fail")
        db.execute = _raise
        db.rollback = AsyncMock()
        yield db
    return gen


class TestListAttachments:
    def test_returns_attachments(self):
        client = make_client(FakeResult([_ATTACHMENT_ROW]))
        resp = client.get("/api/ea-requests/EA001/attachments")
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
        resp = client.get("/api/ea-requests/EA001/attachments")
        assert resp.status_code == 500
        reset_overrides()


class TestUploadAttachment:
    def test_upload_request_not_found(self):
        # DB returns no request row
        client = make_client(FakeResult([]))  # request lookup returns nothing
        resp = client.post(
            "/api/ea-requests/attachments/upload",
            data={"requestId": "NONEXISTENT", "bizType": "App_Arch"},
            files={"file": ("test.pdf", b"content", "application/pdf")},
        )
        assert resp.status_code == 404
        reset_overrides()

    def test_upload_invalid_biz_type(self):
        # DB returns a request row but bizType is invalid
        client = make_client(FakeResult([_REQUEST_ROW]))
        resp = client.post(
            "/api/ea-requests/attachments/upload",
            data={"requestId": "EA001", "bizType": "InvalidType"},
            files={"file": ("test.pdf", b"content", "application/pdf")},
        )
        assert resp.status_code == 400
        reset_overrides()


class TestDeleteAttachment:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/ea-requests/attachments/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_attachment(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            get_r = MagicMock()
            get_r.mappings.return_value.first.return_value = {
                **_ATTACHMENT_ROW, "request_status": "Draft"
            }
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
        with patch("app.architecture_review.attachments.s3_delete", new=AsyncMock()):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.delete("/api/ea-requests/attachments/ATT001")
        assert resp.status_code == 200
        reset_overrides()


class TestPresignAttachment:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/ea-requests/attachments/NONEXISTENT/presign")
        assert resp.status_code == 404
        reset_overrides()
