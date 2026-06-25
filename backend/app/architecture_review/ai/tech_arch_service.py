"""Technical architecture review service entrypoints."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser
from app.architecture_review.ai.service_common import run_attachment_ai_check


async def process_tech_attachment_ai_check(
    *,
    db: AsyncSession,
    user: AuthUser,
    request_id: str,
    language: str,
    attachment_name: str,
    attachment_uuid: str,
    file_content: bytes,
) -> dict[str, Any]:
    return await run_attachment_ai_check(
        db=db,
        user=user,
        request_id=request_id,
        biz_type="Tech_Arch",
        language=language,
        attachment_name=attachment_name,
        attachment_uuid=attachment_uuid,
        file_content=file_content,
    )
