from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
from copy import deepcopy
from datetime import datetime, timezone

from PIL import Image, ImageOps

from app.config import settings
from app.architecture_review.ai.agent_watch import agent_watch
from app.architecture_review.ai.chains import architect_review_chain, architecture_vision_multi_chain
from app.architecture_review.ai.prompts import get_info_extract_prompt, get_review_prompt
from app.architecture_review.ai.state import ArchitectureReviewState

logger = logging.getLogger("eam.ea_agents.workflow")


class BaseArchitectureReviewWorkflow:
    _semaphore = asyncio.Semaphore(settings.EA_AGENT_CONCURRENCY_LIMIT)
    review_type = "Tech_Arch"

    def __init__(self) -> None:
        self.workflow = self._build_workflow().compile()

    def _build_workflow(self):
        raise NotImplementedError

    async def ainvoke(
        self,
        *,
        file_name: str,
        file_content: bytes,
        language: str,
        s3_url: str,
        app_arch_rule_name: str | None = None,
        **kwargs,
    ) -> ArchitectureReviewState:
        async with self._semaphore:
            image_base64 = base64.b64encode(file_content).decode("utf-8")
            initial_state = ArchitectureReviewState(
                file_name=file_name,
                language=language,
                image_base64=image_base64,
                file_content=file_content,
                s3_url=s3_url,
                agent_watch_data=kwargs,
                review_type=self.review_type,
                app_arch_rule_name=app_arch_rule_name,
            )
            state = await self.workflow.ainvoke(initial_state)
            return ArchitectureReviewState(**state)

    async def _upload_architecture(self, state: ArchitectureReviewState) -> ArchitectureReviewState:
        kwargs = state.agent_watch_data or {}
        send_timestamp = datetime.now(timezone.utc)
        span_id = agent_watch.generate_span_id()
        agent_watch.send_request(
            session_id=kwargs.get("session_id"),
            trace_id=kwargs.get("trace_id"),
            span_id=span_id,
            parent_span_id=kwargs.get("span_id"),
            target_application="S3 Service",
            input_data={"document": state.file_name, "s3_url": state.s3_url},
            user_id=kwargs.get("user_id"),
            chatbot_name=kwargs.get("chatbot_name"),
            action="reuse_uploaded_file",
            tags=kwargs.get("tags", []),
            custom_property=kwargs.get("custom_property"),
            scenario=kwargs.get("scenario", "AxisArch"),
        )
        agent_watch.receive_response(
            session_id=kwargs.get("session_id"),
            trace_id=kwargs.get("trace_id"),
            span_id=span_id,
            parent_span_id=kwargs.get("span_id"),
            status_code=200,
            target_application="S3 Service",
            output=f"s3_url: {state.s3_url}",
            output_type="non-stream",
            send_timestamp=send_timestamp,
            first_token_timestamp=datetime.now(timezone.utc),
            result="succeed",
            user_id=kwargs.get("user_id"),
            chatbot_name=kwargs.get("chatbot_name"),
            action="reuse_uploaded_file",
            tags=kwargs.get("tags", []),
            custom_property=kwargs.get("custom_property"),
            scenario=kwargs.get("scenario", "AxisArch"),
        )
        return state

    async def _run_vision_extract(self, state: ArchitectureReviewState, vision_context: dict, kwargs: dict) -> dict:
        result_payload = {
            "ocr_result": None,
            "llm_result": None,
            "content_extract_result": None,
            "vision_token_usage": None,
            "error": None,
        }
        send_timestamp = datetime.now(timezone.utc)
        span_id = agent_watch.generate_span_id()
        agent_watch.send_request(
            session_id=kwargs.get("session_id"),
            trace_id=kwargs.get("trace_id"),
            span_id=span_id,
            parent_span_id=kwargs.get("span_id"),
            target_application="aiVerse",
            input_data={"document": state.file_name, "stage": "ocr_recognition"},
            user_id=kwargs.get("user_id"),
            chatbot_name=kwargs.get("chatbot_name"),
            action="ocr_recognition",
            tags=kwargs.get("tags", []),
            custom_property=kwargs.get("custom_property"),
            scenario=kwargs.get("scenario", "AxisArch"),
        )
        try:
            vision_prompt = get_info_extract_prompt(self.review_type)
            logger.info(
                "Using vision prompt review_type=%s prompt_preview=%r",
                self.review_type,
                vision_prompt[:200],
            )
            vision_json, vision_token_usage = await architecture_vision_multi_chain.ainvoke(
                image_base64s=[state.image_base64],
                context=json.dumps(vision_context, ensure_ascii=False),
                prompt=vision_prompt,
                language=state.language,
                **kwargs,
            )
            state.vision_token_usage = vision_token_usage
            state.content_extract_result = vision_json
            state.ocr_result = json.dumps(vision_json, ensure_ascii=False)
            state.llm_result = state.ocr_result
            result_payload.update(
                {
                    "content_extract_result": state.content_extract_result,
                    "ocr_result": state.ocr_result,
                    "llm_result": state.llm_result,
                    "vision_token_usage": vision_token_usage,
                }
            )
        except Exception as exc:
            if str(exc) == "E_VISION_CONTENT_FILTER":
                blocked_payload = {
                    "error_code": "E_VISION_CONTENT_FILTER",
                    "message": "Vision extraction blocked by content filter",
                }
                state.content_extract_result = blocked_payload
                state.ocr_result = json.dumps(blocked_payload, ensure_ascii=False)
                state.llm_result = state.ocr_result
                result_payload.update(
                    {
                        "content_extract_result": state.content_extract_result,
                        "ocr_result": state.ocr_result,
                        "llm_result": state.llm_result,
                    }
                )
            else:
                logger.exception("Failed to perform OCR vision extraction")
                state.error = f"OCR vision extraction failed: {exc}"
                result_payload["error"] = state.error
        finally:
            agent_watch.receive_response(
                session_id=kwargs.get("session_id"),
                trace_id=kwargs.get("trace_id"),
                span_id=span_id,
                parent_span_id=kwargs.get("span_id"),
                status_code=200 if not state.error else 500,
                target_application="aiVerse",
                output=state.ocr_result or "",
                output_type="non-stream",
                send_timestamp=send_timestamp,
                first_token_timestamp=datetime.now(timezone.utc),
                result="succeed" if not state.error else "failed",
                user_id=kwargs.get("user_id"),
                chatbot_name=kwargs.get("chatbot_name"),
                action="ocr_recognition",
                tags=kwargs.get("tags", []),
                custom_property=kwargs.get("custom_property"),
                scenario=kwargs.get("scenario", "AxisArch"),
            )
        return result_payload

    async def _prepare_image_for_review(
        self,
        state: ArchitectureReviewState,
        *,
        enable_vision_extraction: bool,
    ) -> ArchitectureReviewState:
        if state.error:
            return state
        try:
            image = Image.open(io.BytesIO(state.file_content))
            image = ImageOps.exif_transpose(image).convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=95)
            state.image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            vision_context = {"full_text": "", "tiles": []}
            state.raw_ocr_text = ""
            state.llm_result = json.dumps(vision_context, ensure_ascii=False)
            if not enable_vision_extraction:
                state.content_extract_result = None
                return state
            state.vision_task = asyncio.create_task(self._run_vision_extract(state, vision_context, state.agent_watch_data or {}))
        except Exception as exc:
            logger.exception("Failed to prepare image for OCR recognition")
            state.error = f"OCR recognition failed: {exc}"
        return state

    def _build_review_prompt(self, state: ArchitectureReviewState) -> str:
        return get_review_prompt(self.review_type)

    async def _llm_review(self, state: ArchitectureReviewState) -> ArchitectureReviewState:
        if state.error:
            return state
        review_prompt = self._build_review_prompt(state)
        logger.info(
            "Using review prompt review_type=%s prompt_preview=%r",
            self.review_type,
            review_prompt[:200],
        )
        kwargs = deepcopy(state.agent_watch_data or {})
        send_timestamp = datetime.now(timezone.utc)
        span_id = agent_watch.generate_span_id()
        agent_watch.send_request(
            session_id=kwargs.get("session_id"),
            trace_id=kwargs.get("trace_id"),
            span_id=span_id,
            parent_span_id=kwargs.get("span_id"),
            target_application="aiVerse",
            input_data={"prompt": review_prompt},
            user_id=kwargs.get("user_id"),
            chatbot_name=kwargs.get("chatbot_name"),
            action="llm_architecture_review",
            tags=kwargs.get("tags", []),
            custom_property=kwargs.get("custom_property"),
            scenario=kwargs.get("scenario", "AxisArch"),
        )
        try:
            review_result, review_token_usage = await architect_review_chain.ainvoke(
                review_type=self.review_type,
                image_base64=state.image_base64,
                architect_context=state.llm_result or "",
                language=state.language,
                prompt=review_prompt,
                app_arch_rule_name=state.app_arch_rule_name or "",
                **kwargs,
            )
            state.review_result = review_result
            state.review_token_usage = review_token_usage
        except Exception as exc:
            logger.exception("Failed to perform LLM review")
            state.error = f"LLM review failed: {exc}"

        if state.vision_task:
            vision_result = await state.vision_task
            if isinstance(vision_result, dict):
                if vision_result.get("ocr_result") is not None:
                    state.ocr_result = vision_result.get("ocr_result")
                if vision_result.get("llm_result") is not None:
                    state.llm_result = vision_result.get("llm_result")
                if vision_result.get("content_extract_result") is not None:
                    state.content_extract_result = vision_result.get("content_extract_result")
                if vision_result.get("vision_token_usage") is not None:
                    state.vision_token_usage = vision_result.get("vision_token_usage")
                if vision_result.get("error"):
                    state.error = vision_result.get("error")

        if state.review_result:
            state.review_result.content_extract_result = state.content_extract_result

        agent_watch.receive_response(
            session_id=kwargs.get("session_id"),
            trace_id=kwargs.get("trace_id"),
            span_id=span_id,
            parent_span_id=kwargs.get("span_id"),
            status_code=200 if not state.error else 500,
            target_application="aiVerse",
            output=json.dumps(state.review_result.model_dump(mode="json"), ensure_ascii=False) if state.review_result else "",
            output_type="non-stream",
            send_timestamp=send_timestamp,
            first_token_timestamp=datetime.now(timezone.utc),
            result="succeed" if not state.error else "failed",
            user_id=kwargs.get("user_id"),
            chatbot_name=kwargs.get("chatbot_name"),
            action="llm_architecture_review",
            tags=kwargs.get("tags", []),
            custom_property=kwargs.get("custom_property"),
            scenario=kwargs.get("scenario", "AxisArch"),
        )
        return state


def build_internal_payload(state: ArchitectureReviewState) -> dict:
    if state.error:
        raise ValueError(state.error)
    if not state.review_result:
        raise ValueError("Architecture review did not produce a result")
    return {
        "result": state.review_result.model_dump(mode="json"),
        "ocr_content": state.ocr_result,
        "llm_result": state.llm_result,
        "content_extract_result": state.content_extract_result,
    }
