"""Response envelope contract tests.

These tests validate the backend's unified JSON envelope and ensure that
bypassed endpoints (CSV export) remain unwrapped.
"""

import pytest

from helpers.enveloped_client import is_envelope


@pytest.mark.readonly
def test_health_returns_envelope_shape(unauthenticated_client):
    resp = unauthenticated_client.get("/api/health")
    assert resp.status_code == 200

    body = resp.json()
    assert is_envelope(body)
    assert body["code"] == 200
    assert isinstance(body["message"], str)
    assert isinstance(body["timestamp"], int)

    data = body["data"]
    assert isinstance(data, dict)
    assert data.get("status") == "ok"


@pytest.mark.readonly
def test_export_bypass_is_raw_csv_or_enveloped_error(client):
    resp = client.get("/api/export/projects")

    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        assert content_type.startswith("text/csv")
        assert "content-disposition" in {k.lower() for k in resp.headers.keys()}
        return

    # If export isn't allowed in this environment, it should still be JSON envelope.
    if resp.status_code in (401, 403, 404):
        content_type = resp.headers.get("content-type", "")
        assert content_type.startswith("application/json")
        body = resp.json()
        assert is_envelope(body)
        assert body["code"] == resp.status_code
        return

    pytest.fail(f"Unexpected export status_code={resp.status_code}")


@pytest.mark.readonly
def test_404_returns_envelope(unauthenticated_client):
    resp = unauthenticated_client.get("/api/__does_not_exist__")
    assert resp.status_code == 404
    body = resp.json()
    assert is_envelope(body)
    assert body["code"] == 404


@pytest.mark.readonly
def test_405_returns_envelope(unauthenticated_client):
    resp = unauthenticated_client.post("/api/health")
    assert resp.status_code == 405
    body = resp.json()
    assert is_envelope(body)
    assert body["code"] == 405


@pytest.mark.readonly
def test_validation_errors_map_to_400_when_reachable(client):
    # This should trigger FastAPI's RequestValidationError (422) which we map to HTTP 400.
    resp = client.get("/api/projects", params={"page": "not-an-int"})

    if resp.status_code == 400:
        body = resp.json()
        assert is_envelope(body)
        assert body["code"] == 400
        assert body["data"] is not None
        return

    # In environments where auth is enforced and the test client isn't authenticated,
    # this endpoint may be unreachable. Still assert envelope when possible.
    if resp.status_code in (401, 403):
        body = resp.json()
        assert is_envelope(body)
        assert body["code"] == resp.status_code
        pytest.skip("Endpoint requires auth/permission in this environment")

    pytest.fail(f"Unexpected status_code={resp.status_code}")
