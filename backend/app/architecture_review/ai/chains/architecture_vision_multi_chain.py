from __future__ import annotations

import json
from typing import List, Tuple

from langchain_openai import ChatOpenAI

from app.config import settings
from app.architecture_review.ai.chains.architect_review_chain import extract_json


class ArchitectureVisionMultiChain:
    @staticmethod
    def _extract_token_usage(response) -> dict[str, int]:
        usage = getattr(response, "usage_metadata", {}) or {}
        metadata = getattr(response, "response_metadata", {}) or {}
        token_usage = metadata.get("token_usage", {}) or {}
        prompt_tokens = usage.get("input_tokens", token_usage.get("prompt_tokens", 0) or 0)
        completion_tokens = usage.get("output_tokens", token_usage.get("completion_tokens", 0) or 0)
        total_tokens = usage.get("total_tokens", token_usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _build_messages(prompt: str, context: str, image_base64s: List[str]) -> list[dict]:
        images = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            }
            for image_base64 in image_base64s
        ]
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "text", "text": context}] + images},
        ]

    @staticmethod
    def _build_llm(headers: dict[str, str] | None = None) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=settings.EA_AGENT_LLM_BASE_URL,
            api_key=settings.EA_AGENT_LLM_API_KEY,
            model=settings.EA_AGENT_VISION_MODEL or settings.EA_AGENT_LLM_MODEL,
            default_headers=headers,
            temperature=0,
            timeout=settings.EA_AGENT_LLM_TIMEOUT_SECONDS,
            max_retries=settings.EA_AGENT_LLM_MAX_RETRIES,
        )

    async def ainvoke(
        self,
        image_base64s: List[str],
        context: str,
        prompt: str,
        language: str = "en",
        **kwargs,
    ) -> Tuple[dict, dict[str, int]]:
        headers = {
            "sourceApplication": kwargs.get("source_application", ""),
            "chatbotName": kwargs.get("chatbot_name", ""),
            "sessionId": kwargs.get("session_id", ""),
            "traceId": kwargs.get("trace_id", ""),
            "spanId": kwargs.get("span_id", ""),
            "parentSpanId": kwargs.get("parent_span_id", ""),
        }
        response = await self._build_llm(headers=headers).ainvoke(self._build_messages(prompt, context, image_base64s))
        metadata = getattr(response, "response_metadata", {}) or {}
        if metadata.get("finish_reason") == "content_filter":
            raise RuntimeError("E_VISION_CONTENT_FILTER")
        return json.loads(extract_json(response.content)), self._extract_token_usage(response)


architecture_vision_multi_chain = ArchitectureVisionMultiChain()
