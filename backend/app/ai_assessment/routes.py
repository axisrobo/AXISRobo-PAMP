"""AI Project Self-Assessment & Architecture Review endpoints."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_permission, require_role, get_current_user, Role
from app.auth.models import AuthUser

router = APIRouter()

# checklist sections — AT0-AT8 × L0-L4 matrix, 11 sections
CHECKLIST_SECTIONS = [
    ("A", "Scenario & Adoption", [
        ("A1", "Scenario class defined in assessment (Personal/Enterprise/Domain)", True),
        ("A2", "Adoption Tier (AT0-AT8) self-assessed", True),
        ("A3", "Governance Maturity (L0-L4) self-assessed", True),
        ("A4", "Tier × Maturity not in CRITICAL/DO NOT DEPLOY cell", True),
    ]),
    ("B", "Identity Resolution", [
        ("B1", "Agent Application IAM configured", True),
        ("B2", "Agent User IAM (OBO) configured, scope ≤ user permissions", True),
        ("B3", "Agent Workload IAM (SPIFFE/SVID) issued (server-side only)", True),
        ("B4", "Agent Identity layer: Attestation + Intent + Chaining (RFC 8693)", True),
        ("B5", "Agent registered in Agent Naming Service (ANS)", True),
        ("B6", "Desktop/mobile endpoints managed via MDM/UEM + OIDC/MFA", False),
    ]),
    ("C", "Access Control", [
        ("C1", "PEP deployed at API Gateway (not BFF)", True),
        ("C2", "PDP selected (OPA/Cedar), Policy-as-Code", True),
        ("C3", "ABAC attributes: caller-id + attestation + intent + sensitivity + risk + time", True),
        ("C4", "All call channels go through same PEP", True),
        ("C5", "4-hop chain (human, app, workload, session) resolvable in context", True),
    ]),
    ("D", "Continuous Evaluation", [
        ("D1", "CAEP covers standard events (session revoked, claims change, risk change)", True),
        ("D2", "SOC anomaly → Transmitter connected; IdP/PDP as Receiver", True),
        ("D3", "SET end-to-end < 5s; event triage < 24h; notification readiness < 72h", True),
        ("D4", "If BU serves DORA-scope clients: triage < 1h; reporting < 4h", False),
    ]),
    ("E", "Data & Models", [
        ("E1", "Data classification complete; Crown Jewels access audited", True),
        ("E2", "Pre-LLM controls in place (classify → filter → anonymize)", True),
        ("E3", "RAG corpus provenance traceable", True),
        ("E4", "LLM/AI Gateway: prompt + response full logging enabled", True),
        ("E5", "Model registered + production gating active", True),
        ("E6", "DLP covers prompt input and model output", True),
    ]),
    ("F", "Runtime & Network", [
        ("F1", "Workload runs on governed container/VM/serverless", True),
        ("F2", "Micro-segmentation; East-West encryption", True),
        ("F3", "Device posture → CAEP Device Compliance Change", False),
    ]),
    ("G", "Security Operations", [
        ("G1", "Behavior telemetry ingested into SOC", True),
        ("G2", "Baseline + anomaly detection covers privilege escalation and lateral movement", True),
        ("G3", "AI-enhanced vulnerability discovery feeds into risk signals", False),
        ("G4", "Plan-Divergence Detection deployed", True),
        ("G5", "Trajectory-Level Logging satisfies EU AI Act Art. 72", True),
    ]),
    ("H", "Agent Protocols", [
        ("H1", "MCP servers provenance-approved; OAuth 2.1 + Resource-Indicator-Scoped Tokens", True),
        ("H2", "Tool descriptions signed + hash-pinned", True),
        ("H3", "MCP calls use Token Exchange to carry Principal", True),
        ("H4", "A2A communication: mutual mTLS + SVID + message signing", True),
        ("H5", "Multi-agent cascading blast radius budgeted in scenario declaration", True),
    ]),
    ("I", "AIBOM & Runtime Composition", [
        ("I1", "AIBOM covers 5 layers: model / framework / tool / data / runtime composition", True),
        ("I2", "Runtime new tools: sandbox → provenance → AIBOM → production", True),
        ("I3", "High-impact workflows satisfy Decision-Level Traceability", True),
    ]),
    ("J", "Lethal Trifecta & HITL", [
        ("J1", "Session {private data · untrusted content · external comm} capability combo declared", True),
        ("J2", "Triple-capability sessions have HITL + full trajectory + bidirectional rate-limit + DLP", True),
        ("J3", "HITL approval avoids fatigue (reasonable signal-to-noise ratio)", False),
    ]),
    ("K", "Counterparty Type", [
        ("K1", "Counterparty Type (CP1/CP2/CP3/CP4) registered", True),
        ("K2", "Data residency configured per counterparty jurisdiction", True),
        ("K3", "Cross-counterparty calls go through API Gateway with PDP re-evaluation", True),
        ("K4", "CP2: B2B federated IdP configured; contract scope as PDP attributes", False),
        ("K5", "CP3: Per-supplier SPIFFE Trust Domain; RLS + Tenant ID; KMS Key per Tenant", False),
        ("K6", "CP4: Independent CIAM; explicit consent UI; privacy-designed telemetry", False),
    ]),
]

ADOPTION_TIERS = [
    (0, "AT0 — Shadow AI", "Ungoverned, IT-invisible AI usage"),
    (1, "AT1 — Vendor OOTB", "Off-the-shelf SaaS Copilot"),
    (2, "AT2 — Platform/Configured", "Configured with enterprise data"),
    (3, "AT3 — Citizen Developer", "Low-code by business users"),
    (4, "AT4 — Code-Executing", "Agent can execute code"),
    (5, "AT5 — Custom Code Agent", "Bespoke coding agent"),
    (6, "AT6 — External/MCP-Connected", "External MCP/plugins"),
    (7, "AT7 — Multi-Agent", "Inter-agent orchestration"),
    (8, "AT8 — Federated/Cross-Org", "Cross-organization trust"),
]

GOVERNANCE_MATURITY = [
    (0, "L0 — Unaware/Ad Hoc", "No identification, no policy"),
    (1, "L1 — Experimentation w/o Guardrails", "Pilots exist; no autonomous limits"),
    (2, "L2 — Policy-Defined + HITL", "Formal policy + HITL + AIBOM"),
    (3, "L3 — Integrated Continuous Oversight", "Real-time monitoring + Kill Switch + Governance-as-Code"),
    (4, "L4 — Adaptive Self-Regulating", "Auto-tuning policies + cryptographic identity + regulatory dashboards"),
]

SCENARIO_CLASSES = [
    ("personal", "Personal / Employee Agent"),
    ("enterprise", "Enterprise Agent"),
    ("domain", "Domain Agent"),
]

COUNTERPARTY_TYPES = [
    ("cp1", "CP1 — Internal Employee"),
    ("cp2", "CP2 — External Partner (B2B)"),
    ("cp3", "CP3 — Supplier / Vendor"),
    ("cp4", "CP4 — B2C Consumer"),
]


def _compute_matrix_position(tier: int, maturity: int) -> str:
    if tier == 0:
        return "CRITICAL"
    if tier >= 8 and maturity < 4:
        return "INSUFFICIENT"
    if tier >= 7 and maturity < 3:
        return "INSUFFICIENT"
    if tier >= 5 and maturity < 2:
        return "HIGH_EXPOSURE"
    if tier >= 3 and maturity < 1:
        return "HIGH_EXPOSURE"
    if maturity >= 3:
        return "MANAGEABLE"
    if maturity >= 2:
        return "FEASIBLE"
    return "MONITOR"


VERDICT_LEGEND = {
    "PASS": "Matrix position acceptable and all critical controls satisfied — deployment approved.",
    "CONDITIONAL": "Deployment allowed only after the listed compensating / critical controls are in place.",
    "BLOCKED": "Deployment must not proceed in the current tier × maturity position.",
    "UNASSESSED": "Self-assessment not completed.",
}

_VERDICT_STATUS = {
    "PASS": "approved",
    "CONDITIONAL": "conditional",
    "BLOCKED": "blocked",
    "UNASSESSED": "draft",
}


def _compute_verdict(matrix_position: str | None, items: list[dict]) -> dict:
    if not matrix_position or matrix_position == "unassessed":
        return {"verdict": "UNASSESSED", "reason": VERDICT_LEGEND["UNASSESSED"], "unmetCritical": []}

    unmet_critical = [i for i in items if i.get("isCritical") and not i.get("isChecked")]
    n_unmet = len(unmet_critical)

    if matrix_position in ("CRITICAL", "INSUFFICIENT"):
        reason = {
            "CRITICAL": "Adoption Tier AT0 (Shadow AI) is ungoverned — migrate to AT1+ before deployment.",
            "INSUFFICIENT": "Governance maturity is insufficient for this adoption tier — raise maturity or lower the tier.",
        }[matrix_position]
        return {"verdict": "BLOCKED", "reason": reason, "unmetCritical": _unmet_keys(unmet_critical)}

    if matrix_position == "HIGH_EXPOSURE" or n_unmet > 0:
        parts = []
        if matrix_position == "HIGH_EXPOSURE":
            parts.append("High exposure position requires compensating controls (HITL + sandbox + review).")
        if n_unmet > 0:
            parts.append(f"{n_unmet} critical control(s) not yet satisfied.")
        return {"verdict": "CONDITIONAL", "reason": " ".join(parts), "unmetCritical": _unmet_keys(unmet_critical)}

    return {"verdict": "PASS", "reason": VERDICT_LEGEND["PASS"], "unmetCritical": []}


def _unmet_keys(items: list[dict]) -> list[str]:
    return [f"{i.get('sectionKey', '')}:{i.get('itemKey', '')}".strip(":") for i in items if i.get("itemKey")]


async def _load_verdict(db: AsyncSession, assessment_id: str) -> dict:
    sa = await db.execute(
        text("SELECT matrix_position FROM eam.ai_self_assessment WHERE assessment_id = CAST(:id AS uuid)"),
        {"id": assessment_id},
    )
    sa_row = sa.mappings().first()
    matrix = sa_row["matrix_position"] if sa_row else None
    cl = await db.execute(
        text("SELECT section_key, item_key, is_checked, is_critical FROM eam.ai_review_checklist "
             "WHERE assessment_id = CAST(:id AS uuid)"),
        {"id": assessment_id},
    )
    items = [{
        "sectionKey": r["section_key"], "itemKey": r["item_key"],
        "isChecked": r["is_checked"], "isCritical": r["is_critical"],
    } for r in cl.mappings().all()]
    return _compute_verdict(matrix, items)


class CreateAssessmentRequest(BaseModel):
    projectName: str
    projectIdRef: str = ""


class SelfAssessmentRequest(BaseModel):
    scenarioClass: str = "enterprise"
    counterpartyType: str = "cp1"
    adoptionTier: int = 1
    governanceMaturity: int = 1
    description: str = ""


class ChecklistUpdateRequest(BaseModel):
    items: list[dict]


@router.get("", dependencies=[Depends(require_permission("avdm", "read"))])
async def list_assessments(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_r = await db.execute(text("SELECT COUNT(*) FROM eam.ai_project_assessment"))
    total = count_r.scalar()
    offset = (page - 1) * pageSize
    rows = await db.execute(
        text("SELECT id, project_name, project_id_ref, status, created_by, updated_by, created_at, updated_at "
             "FROM eam.ai_project_assessment ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        {"limit": pageSize, "offset": offset},
    )
    items = [{
        "id": str(r["id"]), "projectName": r["project_name"], "projectIdRef": r["project_id_ref"],
        "status": r["status"], "createdBy": r["created_by"], "updatedBy": r["updated_by"],
        "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
    } for r in rows.mappings().all()]
    return {"data": items, "total": total, "page": page, "pageSize": pageSize}


@router.get("/meta", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_assessment_meta():
    return {
        "adoptionTiers": [{"value": t[0], "label": t[1], "description": t[2]} for t in ADOPTION_TIERS],
        "governanceMaturity": [{"value": t[0], "label": t[1], "description": t[2]} for t in GOVERNANCE_MATURITY],
        "scenarioClasses": [{"value": s[0], "label": s[1]} for s in SCENARIO_CLASSES],
        "counterpartyTypes": [{"value": c[0], "label": c[1]} for c in COUNTERPARTY_TYPES],
        "matrixLegend": {
            "CRITICAL": "Cannot proceed — must migrate AT0 to AT1+ or block",
            "INSUFFICIENT": "Must increase maturity or reduce tier",
            "HIGH_EXPOSURE": "Must add HITL + sandbox + review",
            "FEASIBLE": "Proceed with required controls",
            "MANAGEABLE": "Proceed with continuous monitoring",
            "MONITOR": "Proceed, monitor governance improvements",
        },
        "verdictLegend": VERDICT_LEGEND,
    }


@router.post("", status_code=201, dependencies=[Depends(require_permission("avdm", "write"))])
async def create_assessment(
    body: CreateAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    aid = str(uuid.uuid4())
    await db.execute(text(
        "INSERT INTO eam.ai_project_assessment (id, project_name, project_id_ref, status, created_by, updated_by) "
        "VALUES (CAST(:id AS uuid), :name, :ref, 'draft', :cb, :cb)"
    ), {"id": aid, "name": body.projectName, "ref": body.projectIdRef or "", "cb": user.id})
    await db.commit()
    return {"id": aid}


@router.get("/{assessment_id}", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_assessment(assessment_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(text("SELECT * FROM eam.ai_project_assessment WHERE id = CAST(:id AS uuid)"), {"id": assessment_id})
    row = r.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Assessment not found")

    sa = await db.execute(text("SELECT * FROM eam.ai_self_assessment WHERE assessment_id = CAST(:id AS uuid)"),
                          {"id": assessment_id})
    sa_row = sa.mappings().first()

    cl = await db.execute(text(
        "SELECT section_key, section_label, item_key, item_label, is_checked, is_critical, notes, sort_order "
        "FROM eam.ai_review_checklist WHERE assessment_id = CAST(:id AS uuid) ORDER BY section_key, sort_order"
    ), {"id": assessment_id})
    checklist_items = [{
        "sectionKey": r["section_key"],
        "sectionLabel": r["section_label"],
        "itemKey": r["item_key"],
        "itemLabel": r["item_label"],
        "isChecked": r["is_checked"],
        "isCritical": r["is_critical"],
        "notes": r["notes"] or "",
        "sortOrder": r["sort_order"],
    } for r in cl.mappings().all()]

    self_assessment = None
    if sa_row:
        self_assessment = {
            "scenarioClass": sa_row["scenario_class"],
            "counterpartyType": sa_row["counterparty_type"],
            "adoptionTier": sa_row["adoption_tier"],
            "governanceMaturity": sa_row["governance_maturity"],
            "matrixPosition": sa_row["matrix_position"],
            "description": sa_row["description"],
        }

    return {
        "id": str(row["id"]),
        "projectName": row["project_name"],
        "projectIdRef": row["project_id_ref"],
        "status": row["status"],
        "createdBy": row["created_by"],
        "updatedBy": row["updated_by"],
        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
        "selfAssessment": self_assessment,
        "checklist": checklist_items,
        "checklistSummary": _checklist_summary(checklist_items),
        "verdict": _compute_verdict(sa_row["matrix_position"] if sa_row else None, checklist_items),
    }


@router.put("/{assessment_id}/self-assessment", dependencies=[Depends(require_permission("avdm", "write"))])
async def save_self_assessment(
    assessment_id: str, body: SelfAssessmentRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text("SELECT 1 FROM eam.ai_project_assessment WHERE id = CAST(:id AS uuid)"), {"id": assessment_id})
    if not r.fetchone():
        raise HTTPException(status_code=404, detail="Assessment not found")

    matrix = _compute_matrix_position(body.adoptionTier, body.governanceMaturity)
    await db.execute(text(
        "INSERT INTO eam.ai_self_assessment (assessment_id, scenario_class, counterparty_type, adoption_tier, governance_maturity, matrix_position, description) "
        "VALUES (CAST(:aid AS uuid), :sc, :cp, :at, :gm, :mp, :desc) "
        "ON CONFLICT (assessment_id) DO UPDATE SET scenario_class=EXCLUDED.scenario_class, counterparty_type=EXCLUDED.counterparty_type, "
        "adoption_tier=EXCLUDED.adoption_tier, governance_maturity=EXCLUDED.governance_maturity, matrix_position=EXCLUDED.matrix_position, description=EXCLUDED.description, updated_at=NOW()"
    ), {"aid": assessment_id, "sc": body.scenarioClass, "cp": body.counterpartyType, "at": body.adoptionTier, "gm": body.governanceMaturity, "mp": matrix, "desc": body.description})

    # Generate checklist if empty
    existing = await db.execute(text("SELECT COUNT(*) FROM eam.ai_review_checklist WHERE assessment_id = CAST(:id AS uuid)"), {"id": assessment_id})
    if existing.scalar() == 0:
        await _generate_checklist(db, assessment_id)

    verdict = await _load_verdict(db, assessment_id)
    status = _VERDICT_STATUS[verdict["verdict"]]
    await db.execute(text("UPDATE eam.ai_project_assessment SET status = :st, updated_by = :ub, updated_at = NOW() WHERE id = CAST(:id AS uuid)"), {"id": assessment_id, "ub": user.id, "st": status})
    await db.commit()

    return {"matrixPosition": matrix, "verdict": verdict, "status": status}


@router.put("/{assessment_id}/checklist", dependencies=[Depends(require_permission("avdm", "write"))])
async def update_checklist(
    assessment_id: str, body: ChecklistUpdateRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    for item in body.items:
        await db.execute(text(
            "UPDATE eam.ai_review_checklist SET is_checked = :chk, notes = :notes, updated_at = NOW() "
            "WHERE assessment_id = CAST(:aid AS uuid) AND section_key = :sk AND item_key = :ik"
        ), {"aid": assessment_id, "sk": item["sectionKey"], "ik": item["itemKey"], "chk": item.get("isChecked", False), "notes": item.get("notes", "") or ""})
    verdict = await _load_verdict(db, assessment_id)
    status = _VERDICT_STATUS[verdict["verdict"]]
    await db.execute(text("UPDATE eam.ai_project_assessment SET status = :st, updated_by = :ub, updated_at = NOW() WHERE id = CAST(:id AS uuid)"), {"id": assessment_id, "ub": user.id, "st": status})
    await db.commit()
    return {"message": "ok", "status": status, "verdict": verdict}


@router.delete("/{assessment_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_assessment(assessment_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM eam.ai_project_assessment WHERE id = CAST(:id AS uuid)"), {"id": assessment_id})
    await db.commit()
    return {"message": "deleted"}


async def _generate_checklist(db: AsyncSession, assessment_id: str) -> None:
    for sk, sl, section_items in CHECKLIST_SECTIONS:
        so = 0
        for ik, il, critical in section_items:
            await db.execute(text(
                "INSERT INTO eam.ai_review_checklist (assessment_id, section_key, section_label, item_key, item_label, is_critical, sort_order) "
                "VALUES (CAST(:aid AS uuid), :sk, :sl, :ik, :il, :cr, :so) "
                "ON CONFLICT (assessment_id, section_key, item_key) DO NOTHING"
            ), {"aid": assessment_id, "sk": sk, "sl": sl, "ik": ik, "il": il, "cr": critical, "so": so})
            so += 1


def _checklist_summary(items: list[dict]) -> dict:
    if not items:
        return {"total": 0, "checked": 0, "critical": 0, "criticalChecked": 0, "score": 0}
    total = len(items)
    checked = sum(1 for i in items if i.get("isChecked"))
    critical = sum(1 for i in items if i.get("isCritical"))
    critical_checked = sum(1 for i in items if i.get("isCritical") and i.get("isChecked"))
    score = round(checked / total * 100, 1) if total > 0 else 0
    return {"total": total, "checked": checked, "critical": critical, "criticalChecked": critical_checked, "score": score}
