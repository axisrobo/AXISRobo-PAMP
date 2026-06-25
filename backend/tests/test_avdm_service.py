from app.add.models import (
    AVDMEvaluateRequest,
    AVDMReviewRequest,
    ReviewOverrideItem,
    RiskItem,
)
from app.add.service import (
    apply_review_overrides,
    build_statistics,
    evaluate_avdm,
    judge_avdm_need,
    recommend_artifacts_from_config,
)


def test_evaluate_avdm_promotes_high_risk_concerns_to_recommended():
    payload = AVDMEvaluateRequest(
        projectId="P-100",
        projectComplexity=0.9,
        riskItems=[
            RiskItem(code="compliance", severity=5, likelihood=5),
            RiskItem(code="privacy", severity=4.5, likelihood=5),
        ],
    )

    result = evaluate_avdm(payload)
    by_key = {item.concernKey: item for item in result.decisions}

    assert by_key["D7"].classification == "Recommended"
    assert by_key["SCR7"].classification == "Recommended"


def test_evaluate_avdm_keeps_low_risk_concerns_optional():
    payload = AVDMEvaluateRequest(
        projectId="P-200",
        projectComplexity=0.0,
        riskItems=[],
    )

    result = evaluate_avdm(payload)

    assert all(item.classification == "Optional" for item in result.decisions)


def test_review_override_updates_classification_and_counts_changes():
    evaluation = evaluate_avdm(
        AVDMEvaluateRequest(
            projectId="P-300",
            projectComplexity=0.2,
            riskItems=[RiskItem(code="operations", severity=2, likelihood=2)],
        )
    )

    target = next(item for item in evaluation.decisions if item.concernKey == "OR4")
    requested = "Mandatory" if target.classification != "Mandatory" else "Recommended"

    reviewed = apply_review_overrides(
        AVDMReviewRequest(
            evaluation=evaluation,
            overrides=[
                ReviewOverrideItem(
                    concernKey="OR4",
                    classification=requested,
                    reviewerComment="Critical for this deployment topology",
                )
            ],
        )
    )

    reviewed_target = next(item for item in reviewed.decisions if item.concernKey == "OR4")

    assert reviewed.changeCount == 1
    assert reviewed_target.classification == requested
    assert "Reviewer override" in reviewed_target.rationale


def test_judge_avdm_need_keeps_recommended_only_profile_below_threshold():
    evaluation = evaluate_avdm(
        AVDMEvaluateRequest(
            projectId="P-400",
            projectComplexity=1.0,
            riskItems=[
                RiskItem(code="compliance", severity=5, likelihood=5),
                RiskItem(code="security", severity=5, likelihood=5),
                RiskItem(code="privacy", severity=5, likelihood=5),
            ],
        )
    )

    judgement = judge_avdm_need(evaluation)

    assert judgement.needsAVDM is False
    assert judgement.confidence < 0.5


def test_build_statistics_aggregates_overview_and_trend():
    records = [
        {
            "needs_avdm": True,
            "update_at": "2026-01-05T10:00:00",
            "evaluation": {
                "layerSummary": [
                    {"layer": "Data", "mandatory": 1, "recommended": 0, "optional": 1},
                    {"layer": "Operations", "mandatory": 0, "recommended": 1, "optional": 1},
                ]
            },
        },
        {
            "needs_avdm": False,
            "update_at": "2026-01-20T09:00:00",
            "evaluation": {
                "layerSummary": [
                    {"layer": "Data", "mandatory": 0, "recommended": 0, "optional": 2},
                    {"layer": "Operations", "mandatory": 0, "recommended": 0, "optional": 2},
                ]
            },
        },
        {
            "needs_avdm": True,
            "update_at": "2026-02-02T09:00:00",
            "evaluation": {
                "layerSummary": [
                    {"layer": "Data", "mandatory": 0, "recommended": 0, "optional": 1},
                    {"layer": "Operations", "mandatory": 1, "recommended": 0, "optional": 0},
                ]
            },
        },
    ]

    result = build_statistics(records)

    assert result.overview.totalProjects == 3
    assert result.overview.needsAVDMProjects == 2
    assert result.overview.needsRatio == 0.6667
    assert result.overview.dataBlindSpotRatio == 0.6667
    assert result.overview.operationsBlindSpotRatio == 0.3333
    assert len(result.trend) == 2
    assert result.trend[0].month == "2026-01"
    assert result.trend[0].total == 2
    assert result.trend[0].needsAVDM == 1


def test_recommend_artifacts_ignores_optional_and_returns_major_items():
    evaluation = AVDMEvaluateRequest(
        projectId="P-500",
        projectComplexity=1.0,
        riskItems=[
            RiskItem(code="security", severity=5, likelihood=5),
            RiskItem(code="integration", severity=5, likelihood=5),
        ],
    )

    recommendation = recommend_artifacts_from_config(
        "P-500",
        evaluate_avdm(evaluation),
        artifact_catalog_config={
            "artifactTypes": [
                {"key": "tech_diagram", "name": "Technical Architecture Diagram", "isActive": True, "sortOrder": 1},
                {"key": "app_collab", "name": "Application Collaboration Diagram", "isActive": True, "sortOrder": 2},
                {"key": "auth_flow", "name": "Auth Flow Diagram", "isActive": False, "sortOrder": 3},
            ]
        },
        viewpoint_mapping_config={
            "viewpoints": [
                {
                    "number": 8,
                    "viewpoint": "Application Interaction / Impact View",
                    "concernKeys": ["A3"],
                    "mandatoryArtifacts": ["app_collab"],
                    "optionalArtifacts": ["tech_diagram"],
                    "isActive": True,
                    "sortOrder": 8,
                },
                {
                    "number": 35,
                    "viewpoint": "Service Authentication View",
                    "concernKeys": ["SCR4"],
                    "mandatoryArtifacts": ["auth_flow", "tech_diagram"],
                    "optionalArtifacts": [],
                    "isActive": True,
                    "sortOrder": 35,
                },
            ]
        },
    )

    assert recommendation.projectId == "P-500"
    assert len(recommendation.items) > 0
    assert all(item.classification in {"Mandatory", "Recommended"} for item in recommendation.items)
    assert all(len(item.artifacts) > 0 for item in recommendation.items)
    assert all("Auth Flow Diagram" not in item.artifacts for item in recommendation.items)


def test_recommend_artifacts_includes_project_type_baseline_from_matrix():
    evaluation = AVDMEvaluateRequest(
        projectId="P-600",
        projectComplexity=0.3,
        riskItems=[RiskItem(code="integration", severity=4, likelihood=4)],
    )

    recommendation = recommend_artifacts_from_config(
        "P-600",
        evaluate_avdm(evaluation),
        project_type="IDENTITY_INTERACTION_HEAVY_INTEGRATION",
        artifact_catalog_config={
            "artifactTypes": [
                {"key": "tech_diagram", "name": "Technical Architecture Diagram", "isActive": True, "sortOrder": 1},
                {"key": "app_collab", "name": "Application Collaboration Diagram", "isActive": True, "sortOrder": 2},
                {"key": "auth_flow", "name": "Auth Flow Diagram", "isActive": True, "sortOrder": 3},
                {"key": "system_process_flow", "name": "System Process Flow Diagram", "isActive": True, "sortOrder": 4},
            ]
        },
        viewpoint_mapping_config={"viewpoints": []},
        questionnaire_config={
            "projectTypeProfiles": [
                {
                    "value": "IDENTITY_INTERACTION_HEAVY_INTEGRATION",
                    "label": "Identity & Interaction-Heavy Integration",
                    "artifactSelections": [
                        {"artifactKey": "tech_diagram", "artifactLabel": "Technical Diagram", "status": "Mandatory"},
                        {"artifactKey": "app_collab", "artifactLabel": "App Collaboration Diagram", "status": "Mandatory"},
                        {"artifactKey": "auth_flow", "artifactLabel": "Auth & Service Flow", "status": "Mandatory"},
                        {"artifactKey": "system_process_flow", "artifactLabel": "System Process Flow", "status": "Recommended"},
                    ],
                }
            ]
        },
    )

    baseline_items = [item for item in recommendation.items if item.concernKey.startswith("PROJECT_TYPE:")]

    assert len(baseline_items) == 2
    mandatory_item = next(item for item in baseline_items if item.classification == "Mandatory")
    recommended_item = next(item for item in baseline_items if item.classification == "Recommended")
    assert mandatory_item.concernName == "Project Type Baseline - Identity & Interaction-Heavy Integration"
    assert mandatory_item.artifacts == [
        "Technical Architecture Diagram",
        "Application Collaboration Diagram",
        "Auth Flow Diagram",
    ]
    assert recommended_item.artifacts == ["System Process Flow Diagram"]
