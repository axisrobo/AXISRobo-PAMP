from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.architecture_review.ai.state import ArchitectureReviewState
from app.architecture_review.ai.workflow_common import BaseArchitectureReviewWorkflow, build_internal_payload


class TechArchitectureReviewWorkflow(BaseArchitectureReviewWorkflow):
    review_type = "Tech_Arch"

    def _build_workflow(self) -> StateGraph:
        graph = StateGraph(ArchitectureReviewState)
        graph.add_node("upload_architecture", self._upload_architecture)
        graph.add_node("prepare_review", self._prepare_review)
        graph.add_node("llm_review", self._llm_review)
        graph.add_edge(START, "upload_architecture")
        graph.add_edge("upload_architecture", "prepare_review")
        graph.add_edge("prepare_review", "llm_review")
        graph.add_edge("llm_review", END)
        return graph

    async def _prepare_review(self, state: ArchitectureReviewState) -> ArchitectureReviewState:
        return await self._prepare_image_for_review(state, enable_vision_extraction=False)


tech_architecture_review_workflow = TechArchitectureReviewWorkflow()


async def run_tech_arch_workflow(
    *,
    language: str,
    attachment_name: str,
    file_content: bytes,
    watch_headers: dict[str, str],
) -> dict:
    state = await tech_architecture_review_workflow.ainvoke(
        file_name=attachment_name.split("/")[-1],
        file_content=file_content,
        language=language,
        s3_url=attachment_name,
        source_application=watch_headers.get("sourceApplication", ""),
        chatbot_name=watch_headers.get("chatbotName", ""),
        session_id=watch_headers.get("sessionId", ""),
        trace_id=watch_headers.get("traceId", ""),
        span_id=watch_headers.get("spanId", ""),
        parent_span_id=watch_headers.get("parentSpanId", ""),
    )
    return build_internal_payload(state)
