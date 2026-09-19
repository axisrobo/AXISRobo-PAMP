"""Compatibility export router."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_permission
from app.database import get_db


router = APIRouter()

ENTITY_QUERIES = {
    "certifications": "SELECT * FROM pamp.certification ORDER BY id DESC LIMIT 1000",
    "projects": "SELECT * FROM pamp.pamp_project ORDER BY created_at DESC LIMIT 1000",
    "ea-requests": "SELECT * FROM pamp.pamp_architecture_review ORDER BY id DESC LIMIT 1000",
    "meetings": "SELECT * FROM pamp.pamp_meeting ORDER BY id DESC LIMIT 1000",
    "actions": "SELECT * FROM pamp.pamp_actions ORDER BY id DESC LIMIT 1000",
    "technology-stack": "SELECT * FROM pamp.tech_stack_master_data ORDER BY id DESC LIMIT 1000",
}


@router.get("/{entity}", dependencies=[Depends(require_permission("export", "execute"))])
async def export_entity(entity: str, db: AsyncSession = Depends(get_db)):
    query = ENTITY_QUERIES.get(entity)
    if not query:
        raise HTTPException(status_code=404, detail="Unknown export entity")
    try:
        result = await db.execute(text(query))
        rows = [dict(row) for row in result.mappings().all()]
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        else:
            output.write("\n")
        buffer = io.BytesIO(output.getvalue().encode("utf-8"))
        return StreamingResponse(
            buffer,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={entity}.csv"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to export entity") from exc