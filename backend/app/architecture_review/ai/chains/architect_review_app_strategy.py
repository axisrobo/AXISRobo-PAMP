from __future__ import annotations

from typing import Callable

from app.architecture_review.ai.chains.architect_review_normalizer_base import ReviewResultNormalizer


APP_BREAKDOWN_KEYS = {
    "application_information_completion",
    "relationship_completion",
    "relationship_accuracy",
    "template_matching_rate",
}

APP_BREAKDOWN_DEFAULT = {
    "application_information_completion": 0.0,
    "relationship_completion": 0.0,
    "relationship_accuracy": 0.0,
    "template_matching_rate": 0.0,
}


class AppReviewNormalizer(ReviewResultNormalizer):
    @staticmethod
    def ensure_score_breakdown(result: dict) -> dict:
        # Some model outputs return app score_breakdown directly at root.
        if "score_breakdown" not in result and APP_BREAKDOWN_KEYS.issubset(result.keys()):
            return {"score_breakdown": result}
        return result

    def normalize_score_breakdown(self, score_breakdown_raw: object, normalize_score) -> dict | None:
        if not isinstance(score_breakdown_raw, dict):
            return None

        normalized: dict[str, float] = {}
        for key, default_value in APP_BREAKDOWN_DEFAULT.items():
            raw_value = score_breakdown_raw.get(key, default_value)
            if isinstance(raw_value, dict):
                raw_value = raw_value.get("score", default_value)
            normalized[key] = normalize_score(raw_value)
        return normalized

    @staticmethod
    def normalize_issues(issues_raw) -> list[dict]:
        if not isinstance(issues_raw, list):
            return []
        normalized: list[dict] = []
        for idx, item in enumerate(issues_raw, start=1):
            issue = item if isinstance(item, dict) else {}
            issue_id = str(issue.get("id") or f"I-{idx:03d}")
            normalized.append(
                {
                    "id": issue_id,
                    "description": str(issue.get("description") or ""),
                    "dimension": str(issue.get("dimension") or "General"),
                    "related_entities": issue.get("related_entities", ""),
                    "related_relationshipes": issue.get("related_relationshipes", issue.get("related_relationships", "")),
                    "priority": str(issue.get("priority") or "Medium"),
                    "impact": str(issue.get("impact") or ""),
                    "issue_type": str(issue.get("issue_type") or "suggestion"),
                    "suggestion": str(issue.get("suggestion") or ""),
                }
            )
        return normalized

    def normalize_result(
        self,
        raw_result: object,
        *,
        normalize_score: Callable[[object], float],
        build_normalized_result: Callable[[dict, dict | None, list[dict]], dict],
    ) -> dict:
        result = raw_result if isinstance(raw_result, dict) else {}
        result = self.ensure_score_breakdown(result)
        score_breakdown = self.normalize_score_breakdown(result.get("score_breakdown"), normalize_score)
        issues = self.normalize_issues(result.get("issues", []))
        return build_normalized_result(result, score_breakdown, issues)
