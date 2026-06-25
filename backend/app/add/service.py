"""AVDM risk-driven concern scoring service (Phase 2 core)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from .catalog import CONCERN_CATALOG, PACT_LAYERS
from .models import (
    AVDMEvaluateRequest,
    AVDMEvaluateResponse,
    AVDMReviewRequest,
    AVDMReviewResponse,
    AVDMNeedJudgement,
    ArtifactRecommendationItem,
    ArtifactRecommendationResponse,
    AVDMStatisticsOverview,
    AVDMStatisticsResponse,
    AVDMTrendPoint,
    ConcernDecision,
    LayerSummary,
)


def _normalize_artifact_catalog_config(config: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    raw_items = config.get("artifactTypes") if isinstance(config, dict) else None
    source_items = raw_items if isinstance(raw_items, list) else []

    artifacts: dict[str, dict[str, Any]] = {}
    for index, raw_item in enumerate(source_items, start=1):
        if not isinstance(raw_item, dict):
            continue
        raw_key = str(raw_item.get("key") or "").strip()
        if not raw_key:
            continue
        merged = raw_item
        name = str(merged.get("name") or "").strip()
        if not name or merged.get("isActive") is False:
            continue
        artifacts[raw_key] = {
            "key": raw_key,
            "name": name,
            "sortOrder": int(merged.get("sortOrder") or index),
        }
    return artifacts


def _normalize_viewpoint_mapping_config(config: dict[str, Any] | None) -> list[dict[str, Any]]:
    raw_items = config.get("viewpoints") if isinstance(config, dict) else None
    source_items = raw_items if isinstance(raw_items, list) else []

    viewpoints: list[dict[str, Any]] = []
    for index, raw_item in enumerate(source_items, start=1):
        if not isinstance(raw_item, dict):
            continue
        number = int(raw_item.get("number") or 0)
        merged = raw_item
        viewpoint_name = str(merged.get("viewpoint") or "").strip()
        if not viewpoint_name or merged.get("isActive") is False:
            continue

        mandatory = [
            str(item).strip()
            for item in merged.get("mandatoryArtifacts", [])
            if str(item).strip()
        ]
        optional = [
            str(item).strip()
            for item in merged.get("optionalArtifacts", [])
            if str(item).strip() and str(item).strip() not in mandatory
        ]
        concern_keys = [
            str(item).strip().upper()
            for item in merged.get("concernKeys", [])
            if str(item).strip()
        ]

        viewpoints.append(
            {
                "number": number or index,
                "viewpoint": viewpoint_name,
                "concernKeys": concern_keys,
                "mandatoryArtifacts": mandatory,
                "optionalArtifacts": optional,
                "sortOrder": int(merged.get("sortOrder") or number or index),
            }
        )

    viewpoints.sort(key=lambda item: (item["sortOrder"], item["number"], item["viewpoint"]))
    return viewpoints


def _normalize_project_type_profiles(config: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    raw_items = config.get("projectTypeProfiles") if isinstance(config, dict) else None
    source_items = raw_items if isinstance(raw_items, list) else []

    profiles: dict[str, dict[str, Any]] = {}
    for raw_item in source_items:
        if not isinstance(raw_item, dict):
            continue
        value = str(raw_item.get("value") or "").strip()
        label = str(raw_item.get("label") or "").strip()
        if not value or not label:
            continue

        selections_by_status: dict[str, list[str]] = {
            "Mandatory": [],
            "Recommended": [],
            "Optional": [],
        }
        for selection in raw_item.get("artifactSelections", []):
            if not isinstance(selection, dict):
                continue
            status = str(selection.get("status") or "").strip()
            artifact_key = str(selection.get("artifactKey") or "").strip()
            if status not in selections_by_status or not artifact_key:
                continue
            if artifact_key not in selections_by_status[status]:
                selections_by_status[status].append(artifact_key)

        profiles[value] = {
            "value": value,
            "label": label,
            "artifactSelectionsByStatus": selections_by_status,
        }
    return profiles


def _risk_score_by_code(risk_items) -> dict[str, float]:
    score_map: dict[str, float] = defaultdict(float)
    for item in risk_items:
        code = item.code.strip().lower()
        if not code:
            continue
        score = (item.severity / 5.0) * (item.likelihood / 5.0)
        score_map[code] = max(score_map[code], score)
    return score_map


def _classify(score: float) -> str:
    if score >= 0.66:
        return "Mandatory"
    if score >= 0.38:
        return "Recommended"
    return "Optional"


def build_concern_contributions(
    risk_items: list,
    concern_catalog: list[dict[str, object]] | None = None,
) -> dict[str, dict]:
    risk_map = _risk_score_by_code(risk_items)
    catalog = concern_catalog or CONCERN_CATALOG

    risk_item_map: dict[str, dict] = {}
    for item in risk_items:
        code = item.code.strip().lower()
        if not code:
            continue
        if code not in risk_item_map:
            risk_item_map[code] = {
                "riskCode": item.code.strip(),
                "severity": float(item.severity),
                "likelihood": float(item.likelihood),
                "itemScore": round((float(item.severity) / 5.0) * (float(item.likelihood) / 5.0), 4),
                "question": getattr(item, "question", ""),
                "note": getattr(item, "note", ""),
            }

    result: dict[str, dict] = {}
    for concern in catalog:
        ck = str(concern["key"]).lower()
        tags = [str(t).lower() for t in concern.get("risk_tags", [])]

        direct: list[dict] = []
        tagged: list[dict] = []
        rules: list[dict] = []

        if ck in risk_item_map:
            direct.append({**risk_item_map[ck], "matchType": "direct"})

        for tag in tags:
            if tag in risk_item_map and tag != ck:
                tagged.append({**risk_item_map[tag], "matchType": "tagged"})

        result[str(concern["key"])] = {
            "direct": direct,
            "tagged": tagged,
            "rules": rules,
        }

    return result


def evaluate_avdm(
    payload: AVDMEvaluateRequest,
    concern_catalog: list[dict[str, object]] | None = None,
) -> AVDMEvaluateResponse:
    risk_map = _risk_score_by_code(payload.riskItems)
    complexity_boost = max(0.0, min(payload.projectComplexity, 1.0)) * 0.15
    catalog = concern_catalog or CONCERN_CATALOG

    decisions: list[ConcernDecision] = []

    for concern in catalog:
        concern_key = str(concern["key"])
        tags = [str(tag).lower() for tag in concern.get("risk_tags", [])]
        direct_score = risk_map.get(concern_key.lower(), 0.0)
        if tags:
            tagged_score = sum(risk_map.get(tag, 0.0) for tag in tags) / float(len(tags))
        else:
            tagged_score = 0.0

        risk_score = max(direct_score, tagged_score)
        score = min(1.0, round(risk_score + complexity_boost, 4))
        classification = _classify(score)
        decisions.append(
            ConcernDecision(
                concernKey=concern_key,
                concernName=str(concern["name"]),
                layer=str(concern["layer"]),
                score=score,
                classification=classification,
                rationale=(
                    "Risk-driven AVDM scoring using activated concern keys, matched risk tags, and project complexity."
                ),
            )
        )

    decisions.sort(
        key=lambda item: (
            {"Mandatory": 0, "Recommended": 1, "Optional": 2}[item.classification],
            -item.score,
            item.concernKey,
        )
    )

    discovered_layers = [str(item.get("layer") or "") for item in catalog]
    layer_order = list(dict.fromkeys(PACT_LAYERS + [layer for layer in discovered_layers if layer]))
    summary_counter: dict[str, dict[str, int]] = {
        layer: {"Mandatory": 0, "Recommended": 0, "Optional": 0} for layer in layer_order
    }
    for decision in decisions:
        if decision.layer not in summary_counter:
            summary_counter[decision.layer] = {"Mandatory": 0, "Recommended": 0, "Optional": 0}
        summary_counter[decision.layer][decision.classification] += 1

    layer_summary = [
        LayerSummary(
            layer=layer,
            mandatory=summary_counter[layer]["Mandatory"],
            recommended=summary_counter[layer]["Recommended"],
            optional=summary_counter[layer]["Optional"],
        )
        for layer in layer_order
    ]

    contributions = build_concern_contributions(payload.riskItems, catalog)

    return AVDMEvaluateResponse(
        projectId=payload.projectId,
        decisions=decisions,
        layerSummary=layer_summary,
        contributions=contributions,
    )


def apply_review_overrides(payload: AVDMReviewRequest) -> AVDMReviewResponse:
    override_map = {item.concernKey: item for item in payload.overrides}
    changed = 0
    merged: list[ConcernDecision] = []

    for decision in payload.evaluation.decisions:
        override = override_map.get(decision.concernKey)
        if override and override.classification != decision.classification:
            changed += 1
            rationale_suffix = f" Reviewer override: {override.reviewerComment or 'N/A'}"
            merged.append(
                ConcernDecision(
                    concernKey=decision.concernKey,
                    concernName=decision.concernName,
                    layer=decision.layer,
                    score=decision.score,
                    classification=override.classification,
                    rationale=f"{decision.rationale}{rationale_suffix}",
                )
            )
        else:
            merged.append(decision)

    merged.sort(
        key=lambda item: (
            {"Mandatory": 0, "Recommended": 1, "Optional": 2}[item.classification],
            -item.score,
            item.concernKey,
        )
    )

    return AVDMReviewResponse(
        projectId=payload.evaluation.projectId,
        decisions=merged,
        changeCount=changed,
    )


def judge_avdm_need(evaluation: AVDMEvaluateResponse) -> AVDMNeedJudgement:
    mandatory_count = sum(1 for item in evaluation.decisions if item.classification == "Mandatory")
    recommended_count = sum(1 for item in evaluation.decisions if item.classification == "Recommended")
    avg_score = (
        sum(item.score for item in evaluation.decisions) / float(len(evaluation.decisions))
        if evaluation.decisions
        else 0.0
    )

    needs = mandatory_count >= 4 or avg_score >= 0.5 or (mandatory_count >= 2 and recommended_count >= 4)
    confidence = min(1.0, round((mandatory_count * 0.12) + (avg_score * 0.6), 4))

    if needs:
        rationale = (
            f"High-risk profile detected: mandatory={mandatory_count}, "
            f"recommended={recommended_count}, avgScore={avg_score:.3f}."
        )
    else:
        rationale = (
            f"Current risk profile is moderate/low: mandatory={mandatory_count}, "
            f"recommended={recommended_count}, avgScore={avg_score:.3f}."
        )

    return AVDMNeedJudgement(needsAVDM=needs, confidence=confidence, rationale=rationale)


def _month_key(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m")
    if isinstance(value, str) and len(value) >= 7:
        return value[:7]
    return "unknown"


def build_statistics(records: list[dict[str, Any]]) -> AVDMStatisticsResponse:
    total = len(records)
    needs_count = 0
    mandatory_total = 0.0
    recommended_total = 0.0
    optional_total = 0.0
    data_blind = 0
    ops_blind = 0
    trend_counter: dict[str, dict[str, int]] = {}

    for row in records:
        if row.get("needs_avdm") is True:
            needs_count += 1

        evaluation = row.get("evaluation") or {}
        layer_summary = evaluation.get("layerSummary") if isinstance(evaluation, dict) else None

        layer_map: dict[str, dict[str, int]] = {}
        if isinstance(layer_summary, list):
            for layer_item in layer_summary:
                if not isinstance(layer_item, dict):
                    continue
                name = str(layer_item.get("layer") or "")
                if not name:
                    continue
                mandatory = int(layer_item.get("mandatory") or 0)
                recommended = int(layer_item.get("recommended") or 0)
                optional = int(layer_item.get("optional") or 0)
                layer_map[name] = {
                    "mandatory": mandatory,
                    "recommended": recommended,
                    "optional": optional,
                }
                mandatory_total += mandatory
                recommended_total += recommended
                optional_total += optional

        data_layer = layer_map.get("Data", {"mandatory": 0, "recommended": 0})
        ops_layer = layer_map.get("Operations", {"mandatory": 0, "recommended": 0})
        if (data_layer["mandatory"] + data_layer["recommended"]) == 0:
            data_blind += 1
        if (ops_layer["mandatory"] + ops_layer["recommended"]) == 0:
            ops_blind += 1

        month = _month_key(row.get("update_at"))
        if month not in trend_counter:
            trend_counter[month] = {"total": 0, "needs": 0}
        trend_counter[month]["total"] += 1
        if row.get("needs_avdm") is True:
            trend_counter[month]["needs"] += 1

    safe_total = float(total) if total > 0 else 1.0
    overview = AVDMStatisticsOverview(
        totalProjects=total,
        needsAVDMProjects=needs_count,
        needsRatio=round(needs_count / safe_total, 4),
        avgMandatory=round(mandatory_total / safe_total, 4),
        avgRecommended=round(recommended_total / safe_total, 4),
        avgOptional=round(optional_total / safe_total, 4),
        dataBlindSpotRatio=round(data_blind / safe_total, 4),
        operationsBlindSpotRatio=round(ops_blind / safe_total, 4),
    )

    trend = [
        AVDMTrendPoint(month=month, total=item["total"], needsAVDM=item["needs"])
        for month, item in sorted(trend_counter.items(), key=lambda pair: pair[0])
    ]

    return AVDMStatisticsResponse(overview=overview, trend=trend)


def recommend_artifacts(project_id: str, evaluation: AVDMEvaluateResponse) -> ArtifactRecommendationResponse:
    return recommend_artifacts_from_config(project_id, evaluation)


def recommend_artifacts_from_config(
    project_id: str,
    evaluation: AVDMEvaluateResponse,
    *,
    project_type: str | None = None,
    artifact_catalog_config: dict[str, Any] | None = None,
    viewpoint_mapping_config: dict[str, Any] | None = None,
    questionnaire_config: dict[str, Any] | None = None,
) -> ArtifactRecommendationResponse:
    artifact_by_key = _normalize_artifact_catalog_config(artifact_catalog_config)
    viewpoints = _normalize_viewpoint_mapping_config(viewpoint_mapping_config)
    project_type_profiles = _normalize_project_type_profiles(questionnaire_config)

    items: list[ArtifactRecommendationItem] = []

    normalized_project_type = (project_type or "").strip()
    if normalized_project_type:
        project_type_profile = project_type_profiles.get(normalized_project_type)
        if project_type_profile:
            for classification in ("Mandatory", "Recommended", "Optional"):
                ordered_artifact_names: list[str] = []
                for artifact_key in project_type_profile["artifactSelectionsByStatus"][classification]:
                    artifact = artifact_by_key.get(artifact_key)
                    if not artifact:
                        continue
                    ordered_artifact_names.append(str(artifact["name"]))

                if ordered_artifact_names:
                    items.append(
                        ArtifactRecommendationItem(
                            concernKey=f"PROJECT_TYPE:{normalized_project_type}:{classification.upper()}",
                            concernName=f"Project Type Baseline - {project_type_profile['label']}",
                            classification=classification,
                            artifacts=ordered_artifact_names,
                        )
                    )

    for decision in evaluation.decisions:
        if decision.classification == "Optional":
            continue

        matched_viewpoints = [
            viewpoint
            for viewpoint in viewpoints
            if decision.concernKey.strip().upper() in viewpoint["concernKeys"]
        ]

        ordered_artifact_names: list[str] = []
        seen_artifacts: set[str] = set()
        for field_name in ("mandatoryArtifacts", "optionalArtifacts"):
            for viewpoint in matched_viewpoints:
                for artifact_key in viewpoint[field_name]:
                    artifact = artifact_by_key.get(artifact_key)
                    if not artifact:
                        continue
                    artifact_name = str(artifact["name"])
                    if artifact_name in seen_artifacts:
                        continue
                    seen_artifacts.add(artifact_name)
                    ordered_artifact_names.append(artifact_name)

        if not ordered_artifact_names:
            continue

        items.append(
            ArtifactRecommendationItem(
                concernKey=decision.concernKey,
                concernName=decision.concernName,
                classification=decision.classification,
                artifacts=ordered_artifact_names,
            )
        )
    return ArtifactRecommendationResponse(projectId=project_id, items=items)
