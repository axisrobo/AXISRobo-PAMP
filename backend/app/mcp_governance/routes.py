"""MCP Server & Tool Governance endpoints — registration, approval, provenance."""
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

router = APIRouter()

SERVER_STATUSES = ["draft", "registered", "approved", "restricted", "retired"]
TRANSPORTS = ["stdio", "http", "sse", "websocket", "other"]
AUTH_METHODS = ["none", "api_key", "oauth2.1", "token_exchange", "mtls"]
PROVENANCE_SOURCES = ["official", "internal", "community", "third_party", "other"]
TOOL_RISK_LEVELS = ["low", "medium", "high", "critical"]
TOOL_APPROVAL_STATUSES = ["pending", "approved", "rejected"]
TOOL_LIFECYCLE_STAGES = ["sandbox", "provenance_review", "aibom", "production"]


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "mcp-server"


def _parse_str_list(raw) -> list[str]:
    if raw is None:
        return []
    val = raw
    if isinstance(raw, str):
        try:
            val = json.loads(raw)
        except (ValueError, TypeError):
            return []
    return [s for s in val if isinstance(s, str)] if isinstance(val, list) else []


def _server_row(r) -> dict:
    return {
        "id": str(r["id"]),
        "serverKey": r["server_key"],
        "name": r["name"],
        "description": r["description"] or "",
        "owner": r["owner"] or "",
        "provider": r["provider"] or "",
        "transport": r["transport"],
        "endpointUri": r["endpoint_uri"] or "",
        "authMethod": r["auth_method"],
        "provenanceSource": r["provenance_source"] or "",
        "provenanceUri": r["provenance_uri"] or "",
        "scopes": _parse_str_list(r["scopes"]),
        "status": r["status"],
        "createdBy": r["created_by"],
        "updatedBy": r["updated_by"],
        "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
    }


def _tool_row(r) -> dict:
    return {
        "id": str(r["id"]),
        "serverId": str(r["server_id"]),
        "toolName": r["tool_name"],
        "description": r["description"] or "",
        "descriptionHash": r["description_hash"] or "",
        "signature": r["signature"] or "",
        "riskLevel": r["risk_level"],
        "approvalStatus": r["approval_status"],
        "lifecycleStage": r["lifecycle_stage"],
        "notes": r["notes"] or "",
        "createdBy": r["created_by"],
        "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
    }


class CreateServerRequest(BaseModel):
    name: str
    description: str = ""
    owner: str = ""
    provider: str = ""
    transport: str = "stdio"
    endpointUri: str = ""
    authMethod: str = "none"
    provenanceSource: str = ""
    provenanceUri: str = ""
    scopes: list[str] = []
    status: str = "draft"


class UpdateServerRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    owner: str | None = None
    provider: str | None = None
    transport: str | None = None
    endpointUri: str | None = None
    authMethod: str | None = None
    provenanceSource: str | None = None
    provenanceUri: str | None = None
    scopes: list[str] | None = None
    status: str | None = None


class ToolRequest(BaseModel):
    toolName: str
    description: str = ""
    descriptionHash: str = ""
    signature: str = ""
    riskLevel: str = "low"
    approvalStatus: str = "pending"
    lifecycleStage: str = "sandbox"
    notes: str = ""


def _validate_server(*, transport, auth_method, provenance_source, status) -> None:
    if transport is not None and transport not in TRANSPORTS:
        raise HTTPException(status_code=400, detail=f"Invalid transport: {transport}")
    if auth_method is not None and auth_method not in AUTH_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid authMethod: {auth_method}")
    if provenance_source not in (None, "") and provenance_source not in PROVENANCE_SOURCES:
        raise HTTPException(status_code=400, detail=f"Invalid provenanceSource: {provenance_source}")
    if status is not None and status not in SERVER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")


def _check_server_gate(status: str, provenance_source: str) -> None:
    if status == "approved" and not (provenance_source or "").strip():
        raise HTTPException(status_code=400, detail="MCP server must declare a provenance source before approval.")


def _validate_tool(body: ToolRequest) -> None:
    if not body.toolName.strip():
        raise HTTPException(status_code=400, detail="Tool name is required")
    if body.riskLevel not in TOOL_RISK_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid riskLevel: {body.riskLevel}")
    if body.approvalStatus not in TOOL_APPROVAL_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid approvalStatus: {body.approvalStatus}")
    if body.lifecycleStage not in TOOL_LIFECYCLE_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid lifecycleStage: {body.lifecycleStage}")


def _check_tool_gate(lifecycle_stage: str, approval_status: str, description_hash: str) -> None:
    if lifecycle_stage == "production" and (approval_status != "approved" or not (description_hash or "").strip()):
        raise HTTPException(
            status_code=400,
            detail="Tool requires approval and a hash-pinned description before promotion to production.",
        )


@router.get("/meta", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_mcp_meta():
    return {
        "statuses": SERVER_STATUSES,
        "transports": TRANSPORTS,
        "authMethods": AUTH_METHODS,
        "provenanceSources": PROVENANCE_SOURCES,
        "toolRiskLevels": TOOL_RISK_LEVELS,
        "toolApprovalStatuses": TOOL_APPROVAL_STATUSES,
        "toolLifecycleStages": TOOL_LIFECYCLE_STAGES,
    }


@router.get("", dependencies=[Depends(require_permission("avdm", "read"))])
async def list_servers(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    status: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    where = []
    params: dict = {}
    if q:
        where.append("(s.name ILIKE :q OR s.server_key ILIKE :q OR s.provider ILIKE :q)")
        params["q"] = f"%{q}%"
    if status:
        where.append("s.status = :status")
        params["status"] = status
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    count_r = await db.execute(text(f"SELECT COUNT(*) FROM eam.mcp_server_registry s {where_sql}"), params)
    total = count_r.scalar()

    offset = (page - 1) * pageSize
    rows = await db.execute(text(
        "SELECT s.*, "
        "(SELECT COUNT(*) FROM eam.mcp_tool t WHERE t.server_id = s.id) AS tool_count, "
        "(SELECT COUNT(*) FROM eam.mcp_tool t WHERE t.server_id = s.id AND t.lifecycle_stage = 'production') AS production_tool_count "
        f"FROM eam.mcp_server_registry s {where_sql} "
        "ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset"
    ), {**params, "limit": pageSize, "offset": offset})

    items = []
    for r in rows.mappings().all():
        item = _server_row(r)
        item["toolCount"] = r["tool_count"]
        item["productionToolCount"] = r["production_tool_count"]
        items.append(item)
    return {"data": items, "total": total, "page": page, "pageSize": pageSize}


@router.post("", status_code=201, dependencies=[Depends(require_permission("avdm", "write"))])
async def create_server(
    body: CreateServerRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Server name is required")
    _validate_server(transport=body.transport, auth_method=body.authMethod,
                      provenance_source=body.provenanceSource, status=body.status)
    _check_server_gate(body.status, body.provenanceSource)

    sid = str(uuid.uuid4())
    server_key = f"{_slugify(body.name)}-{uuid.uuid4().hex[:8]}"
    await db.execute(text(
        "INSERT INTO eam.mcp_server_registry (id, server_key, name, description, owner, provider, transport, "
        "endpoint_uri, auth_method, provenance_source, provenance_uri, scopes, status, created_by, updated_by) "
        "VALUES (CAST(:id AS uuid), :key, :name, :desc, :owner, :prov, :tr, :uri, :auth, :psrc, :puri, "
        "CAST(:scopes AS jsonb), :st, :cb, :cb)"
    ), {
        "id": sid, "key": server_key, "name": body.name.strip(), "desc": body.description, "owner": body.owner,
        "prov": body.provider, "tr": body.transport, "uri": body.endpointUri, "auth": body.authMethod,
        "psrc": body.provenanceSource, "puri": body.provenanceUri,
        "scopes": json.dumps(body.scopes or [], ensure_ascii=False), "st": body.status, "cb": user.id,
    })
    await db.commit()
    return {"id": sid, "serverKey": server_key}


@router.get("/{server_id}", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_server(server_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(text("SELECT * FROM eam.mcp_server_registry WHERE id = CAST(:id AS uuid)"), {"id": server_id})
    row = r.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="MCP server not found")

    tr = await db.execute(text(
        "SELECT * FROM eam.mcp_tool WHERE server_id = CAST(:id AS uuid) ORDER BY tool_name"
    ), {"id": server_id})
    tools = [_tool_row(t) for t in tr.mappings().all()]

    result = _server_row(row)
    result["tools"] = tools
    return result


@router.put("/{server_id}", dependencies=[Depends(require_permission("avdm", "write"))])
async def update_server(
    server_id: str, body: UpdateServerRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text("SELECT * FROM eam.mcp_server_registry WHERE id = CAST(:id AS uuid)"), {"id": server_id})
    cur = r.mappings().first()
    if not cur:
        raise HTTPException(status_code=404, detail="MCP server not found")

    merged = {
        "name": body.name if body.name is not None else cur["name"],
        "description": body.description if body.description is not None else cur["description"],
        "owner": body.owner if body.owner is not None else cur["owner"],
        "provider": body.provider if body.provider is not None else cur["provider"],
        "transport": body.transport if body.transport is not None else cur["transport"],
        "endpoint_uri": body.endpointUri if body.endpointUri is not None else cur["endpoint_uri"],
        "auth_method": body.authMethod if body.authMethod is not None else cur["auth_method"],
        "provenance_source": body.provenanceSource if body.provenanceSource is not None else cur["provenance_source"],
        "provenance_uri": body.provenanceUri if body.provenanceUri is not None else cur["provenance_uri"],
        "status": body.status if body.status is not None else cur["status"],
    }
    scopes = body.scopes if body.scopes is not None else _parse_str_list(cur["scopes"])

    _validate_server(transport=merged["transport"], auth_method=merged["auth_method"],
                     provenance_source=merged["provenance_source"], status=merged["status"])
    _check_server_gate(merged["status"], merged["provenance_source"] or "")

    await db.execute(text(
        "UPDATE eam.mcp_server_registry SET name = :name, description = :description, owner = :owner, provider = :provider, "
        "transport = :transport, endpoint_uri = :endpoint_uri, auth_method = :auth_method, "
        "provenance_source = :provenance_source, provenance_uri = :provenance_uri, scopes = CAST(:scopes AS jsonb), "
        "status = :status, updated_by = :ub, updated_at = NOW() WHERE id = CAST(:id AS uuid)"
    ), {**merged, "scopes": json.dumps(scopes or [], ensure_ascii=False), "ub": user.id, "id": server_id})
    await db.commit()
    return {"message": "ok"}


@router.delete("/{server_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_server(server_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM eam.mcp_server_registry WHERE id = CAST(:id AS uuid)"), {"id": server_id})
    await db.commit()
    return {"message": "deleted"}


@router.post("/{server_id}/tools", status_code=201, dependencies=[Depends(require_permission("avdm", "write"))])
async def add_tool(
    server_id: str, body: ToolRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text("SELECT 1 FROM eam.mcp_server_registry WHERE id = CAST(:id AS uuid)"), {"id": server_id})
    if not r.fetchone():
        raise HTTPException(status_code=404, detail="MCP server not found")
    _validate_tool(body)
    _check_tool_gate(body.lifecycleStage, body.approvalStatus, body.descriptionHash)

    dup = await db.execute(text(
        "SELECT 1 FROM eam.mcp_tool WHERE server_id = CAST(:id AS uuid) AND tool_name = :name"
    ), {"id": server_id, "name": body.toolName.strip()})
    if dup.fetchone():
        raise HTTPException(status_code=400, detail=f"Tool '{body.toolName}' already exists for this server")

    tid = str(uuid.uuid4())
    await db.execute(text(
        "INSERT INTO eam.mcp_tool (id, server_id, tool_name, description, description_hash, signature, risk_level, "
        "approval_status, lifecycle_stage, notes, created_by, updated_by) "
        "VALUES (CAST(:tid AS uuid), CAST(:sid AS uuid), :name, :desc, :hash, :sig, :risk, :appr, :stage, :notes, :cb, :cb)"
    ), {
        "tid": tid, "sid": server_id, "name": body.toolName.strip(), "desc": body.description,
        "hash": body.descriptionHash, "sig": body.signature, "risk": body.riskLevel,
        "appr": body.approvalStatus, "stage": body.lifecycleStage, "notes": body.notes, "cb": user.id,
    })
    await db.execute(text("UPDATE eam.mcp_server_registry SET updated_at = NOW() WHERE id = CAST(:id AS uuid)"), {"id": server_id})
    await db.commit()
    return {"id": tid}


@router.put("/{server_id}/tools/{tool_id}", dependencies=[Depends(require_permission("avdm", "write"))])
async def update_tool(
    server_id: str, tool_id: str, body: ToolRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text(
        "SELECT 1 FROM eam.mcp_tool WHERE id = CAST(:tid AS uuid) AND server_id = CAST(:sid AS uuid)"
    ), {"tid": tool_id, "sid": server_id})
    if not r.fetchone():
        raise HTTPException(status_code=404, detail="Tool not found")
    _validate_tool(body)
    _check_tool_gate(body.lifecycleStage, body.approvalStatus, body.descriptionHash)

    dup = await db.execute(text(
        "SELECT 1 FROM eam.mcp_tool WHERE server_id = CAST(:sid AS uuid) AND tool_name = :name AND id <> CAST(:tid AS uuid)"
    ), {"sid": server_id, "name": body.toolName.strip(), "tid": tool_id})
    if dup.fetchone():
        raise HTTPException(status_code=400, detail=f"Tool '{body.toolName}' already exists for this server")

    await db.execute(text(
        "UPDATE eam.mcp_tool SET tool_name = :name, description = :desc, description_hash = :hash, signature = :sig, "
        "risk_level = :risk, approval_status = :appr, lifecycle_stage = :stage, notes = :notes, "
        "updated_by = :ub, updated_at = NOW() WHERE id = CAST(:tid AS uuid)"
    ), {
        "name": body.toolName.strip(), "desc": body.description, "hash": body.descriptionHash, "sig": body.signature,
        "risk": body.riskLevel, "appr": body.approvalStatus, "stage": body.lifecycleStage, "notes": body.notes,
        "ub": user.id, "tid": tool_id,
    })
    await db.commit()
    return {"message": "ok"}


@router.delete("/{server_id}/tools/{tool_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_tool(server_id: str, tool_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text(
        "DELETE FROM eam.mcp_tool WHERE id = CAST(:tid AS uuid) AND server_id = CAST(:sid AS uuid)"
    ), {"tid": tool_id, "sid": server_id})
    await db.commit()
    return {"message": "deleted"}
