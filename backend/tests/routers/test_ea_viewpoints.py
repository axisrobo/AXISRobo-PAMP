"""Tests for the EA request viewpoints endpoint (concern -> viewpoint -> artifact)."""
from __future__ import annotations

from .conftest import FakeResult, make_client, reset_overrides


_REQUEST_ROW = {"request_id": "REQ-1", "project_id": "PRJ-1"}

_EVALUATION = {
    "decisions": [
        {"concernKey": "D9", "concernName": "Data Sovereignty", "classification": "Mandatory", "score": 0.9},
        {"concernKey": "B1", "concernName": "Business Capability", "classification": "Recommended", "score": 0.4},
    ],
}

_ASSESSMENT_ROW = {"project_id": "PRJ-1", "evaluation": _EVALUATION}

_JOIN_ROWS = [
    {
        "viewpoint_id": "vp-29",
        "viewpoint_number": 29,
        "layer_name": "Data Architecture",
        "viewpoint_name": "Data Sovereignty View",
        "concern_key": "D9",
        "concern_name": "Data Sovereignty",
        "artifact_name": "Data Compliance Diagram",
        "concern_sort_order": 290,
        "artifact_sort_order": 10,
    },
    {
        "viewpoint_id": "vp-1",
        "viewpoint_number": 1,
        "layer_name": "Business / Organization Layer",
        "viewpoint_name": "Business Capability View",
        "concern_key": "B1",
        "concern_name": "Business Capability",
        "artifact_name": "Business Diagram",
        "concern_sort_order": 10,
        "artifact_sort_order": 10,
    },
]


class TestRequestViewpoints:
    def test_returns_viewpoint_chain(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([_ASSESSMENT_ROW]),
            FakeResult(_JOIN_ROWS),
        )
        resp = client.get("/api/ea-requests/REQ-1/viewpoints")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["projectId"] == "PRJ-1"
        viewpoints = data["viewpoints"]
        assert len(viewpoints) == 2
        # Mandatory viewpoint should sort before the recommended one.
        first = viewpoints[0]
        assert first["viewpointName"] == "Data Sovereignty View"
        assert first["classification"] == "Mandatory"
        assert "Data Compliance Diagram" in first["artifacts"]
        assert first["concerns"][0]["concernKey"] == "D9"
        reset_overrides()

    def test_no_assessment_returns_empty(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([]),
        )
        resp = client.get("/api/ea-requests/REQ-1/viewpoints")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["viewpoints"] == []
        reset_overrides()

    def test_missing_request_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/ea-requests/UNKNOWN/viewpoints")
        assert resp.status_code == 404
        reset_overrides()
