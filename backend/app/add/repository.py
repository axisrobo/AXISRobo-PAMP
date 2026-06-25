"""Repository helpers for AVDM persistence."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _normalize_risk_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []
    return []


def _to_concern(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "concernKey": row["concern_key"],
        "concernName": row["concern_name"],
        "layer": row["layer"],
        "riskTags": _normalize_risk_tags(row.get("risk_tags")),
        "description": row.get("description") or "",
        "isActive": bool(row.get("is_active", True)),
        "updatedAt": row.get("update_at"),
        "updatedBy": row.get("update_by") or "system",
    }


def _to_assessment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "projectId": row["project_id"],
        "projectType": row.get("project_type"),
        "projectComplexity": float(row.get("project_complexity") or 0.5),
        "questionnaire": row.get("questionnaire") or {},
        "riskItems": row.get("risk_items") or [],
        "evaluation": row.get("evaluation"),
        "reviewResult": row.get("review_result"),
        "artifactSelection": row.get("artifact_selection"),
        "needsAVDM": row.get("needs_avdm"),
        "judgementReason": row.get("judgement_reason"),
        "version": int(row.get("version") or 1),
        "status": row.get("status") or "draft",
        "questionnaireSubmittedAt": row.get("questionnaire_submitted_at"),
        "questionnaireConfirmedAt": row.get("questionnaire_confirmed_at"),
        "concernRequirementConfirmedAt": row.get("concern_requirement_confirmed_at"),
        "artifactRequirementConfirmedAt": row.get("artifact_requirement_confirmed_at"),
        "artifactSubmittedAt": row.get("artifact_submitted_at"),
        "updatedAt": row.get("update_at"),
        "updatedBy": row.get("update_by") or "system",
    }


async def list_concerns(
    db: AsyncSession,
    *,
    layer: str | None = None,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    conditions = []
    params: dict[str, Any] = {}
    if not include_inactive:
        conditions.append("is_active = TRUE")
    if layer:
        conditions.append("LOWER(layer) = :layer")
        params["layer"] = layer.strip().casefold()

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    result = await db.execute(
        text(
            f"""
            SELECT id, concern_key, concern_name, layer, risk_tags, description, is_active, update_at, update_by
            FROM eam.avdm_pact_concern
            WHERE {where_clause}
            ORDER BY layer ASC, concern_key ASC
            """
        ),
        params,
    )
    return [_to_concern(row) for row in result.mappings().all()]


async def upsert_concern(
    db: AsyncSession,
    *,
    concern_key: str,
    concern_name: str,
    layer: str,
    risk_tags: list[str],
    description: str,
    is_active: bool,
    operator: str,
) -> dict[str, Any]:
    payload = {
        "concern_key": concern_key,
        "concern_name": concern_name,
        "layer": layer,
        "risk_tags": json.dumps(risk_tags),
        "description": description,
        "is_active": is_active,
        "operator": operator or "system",
    }
    result = await db.execute(
        text(
            """
            INSERT INTO eam.avdm_pact_concern (
                concern_key, concern_name, layer, risk_tags, description, is_active, create_by, update_by
            )
            VALUES (
                :concern_key, :concern_name, :layer, CAST(:risk_tags AS jsonb), :description, :is_active, :operator, :operator
            )
            ON CONFLICT (concern_key) DO UPDATE SET
                concern_name = EXCLUDED.concern_name,
                layer = EXCLUDED.layer,
                risk_tags = EXCLUDED.risk_tags,
                description = EXCLUDED.description,
                is_active = EXCLUDED.is_active,
                update_by = EXCLUDED.update_by,
                update_at = NOW()
            RETURNING id, concern_key, concern_name, layer, risk_tags, description, is_active, update_at, update_by
            """
        ),
        payload,
    )
    await db.commit()
    row = result.mappings().one()
    return _to_concern(row)


async def get_assessment_by_project(db: AsyncSession, project_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            """
                 SELECT id, project_id, project_type, project_complexity, questionnaire, risk_items,
                     evaluation, review_result, artifact_selection,
                     needs_avdm, judgement_reason, version, status,
                                         questionnaire_submitted_at, questionnaire_confirmed_at,
                                         concern_requirement_confirmed_at, artifact_requirement_confirmed_at, artifact_submitted_at,
                   update_at, update_by
            FROM eam.avdm_project_assessment
            WHERE project_id = :project_id
            """
        ),
        {"project_id": project_id},
    )
    row = result.mappings().first()
    return _to_assessment(row) if row else None


async def upsert_project_assessment(
    db: AsyncSession,
    *,
    project_id: str,
    project_type: str | None,
    project_complexity: float,
    questionnaire: dict[str, Any],
    risk_items: list[dict[str, Any]],
    evaluation: dict[str, Any] | None,
    review_result: dict[str, Any] | None,
    artifact_selection: list[dict[str, Any]] | None,
    needs_avdm: bool | None,
    judgement_reason: str | None,
    status: str,
    operator: str,
) -> dict[str, Any]:
    payload = {
        "project_id": project_id,
        "project_type": project_type,
        "project_complexity": project_complexity,
        "questionnaire": json.dumps(questionnaire or {}),
        "risk_items": json.dumps(risk_items or []),
        "evaluation": json.dumps(evaluation) if evaluation is not None else None,
        "review_result": json.dumps(review_result) if review_result is not None else None,
        "artifact_selection": json.dumps(artifact_selection) if artifact_selection is not None else None,
        "needs_avdm": needs_avdm,
        "judgement_reason": judgement_reason,
        "status": status,
        "questionnaire_submitted": bool(questionnaire),
        "artifact_submitted": bool(artifact_selection),
        "operator": operator or "system",
    }
    result = await db.execute(
        text(
            """
            INSERT INTO eam.avdm_project_assessment (
                project_id, project_type, project_complexity,
                questionnaire, risk_items, evaluation, review_result, artifact_selection,
                needs_avdm, judgement_reason, status,
                questionnaire_submitted_at, artifact_submitted_at,
                version, create_by, update_by
            )
            VALUES (
                :project_id, :project_type, :project_complexity,
                CAST(:questionnaire AS jsonb), CAST(:risk_items AS jsonb),
                CAST(:evaluation AS jsonb), CAST(:review_result AS jsonb), CAST(:artifact_selection AS jsonb),
                :needs_avdm, :judgement_reason, :status,
                CASE WHEN :questionnaire_submitted THEN NOW() ELSE NULL END,
                CASE WHEN :artifact_submitted THEN NOW() ELSE NULL END,
                1, :operator, :operator
            )
            ON CONFLICT (project_id) DO UPDATE SET
                project_type = EXCLUDED.project_type,
                project_complexity = EXCLUDED.project_complexity,
                questionnaire = EXCLUDED.questionnaire,
                risk_items = EXCLUDED.risk_items,
                evaluation = EXCLUDED.evaluation,
                review_result = EXCLUDED.review_result,
                artifact_selection = EXCLUDED.artifact_selection,
                needs_avdm = EXCLUDED.needs_avdm,
                judgement_reason = EXCLUDED.judgement_reason,
                status = EXCLUDED.status,
                questionnaire_submitted_at = CASE
                    WHEN eam.avdm_project_assessment.questionnaire_submitted_at IS NOT NULL THEN eam.avdm_project_assessment.questionnaire_submitted_at
                    WHEN :questionnaire_submitted THEN NOW()
                    ELSE eam.avdm_project_assessment.questionnaire_submitted_at
                END,
                artifact_submitted_at = CASE
                    WHEN :artifact_submitted THEN NOW()
                    ELSE eam.avdm_project_assessment.artifact_submitted_at
                END,
                version = eam.avdm_project_assessment.version + 1,
                update_by = EXCLUDED.update_by,
                update_at = NOW()
            RETURNING id, project_id, project_type, project_complexity, questionnaire, risk_items,
                      evaluation, review_result, artifact_selection,
                      needs_avdm, judgement_reason, version, status,
                      questionnaire_submitted_at, questionnaire_confirmed_at,
                      concern_requirement_confirmed_at, artifact_requirement_confirmed_at, artifact_submitted_at,
                      update_at, update_by
            """
        ),
        payload,
    )
    await db.commit()
    row = result.mappings().one()
    return _to_assessment(row)


async def list_assessment_records_for_stats(
    db: AsyncSession,
    *,
    status: str | None = None,
) -> list[dict[str, Any]]:
    conditions = []
    params: dict[str, Any] = {}
    if status:
        conditions.append("status = :status")
        params["status"] = status

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    result = await db.execute(
        text(
            f"""
            SELECT project_id, needs_avdm, evaluation, update_at
            FROM eam.avdm_project_assessment
            WHERE {where_clause}
            ORDER BY update_at ASC
            """
        ),
        params,
    )
    rows = result.mappings().all()
    return [dict(row) for row in rows]
