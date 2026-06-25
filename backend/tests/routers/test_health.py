"""Tests for GET /api/health."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok():
    from app.main import app
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    # Envelope wraps the response
    data = body.get("data") or body
    assert data.get("status") == "ok"
