"""Tests for the configurable AVDM classification policy."""
from app.add.policy import (
    DEFAULT_CLASSIFICATION_POLICY,
    apply_policy,
    classify,
    complexity_boost,
    normalize_policy,
)
from app.add.models import AVDMEvaluateRequest, RiskItem
from app.add.service import evaluate_avdm


CATALOG = [
    {"key": "A1", "name": "Alpha", "layer": "L1", "risk_tags": []},
    {"key": "A2", "name": "Beta", "layer": "L1", "risk_tags": []},
    {"key": "A3", "name": "Gamma", "layer": "L1", "risk_tags": []},
]


def _request():
    return AVDMEvaluateRequest(
        projectId="p1",
        projectComplexity=0.0,
        riskItems=[
            RiskItem(code="A1", severity=5, likelihood=5),
            RiskItem(code="A2", severity=5, likelihood=5),
            RiskItem(code="A3", severity=2, likelihood=2),
        ],
    )


def test_defaults_match_reference_policy():
    result = evaluate_avdm(_request(), concern_catalog=CATALOG)
    by_key = {decision.concernKey: decision for decision in result.decisions}
    assert by_key["A1"].classification == "Mandatory"
    assert by_key["A3"].classification == "Optional"
    assert by_key["A3"].score == 0.16


def test_normalize_clamps_invalid_values():
    policy = normalize_policy(
        {
            "mandatoryThreshold": 0.5,
            "recommendedThreshold": 0.9,
            "complexityCoefficient": 5,
            "tieBreakStrategy": "nonsense",
            "maxMandatoryRatio": 3,
        }
    )
    assert policy["recommendedThreshold"] == 0.5
    assert policy["complexityCoefficient"] == 1.0
    assert policy["tieBreakStrategy"] == "score_then_key"
    assert policy["maxMandatoryRatio"] == 1.0


def test_complexity_coefficient_is_configurable():
    default_boost = complexity_boost(1.0, DEFAULT_CLASSIFICATION_POLICY)
    custom_boost = complexity_boost(
        1.0, normalize_policy({"complexityCoefficient": 0.5})
    )
    assert default_boost == 0.15
    assert custom_boost == 0.5


def test_thresholds_are_configurable():
    strict = normalize_policy({"mandatoryThreshold": 0.99, "recommendedThreshold": 0.95})
    assert classify(0.8, DEFAULT_CLASSIFICATION_POLICY) == "Recommended"
    assert classify(0.8, strict) == "Optional"


def test_reference_threshold_boundaries():
    assert classify(0.49, DEFAULT_CLASSIFICATION_POLICY) == "Optional"
    assert classify(0.50, DEFAULT_CLASSIFICATION_POLICY) == "Recommended"
    assert classify(0.89, DEFAULT_CLASSIFICATION_POLICY) == "Recommended"
    assert classify(0.90, DEFAULT_CLASSIFICATION_POLICY) == "Mandatory"


def test_max_mandatory_count_downgrades_lowest_scores():
    result = evaluate_avdm(
        _request(),
        concern_catalog=CATALOG,
        policy={"maxMandatoryCount": 1},
    )
    mandatory = [d for d in result.decisions if d.classification == "Mandatory"]
    assert len(mandatory) == 1
    assert mandatory[0].concernKey == "A1"


def test_max_mandatory_ratio_applies():
    result = evaluate_avdm(
        _request(),
        concern_catalog=CATALOG,
        policy={"maxMandatoryRatio": 0.34},
    )
    mandatory = [d for d in result.decisions if d.classification == "Mandatory"]
    assert len(mandatory) == 1


def test_top_n_budget_sets_priority_rank():
    result = evaluate_avdm(_request(), concern_catalog=CATALOG, policy={"topNPriorityBudget": 2})
    ranked = sorted(
        [d for d in result.decisions if d.priorityRank is not None],
        key=lambda d: d.priorityRank,
    )
    assert [d.concernKey for d in ranked] == ["A1", "A2"]
    assert all(d.priority for d in ranked)


def test_tie_break_catalog_order_is_stable():
    items = [
        {"concernKey": "Z1", "score": 0.5, "catalogIndex": 5},
        {"concernKey": "A9", "score": 0.5, "catalogIndex": 1},
        {"concernKey": "M5", "score": 0.5, "catalogIndex": 3},
    ]
    apply_policy(items, normalize_policy({"tieBreakStrategy": "catalog_order", "topNPriorityBudget": 2}))
    ranked = sorted(
        [item for item in items if item["priorityRank"] is not None],
        key=lambda item: item["priorityRank"],
    )
    assert [item["concernKey"] for item in ranked] == ["A9", "M5"]
