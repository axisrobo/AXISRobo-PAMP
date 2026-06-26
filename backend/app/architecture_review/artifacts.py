"""EA Request Artifacts -- per-request artifact list with concern contributions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

router = APIRouter()


@router.get("/{request_id}/artifacts", dependencies=[Depends(require_permission("ea_request", "read"))])
async def get_request_artifacts(
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
            "SELECT project_id, evaluation, artifact_selection, concern_requirement_confirmed_at, "
            "artifact_requirement_confirmed_at, artifact_submitted_at, status "
            "FROM eam.avdm_project_assessment WHERE project_id = :pid"
        ),
        {"pid": project_id},
    )
    assessment = assessment_result.mappings().first()

    if not assessment or not assessment.get("evaluation"):
        return {
            "requestId": req_row["request_id"],
            "projectId": project_id,
            "artifacts": [],
        }

    evaluation = assessment["evaluation"]
    if isinstance(evaluation, str):
        import json
        evaluation = json.loads(evaluation)

    contributions = evaluation.get("contributions") or {}
    artifact_selections = assessment.get("artifact_selection") or []
    if isinstance(artifact_selections, str):
        import json
        artifact_selections = json.loads(artifact_selections) or []

    selected_keys = set()
    for sel in artifact_selections:
        if isinstance(sel, dict):
            selected_keys.add((sel.get("concernKey", ""), sel.get("artifactName", "")))

    concern_keys = [d.get("concernKey", "") for d in evaluation.get("decisions", []) if d.get("concernKey")]
    artifacts = []
    if concern_keys:
        # Canonical chain: concern -> viewpoint -> artifact.
        map_rows = await db.execute(
            text(
                "SELECT c.concern_key, a.artifact_name "
                "FROM eam.avdm_pact_concern c "
                "JOIN eam.avdm_viewpoint_concern_mapping vc ON vc.concern_id = c.id AND vc.is_active = TRUE "
                "JOIN eam.avdm_viewpoint v ON v.id = vc.viewpoint_id AND v.is_active = TRUE "
                "JOIN eam.avdm_viewpoint_artifact_mapping va ON va.viewpoint_id = v.id AND va.is_active = TRUE "
                "JOIN eam.avdm_artifact a ON a.id = va.artifact_id AND a.is_active = TRUE "
                "WHERE c.is_active = TRUE AND c.concern_key = ANY(:keys) "
                "ORDER BY c.concern_key, vc.sort_order, va.sort_order, a.artifact_name"
            ),
            {"keys": concern_keys},
        )
        canonical_map: dict[str, list[str]] = {}
        for mr in map_rows.mappings().all():
            names = canonical_map.setdefault(mr["concern_key"], [])
            if mr["artifact_name"] not in names:
                names.append(mr["artifact_name"])

        for d in evaluation.get("decisions", []):
            ck = d.get("concernKey", "")
            cn = d.get("concernName", "")
            cl = d.get("classification", "Optional")
            score = d.get("score", 0)
            concern_contrib = contributions.get(ck, {"direct": [], "tagged": [], "rules": []})
            artifact_names = canonical_map.get(ck, [])
            for aname in artifact_names:
                sel_status = "selected" if (ck, aname) in selected_keys else "recommended"
                artifacts.append({
                    "artifactId": f"{ck}_{aname}",
                    "artifactName": aname,
                    "associatedConcernKey": ck,
                    "associatedConcernName": cn,
                    "classification": cl,
                    "totalScore": score,
                    "status": sel_status,
                    "contributions": concern_contrib,
                })

    return {
        "requestId": req_row["request_id"],
        "projectId": project_id,
        "artifacts": artifacts,
    }
