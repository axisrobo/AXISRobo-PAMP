from __future__ import annotations

import json
import re
from typing import Tuple, Union

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import TypeAdapter

from app.config import settings
from app.architecture_review.ai.chains.architect_review_app_strategy import AppReviewNormalizer
from app.architecture_review.ai.chains.architect_review_normalizer_base import ReviewResultNormalizer
from app.architecture_review.ai.chains.architect_review_response_extractor import ArchitectReviewResponseExtractor
from app.architecture_review.ai.chains.architect_review_tech_strategy import TechReviewNormalizer
from app.architecture_review.ai.models import ArchitectureReviewResult, AppArchitectureReviewResult


ReviewResult = Union[ArchitectureReviewResult, AppArchitectureReviewResult]

REVIEW_TYPE_APP = "App_Arch"
REVIEW_TYPE_TECH = "Tech_Arch"


def extract_json(content: str) -> str:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM response is empty")

    decoder = json.JSONDecoder()
    candidates: list[str] = []

    # Prefer fenced JSON block when model wraps output in markdown.
    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.IGNORECASE | re.DOTALL)
    candidates.extend(fenced_blocks)
    candidates.append(content)

    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        text = candidate.strip()
        if not text:
            continue
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError as exc:
            last_error = exc

        for idx, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                _, end = decoder.raw_decode(text[idx:])
                return text[idx : idx + end]
            except json.JSONDecodeError as exc:
                last_error = exc

    raise ValueError("LLM response does not contain valid JSON") from last_error


class ArchitectReviewChain:
    def __init__(self) -> None:
        self.response_extractor = ArchitectReviewResponseExtractor()
        self.tech_normalizer = TechReviewNormalizer()
        self.app_normalizer = AppReviewNormalizer()
        self.type_adapters: dict[str, TypeAdapter] = {
            REVIEW_TYPE_TECH: TypeAdapter(ArchitectureReviewResult),
            REVIEW_TYPE_APP: TypeAdapter(AppArchitectureReviewResult),
        }
        self.result_normalizers: dict[str, ReviewResultNormalizer] = {
            REVIEW_TYPE_TECH: self.tech_normalizer,
            REVIEW_TYPE_APP: self.app_normalizer,
        }

    def _get_type_adapter(self, review_type: str) -> TypeAdapter:
        return self.type_adapters.get(review_type, self.type_adapters[REVIEW_TYPE_TECH])

    def _get_result_normalizer(self, review_type: str) -> ReviewResultNormalizer:
        return self.result_normalizers.get(review_type, self.result_normalizers[REVIEW_TYPE_TECH])

    @staticmethod
    def _derive_summary(score: float, issues: list[dict]) -> str:
        if issues:
            issue_count = len(issues)
            noun = "issue" if issue_count == 1 else "issues"
            return f"Overall evaluation derived from score breakdown. {issue_count} {noun} identified."
        if score > 0:
            return "Overall evaluation derived from score breakdown."
        return ""

    @staticmethod
    def _derive_recommendations(issues: list[dict], recommendations_raw: object) -> list[str]:
        if isinstance(recommendations_raw, list):
            cleaned = [str(item).strip() for item in recommendations_raw if str(item).strip()]
            if cleaned:
                return cleaned

        recommendations: list[str] = []
        seen: set[str] = set()
        for issue in issues:
            suggestion = str(issue.get("suggestion") or "").strip()
            if suggestion and suggestion not in seen:
                seen.add(suggestion)
                recommendations.append(suggestion)
        return recommendations

    def _build_normalized_result(self, result: dict, score_breakdown: dict | None, issues: list[dict]) -> dict:
        title = str(result.get("title") or "")

        overall = result.get("overall_evaluation")
        if not isinstance(overall, dict):
            overall = result.get("overall") if isinstance(result.get("overall"), dict) else {}

        raw_score = overall.get("score")
        if isinstance(raw_score, str):
            raw_score = raw_score.strip()
        if raw_score in (None, ""):
            raw_score = result.get("score")
            if isinstance(raw_score, str):
                raw_score = raw_score.strip()
        raw_summary = overall.get("summary", result.get("summary", ""))
        has_explicit_score = raw_score not in (None, "")
        normalized_score = self.response_extractor.normalize_score(raw_score) if has_explicit_score else 0.0
        derived_score = self.response_extractor.derive_overall_score(score_breakdown)
        if derived_score is not None and not has_explicit_score:
            normalized_score = derived_score
        normalized_summary = str(raw_summary or "").strip()
        if not normalized_summary:
            normalized_summary = self._derive_summary(normalized_score, issues)
        normalized_overall = {
            "score": normalized_score,
            "summary": normalized_summary,
        }

        return {
            "title": title,
            "overall_evaluation": normalized_overall,
            "score_breakdown": score_breakdown,
            "issues": issues,
            "recommendations": self._derive_recommendations(issues, result.get("recommendations")),
        }

    def _new_chat_prompt_template(self, prompt_template: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                ("system", prompt_template),
                (
                    "user",
                    [
                        {
                            "type": "text",
                            "text": "Please review the following architecture diagram.\nYou must review in language {language}\n# architecture context\n{architect_context}",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                ),
            ]
        )

    def _build_llm(self, headers: dict[str, str] | None = None) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=settings.EA_AGENT_LLM_BASE_URL,
            api_key=settings.EA_AGENT_LLM_API_KEY,
            model=settings.EA_AGENT_LLM_MODEL,
            default_headers=headers,
            temperature=0,
            timeout=settings.EA_AGENT_LLM_TIMEOUT_SECONDS,
            max_retries=settings.EA_AGENT_LLM_MAX_RETRIES,
        )

    async def ainvoke(
        self,
        review_type: str,
        image_base64: str,
        prompt: str,
        architect_context: str = "",
        language: str = "en",
        **kwargs,
    ) -> Tuple[ReviewResult, dict[str, int]]:
        headers = {
            "sourceApplication": kwargs.get("source_application", ""),
            "chatbotName": kwargs.get("chatbot_name", ""),
            "sessionId": kwargs.get("session_id", ""),
            "traceId": kwargs.get("trace_id", ""),
            "spanId": kwargs.get("span_id", ""),
            "parentSpanId": kwargs.get("parent_span_id", ""),
        }
        prompt_template = self._new_chat_prompt_template(prompt)
        response = await (prompt_template | self._build_llm(headers=headers)).ainvoke(
            {
                "image_base64": image_base64,
                "architect_context": architect_context,
                "language": language,
                "app_arch_rule_name": kwargs.get("app_arch_rule_name", ""),
            }
        )
        token_usage = self.response_extractor.extract_token_usage(response)
        raw_result = json.loads(extract_json(response.content))
        normalizer = self._get_result_normalizer(review_type)
        result = normalizer.normalize_result(
            raw_result,
            normalize_score=self.response_extractor.normalize_score,
            build_normalized_result=self._build_normalized_result,
        )
        adapter = self._get_type_adapter(review_type)
        return adapter.validate_python(result), token_usage

    def build_chain(self, review_type: str, prompt: str, headers: dict[str, str] | None = None):
        prompt_template = self._new_chat_prompt_template(prompt)
        chain = (
            prompt_template
            | self._build_llm(headers=headers)
            | StrOutputParser()
            | RunnableLambda(extract_json)
            | JsonOutputParser()
        )
        adapter = self._get_type_adapter(review_type)
        return chain, adapter


architect_review_chain = ArchitectReviewChain()
