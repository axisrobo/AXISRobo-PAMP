"""EA Request Attachments — upload, delete, download, AI check."""
from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser
from app.auth.ownership import check_request_not_completed
from app.utils.s3_storage import make_key
from app.utils.storage import get_storage_provider
from app.architecture_review.ai import process_attachment_ai_check

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# POST /upload — Upload attachment
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    dependencies=[Depends(require_permission("ea_request", "write"))],
)
async def upload_attachment(
    file: UploadFile = File(...),
    requestId: str = Form(...),
    bizType: str = Form(...),
    appArchType: str = Form(""),
    originalName: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    if bizType not in ("App_Arch", "Tech_Arch", "Proj_Intro"):
        raise HTTPException(status_code=400, detail="bizType must be App_Arch, Tech_Arch, or Proj_Intro")

    req_result = await db.execute(
        text("SELECT status, project_id FROM eam.eam_request WHERE request_id = :rid"),
        {"rid": requestId},
    )
    req_row = req_result.mappings().first()
    if not req_row:
        raise HTTPException(status_code=404, detail="EA request not found")
    if not user.is_admin and not user.is_reviewer:
        await check_request_not_completed(dict(req_row), operation="upload")

    if bizType in ("App_Arch", "Tech_Arch"):
        project_id = req_row.get("project_id")
        assessment_result = await db.execute(
            text(
                "SELECT evaluation, artifact_selection FROM eam.avdm_project_assessment "
                "WHERE project_id = :pid"
            ),
            {"pid": project_id},
        )
        assessment = assessment_result.mappings().first()
        if not assessment or not assessment.get("evaluation"):
            raise HTTPException(
                status_code=400,
                detail="Please complete AVDM questionnaire and concern identification before uploading architecture diagrams",
            )
        artifact_selection = assessment.get("artifact_selection") or []
        if not artifact_selection:
            raise HTTPException(
                status_code=400,
                detail="Please complete artifact selection from major concerns before uploading architecture diagrams",
            )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    count_result = await db.execute(
        text(
            "SELECT COUNT(*) FROM eam.eam_request_attachment "
            "WHERE request_id = :rid AND biz_type = :btype"
        ),
        {"rid": requestId, "btype": bizType},
    )
    seq = (count_result.scalar() or 0) + 1

    ext = (file.filename or "file.png").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "png"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S") + f"{datetime.now().microsecond // 1000:03d}"
    new_filename = f"{seq}-{timestamp}.{ext}"

    storage = get_storage_provider(db)
    storage_key = make_key(new_filename)
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    await storage.upload(storage_key, content, content_type=content_type)

    attachment_id = str(uuid.uuid4())
    original_name = originalName or file.filename or new_filename
    await db.execute(
        text(
            "INSERT INTO eam.eam_request_attachment "
            "(id, request_id, attachment_name, biz_type, app_arch_type, original_name, create_by, create_at) "
            "VALUES (:id, :rid, :aname, :btype, :atype, :oname, :cby, NOW())"
        ),
        {
            "id": attachment_id,
            "rid": requestId,
            "aname": storage_key,
            "btype": bizType,
            "atype": appArchType or None,
            "oname": original_name,
            "cby": user.id,
        },
    )
    await db.commit()

    return {
        "attachmentName": storage_key,
        "attachmentUuid": attachment_id,
        "fileName": new_filename,
        "originalName": original_name,
    }


# ---------------------------------------------------------------------------
# DELETE /{id} — Delete attachment
# ---------------------------------------------------------------------------

@router.delete(
    "/{attachment_id}",
    dependencies=[Depends(require_permission("ea_request", "write"))],
)
async def delete_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM eam.eam_request_attachment WHERE id = :id"),
        {"id": attachment_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")
    attachment = dict(row._mapping)

    storage = get_storage_provider(db)
    storage_key = attachment.get("attachment_name") or ""
    if storage_key:
        await storage.delete(storage_key)

    ai_check_rows = await db.execute(
        text("SELECT id::text FROM eam.eam_arch_ai_check WHERE attachment_uuid = :uuid"),
        {"uuid": attachment_id},
    )
    ai_check_ids = [row[0] for row in ai_check_rows.fetchall()]

    if ai_check_ids:
        await db.execute(
            text("DELETE FROM eam.eam_arch_ai_check_app WHERE ai_check_id = ANY(:ids)"),
            {"ids": ai_check_ids},
        )
        await db.execute(
            text("DELETE FROM eam.eam_arch_ai_check_interaction WHERE ai_check_id = ANY(:ids)"),
            {"ids": ai_check_ids},
        )

    await db.execute(
        text("DELETE FROM eam.eam_arch_ai_check WHERE attachment_uuid = :uuid"),
        {"uuid": attachment_id},
    )

    await db.execute(
        text("DELETE FROM eam.eam_request_attachment WHERE id = :id"),
        {"id": attachment_id},
    )
    await db.commit()

    return {"message": "deleted"}


# ---------------------------------------------------------------------------
# GET /{id}/file — Download/serve attachment file
# ---------------------------------------------------------------------------

@router.get(
    "/{attachment_id}/file",
    dependencies=[Depends(require_permission("ea_request", "read"))],
)
async def download_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT attachment_name FROM eam.eam_request_attachment WHERE id = :id"),
        {"id": attachment_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")

    storage_key = row._mapping.get("attachment_name") or ""
    if not storage_key:
        raise HTTPException(status_code=404, detail="Attachment path is empty")

    storage = get_storage_provider(db)
    try:
        content = await storage.download(storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in storage")

    media_type = mimetypes.guess_type(storage_key)[0] or "application/octet-stream"
    return Response(content=content, media_type=media_type)


# ---------------------------------------------------------------------------
# GET /{id}/download — Stream file content with Content-Disposition: attachment
# ---------------------------------------------------------------------------

@router.get(
    "/{attachment_id}/download",
    dependencies=[Depends(require_permission("ea_request", "read"))],
)
async def download_attachment_file(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
):
    import os
    import urllib.parse

    result = await db.execute(
        text("SELECT attachment_name FROM eam.eam_request_attachment WHERE id = :id"),
        {"id": attachment_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")

    storage_key = row._mapping.get("attachment_name") or ""
    if not storage_key:
        raise HTTPException(status_code=404, detail="Attachment path is empty")

    storage = get_storage_provider(db)
    try:
        content = await storage.download(storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in storage")

    filename = os.path.basename(storage_key)
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    encoded_name = urllib.parse.quote(filename)

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{encoded_name}"; filename*=UTF-8\'\'{encoded_name}',
        },
    )


# ---------------------------------------------------------------------------
# PUT /{id} — Update attachment (e.g. appArchType)
# ---------------------------------------------------------------------------

@router.put(
    "/{attachment_id}",
    dependencies=[Depends(require_permission("ea_request", "write"))],
)
async def update_attachment(
    attachment_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id FROM eam.eam_request_attachment WHERE id = :id"),
        {"id": attachment_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Attachment not found")

    app_arch_type = body.get("appArchType")
    if app_arch_type is not None:
        await db.execute(
            text(
                "UPDATE eam.eam_request_attachment SET app_arch_type = :atype WHERE id = :id"
            ),
            {"atype": app_arch_type, "id": attachment_id},
        )
        await db.commit()

    return {"message": "updated"}


# ---------------------------------------------------------------------------
# POST /ai-check — AI architecture check
# ---------------------------------------------------------------------------

@router.post(
    "/ai-check",
    dependencies=[Depends(require_permission("ea_request", "write"))],
)
async def ai_check(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    request_id = body.get("requestId")
    biz_type = body.get("bizType")
    language = body.get("language", "zh")
    attachment_name = body.get("attachmentName")
    attachment_uuid = body.get("attachmentUuid")

    if not all([request_id, biz_type, attachment_name, attachment_uuid]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    storage = get_storage_provider(db)
    try:
        file_content = await storage.download(attachment_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Architecture diagram file not found")

    return await process_attachment_ai_check(
        db=db,
        user=user,
        request_id=request_id,
        biz_type=biz_type,
        language=language,
        attachment_name=attachment_name,
        attachment_uuid=attachment_uuid,
        file_content=file_content,
    )
