"""Application architecture review service entrypoints."""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser
from app.config import settings
from app.architecture_review.ai.service_common import normalize_string, normalize_string_list, run_attachment_ai_check


async def persist_app_content_extract_result(
    *,
    db: AsyncSession,
    ai_check_id: str,
    content_extract_result: Any,
    user_id: str,
) -> None:
    if not isinstance(content_extract_result, dict):
        return

    applications = content_extract_result.get("applications")
    interactions = content_extract_result.get("interactions")

    if isinstance(applications, list):
        for app in applications:
            if not isinstance(app, dict):
                continue
            await db.execute(
                text(
                    """
                    INSERT INTO eam.eam_arch_ai_check_app (
                        id, ai_check_id, app_id, id_is_standard, standard_id, app_name,
                        functions, check_app_status, status, create_at, create_by, type
                    ) VALUES (
                        gen_random_uuid(), :ai_check_id, :app_id, :id_is_standard, :standard_id, :app_name,
                        :functions, :check_app_status, :status, NOW(), :create_by, :type
                    )
                    """
                ),
                {
                    "ai_check_id": ai_check_id,
                    "app_id": normalize_string(app.get("id")),
                    "id_is_standard": app.get("id_is_standard"),
                    "standard_id": normalize_string(app.get("standard_id")),
                    "app_name": normalize_string(app.get("name")),
                    "functions": normalize_string_list(app.get("functions")),
                    "check_app_status": normalize_string(app.get("application_status")),
                    "status": "Waiting to Confirm",
                    "create_by": user_id,
                    "type": "aicheck",
                },
            )

    if isinstance(interactions, list):
        for interaction in interactions:
            if not isinstance(interaction, dict):
                continue
            await db.execute(
                text(
                    """
                    INSERT INTO eam.eam_arch_ai_check_interaction (
                        id, ai_check_id, source_app_id, target_app_id, interaction_type,
                        direction, source_function, target_function, interface_status,
                        status,
                        business_object, create_at, create_by, type
                    ) VALUES (
                        gen_random_uuid(), :ai_check_id, :source_app_id, :target_app_id, :interaction_type,
                        :direction, :source_function, :target_function, :interface_status,
                        :status,
                        :business_object, NOW(), :create_by, :type
                    )
                    """
                ),
                {
                    "ai_check_id": ai_check_id,
                    "source_app_id": normalize_string(interaction.get("source_app_id")),
                    "target_app_id": normalize_string(interaction.get("target_app_id")),
                    "interaction_type": normalize_string(interaction.get("interaction_type")),
                    "direction": normalize_string(interaction.get("direction")),
                    "source_function": normalize_string(interaction.get("source_function")),
                    "target_function": normalize_string(interaction.get("target_function")),
                    "interface_status": normalize_string(interaction.get("interface_status")),
                    "status": "Waiting to Confirm",
                    "business_object": normalize_string(interaction.get("business_object")),
                    "create_by": user_id,
                    "type": "aicheck",
                },
            )


async def resolve_app_arch_rule_name(
    *,
    db: AsyncSession,
    attachment_uuid: str,
) -> str:
    result = await db.execute(
        text("SELECT app_arch_type FROM eam.eam_request_attachment WHERE id = :id"),
        {"id": attachment_uuid},
    )
    row = result.fetchone()
    return (row._mapping.get("app_arch_type") if row else None) or settings.EA_AGENT_APP_ARCH_RULE_NAME


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
    return await run_attachment_ai_check(
        db=db,
        user=user,
        request_id=request_id,
        biz_type="App_Arch",
        language=language,
        attachment_name=attachment_name,
        attachment_uuid=attachment_uuid,
        file_content=file_content,
        app_arch_rule_name=await resolve_app_arch_rule_name(db=db, attachment_uuid=attachment_uuid),
        persist_app_extract_result=True,
        persist_content_extract_result=persist_app_content_extract_result,
    )
