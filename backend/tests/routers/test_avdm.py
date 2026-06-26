"""Tests for AVDM workflow status and confirmation endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.add.models import ArtifactRecommendationItem, ArtifactRecommendationResponse
from app.add import routes as avdm_routes

from .conftest import FakeResult, make_client, reset_overrides


_ASSESSMENT_BASE = {
    "id": "11111111-1111-1111-1111-111111111111",
    "project_id": "P-AVDM-1",
    "project_type": "Core",
    "project_complexity": 0.7,
    "questionnaire": {"q1": "yes"},
    "risk_items": [],
    "evaluation": {"projectId": "P-AVDM-1", "decisions": [], "layerSummary": []},
    "review_result": None,
    "artifact_selection": [],
    "needs_avdm": True,
    "judgement_reason": "test",
    "version": 1,
    "status": "questionnaire_submitted",
    "questionnaire_submitted_at": "2026-04-29T10:00:00",
    "questionnaire_confirmed_at": None,
    "concern_requirement_confirmed_at": None,
    "artifact_requirement_confirmed_at": None,
    "artifact_submitted_at": None,
}


class TestAVDMWorkflowStatus:
    def test_returns_request_created_when_no_record(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/avdm/projects/P-AVDM-EMPTY/workflow-status")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["currentStatus"] == "request_created"
        assert data["diagramUploadAllowed"] is False
        reset_overrides()

    def test_status_alias_typo_is_normalized(self):
        typo_record = {**_ASSESSMENT_BASE, "status": "questionnare submited"}
        client = make_client(FakeResult([typo_record]))
        resp = client.get("/api/avdm/projects/P-AVDM-1/workflow-status")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["currentStatus"] == "questionnaire_submitted"
        reset_overrides()


class TestPACTConcernCatalog:
    def test_returns_concern_catalog(self, monkeypatch):
        from app.domain.add.entities import Concern
        from uuid import UUID

        entity = Concern(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            code="B1",
            name="Business Capability View",
            category="Business / Organization",
            description="Capability structure.",
            severity="medium",
            likelihood="medium",
            classification="recommended",
        )

        mock_service_instance = MagicMock()
        mock_service_instance.list_concerns = AsyncMock(return_value=([entity], 1))

        def _mock_service_factory(_repo):
            return mock_service_instance

        monkeypatch.setattr(avdm_routes, "ConcernService", _mock_service_factory)

        client = make_client()
        resp = client.get("/api/avdm/concerns?includeInactive=true")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["items"][0]["concernKey"] == "B1"
        assert data["items"][0]["layer"] == "Business / Organization"
        assert data["items"][0]["concernName"] == "Business Capability View"
        reset_overrides()

    def test_exports_concern_catalog_json_payload(self):
        concern_row = {
            "id": "11111111-1111-1111-1111-111111111111",
            "concern_key": "D9",
            "concern_name": "Data Sovereignty View",
            "layer": "Data Architecture",
            "risk_tags": ["D9", "data", "sovereignty"],
            "description": "Residency constraints.",
            "is_active": True,
            "update_at": None,
            "update_by": "tester",
        }
        client = make_client(FakeResult([concern_row]))
        resp = client.get("/api/avdm/concerns/export")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["catalogName"] == "PACT Concern Catalog"
        assert data["total"] == 1
        assert data["items"][0]["concernKey"] == "D9"
        reset_overrides()


class TestAVDMConfigRoutes:
    @pytest.mark.parametrize(
        ("path", "loader_attr"),
        [
            ("questionnaire-config", "load_questionnaire_config"),
            ("concern-mapping-config", "load_concern_mapping_config"),
            ("artifact-catalog-config", "load_artifact_catalog_config"),
            ("viewpoint-artifact-mapping-config", "load_viewpoint_artifact_mapping_config"),
        ],
    )
    def test_get_config_route_returns_repository_backed_payload(self, monkeypatch, path: str, loader_attr: str):
        load_mock = AsyncMock(return_value={"marker": path})
        metadata_mock = AsyncMock(
            return_value={
                "version": 7,
                "changeNote": f"loaded {path}",
                "updatedBy": "tester",
                "updatedAt": None,
                "source": "db",
            }
        )
        monkeypatch.setattr(avdm_routes, loader_attr, load_mock)
        monkeypatch.setattr(avdm_routes, "get_config_metadata", metadata_mock)

        client = make_client(FakeResult([]))
        resp = client.get(f"/api/avdm/{path}?configKey=default")

        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["configKey"] == "default"
        assert data["version"] == 7
        assert data["config"] == {"marker": path}
        assert data["changeNote"] == f"loaded {path}"
        assert data["updatedBy"] == "tester"
        assert data["source"] == "db"
        reset_overrides()

    @pytest.mark.parametrize(
        ("path", "saver_attr"),
        [
            ("questionnaire-config", "save_questionnaire_config"),
            ("concern-mapping-config", "save_concern_mapping_config"),
            ("artifact-catalog-config", "save_artifact_catalog_config"),
            ("viewpoint-artifact-mapping-config", "save_viewpoint_artifact_mapping_config"),
        ],
    )
    def test_put_config_route_trims_operator_and_returns_saved_payload(self, monkeypatch, path: str, saver_attr: str):
        save_mock = AsyncMock(
            return_value={
                "config": {"saved": path},
                "version": 9,
                "changeNote": "saved note",
                "updatedBy": "tester",
                "updatedAt": None,
                "source": "db",
            }
        )
        monkeypatch.setattr(avdm_routes, saver_attr, save_mock)

        client = make_client(FakeResult([]))
        resp = client.put(
            f"/api/avdm/{path}?configKey=default",
            json={
                "config": {"saved": path},
                "changeNote": "saved note",
                "operator": "  tester  ",
            },
        )

        assert resp.status_code == 200
        assert save_mock.await_args.kwargs["operator"] == "tester"
        data = resp.json().get("data") or resp.json()
        assert data["config"] == {"saved": path}
        assert data["version"] == 9
        assert data["changeNote"] == "saved note"
        reset_overrides()


class TestAVDMArtifactRecommendation:
    def test_recommendation_route_merges_project_type_baseline_and_concern_items(self, monkeypatch):
        monkeypatch.setattr(
            avdm_routes,
            "get_assessment_by_project",
            AsyncMock(
                return_value={
                    "projectType": "IDENTITY_INTERACTION_HEAVY_INTEGRATION",
                    "evaluation": {
                        "projectId": "P-AVDM-1",
                        "decisions": [
                            {
                                "concernKey": "SCR7",
                                "concernName": "Compliance Boundary View",
                                "layer": "Security, Compliance & Risk",
                                "score": 0.4,
                                "classification": "Recommended",
                                "rationale": "seeded",
                            }
                        ],
                        "layerSummary": [],
                    },
                }
            ),
        )
        monkeypatch.setattr(avdm_routes, "load_artifact_catalog_config", AsyncMock(return_value={"artifactTypes": []}))
        monkeypatch.setattr(avdm_routes, "load_questionnaire_config", AsyncMock(return_value={"projectTypeProfiles": []}))
        monkeypatch.setattr(
            avdm_routes,
            "recommend_artifacts_from_config",
            lambda *args, **kwargs: ArtifactRecommendationResponse(
                projectId="P-AVDM-1",
                items=[
                    ArtifactRecommendationItem(
                        concernKey="PROJECT_TYPE:IDENTITY_INTERACTION_HEAVY_INTEGRATION:MANDATORY",
                        concernName="Project Type Baseline - Identity & Interaction-Heavy Integration",
                        classification="Mandatory",
                        artifacts=["Technical Architecture Diagram"],
                    )
                ],
            ),
        )
        monkeypatch.setattr(
            avdm_routes,
            "list_viewpoint_artifact_recommendation_items",
            AsyncMock(
                return_value=[
                    ArtifactRecommendationItem(
                        concernKey="SCR7",
                        concernName="Compliance Boundary View",
                        classification="Recommended",
                        artifacts=["Data Compliance Diagram"],
                    )
                ]
            ),
        )

        client = make_client(FakeResult([]))
        resp = client.get("/api/avdm/projects/P-AVDM-1/artifacts/recommendation")

        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["projectId"] == "P-AVDM-1"
        assert len(data["items"]) == 2
        assert data["items"][0]["concernKey"].startswith("PROJECT_TYPE:")
        assert data["items"][1]["concernKey"] == "SCR7"
        assert data["items"][1]["artifacts"] == ["Data Compliance Diagram"]
        reset_overrides()


class TestAVDMWorkflowConfirmations:
    def test_confirm_questionnaire(self):
        before = {**_ASSESSMENT_BASE, "status": "questionnaire_submitted"}
        after = {**before, "questionnaire_confirmed_at": "2026-04-29T11:00:00", "status": "questionnaire_confirmed"}
        client = make_client(
            FakeResult([before]),
            FakeResult([]),
            FakeResult([after]),
        )
        resp = client.post(
            "/api/avdm/projects/P-AVDM-1/questionnaire/confirm",
            json={"operator": "tester"},
        )
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["currentStatus"] == "questionnaire_confirmed"
        reset_overrides()

    def test_confirm_concern_requires_evaluation(self):
        before = {**_ASSESSMENT_BASE, "evaluation": None}
        client = make_client(FakeResult([before]))
        resp = client.post(
            "/api/avdm/projects/P-AVDM-1/concerns/confirm",
            json={"operator": "tester"},
        )
        assert resp.status_code == 400
        reset_overrides()

    def test_confirm_artifact_requirement(self):
        before = {
            **_ASSESSMENT_BASE,
            "questionnaire_confirmed_at": "2026-04-29T11:00:00",
            "concern_requirement_confirmed_at": "2026-04-29T12:00:00",
            "status": "concern_requirement_confirmed",
        }
        after = {
            **before,
            "artifact_requirement_confirmed_at": "2026-04-29T13:00:00",
            "status": "artifact_requirement_confirmed",
        }
        client = make_client(
            FakeResult([before]),
            FakeResult([]),
            FakeResult([after]),
        )
        resp = client.post(
            "/api/avdm/projects/P-AVDM-1/artifacts/requirements/confirm",
            json={"operator": "tester"},
        )
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert data["currentStatus"] == "artifact_requirement_confirmed"
        reset_overrides()
