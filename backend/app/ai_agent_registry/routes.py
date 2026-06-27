"""AI Agent Registry endpoints — registration & governance (NOT runtime identity)."""
from __future__ import annotations

import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_permission, require_role, get_current_user, Role
from app.auth.models import AuthUser
from app.ai_assessment.routes import SCENARIO_CLASSES, COUNTERPARTY_TYPES, ADOPTION_TIERS

router = APIRouter()

AGENT_TYPES = ["assistant", "copilot", "workflow", "autonomous", "orchestrator", "retrieval", "other"]
AUTONOMY_LEVELS = ["suggest_only", "human_approval", "supervised", "autonomous"]
TRUST_LEVELS = ["untrusted", "limited", "trusted", "privileged"]
AGENT_STATUSES = ["draft", "registered", "approved", "restricted", "retired"]
CAPABILITIES = [
    {"value": "code_execution", "label": "Code execution"},
    {"value": "tool_use", "label": "Tool / function calling"},
    {"value": "private_data_access", "label": "Private data access"},
    {"value": "untrusted_content", "label": "Untrusted content ingestion"},
    {"value": "external_comm", "label": "External communication"},
    {"value": "external_mcp", "label": "External MCP / plugins"},
    {"value": "multi_agent", "label": "Multi-agent / A2A"},
    {"value": "memory_persistence", "label": "Persistent memory"},
]
CAPABILITY_VALUES = {c["value"] for c in CAPABILITIES}
LETHAL_TRIFECTA = {"private_data_access", "untrusted_content", "external_comm"}

_SCENARIO_VALUES = {s[0] for s in SCENARIO_CLASSES}
_COUNTERPARTY_VALUES = {c[0] for c in COUNTERPARTY_TYPES}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "agent"


def _parse_caps(raw) -> list[str]:
    if raw is None:
        return []
    val = raw
    if isinstance(raw, str):
        try:
            val = json.loads(raw)
        except (ValueError, TypeError):
            return []
    return [c for c in val if isinstance(c, str)] if isinstance(val, list) else []


def _agent_row(r) -> dict:
    return {
        "id": str(r["id"]),
        "agentKey": r["agent_key"],
        "name": r["name"],
        "agentType": r["agent_type"] or "",
        "description": r["description"] or "",
        "owner": r["owner"] or "",
        "scenarioClass": r["scenario_class"],
        "counterpartyType": r["counterparty_type"],
        "adoptionTier": r["adoption_tier"],
        "autonomyLevel": r["autonomy_level"],
        "trustLevel": r["trust_level"],
        "hitlRequired": r["hitl_required"],
        "capabilities": _parse_caps(r["capabilities"]),
        "modelIdRef": str(r["model_id_ref"]) if r["model_id_ref"] else None,
        "status": r["status"],
        "createdBy": r["created_by"],
        "updatedBy": r["updated_by"],
        "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
    }


class CreateAgentRequest(BaseModel):
    name: str
    agentType: str = "assistant"
    description: str = ""
    owner: str = ""
    scenarioClass: str = "enterprise"
    counterpartyType: str = "cp1"
    adoptionTier: int = 1
    autonomyLevel: str = "human_approval"
    trustLevel: str = "limited"
    hitlRequired: bool = False
    capabilities: list[str] = []
    modelIdRef: str | None = None
    status: str = "draft"


class UpdateAgentRequest(BaseModel):
    name: str | None = None
    agentType: str | None = None
    description: str | None = None
    owner: str | None = None
    scenarioClass: str | None = None
    counterpartyType: str | None = None
    adoptionTier: int | None = None
    autonomyLevel: str | None = None
    trustLevel: str | None = None
    hitlRequired: bool | None = None
    capabilities: list[str] | None = None
    modelIdRef: str | None = None
    status: str | None = None


def _validate_agent(*, agent_type, scenario_class, counterparty_type, adoption_tier,
                    autonomy_level, trust_level, status, capabilities) -> None:
    if agent_type is not None and agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid agentType: {agent_type}")
    if scenario_class is not None and scenario_class not in _SCENARIO_VALUES:
        raise HTTPException(status_code=400, detail=f"Invalid scenarioClass: {scenario_class}")
    if counterparty_type is not None and counterparty_type not in _COUNTERPARTY_VALUES:
        raise HTTPException(status_code=400, detail=f"Invalid counterpartyType: {counterparty_type}")
    if adoption_tier is not None and not (0 <= adoption_tier <= 8):
        raise HTTPException(status_code=400, detail="adoptionTier must be between 0 and 8")
    if autonomy_level is not None and autonomy_level not in AUTONOMY_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid autonomyLevel: {autonomy_level}")
    if trust_level is not None and trust_level not in TRUST_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid trustLevel: {trust_level}")
    if status is not None and status not in AGENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if capabilities is not None:
        bad = [c for c in capabilities if c not in CAPABILITY_VALUES]
        if bad:
            raise HTTPException(status_code=400, detail=f"Invalid capabilities: {bad}")


def _check_approval_gate(status: str, capabilities: list[str], hitl_required: bool) -> None:
    if status == "approved" and LETHAL_TRIFECTA.issubset(set(capabilities or [])) and not hitl_required:
        raise HTTPException(
            status_code=400,
            detail="Lethal trifecta capabilities (private data + untrusted content + external "
                   "communication) require Human-in-the-Loop before approval.",
        )


async def _ensure_model_exists(db: AsyncSession, model_id: str) -> None:
    r = await db.execute(text("SELECT 1 FROM eam.ai_model_registry WHERE id = CAST(:id AS uuid)"), {"id": model_id})
    if not r.fetchone():
        raise HTTPException(status_code=400, detail="Referenced model not found")


@router.get("/meta", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_agent_meta():
    return {
        "agentTypes": AGENT_TYPES,
        "autonomyLevels": AUTONOMY_LEVELS,
        "trustLevels": TRUST_LEVELS,
        "statuses": AGENT_STATUSES,
        "capabilities": CAPABILITIES,
        "scenarioClasses": [{"value": s[0], "label": s[1]} for s in SCENARIO_CLASSES],
        "counterpartyTypes": [{"value": c[0], "label": c[1]} for c in COUNTERPARTY_TYPES],
        "adoptionTiers": [{"value": t[0], "label": t[1], "description": t[2]} for t in ADOPTION_TIERS],
        "lethalTrifecta": sorted(LETHAL_TRIFECTA),
    }


@router.get("", dependencies=[Depends(require_permission("avdm", "read"))])
async def list_agents(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    status: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    where = []
    params: dict = {}
    if q:
        where.append("(a.name ILIKE :q OR a.agent_key ILIKE :q OR a.owner ILIKE :q)")
        params["q"] = f"%{q}%"
    if status:
        where.append("a.status = :status")
        params["status"] = status
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    count_r = await db.execute(text(f"SELECT COUNT(*) FROM eam.ai_agent_registry a {where_sql}"), params)
    total = count_r.scalar()

    offset = (page - 1) * pageSize
    rows = await db.execute(text(
        "SELECT a.*, (SELECT m.name FROM eam.ai_model_registry m WHERE m.id = a.model_id_ref) AS model_name "
        f"FROM eam.ai_agent_registry a {where_sql} "
        "ORDER BY a.created_at DESC LIMIT :limit OFFSET :offset"
    ), {**params, "limit": pageSize, "offset": offset})

    items = []
    for r in rows.mappings().all():
        item = _agent_row(r)
        item["modelName"] = r["model_name"]
        items.append(item)
    return {"data": items, "total": total, "page": page, "pageSize": pageSize}


@router.post("", status_code=201, dependencies=[Depends(require_permission("avdm", "write"))])
async def create_agent(
    body: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Agent name is required")
    _validate_agent(
        agent_type=body.agentType, scenario_class=body.scenarioClass, counterparty_type=body.counterpartyType,
        adoption_tier=body.adoptionTier, autonomy_level=body.autonomyLevel, trust_level=body.trustLevel,
        status=body.status, capabilities=body.capabilities,
    )
    _check_approval_gate(body.status, body.capabilities, body.hitlRequired)

    model_id = (body.modelIdRef or "").strip() or None
    if model_id:
        await _ensure_model_exists(db, model_id)

    aid = str(uuid.uuid4())
    agent_key = f"{_slugify(body.name)}-{uuid.uuid4().hex[:8]}"
    await db.execute(text(
        "INSERT INTO eam.ai_agent_registry (id, agent_key, name, agent_type, description, owner, scenario_class, "
        "counterparty_type, adoption_tier, autonomy_level, trust_level, hitl_required, capabilities, model_id_ref, "
        "status, created_by, updated_by) "
        "VALUES (CAST(:id AS uuid), :key, :name, :atype, :desc, :owner, :sc, :cp, :tier, :auto, :trust, :hitl, "
        "CAST(:caps AS jsonb), CAST(:mref AS uuid), :st, :cb, :cb)"
    ), {
        "id": aid, "key": agent_key, "name": body.name.strip(), "atype": body.agentType, "desc": body.description,
        "owner": body.owner, "sc": body.scenarioClass, "cp": body.counterpartyType, "tier": body.adoptionTier,
        "auto": body.autonomyLevel, "trust": body.trustLevel, "hitl": body.hitlRequired,
        "caps": json.dumps(body.capabilities or [], ensure_ascii=False), "mref": model_id, "st": body.status, "cb": user.id,
    })
    await db.commit()
    return {"id": aid, "agentKey": agent_key}


@router.get("/{agent_id}", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(text(
        "SELECT a.*, (SELECT m.name FROM eam.ai_model_registry m WHERE m.id = a.model_id_ref) AS model_name "
        "FROM eam.ai_agent_registry a WHERE a.id = CAST(:id AS uuid)"
    ), {"id": agent_id})
    row = r.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = _agent_row(row)
    result["modelName"] = row["model_name"]
    return result


@router.put("/{agent_id}", dependencies=[Depends(require_permission("avdm", "write"))])
async def update_agent(
    agent_id: str, body: UpdateAgentRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text("SELECT * FROM eam.ai_agent_registry WHERE id = CAST(:id AS uuid)"), {"id": agent_id})
    cur = r.mappings().first()
    if not cur:
        raise HTTPException(status_code=404, detail="Agent not found")

    merged = {
        "name": body.name if body.name is not None else cur["name"],
        "agent_type": body.agentType if body.agentType is not None else cur["agent_type"],
        "description": body.description if body.description is not None else cur["description"],
        "owner": body.owner if body.owner is not None else cur["owner"],
        "scenario_class": body.scenarioClass if body.scenarioClass is not None else cur["scenario_class"],
        "counterparty_type": body.counterpartyType if body.counterpartyType is not None else cur["counterparty_type"],
        "adoption_tier": body.adoptionTier if body.adoptionTier is not None else cur["adoption_tier"],
        "autonomy_level": body.autonomyLevel if body.autonomyLevel is not None else cur["autonomy_level"],
        "trust_level": body.trustLevel if body.trustLevel is not None else cur["trust_level"],
        "hitl_required": body.hitlRequired if body.hitlRequired is not None else cur["hitl_required"],
        "capabilities": body.capabilities if body.capabilities is not None else _parse_caps(cur["capabilities"]),
        "status": body.status if body.status is not None else cur["status"],
    }
    # modelIdRef: None = leave unchanged, "" = clear, value = set
    if body.modelIdRef is None:
        model_id = str(cur["model_id_ref"]) if cur["model_id_ref"] else None
    else:
        model_id = body.modelIdRef.strip() or None

    _validate_agent(
        agent_type=merged["agent_type"], scenario_class=merged["scenario_class"],
        counterparty_type=merged["counterparty_type"], adoption_tier=merged["adoption_tier"],
        autonomy_level=merged["autonomy_level"], trust_level=merged["trust_level"],
        status=merged["status"], capabilities=merged["capabilities"],
    )
    if model_id:
        await _ensure_model_exists(db, model_id)
    _check_approval_gate(merged["status"], merged["capabilities"], merged["hitl_required"])

    await db.execute(text(
        "UPDATE eam.ai_agent_registry SET name = :name, agent_type = :agent_type, description = :description, "
        "owner = :owner, scenario_class = :scenario_class, counterparty_type = :counterparty_type, "
        "adoption_tier = :adoption_tier, autonomy_level = :autonomy_level, trust_level = :trust_level, "
        "hitl_required = :hitl_required, capabilities = CAST(:capabilities AS jsonb), "
        "model_id_ref = CAST(:model_id AS uuid), status = :status, updated_by = :ub, updated_at = NOW() "
        "WHERE id = CAST(:id AS uuid)"
    ), {
        **{k: v for k, v in merged.items() if k != "capabilities"},
        "capabilities": json.dumps(merged["capabilities"] or [], ensure_ascii=False),
        "model_id": model_id, "ub": user.id, "id": agent_id,
    })
    await db.commit()
    return {"message": "ok"}


@router.delete("/{agent_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM eam.ai_agent_registry WHERE id = CAST(:id AS uuid)"), {"id": agent_id})
    await db.commit()
    return {"message": "deleted"}
