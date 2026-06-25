from __future__ import annotations

from app.config import settings
from app.architecture_review.ai.app_arch_workflow import run_app_arch_workflow
from app.architecture_review.ai.tech_arch_workflow import run_tech_arch_workflow


async def run_internal_workflow(
    *,
    review_type: str,
    language: str,
    attachment_name: str,
    file_content: bytes,
    watch_headers: dict[str, str],
    app_arch_rule_name: str | None = None,
) -> dict:
    if not (settings.EA_AGENT_LLM_BASE_URL and settings.EA_AGENT_LLM_API_KEY and settings.EA_AGENT_LLM_MODEL):
        raise ValueError("EA agent internal LLM configuration is incomplete")
    if review_type == "App_Arch":
        return await run_app_arch_workflow(
            language=language,
            attachment_name=attachment_name,
            file_content=file_content,
            watch_headers=watch_headers,
            app_arch_rule_name=app_arch_rule_name,
        )
    if review_type == "Tech_Arch":
        return await run_tech_arch_workflow(
            language=language,
            attachment_name=attachment_name,
            file_content=file_content,
            watch_headers=watch_headers,
        )
    raise ValueError(f"Unsupported architecture review type: {review_type}")
