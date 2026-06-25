"""Shared EA review service helpers."""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser
from app.config import settings
from app.architecture_review.ai.agent_watch import agent_watch
from app.architecture_review.ai.workflow import run_internal_workflow

logger = logging.getLogger("eam.ea_agents.service")


def build_watch_context(user: AuthUser) -> dict[str, str]:
    return {
        "source_application": settings.AGENT_WATCH_APPLICATION_NAME,
        "chatbot_name": settings.AGENT_WATCH_CHATBOT_NAME,
        "session_id": agent_watch.generate_trace_id(),
        "trace_id": agent_watch.generate_trace_id(),
        "span_id": agent_watch.generate_span_id(),
        "parent_span_id": agent_watch.generate_span_id(),
        "user_id": getattr(user, "itcode", user.id),
    }


def build_llm_watch_headers(watch: dict[str, str]) -> dict[str, str]:
    return {
        "sourceApplication": watch["source_application"],
        "chatbotName": watch["chatbot_name"],
        "sessionId": watch["session_id"],
        "traceId": watch["trace_id"],
        "spanId": watch["span_id"],
        "parentSpanId": watch["parent_span_id"],
    }


def normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        item_text = normalize_string(item)
        if item_text:
            normalized.append(item_text)
    return normalized


async def run_attachment_ai_check(
    *,
    db: AsyncSession,
    user: AuthUser,
    request_id: str,
    biz_type: str,
    language: str,
    attachment_name: str,
    attachment_uuid: str,
    file_content: bytes,
    app_arch_rule_name: str | None = None,
    persist_app_extract_result: bool = False,
    persist_content_extract_result: Any | None = None,
) -> dict[str, Any]:
    total_started_at = time.perf_counter()
    watch = build_watch_context(user)
    send_timestamp = datetime.now(timezone.utc)
    filename = Path(attachment_name).name

    agent_watch.send_request(
        session_id=watch["session_id"],
        trace_id=watch["trace_id"],
        span_id=watch["span_id"],
        parent_span_id=watch["parent_span_id"],
        chatbot_name=watch["chatbot_name"],
        target_application=watch["source_application"],
        input_data={"document": filename},
        user_id=watch["user_id"],
        action="do_architecture_review",
        scenario="AxisArch",
    )
    check_started_at = time.perf_counter()
    internal_payload = await run_internal_workflow(
        review_type=biz_type,
        language=language,
        attachment_name=attachment_name,
        file_content=file_content,
        watch_headers=build_llm_watch_headers(watch),
        app_arch_rule_name=app_arch_rule_name,
    )
    check_cost_ms = int((time.perf_counter() - check_started_at) * 1000)
    ai_result = internal_payload.get("result")
    content_extract_result = internal_payload.get("content_extract_result")
    ai_check_id = str(uuid.uuid4())

    score = None
    if isinstance(ai_result, dict):
        overall = ai_result.get("overall_evaluation")
        if isinstance(overall, dict):
            score = overall.get("score")

    if persist_app_extract_result and callable(persist_content_extract_result):
        await persist_content_extract_result(
            db=db,
            ai_check_id=ai_check_id,
            content_extract_result=content_extract_result,
            user_id=user.id,
        )

    total_cost_ms = int((time.perf_counter() - total_started_at) * 1000)

    await db.execute(
        text(
            """
            INSERT INTO eam.eam_arch_ai_check
                (id, attachment_uuid, result, request, create_by, create_at, total_cost, check_cost)
            VALUES
                (:id, :uuid, :result, :req, :cby, NOW(), :total_cost, :check_cost)
            """
        ),
        {
            "id": ai_check_id,
            "uuid": attachment_uuid,
            "result": json.dumps(ai_result, ensure_ascii=False),
            "req": json.dumps(
                {
                    "requestId": request_id,
                    "bizType": biz_type,
                    "language": language,
                    "attachmentName": attachment_name,
                    "attachmentUuid": attachment_uuid,
                },
                ensure_ascii=False,
            ),
            "cby": user.id,
            "total_cost": total_cost_ms,
            "check_cost": check_cost_ms,
        },
    )

    await db.commit()

    agent_watch.receive_response(
        session_id=watch["session_id"],
        trace_id=watch["trace_id"],
        span_id=watch["span_id"],
        parent_span_id=watch["parent_span_id"],
        chatbot_name=watch["chatbot_name"],
        status_code=200,
        target_application=watch["source_application"],
        output=json.dumps(ai_result, ensure_ascii=False) if isinstance(ai_result, dict) else str(ai_result),
        output_type="non-stream",
        send_timestamp=send_timestamp,
        first_token_timestamp=datetime.now(timezone.utc),
        result="succeed",
        user_id=watch["user_id"],
        action="do_architecture_review",
        scenario="AxisArch",
    )

    return {
        "score": score,
        "result": ai_result,
        "attachmentUuid": attachment_uuid,
        "aiCheckId": ai_check_id,
    }
