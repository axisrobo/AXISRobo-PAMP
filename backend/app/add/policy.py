"""Configurable AVDM classification policy.

The classification policy controls the previously hard-coded scoring and
threshold behaviour:

* mandatory and recommended thresholds
* project-complexity coefficient
* optional cap on the number of Mandatory concerns (absolute count or ratio)
* optional top-N priority budget
* tie-breaking strategy when scores are equal

All values have defaults that reproduce the historical behaviour, so existing
callers that do not supply a policy keep the same output.
"""
from __future__ import annotations

from typing import Any, Iterable

DEFAULT_CLASSIFICATION_POLICY: dict[str, Any] = {
    "mandatoryThreshold": 0.90,
    "recommendedThreshold": 0.50,
    "complexityCoefficient": 0.15,
    "maxMandatoryCount": None,
    "maxMandatoryRatio": None,
    "topNPriorityBudget": None,
    "tieBreakStrategy": "score_then_key",
}

TIE_BREAK_STRATEGIES = ("score_then_key", "catalog_order", "stable_input")

CLASSIFICATION_ORDER = {"Mandatory": 0, "Recommended": 1, "Optional": 2}


def _as_float(value: Any, default: float, *, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _as_optional_int(value: Any, *, minimum: int) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= minimum else None


def _as_optional_ratio(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return min(1.0, number)


def normalize_policy(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Return a validated policy, filling missing values with defaults."""
    source = raw or {}
    mandatory = _as_float(
        source.get("mandatoryThreshold"), 0.90, minimum=0.0, maximum=1.0
    )
    recommended = _as_float(
        source.get("recommendedThreshold"), 0.50, minimum=0.0, maximum=1.0
    )
    if recommended > mandatory:
        recommended = mandatory
    strategy = str(source.get("tieBreakStrategy") or "score_then_key")
    if strategy not in TIE_BREAK_STRATEGIES:
        strategy = "score_then_key"
    top_n = _as_optional_int(source.get("topNPriorityBudget"), minimum=1)
    max_count = _as_optional_int(source.get("maxMandatoryCount"), minimum=0)
    max_ratio = _as_optional_ratio(source.get("maxMandatoryRatio"))
    return {
        "mandatoryThreshold": mandatory,
        "recommendedThreshold": recommended,
        "complexityCoefficient": _as_float(
            source.get("complexityCoefficient"), 0.15, minimum=0.0, maximum=1.0
        ),
        "maxMandatoryCount": max_count,
        "maxMandatoryRatio": max_ratio,
        "topNPriorityBudget": top_n,
        "tieBreakStrategy": strategy,
    }


def complexity_boost(complexity: float, policy: dict[str, Any]) -> float:
    normalized = _as_float(complexity, 0.0, minimum=0.0, maximum=1.0)
    return normalized * float(policy["complexityCoefficient"])


def classify(score: float, policy: dict[str, Any]) -> str:
    if score >= float(policy["mandatoryThreshold"]):
        return "Mandatory"
    if score >= float(policy["recommendedThreshold"]):
        return "Recommended"
    return "Optional"


def _tie_key(item: dict[str, Any], policy: dict[str, Any], position: int):
    """Ascending tie-break key used after a descending score sort."""
    strategy = policy["tieBreakStrategy"]
    if strategy == "catalog_order":
        return (int(item.get("catalogIndex", position)), item["concernKey"])
    if strategy == "stable_input":
        return (int(item.get("inputIndex", position)),)
    return (item["concernKey"],)


def _ranked(items: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (-float(item["score"]),)
        + _tie_key(item, policy, 0),
    )


def _effective_mandatory_cap(
    policy: dict[str, Any], concern_count: int
) -> int | None:
    caps: list[int] = []
    if policy["maxMandatoryCount"] is not None:
        caps.append(int(policy["maxMandatoryCount"]))
    if policy["maxMandatoryRatio"] is not None:
        caps.append(int(concern_count * float(policy["maxMandatoryRatio"])))
    return min(caps) if caps else None


def apply_policy(
    items: list[dict[str, Any]], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """Apply caps, the top-N priority budget, and ranking to scored concerns.

    ``items`` must contain ``concernKey`` and ``score``. Items may also carry
    ``classification`` (recomputed here), ``catalogIndex`` and ``inputIndex``.
    Returns new dicts with classification, priorityRank, and priority set.
    """
    concern_count = len(items)
    for item in items:
        item["classification"] = classify(float(item["score"]), policy)

    ranked = _ranked(items, policy)

    cap = _effective_mandatory_cap(policy, concern_count)
    if cap is not None:
        kept = 0
        for item in ranked:
            if item["classification"] != "Mandatory":
                continue
            kept += 1
            if kept > cap:
                item["classification"] = "Recommended"

    top_n = policy["topNPriorityBudget"]
    for index, item in enumerate(ranked, start=1):
        if top_n is not None and index <= int(top_n):
            item["priorityRank"] = index
            item["priority"] = True
        else:
            item["priorityRank"] = None
            item["priority"] = False
    return items
