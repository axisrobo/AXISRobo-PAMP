import pytest

from app.add.master_data_repository import validate_concern_mapping_scores


def _config(score):
    return {
        "questionConcernMappings": [
            {"questionId": 1, "answer": "Y", "concernScores": [{"concernKey": "A1", "score": score}]}
        ],
        "concernActivationRules": [],
    }


@pytest.mark.parametrize("score", [0, 5, 2.5])
def test_mapping_score_accepts_contract_boundaries(score):
    validate_concern_mapping_scores(_config(score))


@pytest.mark.parametrize("score", [-1, 5.01, "not-a-number", float("nan"), float("inf")])
def test_mapping_score_rejects_values_outside_contract(score):
    with pytest.raises(ValueError, match="must be a number from 0 to 5"):
        validate_concern_mapping_scores(_config(score))


def test_rule_score_uses_same_contract():
    config = {
        "questionConcernMappings": [],
        "concernActivationRules": [
            {"id": "rule", "concernScores": [{"concernKey": "A1", "score": 6}]}
        ],
    }
    with pytest.raises(ValueError, match="concernActivationRules"):
        validate_concern_mapping_scores(config)
