"""EA Request Concerns -- per-request concern list with contribution breakdown."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

router = APIRouter()


@router.get("/{request_id}/concerns", dependencies=[Depends(require_permission("ea_request", "read"))])
async def get_request_concerns(
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
        text(
            "SELECT project_id, evaluation, concern_requirement_confirmed_at, "
            "artifact_requirement_confirmed_at, artifact_submitted_at, "
            "questionnaire, risk_items, status "
            "FROM eam.avdm_project_assessment WHERE project_id = :pid"
        ),
        {"pid": project_id},
    )
    assessment = assessment_result.mappings().first()

    if not assessment or not assessment.get("evaluation"):
        return {
            "requestId": req_row["request_id"],
            "projectId": project_id,
            "workflowStatus": "request_created",
            "concerns": [],
        }

    evaluation = assessment["evaluation"]
    if isinstance(evaluation, str):
        import json
        evaluation = json.loads(evaluation)

    decisions = evaluation.get("decisions", [])
    contributions = evaluation.get("contributions") or {}

    def _status_from_timestamps(row) -> str:
        if row.get("artifact_submitted_at"):
            return "artifact_submitted"
        if row.get("artifact_requirement_confirmed_at"):
            return "artifact_requirement_confirmed"
        if row.get("concern_requirement_confirmed_at"):
            return "concern_requirement_confirmed"
        q = row.get("questionnaire") or {}
        if isinstance(q, str):
            import json
            q = json.loads(q)
        if q and isinstance(q, dict) and q.get("checkpoint1"):
            return "questionnaire_confirmed"
        return "questionnaire_submitted"

    workflow_status = _status_from_timestamps(assessment)

    concerns = []
    for d in decisions:
        ck = d.get("concernKey", "")
        concerns.append({
            "concernKey": ck,
            "concernName": d.get("concernName", ""),
            "layer": d.get("layer", ""),
            "classification": d.get("classification", "Optional"),
            "totalScore": d.get("score", 0),
            "rationale": d.get("rationale", ""),
            "contributions": contributions.get(ck, {"direct": [], "tagged": [], "rules": []}),
        })

    concerns.sort(key=lambda c: (
        {"Mandatory": 0, "Recommended": 1, "Optional": 2}.get(c["classification"], 3),
        -c["totalScore"],
        c["concernKey"],
    ))

    return {
        "requestId": req_row["request_id"],
        "projectId": project_id,
        "workflowStatus": workflow_status,
        "concerns": concerns,
    }
