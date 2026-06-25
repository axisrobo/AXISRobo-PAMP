from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.architecture_review.ai.models import ArchitectureReviewResult, AppArchitectureReviewResult


class ArchitectureReviewState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_name: str
    language: str
    image_base64: str
    file_content: bytes
    s3_url: str | None = None

    ocr_result: str | None = None
    llm_result: str | None = None
    raw_ocr_text: str | None = None
    content_extract_result: Any | None = None
    review_result: ArchitectureReviewResult | AppArchitectureReviewResult | None = None
    vision_token_usage: dict[str, int] | None = None
    review_token_usage: dict[str, int] | None = None
    error: str | None = None

    agent_watch_data: dict[str, Any] | None = None
    review_type: str | None = None
    app_arch_rule_name: str | None = None
    vision_task: asyncio.Task | None = None
