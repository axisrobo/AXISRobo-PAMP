from __future__ import annotations

import copy
import os
import uuid
from collections import Counter

import pytest

from app.add.master_data_repository import (
    ARTIFACT_CATALOG_DOMAIN,
    CONCERN_MAPPING_DOMAIN,
    QUESTIONNAIRE_DOMAIN,
    VIEWPOINT_ARTIFACT_MAPPING_DOMAIN,
    get_config_metadata,
    load_artifact_catalog_config,
    load_concern_mapping_config,
    load_questionnaire_config,
    load_viewpoint_artifact_mapping_config,
    save_artifact_catalog_config,
    save_concern_mapping_config,
    save_questionnaire_config,
    save_viewpoint_artifact_mapping_config,
)
from app.database import AsyncSessionLocal, engine, run_migrations


REAL_DB_ENABLED = os.getenv("RUN_REAL_DB_TESTS", "").strip().lower() in {"1", "true", "yes"}
REAL_DB_OPERATOR = "pytest-real-db"

pytestmark = [
    pytest.mark.real_db,
    pytest.mark.skipif(
        not REAL_DB_ENABLED,
        reason="requires RUN_REAL_DB_TESTS=1 and the local eam PostgreSQL database",
    ),
]


def _marker(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
async def ensure_avdm_schema() -> None:
    await engine.dispose()
    await run_migrations()
    yield
    await engine.dispose()


async def _read_metadata(domain_key: str) -> dict:
    async with AsyncSessionLocal() as session:
        return await get_config_metadata(
            session,
            domain_key=domain_key,
            default_change_note="pytest baseline",
        )


@pytest.mark.asyncio
async def test_questionnaire_config_loads_all_normalized_questions_real_db() -> None:
    async with AsyncSessionLocal() as session:
        config = await load_questionnaire_config(session)

    scope_counts = Counter(item.get("sourceScope") or "question_bank" for item in config["questionBank"])
    assert len(config["questionBank"]) == 69
    assert scope_counts == Counter({
        "question_bank": 25,
        "questionnaire_section": 29,
        "assessment_matrix": 15,
    })
    assert len(config["assessmentMatrices"]) == 3
    matrix_questions = [question for section in config["assessmentMatrices"] for question in section["questions"]]
    assert len(matrix_questions) == 15
    assert {question["id"] for question in matrix_questions} == set(range(2001, 2016))
    architecture_impact = next(question for question in matrix_questions if question["id"] == 2012)
    assert architecture_impact["options"] == [
        {"label": "Yes", "value": "Yes", "score": 10.0},
        {"label": "No", "value": "No", "score": 0.0},
    ]

    async with AsyncSessionLocal() as session:
        concern_config = await load_concern_mapping_config(session)
    matrix_mapping = next(
        item for item in concern_config["questionConcernMappings"]
        if item["questionId"] == 2012 and item["answer"] == "Yes"
    )
    assert {score["concernKey"] for score in matrix_mapping["concernScores"]} >= {"AGD1", "A1", "C1"}


@pytest.mark.asyncio
async def test_questionnaire_config_round_trip_real_db() -> None:
    marker = _marker("questionnaire")
    change_note = f"pytest questionnaire round-trip {marker}"

    async with AsyncSessionLocal() as session:
        original = copy.deepcopy(await load_questionnaire_config(session))
    before_meta = await _read_metadata(QUESTIONNAIRE_DOMAIN)

    mutated = copy.deepcopy(original)
    mutated["questionnaireCategories"][0]["description"] = f"{original['questionnaireCategories'][0]['description']} [{marker}]"
    mutated["questionBank"][0]["text"] = f"{original['questionBank'][0]['text']} [{marker}]"
    mutated["projectTypeGuide"]["title"] = f"{original['projectTypeGuide']['title']} [{marker}]"

    try:
        async with AsyncSessionLocal() as session:
            saved = await save_questionnaire_config(
                session,
                config=mutated,
                change_note=change_note,
                operator=REAL_DB_OPERATOR,
            )

        assert saved["changeNote"] == change_note
        assert saved["updatedBy"] == REAL_DB_OPERATOR
        assert saved["version"] >= before_meta["version"] + 1

        async with AsyncSessionLocal() as session:
            reloaded = await load_questionnaire_config(session)

        assert reloaded["questionnaireCategories"][0]["description"].endswith(f"[{marker}]")
        assert reloaded["questionBank"][0]["text"].endswith(f"[{marker}]")
        assert reloaded["projectTypeGuide"]["title"].endswith(f"[{marker}]")
    finally:
        async with AsyncSessionLocal() as session:
            await save_questionnaire_config(
                session,
                config=original,
                change_note=f"restore {change_note}",
                operator=REAL_DB_OPERATOR,
            )


@pytest.mark.asyncio
async def test_concern_mapping_config_round_trip_real_db() -> None:
    marker = _marker("concern-mapping")
    change_note = f"pytest concern mapping round-trip {marker}"

    async with AsyncSessionLocal() as session:
        original = copy.deepcopy(await load_concern_mapping_config(session))
    before_meta = await _read_metadata(CONCERN_MAPPING_DOMAIN)

    mutated = copy.deepcopy(original)
    mutated["questionConcernMappings"][0]["hints"] = [f"pytest hint {marker}"]
    duplicated_score = copy.deepcopy(mutated["questionConcernMappings"][0]["concernScores"][0])
    mutated["questionConcernMappings"][0]["concernScores"].append(duplicated_score)
    mutated["concernActivationRules"][0]["description"] = f"{original['concernActivationRules'][0]['description']} [{marker}]"
    duplicated_rule_score = copy.deepcopy(mutated["concernActivationRules"][0]["concernScores"][0])
    mutated["concernActivationRules"][0]["concernScores"].append(duplicated_rule_score)
    mutated["concernActivationRules"][0]["concernScores"][0]["note"] = f"pytest note {marker}"

    try:
        async with AsyncSessionLocal() as session:
            saved = await save_concern_mapping_config(
                session,
                config=mutated,
                change_note=change_note,
                operator=REAL_DB_OPERATOR,
            )

        assert saved["changeNote"] == change_note
        assert saved["updatedBy"] == REAL_DB_OPERATOR
        assert saved["version"] >= before_meta["version"] + 1

        async with AsyncSessionLocal() as session:
            reloaded = await load_concern_mapping_config(session)

        assert reloaded["questionConcernMappings"][0]["hints"] == [f"pytest hint {marker}"]
        assert len(reloaded["questionConcernMappings"][0]["concernScores"]) == len(original["questionConcernMappings"][0]["concernScores"])
        assert reloaded["concernActivationRules"][0]["description"].endswith(f"[{marker}]")
        assert len(reloaded["concernActivationRules"][0]["concernScores"]) == len(original["concernActivationRules"][0]["concernScores"])
        assert reloaded["concernActivationRules"][0]["concernScores"][0]["note"] == f"pytest note {marker}"
    finally:
        async with AsyncSessionLocal() as session:
            await save_concern_mapping_config(
                session,
                config=original,
                change_note=f"restore {change_note}",
                operator=REAL_DB_OPERATOR,
            )


@pytest.mark.asyncio
async def test_artifact_catalog_config_round_trip_real_db() -> None:
    marker = _marker("artifact-catalog")
    change_note = f"pytest artifact catalog round-trip {marker}"

    async with AsyncSessionLocal() as session:
        original = copy.deepcopy(await load_artifact_catalog_config(session))
    before_meta = await _read_metadata(ARTIFACT_CATALOG_DOMAIN)

    mutated = copy.deepcopy(original)
    mutated["artifactTypes"][0]["purpose"] = f"{original['artifactTypes'][0]['purpose']} [{marker}]"
    mutated["artifactTypes"][0]["typicalContents"] = [
        *original["artifactTypes"][0]["typicalContents"],
        f"pytest content {marker}",
    ]

    try:
        async with AsyncSessionLocal() as session:
            saved = await save_artifact_catalog_config(
                session,
                config=mutated,
                change_note=change_note,
                operator=REAL_DB_OPERATOR,
            )

        assert saved["changeNote"] == change_note
        assert saved["updatedBy"] == REAL_DB_OPERATOR
        assert saved["version"] >= before_meta["version"] + 1

        async with AsyncSessionLocal() as session:
            reloaded = await load_artifact_catalog_config(session)

        assert reloaded["artifactTypes"][0]["purpose"].endswith(f"[{marker}]")
        assert reloaded["artifactTypes"][0]["typicalContents"][-1] == f"pytest content {marker}"
    finally:
        async with AsyncSessionLocal() as session:
            await save_artifact_catalog_config(
                session,
                config=original,
                change_note=f"restore {change_note}",
                operator=REAL_DB_OPERATOR,
            )


@pytest.mark.asyncio
async def test_viewpoint_artifact_mapping_config_round_trip_real_db() -> None:
    marker = _marker("viewpoint-artifact")
    change_note = f"pytest viewpoint artifact mapping round-trip {marker}"

    async with AsyncSessionLocal() as session:
        original = copy.deepcopy(await load_viewpoint_artifact_mapping_config(session))
    before_meta = await _read_metadata(VIEWPOINT_ARTIFACT_MAPPING_DOMAIN)

    mutated = copy.deepcopy(original)
    mutated["guideName"] = f"{original['guideName']} [{marker}]"
    mutated["viewpoints"][0]["notes"] = f"{original['viewpoints'][0].get('notes') or ''} [{marker}]".strip()

    try:
        async with AsyncSessionLocal() as session:
            saved = await save_viewpoint_artifact_mapping_config(
                session,
                config=mutated,
                change_note=change_note,
                operator=REAL_DB_OPERATOR,
            )

        assert saved["changeNote"] == change_note
        assert saved["updatedBy"] == REAL_DB_OPERATOR
        assert saved["version"] >= before_meta["version"] + 1

        async with AsyncSessionLocal() as session:
            reloaded = await load_viewpoint_artifact_mapping_config(session)

        assert reloaded["guideName"].endswith(f"[{marker}]")
        assert reloaded["viewpoints"][0]["notes"].endswith(f"[{marker}]")
    finally:
        async with AsyncSessionLocal() as session:
            await save_viewpoint_artifact_mapping_config(
                session,
                config=original,
                change_note=f"restore {change_note}",
                operator=REAL_DB_OPERATOR,
            )