"""EA Review agent service entrypoints."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser
from app.architecture_review.ai.app_arch_service import process_app_attachment_ai_check as process_app_attachment_ai_check_impl
from app.architecture_review.ai.tech_arch_service import process_tech_attachment_ai_check as process_tech_attachment_ai_check_impl


async def process_app_attachment_ai_check(
    *,
    db: AsyncSession,
    user: AuthUser,
    request_id: str,
    language: str,
    attachment_name: str,
    attachment_uuid: str,
    file_content: bytes,
) -> dict[str, Any]:
    return await process_app_attachment_ai_check_impl(
        db=db,
        user=user,
        request_id=request_id,
        language=language,
        attachment_name=attachment_name,
        attachment_uuid=attachment_uuid,
        file_content=file_content,
    )


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
    return await process_tech_attachment_ai_check_impl(
        db=db,
        user=user,
        request_id=request_id,
        language=language,
        attachment_name=attachment_name,
        attachment_uuid=attachment_uuid,
        file_content=file_content,
    )


async def process_attachment_ai_check(
    *,
    db: AsyncSession,
    user: AuthUser,
    request_id: str,
    biz_type: str,
    language: str,
    attachment_name: str,
    attachment_uuid: str,
    file_content: bytes,
) -> dict[str, Any]:
    if biz_type == "App_Arch":
        return await process_app_attachment_ai_check(
            db=db,
            user=user,
            request_id=request_id,
            language=language,
            attachment_name=attachment_name,
            attachment_uuid=attachment_uuid,
            file_content=file_content,
        )
    if biz_type == "Tech_Arch":
        return await process_tech_attachment_ai_check(
            db=db,
            user=user,
            request_id=request_id,
            language=language,
            attachment_name=attachment_name,
            attachment_uuid=attachment_uuid,
            file_content=file_content,
        )
    raise ValueError(f"Unsupported attachment ai-check bizType: {biz_type}")
