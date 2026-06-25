from __future__ import annotations

from typing import Callable

from app.architecture_review.ai.chains.architect_review_normalizer_base import ReviewResultNormalizer


TECH_BREAKDOWN_KEYS = {
    "cloud_network_completeness",
    "connectivity",
    "technical_component_completeness",
    "interaction_integration",
    "security_compliance",
    "terminology_expression",
}

TECH_BREAKDOWN_MAX = {
    "cloud_network_completeness": 2.0,
    "connectivity": 1.0,
    "technical_component_completeness": 2.0,
    "interaction_integration": 2.0,
    "security_compliance": 2.0,
    "terminology_expression": 1.0,
}

TECH_DIMENSION_FALLBACKS = {
    "cloud_network_completeness": {
        "label": "Cloud Network Completeness",
        "description": "Cloud and network topology information is incomplete or insufficiently labeled.",
        "impact": "Reviewers may not be able to confirm network zones, deployment boundaries, or routing context.",
        "suggestion": "Add missing cloud/network topology, security zones, and boundary annotations to the diagram.",
    },
    "connectivity": {
        "label": "Connectivity",
        "description": "System connectivity paths or connection methods are not fully described.",
        "impact": "Key upstream/downstream communication paths may remain ambiguous during review and implementation.",
        "suggestion": "Explicitly label connection paths, protocols, and cross-boundary connectivity methods.",
    },
    "technical_component_completeness": {
        "label": "Technical Component Completeness",
        "description": "Important technical components are missing or not clearly represented.",
        "impact": "The architecture view may hide runtime dependencies, middleware, or platform responsibilities.",
        "suggestion": "Add the missing technical components and clarify their responsibilities in the architecture diagram.",
    },
    "interaction_integration": {
        "label": "Interaction Integration",
        "description": "Integration relationships or interaction flows are only partially described.",
        "impact": "Data exchange and service collaboration risks may be missed during architecture review.",
        "suggestion": "Show major integrations, interaction directions, and key data or service exchange paths.",
    },
    "security_compliance": {
        "label": "Security Compliance",
        "description": "Security controls, trust boundaries, or compliance-related markings are incomplete.",
        "impact": "Security review may miss authentication, authorization, encryption, or zone isolation concerns.",
        "suggestion": "Add security controls, trust boundaries, and compliance-relevant annotations to the diagram.",
    },
    "terminology_expression": {
        "label": "Terminology Expression",
        "description": "Architecture terminology or labels are inconsistent or not sufficiently clear.",
        "impact": "Inconsistent naming reduces readability and increases interpretation risk during review.",
        "suggestion": "Standardize component names, labels, and terminology across the diagram.",
    },
}


class TechReviewNormalizer(ReviewResultNormalizer):
    @staticmethod
    def ensure_score_breakdown(result: dict) -> dict:
        # Some model outputs return tech score_breakdown directly at root.
        if "score_breakdown" not in result and TECH_BREAKDOWN_KEYS.issubset(result.keys()):
            return {"score_breakdown": result}
        return result

    def normalize_score_breakdown(self, score_breakdown_raw: object, normalize_score) -> dict | None:
        if not isinstance(score_breakdown_raw, dict):
            return None

        normalized = {}
        for key, max_value in TECH_BREAKDOWN_MAX.items():
            raw_value = score_breakdown_raw.get(key, {})
            if isinstance(raw_value, dict):
                normalized[key] = {
                    "score": normalize_score(raw_value.get("score")),
                    "max": normalize_score(raw_value.get("max")) or max_value,
                }
                continue

            normalized[key] = {
                "score": normalize_score(raw_value),
                "max": max_value,
            }
        return normalized

    @staticmethod
    def normalize_issues(issues_raw) -> list[dict]:
        if not isinstance(issues_raw, list):
            return []
        normalized: list[dict] = []
        for idx, item in enumerate(issues_raw, start=1):
            issue = item if isinstance(item, dict) else {}
            issue_id = str(issue.get("id") or f"I-{idx:03d}")
            description = str(issue.get("description") or "")
            dimension = str(issue.get("dimension") or "General")
            priority = str(issue.get("priority") or "Medium")
            impact = str(issue.get("impact") or "")
            issue_type = str(issue.get("issue_type") or "suggestion")
            suggestion = str(issue.get("suggestion") or "")
            related_entities = issue.get("related_entities", "")

            normalized.append(
                {
                    "id": issue_id,
                    "description": description,
                    "dimension": dimension,
                    "related_entities": str(related_entities),
                    "related_relationships": str(issue.get("related_relationships", issue.get("related_relationshipes", ""))),
                    "priority": priority,
                    "impact": impact,
                    "issue_type": issue_type,
                    "suggestion": suggestion,
                }
            )
        return normalized

    @staticmethod
    def derive_priority(score: float, max_score: float) -> str:
        if max_score <= 0:
            return "Medium"
        gap_ratio = max(0.0, max_score - score) / max_score
        if gap_ratio >= 0.5:
            return "High"
        if gap_ratio >= 0.2:
            return "Medium"
        return "Low"

    def derive_issues(self, score_breakdown: object, normalize_score) -> list[dict]:
        if not isinstance(score_breakdown, dict):
            return []

        derived_issues: list[dict] = []
        for index, key in enumerate(TECH_BREAKDOWN_MAX.keys(), start=1):
            raw_dimension = score_breakdown.get(key)
            if not isinstance(raw_dimension, dict):
                continue

            score = normalize_score(raw_dimension.get("score"))
            max_score = normalize_score(raw_dimension.get("max")) or TECH_BREAKDOWN_MAX[key]
            if max_score <= 0 or score >= max_score:
                continue

            fallback = TECH_DIMENSION_FALLBACKS[key]
            priority = self.derive_priority(score, max_score)
            derived_issues.append(
                {
                    "id": f"T-{index:03d}",
                    "description": fallback["description"],
                    "dimension": fallback["label"],
                    "related_entities": "Architecture Diagram",
                    "related_relationships": "",
                    "priority": priority,
                    "impact": fallback["impact"],
                    "issue_type": "must_fix" if priority in {"High", "Medium"} else "suggestion",
                    "suggestion": fallback["suggestion"],
                }
            )

        return derived_issues

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
        if not issues:
            issues = self.derive_issues(score_breakdown, normalize_score)
        return build_normalized_result(result, score_breakdown, issues)
