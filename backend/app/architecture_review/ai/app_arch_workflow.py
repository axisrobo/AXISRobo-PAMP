from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.architecture_review.ai.prompts import get_review_prompt
from app.architecture_review.ai.state import ArchitectureReviewState
from app.architecture_review.ai.workflow_common import BaseArchitectureReviewWorkflow, build_internal_payload


class AppArchitectureReviewWorkflow(BaseArchitectureReviewWorkflow):
    review_type = "App_Arch"

    def _build_workflow(self) -> StateGraph:
        graph = StateGraph(ArchitectureReviewState)
        graph.add_node("upload_architecture", self._upload_architecture)
        graph.add_node("ocr_recognition", self._ocr_recognition)
        graph.add_node("llm_review", self._llm_review)
        graph.add_edge(START, "upload_architecture")
        graph.add_edge("upload_architecture", "ocr_recognition")
        graph.add_edge("ocr_recognition", "llm_review")
        graph.add_edge("llm_review", END)
        return graph

    async def _ocr_recognition(self, state: ArchitectureReviewState) -> ArchitectureReviewState:
        return await self._prepare_image_for_review(state, enable_vision_extraction=True)

    def _build_review_prompt(self, state: ArchitectureReviewState) -> str:
        return get_review_prompt(self.review_type).replace(
            "{app_arch_rule_name}",
            state.app_arch_rule_name or settings.EA_AGENT_APP_ARCH_RULE_NAME,
        )


app_architecture_review_workflow = AppArchitectureReviewWorkflow()


async def run_app_arch_workflow(
    *,
    language: str,
    attachment_name: str,
    file_content: bytes,
    watch_headers: dict[str, str],
    app_arch_rule_name: str | None = None,
) -> dict:
    state = await app_architecture_review_workflow.ainvoke(
        file_name=attachment_name.split("/")[-1],
        file_content=file_content,
        language=language,
        s3_url=attachment_name,
        app_arch_rule_name=app_arch_rule_name,
        source_application=watch_headers.get("sourceApplication", ""),
        chatbot_name=watch_headers.get("chatbotName", ""),
        session_id=watch_headers.get("sessionId", ""),
        trace_id=watch_headers.get("traceId", ""),
        span_id=watch_headers.get("spanId", ""),
        parent_span_id=watch_headers.get("parentSpanId", ""),
    )
    return build_internal_payload(state)
