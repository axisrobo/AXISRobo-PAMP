from __future__ import annotations


class ArchitectReviewResponseExtractor:
    @staticmethod
    def extract_token_usage(response) -> dict[str, int]:
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
    def normalize_score(raw_score) -> float:
        try:
            return float(raw_score)
        except (TypeError, ValueError):
            return 0.0

    def derive_overall_score(self, score_breakdown: object) -> float | None:
        if not isinstance(score_breakdown, dict):
            return None

        total = 0.0
        found_dimension = False
        for value in score_breakdown.values():
            if isinstance(value, dict):
                score = self.normalize_score(value.get("score"))
                total += score
                found_dimension = True
                continue

            if isinstance(value, (int, float, str)):
                total += self.normalize_score(value)
                found_dimension = True

        if not found_dimension:
            return None
        return round(total, 2)
