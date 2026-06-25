"""Tests for certifications router."""
from __future__ import annotations

from datetime import date, datetime
from .conftest import make_client, reset_overrides, FakeResult


_CERT_ROW = {
    "id": 1, "cert_id": "CERT001", "cert_name": "AWS Solutions Architect",
    "cert_type": "Cloud", "vendor": "AWS", "level": "Associate",
    "holder": "user01", "holder_name": "Alice",
    "issue_date": date(2024, 6, 1), "expiry_date": date(2026, 6, 1),
    "cert_no": "ABC123", "status": "Active",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2), "image_path": None, "pdf_path": None,
    "description": None, "domain": "Cloud",
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


class TestListCertifications:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_CERT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/certifications")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_status_filter(self):
        client = make_client(
            FakeResult([_CERT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/certifications?status=Active")
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
        resp = client.get("/api/certifications")
        assert resp.status_code == 500
        reset_overrides()


class TestGetCertification:
    def test_returns_cert(self):
        client = make_client(FakeResult([_CERT_ROW]))
        resp = client.get("/api/certifications/CERT001")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/certifications/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()


class TestCreateCertification:
    def test_creates_cert(self):
        client = make_client(FakeResult([_CERT_ROW]))
        resp = client.post("/api/certifications", json={
            "certName": "AWS SA", "certType": "Cloud", "holder": "user01",
            "issueDate": "2024-06-01", "expiryDate": "2026-06-01",
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
        resp = client.post("/api/certifications", json={"certName": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateCertification:
    def test_updates_cert(self):
        client = make_client(
            FakeResult([_CERT_ROW]),  # get existing
            FakeResult([_CERT_ROW]),  # update result
        )
        resp = client.put("/api/certifications/CERT001", json={"status": "Expired"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/certifications/NONEXISTENT", json={"status": "Expired"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteCertification:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/certifications/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_cert(self):
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
            get_r.mappings.return_value.first.return_value = _CERT_ROW
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
        resp = client.delete("/api/certifications/CERT001")
        assert resp.status_code == 200
        reset_overrides()


class TestTemplateDownload:
    def test_returns_template(self):
        client = make_client()
        resp = client.get("/api/certifications/template/download")
        assert resp.status_code == 200
        reset_overrides()


class TestImportValidate:
    def test_validates_import_file(self):
        client = make_client(FakeResult([]))
        csv_content = b"certName,certType,holder,issueDate,expiryDate\n"
        resp = client.post(
            "/api/certifications/import/validate",
            files={"file": ("certs.csv", csv_content, "text/csv")},
        )
        assert resp.status_code in (200, 422)
        reset_overrides()


class TestExportCertifications:
    def test_export_returns_data(self):
        client = make_client(FakeResult([_CERT_ROW]))
        resp = client.post("/api/certifications/export", json={})
        assert resp.status_code == 200
        reset_overrides()
