"""EA Request Viewpoints -- derived concern -> viewpoint -> artifact chain."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_permission
from app.auth.models import AuthUser
from app.database import get_db


router = APIRouter()


@router.get("/{request_id}/viewpoints", dependencies=[Depends(require_permission("ea_request", "read"))])
async def get_request_viewpoints(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    req_result = await db.execute(
        text("SELECT request_id, project_id FROM eam.eam_request WHERE request_id = :rid OR id::text = :rid LIMIT 1"),
        {"rid": request_id},
    )
    req_row = req_result.mappings().first()
    if not req_row:
        raise HTTPException(status_code=404, detail="EA request not found")

    project_id = req_row["project_id"]
    if not project_id:
        raise HTTPException(status_code=404, detail="No project associated with this request")

    assessment_result = await db.execute(
        text("SELECT project_id, evaluation FROM eam.avdm_project_assessment WHERE project_id = :pid"),
        {"pid": project_id},
    )
    assessment = assessment_result.mappings().first()
    if not assessment or not assessment.get("evaluation"):
        return {"requestId": req_row["request_id"], "projectId": project_id, "viewpoints": []}

    evaluation = assessment["evaluation"]
    if isinstance(evaluation, str):
        evaluation = json.loads(evaluation)

    decisions = [item for item in evaluation.get("decisions", []) if item.get("concernKey")]
    concern_keys = [str(item["concernKey"]).strip().upper() for item in decisions]
    if not concern_keys:
        return {"requestId": req_row["request_id"], "projectId": project_id, "viewpoints": []}

    decision_by_key = {str(item["concernKey"]).strip().upper(): item for item in decisions}
    rows = (
        await db.execute(
            text(
                """
                SELECT v.id::text AS viewpoint_id,
                       v.viewpoint_number,
                       v.layer_name,
                       v.viewpoint_name,
                       UPPER(c.concern_key) AS concern_key,
                       c.concern_name,
                       a.artifact_name,
                       vc.sort_order AS concern_sort_order,
                       va.sort_order AS artifact_sort_order
                FROM eam.avdm_pact_concern c
                JOIN eam.avdm_viewpoint_concern_mapping vc
                  ON vc.concern_id = c.id AND vc.is_active = TRUE
                JOIN eam.avdm_viewpoint v
                  ON v.id = vc.viewpoint_id AND v.is_active = TRUE
                LEFT JOIN eam.avdm_viewpoint_artifact_mapping va
                  ON va.viewpoint_id = v.id AND va.is_active = TRUE
                LEFT JOIN eam.avdm_artifact a
                  ON a.id = va.artifact_id AND a.is_active = TRUE
                WHERE c.is_active = TRUE
                  AND UPPER(c.concern_key) = ANY(:concern_keys)
                ORDER BY v.sort_order, v.viewpoint_number, vc.sort_order, va.sort_order, a.artifact_name
                """
            ),
            {"concern_keys": concern_keys},
        )
    ).mappings().all()

    severity_rank = {"Mandatory": 0, "Recommended": 1, "Optional": 2}
    viewpoints: dict[str, dict] = {}
    for row in rows:
        key = row["viewpoint_id"]
        item = viewpoints.setdefault(
            key,
            {
                "viewpointId": key,
                "viewpointNumber": row["viewpoint_number"],
                "viewpointName": row["viewpoint_name"],
                "layerName": row["layer_name"],
                "classification": "Optional",
                "totalScore": 0,
                "concerns": [],
                "artifacts": [],
            },
        )

        concern_key = row["concern_key"]
        decision = decision_by_key.get(concern_key, {})
        classification = str(decision.get("classification") or "Optional")
        score = float(decision.get("score") or 0)

        if severity_rank.get(classification, 99) < severity_rank.get(item["classification"], 99):
            item["classification"] = classification
        item["totalScore"] = max(item["totalScore"], score)

        if not any(c["concernKey"] == concern_key for c in item["concerns"]):
            item["concerns"].append(
                {
                    "concernKey": concern_key,
                    "concernName": row["concern_name"],
                    "classification": classification,
                    "totalScore": score,
                }
            )

        artifact_name = row.get("artifact_name")
        if artifact_name and artifact_name not in item["artifacts"]:
            item["artifacts"].append(artifact_name)

    ordered = sorted(
        viewpoints.values(),
        key=lambda item: (
            severity_rank.get(item["classification"], 99),
            -(item["totalScore"] or 0),
            item["viewpointNumber"] or 999,
        ),
    )
    return {"requestId": req_row["request_id"], "projectId": project_id, "viewpoints": ordered}
