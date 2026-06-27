"""AI Model Registry endpoints — models, versions, and provenance tracking."""
from __future__ import annotations

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

MODEL_TYPES = ["llm", "embedding", "vision", "multimodal", "classifier", "speech", "generative_image", "other"]
MODEL_STATUSES = ["draft", "approved", "restricted", "retired"]
PROVENANCE_SOURCES = ["vendor_api", "open_weights", "huggingface", "internal_trained", "fine_tuned", "other"]
APPROVAL_STATUSES = ["pending", "approved", "rejected"]


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "model"


def _model_row(r) -> dict:
    return {
        "id": str(r["id"]),
        "modelKey": r["model_key"],
        "name": r["name"],
        "provider": r["provider"] or "",
        "modelType": r["model_type"] or "",
        "description": r["description"] or "",
        "owner": r["owner"] or "",
        "status": r["status"],
        "createdBy": r["created_by"],
        "updatedBy": r["updated_by"],
        "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
    }


def _version_row(r) -> dict:
    return {
        "id": str(r["id"]),
        "modelId": str(r["model_id"]),
        "version": r["version"],
        "source": r["source"] or "",
        "sourceUri": r["source_uri"] or "",
        "checksum": r["checksum"] or "",
        "license": r["license"] or "",
        "trainingDataProvenance": r["training_data_provenance"] or "",
        "approvalStatus": r["approval_status"],
        "isProduction": r["is_production"],
        "notes": r["notes"] or "",
        "createdBy": r["created_by"],
        "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
    }


class CreateModelRequest(BaseModel):
    name: str
    provider: str = ""
    modelType: str = "llm"
    description: str = ""
    owner: str = ""
    status: str = "draft"


class UpdateModelRequest(BaseModel):
    name: str | None = None
    provider: str | None = None
    modelType: str | None = None
    description: str | None = None
    owner: str | None = None
    status: str | None = None


class VersionRequest(BaseModel):
    version: str
    source: str = ""
    sourceUri: str = ""
    checksum: str = ""
    license: str = ""
    trainingDataProvenance: str = ""
    approvalStatus: str = "pending"
    isProduction: bool = False
    notes: str = ""


@router.get("/meta", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_registry_meta():
    return {
        "modelTypes": MODEL_TYPES,
        "statuses": MODEL_STATUSES,
        "provenanceSources": PROVENANCE_SOURCES,
        "approvalStatuses": APPROVAL_STATUSES,
    }


@router.get("", dependencies=[Depends(require_permission("avdm", "read"))])
async def list_models(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    status: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    where = []
    params: dict = {}
    if q:
        where.append("(m.name ILIKE :q OR m.provider ILIKE :q OR m.model_key ILIKE :q)")
        params["q"] = f"%{q}%"
    if status:
        where.append("m.status = :status")
        params["status"] = status
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    count_r = await db.execute(text(f"SELECT COUNT(*) FROM eam.ai_model_registry m {where_sql}"), params)
    total = count_r.scalar()

    offset = (page - 1) * pageSize
    rows = await db.execute(text(
        "SELECT m.*, "
        "(SELECT COUNT(*) FROM eam.ai_model_version v WHERE v.model_id = m.id) AS version_count, "
        "(SELECT v.version FROM eam.ai_model_version v WHERE v.model_id = m.id AND v.is_production LIMIT 1) AS production_version "
        f"FROM eam.ai_model_registry m {where_sql} "
        "ORDER BY m.created_at DESC LIMIT :limit OFFSET :offset"
    ), {**params, "limit": pageSize, "offset": offset})

    items = []
    for r in rows.mappings().all():
        item = _model_row(r)
        item["versionCount"] = r["version_count"]
        item["productionVersion"] = r["production_version"]
        items.append(item)
    return {"data": items, "total": total, "page": page, "pageSize": pageSize}


@router.post("", status_code=201, dependencies=[Depends(require_permission("avdm", "write"))])
async def create_model(
    body: CreateModelRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Model name is required")
    if body.status not in MODEL_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")
    if body.modelType and body.modelType not in MODEL_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid modelType: {body.modelType}")

    mid = str(uuid.uuid4())
    model_key = f"{_slugify(body.name)}-{uuid.uuid4().hex[:8]}"
    await db.execute(text(
        "INSERT INTO eam.ai_model_registry (id, model_key, name, provider, model_type, description, owner, status, created_by, updated_by) "
        "VALUES (CAST(:id AS uuid), :key, :name, :prov, :mt, :desc, :owner, :st, :cb, :cb)"
    ), {"id": mid, "key": model_key, "name": body.name.strip(), "prov": body.provider, "mt": body.modelType or "llm",
        "desc": body.description, "owner": body.owner, "st": body.status, "cb": user.id})
    await db.commit()
    return {"id": mid, "modelKey": model_key}


@router.get("/{model_id}", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(text("SELECT * FROM eam.ai_model_registry WHERE id = CAST(:id AS uuid)"), {"id": model_id})
    row = r.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")

    vr = await db.execute(text(
        "SELECT * FROM eam.ai_model_version WHERE model_id = CAST(:id AS uuid) ORDER BY is_production DESC, created_at DESC"
    ), {"id": model_id})
    versions = [_version_row(v) for v in vr.mappings().all()]

    result = _model_row(row)
    result["versions"] = versions
    return result


@router.put("/{model_id}", dependencies=[Depends(require_permission("avdm", "write"))])
async def update_model(
    model_id: str, body: UpdateModelRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text("SELECT 1 FROM eam.ai_model_registry WHERE id = CAST(:id AS uuid)"), {"id": model_id})
    if not r.fetchone():
        raise HTTPException(status_code=404, detail="Model not found")

    fields = {
        "name": body.name, "provider": body.provider, "model_type": body.modelType,
        "description": body.description, "owner": body.owner, "status": body.status,
    }
    if body.status is not None and body.status not in MODEL_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")
    if body.modelType is not None and body.modelType not in MODEL_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid modelType: {body.modelType}")

    sets = []
    params: dict = {"id": model_id, "ub": user.id}
    for col, val in fields.items():
        if val is not None:
            sets.append(f"{col} = :{col}")
            params[col] = val
    if not sets:
        return {"message": "no changes"}
    sets.append("updated_by = :ub")
    sets.append("updated_at = NOW()")
    await db.execute(text(f"UPDATE eam.ai_model_registry SET {', '.join(sets)} WHERE id = CAST(:id AS uuid)"), params)
    await db.commit()
    return {"message": "ok"}


@router.delete("/{model_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM eam.ai_model_registry WHERE id = CAST(:id AS uuid)"), {"id": model_id})
    await db.commit()
    return {"message": "deleted"}


def _validate_version_payload(body: VersionRequest) -> None:
    if not body.version.strip():
        raise HTTPException(status_code=400, detail="Version is required")
    if body.approvalStatus not in APPROVAL_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid approvalStatus: {body.approvalStatus}")
    if body.source and body.source not in PROVENANCE_SOURCES:
        raise HTTPException(status_code=400, detail=f"Invalid source: {body.source}")
    if body.isProduction and body.approvalStatus != "approved":
        raise HTTPException(status_code=400, detail="A version must be approved before it can be marked production (production gating)")


@router.post("/{model_id}/versions", status_code=201, dependencies=[Depends(require_permission("avdm", "write"))])
async def add_version(
    model_id: str, body: VersionRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text("SELECT 1 FROM eam.ai_model_registry WHERE id = CAST(:id AS uuid)"), {"id": model_id})
    if not r.fetchone():
        raise HTTPException(status_code=404, detail="Model not found")
    _validate_version_payload(body)

    dup = await db.execute(text(
        "SELECT 1 FROM eam.ai_model_version WHERE model_id = CAST(:id AS uuid) AND version = :v"
    ), {"id": model_id, "v": body.version.strip()})
    if dup.fetchone():
        raise HTTPException(status_code=400, detail=f"Version '{body.version}' already exists for this model")

    if body.isProduction:
        await db.execute(text(
            "UPDATE eam.ai_model_version SET is_production = false, updated_at = NOW() WHERE model_id = CAST(:id AS uuid)"
        ), {"id": model_id})

    vid = str(uuid.uuid4())
    await db.execute(text(
        "INSERT INTO eam.ai_model_version (id, model_id, version, source, source_uri, checksum, license, "
        "training_data_provenance, approval_status, is_production, notes, created_by, updated_by) "
        "VALUES (CAST(:vid AS uuid), CAST(:mid AS uuid), :v, :src, :uri, :chk, :lic, :prov, :appr, :prod, :notes, :cb, :cb)"
    ), {"vid": vid, "mid": model_id, "v": body.version.strip(), "src": body.source, "uri": body.sourceUri,
        "chk": body.checksum, "lic": body.license, "prov": body.trainingDataProvenance,
        "appr": body.approvalStatus, "prod": body.isProduction, "notes": body.notes, "cb": user.id})
    await db.execute(text("UPDATE eam.ai_model_registry SET updated_at = NOW() WHERE id = CAST(:id AS uuid)"), {"id": model_id})
    await db.commit()
    return {"id": vid}


@router.put("/{model_id}/versions/{version_id}", dependencies=[Depends(require_permission("avdm", "write"))])
async def update_version(
    model_id: str, version_id: str, body: VersionRequest,
    db: AsyncSession = Depends(get_db), user: AuthUser = Depends(get_current_user),
):
    r = await db.execute(text(
        "SELECT 1 FROM eam.ai_model_version WHERE id = CAST(:vid AS uuid) AND model_id = CAST(:mid AS uuid)"
    ), {"vid": version_id, "mid": model_id})
    if not r.fetchone():
        raise HTTPException(status_code=404, detail="Version not found")
    _validate_version_payload(body)

    dup = await db.execute(text(
        "SELECT 1 FROM eam.ai_model_version WHERE model_id = CAST(:mid AS uuid) AND version = :v AND id <> CAST(:vid AS uuid)"
    ), {"mid": model_id, "v": body.version.strip(), "vid": version_id})
    if dup.fetchone():
        raise HTTPException(status_code=400, detail=f"Version '{body.version}' already exists for this model")

    if body.isProduction:
        await db.execute(text(
            "UPDATE eam.ai_model_version SET is_production = false, updated_at = NOW() "
            "WHERE model_id = CAST(:mid AS uuid) AND id <> CAST(:vid AS uuid)"
        ), {"mid": model_id, "vid": version_id})

    await db.execute(text(
        "UPDATE eam.ai_model_version SET version = :v, source = :src, source_uri = :uri, checksum = :chk, license = :lic, "
        "training_data_provenance = :prov, approval_status = :appr, is_production = :prod, notes = :notes, "
        "updated_by = :ub, updated_at = NOW() WHERE id = CAST(:vid AS uuid)"
    ), {"v": body.version.strip(), "src": body.source, "uri": body.sourceUri, "chk": body.checksum, "lic": body.license,
        "prov": body.trainingDataProvenance, "appr": body.approvalStatus, "prod": body.isProduction,
        "notes": body.notes, "ub": user.id, "vid": version_id})
    await db.commit()
    return {"message": "ok"}


@router.delete("/{model_id}/versions/{version_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_version(model_id: str, version_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text(
        "DELETE FROM eam.ai_model_version WHERE id = CAST(:vid AS uuid) AND model_id = CAST(:mid AS uuid)"
    ), {"vid": version_id, "mid": model_id})
    await db.commit()
    return {"message": "deleted"}
