"""Repository helpers for normalized AVDM master data."""
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ArtifactRecommendationItem
from .master_data_seeds import DEFAULT_QUESTION_ANSWER_TYPES, DEFAULT_QUESTION_GROUPS
from .questionnaire_config import (
    DEFAULT_QUESTIONNAIRE_CONFIG,
)


QUESTIONNAIRE_DOMAIN = "questionnaire"
CONCERN_MAPPING_DOMAIN = "concern_mapping"
ARTIFACT_CATALOG_DOMAIN = "artifact_catalog"
VIEWPOINT_ARTIFACT_MAPPING_DOMAIN = "viewpoint_artifact_mapping"
PROJECT_TYPE_PROFILE_DOMAIN = "project_type_profiles"

STATIC_DOCUMENT_KEYS = {
    "questionnaireSections": "questionnaire_sections",
    "assessmentMatrices": "assessment_matrices",
    "projectTypeGuide": "project_type_guide",
    "projectTypeProfiles": "project_type_profiles",
    "viewpointArtifactMapping": "viewpoint_artifact_mapping",
}

QUESTIONNAIRE_OPTION_KEYS = [
    "questionYesNoOptions",
    "projectTypeOptions",
    "applicationCountRangeOptions",
    "externalSystemCountRangeOptions",
    "newApplicationCountRangeOptions",
    "modifiedApplicationCountRangeOptions",
    "dataCenterCountRangeOptions",
    "cloudRegionScopeOptions",
    "techStackKindsCountRangeOptions",
    "integrationTechKindsCountRangeOptions",
]

ASSESSMENT_MATRIX_SECTION_META = {
    "requirementComplexitySection": {
        "title": "Requirement Complexity",
        "description": "1. How complex is the requirement?",
        "sortOrder": 10,
    },
    "solutionComplexitySection": {
        "title": "Solution Complexity",
        "description": "2. How complex is the solution?",
        "sortOrder": 20,
    },
    "resourceSizeSection": {
        "title": "Project Resource and Size",
        "description": "Resource and funding scale for the solution.",
        "sortOrder": 30,
    },
}


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


ARTIFACT_CATEGORY_DEFINITIONS = [
    {
        "key": "architecture_diagram",
        "name": "Architecture Diagram",
        "description": "Core architecture and application relationship diagrams.",
        "sortOrder": 10,
    },
    {
        "key": "business_architecture_artifact",
        "name": "Business Architecture Artifact",
        "description": "Business capability and business interaction artifacts.",
        "sortOrder": 20,
    },
    {
        "key": "data_architecture_artifact",
        "name": "Data Architecture Artifact",
        "description": "Data model, compliance, and pipeline artifacts.",
        "sortOrder": 30,
    },
    {
        "key": "security_architecture_artifact",
        "name": "Security Architecture Artifact",
        "description": "Identity, trust, and control artifacts.",
        "sortOrder": 40,
    },
    {
        "key": "process_architecture_artifact",
        "name": "Process Architecture Artifact",
        "description": "Process and execution-flow artifacts.",
        "sortOrder": 50,
    },
    {
        "key": "inventory_artifact",
        "name": "Inventory Artifact",
        "description": "Inventory-style reference artifacts.",
        "sortOrder": 60,
    },
]

DEFAULT_ARTIFACT_CATEGORY_BY_KEY = {
    "tech_diagram": "architecture_diagram",
    "app_collab": "architecture_diagram",
    "biz_diagram": "business_architecture_artifact",
    "data_compliance_diagram": "data_architecture_artifact",
    "data_model": "data_architecture_artifact",
    "data_asset_matrix": "data_architecture_artifact",
    "auth_flow": "security_architecture_artifact",
    "business_process": "process_architecture_artifact",
    "data_pipeline": "data_architecture_artifact",
    "system_process_flow": "process_architecture_artifact",
    "resource_list": "inventory_artifact",
}


def _clone(value: Any) -> Any:
    return deepcopy(value)


def _default_static_payload(document_key: str) -> Any:
    if document_key == STATIC_DOCUMENT_KEYS["questionnaireSections"]:
        return _clone(DEFAULT_QUESTIONNAIRE_CONFIG.get("questionnaireSections", []))
    if document_key == STATIC_DOCUMENT_KEYS["assessmentMatrices"]:
        return _clone(DEFAULT_QUESTIONNAIRE_CONFIG.get("assessmentMatrices", []))
    if document_key == STATIC_DOCUMENT_KEYS["projectTypeGuide"]:
        return _clone(DEFAULT_QUESTIONNAIRE_CONFIG.get("projectTypeGuide", {}))
    if document_key == STATIC_DOCUMENT_KEYS["viewpointArtifactMapping"]:
        return {
            "guideName": "Architecture Viewpoint and Artifact Mapping Guide",
            "stage": "Preparation",
            "positioning": "Canonical reference for the semantic mapping between architecture viewpoints and artifact types.",
            "viewpoints": [],
        }
    return {}


def _build_assessment_matrices_from_questions(question_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: dict[str, dict[str, Any]] = {}
    for item in question_items:
        if item.get("sourceScope") != "assessment_matrix":
            continue
        source_ref = str(item.get("sourceRef") or "")
        if "." not in source_ref:
            continue
        section_key, question_key = source_ref.split(".", 1)
        section_meta = ASSESSMENT_MATRIX_SECTION_META.get(section_key, {})
        section = sections.setdefault(
            section_key,
            {
                "key": section_key,
                "title": section_meta.get("title") or section_key,
                "description": section_meta.get("description") or "",
                "sortOrder": int(section_meta.get("sortOrder") or 999),
                "questions": [],
            },
        )
        question = {
            "id": item["id"],
            "key": question_key,
            "title": item.get("text") or question_key,
            "helperText": item.get("designIntent") or "",
            "control": item.get("control") or "radio",
            "options": item.get("options") or [],
        }
        section["questions"].append(question)
    return [
        {key: value for key, value in section.items() if key != "sortOrder"}
        for section in sorted(sections.values(), key=lambda value: (value["sortOrder"], value["key"]))
    ]


async def _get_revision(
    db: AsyncSession,
    *,
    domain_key: str,
    default_change_note: str,
) -> dict[str, Any]:
    result = await db.execute(
        text(
            "SELECT domain_key, version, change_note, update_by, update_at "
            "FROM eam.avdm_master_data_revision WHERE domain_key = :domain_key"
        ),
        {"domain_key": domain_key},
    )
    row = result.mappings().first()
    if not row:
        return {
            "version": 1,
            "changeNote": default_change_note,
            "updatedBy": "system",
            "updatedAt": None,
            "source": "default",
        }
    return {
        "version": int(row.get("version") or 1),
        "changeNote": row.get("change_note") or default_change_note,
        "updatedBy": row.get("update_by") or "system",
        "updatedAt": row.get("update_at"),
        "source": "db",
    }


async def _bump_revision(
    db: AsyncSession,
    *,
    domain_key: str,
    change_note: str | None,
    operator: str,
) -> dict[str, Any]:
    result = await db.execute(
        text(
            """
            INSERT INTO eam.avdm_master_data_revision (
                domain_key, version, change_note, create_by, update_by
            )
            VALUES (:domain_key, 1, :change_note, :operator, :operator)
            ON CONFLICT (domain_key) DO UPDATE SET
                version = eam.avdm_master_data_revision.version + 1,
                change_note = EXCLUDED.change_note,
                update_by = EXCLUDED.update_by,
                update_at = NOW()
            RETURNING version, change_note, update_by, update_at
            """
        ),
        {
            "domain_key": domain_key,
            "change_note": change_note,
            "operator": operator or "system",
        },
    )
    row = result.mappings().one()
    return {
        "version": int(row.get("version") or 1),
        "changeNote": row.get("change_note"),
        "updatedBy": row.get("update_by") or operator or "system",
        "updatedAt": row.get("update_at"),
        "source": "db",
    }


async def _get_static_document(db: AsyncSession, *, document_key: str) -> Any:
    result = await db.execute(
        text(
            "SELECT document_json FROM eam.avdm_static_document WHERE document_key = :document_key"
        ),
        {"document_key": document_key},
    )
    row = result.mappings().first()
    if not row:
        return _default_static_payload(document_key)
    return row.get("document_json")


async def _upsert_static_document(
    db: AsyncSession,
    *,
    document_key: str,
    payload: Any,
    operator: str,
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO eam.avdm_static_document (
                document_key, document_json, create_by, update_by
            )
            VALUES (:document_key, CAST(:document_json AS jsonb), :operator, :operator)
            ON CONFLICT (document_key) DO UPDATE SET
                document_json = EXCLUDED.document_json,
                update_by = EXCLUDED.update_by,
                update_at = NOW()
            """
        ),
        {
            "document_key": document_key,
            "document_json": json.dumps(payload, ensure_ascii=False),
            "operator": operator or "system",
        },
    )


async def _load_project_type_profiles_config(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT p.project_type_key, p.project_type_label, p.description,
                       p.typical_patterns, p.typical_risks, p.sort_order AS profile_sort_order,
                       a.artifact_key, a.artifact_name, m.default_status, m.sort_order AS mapping_sort_order
                FROM eam.avdm_project_type_profile p
                LEFT JOIN eam.avdm_project_type_artifact_mapping m
                  ON m.project_type_profile_id = p.id AND m.is_active = TRUE
                LEFT JOIN eam.avdm_artifact a
                  ON a.id = m.artifact_id AND a.is_active = TRUE
                WHERE p.is_active = TRUE
                ORDER BY p.sort_order, p.project_type_key, m.sort_order, a.sort_order, a.artifact_key
                """
            )
        )
    ).mappings().all()
    profiles: dict[str, dict[str, Any]] = {}
    for row in rows:
        profile = profiles.setdefault(
            row["project_type_key"],
            {
                "value": row["project_type_key"],
                "label": row["project_type_label"],
                "description": row.get("description") or "",
                "artifactSelections": [],
                "typicalPatterns": row.get("typical_patterns") or [],
                "typicalRisks": row.get("typical_risks") or [],
                "sortOrder": int(row.get("profile_sort_order") or 0),
            },
        )
        if row.get("artifact_key"):
            profile["artifactSelections"].append(
                {
                    "artifactKey": row["artifact_key"],
                    "artifactLabel": row.get("artifact_name") or row["artifact_key"],
                    "status": row.get("default_status") or "Optional",
                }
            )
    return list(profiles.values())


async def _save_project_type_profiles_config(
    db: AsyncSession,
    *,
    profiles: list[dict[str, Any]],
    operator: str,
) -> None:
    await db.execute(
        text("UPDATE eam.avdm_project_type_profile SET is_active = FALSE, update_by = :operator, update_at = NOW()"),
        {"operator": operator or "system"},
    )
    await db.execute(
        text("UPDATE eam.avdm_project_type_artifact_mapping SET is_active = FALSE, update_by = :operator, update_at = NOW()"),
        {"operator": operator or "system"},
    )
    for index, profile in enumerate(profiles, start=1):
        project_type_key = str(profile.get("value") or profile.get("key") or "").strip()
        if not project_type_key:
            continue
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_project_type_profile (
                    project_type_key, project_type_label, description, typical_patterns, typical_risks,
                    sort_order, is_active, create_by, update_by
                ) VALUES (
                    :project_type_key, :project_type_label, :description,
                    CAST(:typical_patterns AS jsonb), CAST(:typical_risks AS jsonb),
                    :sort_order, TRUE, :operator, :operator
                )
                ON CONFLICT (project_type_key) DO UPDATE SET
                    project_type_label = EXCLUDED.project_type_label,
                    description = EXCLUDED.description,
                    typical_patterns = EXCLUDED.typical_patterns,
                    typical_risks = EXCLUDED.typical_risks,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "project_type_key": project_type_key,
                "project_type_label": str(profile.get("label") or project_type_key).strip(),
                "description": str(profile.get("description") or "").strip(),
                "typical_patterns": json.dumps(profile.get("typicalPatterns") or [], ensure_ascii=False),
                "typical_risks": json.dumps(profile.get("typicalRisks") or [], ensure_ascii=False),
                "sort_order": int(profile.get("sortOrder") or index * 10),
                "operator": operator or "system",
            },
        )
        for selection_index, selection in enumerate(profile.get("artifactSelections") or [], start=1):
            artifact_key = str(selection.get("artifactKey") or "").strip()
            status = str(selection.get("status") or "").strip()
            if not artifact_key or status not in {"Mandatory", "Recommended", "Optional", "Not Required"}:
                continue
            await db.execute(
                text(
                    """
                    INSERT INTO eam.avdm_project_type_artifact_mapping (
                        project_type_profile_id, artifact_id, default_status, sort_order,
                        is_active, create_by, update_by
                    ) VALUES (
                        (SELECT id FROM eam.avdm_project_type_profile WHERE project_type_key = :project_type_key),
                        (SELECT id FROM eam.avdm_artifact WHERE artifact_key = :artifact_key),
                        :default_status, :sort_order, TRUE, :operator, :operator
                    )
                    ON CONFLICT (project_type_profile_id, artifact_id) DO UPDATE SET
                        default_status = EXCLUDED.default_status,
                        sort_order = EXCLUDED.sort_order,
                        is_active = TRUE,
                        update_by = EXCLUDED.update_by,
                        update_at = NOW()
                    """
                ),
                {
                    "project_type_key": project_type_key,
                    "artifact_key": artifact_key,
                    "default_status": status,
                    "sort_order": selection_index * 10,
                    "operator": operator or "system",
                },
            )


async def _seed_question_reference_data(db: AsyncSession, *, operator: str) -> None:
    for group in DEFAULT_QUESTION_GROUPS:
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_question_group (
                    group_key, group_name, description, sort_order, is_active, create_by, update_by
                ) VALUES (
                    :group_key, :group_name, :description, :sort_order, TRUE, :operator, :operator
                )
                ON CONFLICT (group_key) DO UPDATE SET
                    group_name = EXCLUDED.group_name,
                    description = EXCLUDED.description,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "group_key": group.key,
                "group_name": group.name,
                "description": group.description,
                "sort_order": group.sort_order,
                "operator": operator or "system",
            },
        )

    for answer_type in DEFAULT_QUESTION_ANSWER_TYPES:
        await _upsert_answer_type(
            db,
            answer_type_key=answer_type.key,
            answer_type_name=answer_type.name,
            storage_kind=answer_type.storage_kind,
            widget=answer_type.widget,
            allows_multiple=answer_type.allows_multiple,
            allows_free_text=answer_type.allows_free_text,
            description=answer_type.description,
            operator=operator,
        )


async def _upsert_answer_type(
    db: AsyncSession,
    *,
    answer_type_key: str,
    answer_type_name: str,
    storage_kind: str,
    widget: str,
    allows_multiple: bool,
    allows_free_text: bool,
    description: str,
    operator: str,
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO eam.avdm_question_answer_type (
                answer_type_key, answer_type_name, storage_kind, widget,
                allows_multiple, allows_free_text, description, is_active, create_by, update_by
            ) VALUES (
                :answer_type_key, :answer_type_name, :storage_kind, :widget,
                :allows_multiple, :allows_free_text, :description, TRUE, :operator, :operator
            )
            ON CONFLICT (answer_type_key) DO UPDATE SET
                answer_type_name = EXCLUDED.answer_type_name,
                storage_kind = EXCLUDED.storage_kind,
                widget = EXCLUDED.widget,
                allows_multiple = EXCLUDED.allows_multiple,
                allows_free_text = EXCLUDED.allows_free_text,
                description = EXCLUDED.description,
                is_active = TRUE,
                update_by = EXCLUDED.update_by,
                update_at = NOW()
            """
        ),
        {
            "answer_type_key": answer_type_key,
            "answer_type_name": answer_type_name,
            "storage_kind": storage_kind,
            "widget": widget,
            "allows_multiple": allows_multiple,
            "allows_free_text": allows_free_text,
            "description": description,
            "operator": operator or "system",
        },
    )

async def _set_all_questionnaire_records_inactive(db: AsyncSession, *, operator: str) -> None:
    statements = [
        "UPDATE eam.avdm_question SET is_active = FALSE, update_by = :operator, update_at = NOW()",
        "UPDATE eam.avdm_question_category SET is_active = FALSE, update_by = :operator, update_at = NOW()",
        "UPDATE eam.avdm_question_option_item SET is_active = FALSE, update_by = :operator, update_at = NOW()",
        "UPDATE eam.avdm_question_option_set SET is_active = FALSE, update_by = :operator, update_at = NOW()",
    ]
    for sql_text in statements:
        await db.execute(text(sql_text), {"operator": operator or "system"})


async def _upsert_option_set(
    db: AsyncSession,
    *,
    option_set_key: str,
    option_set_name: str,
    description: str,
    is_shared: bool,
    sort_order: int,
    options: list[dict[str, Any]],
    operator: str,
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO eam.avdm_question_option_set (
                option_set_key, option_set_name, description, is_shared, sort_order, is_active, create_by, update_by
            ) VALUES (
                :option_set_key, :option_set_name, :description, :is_shared, :sort_order, TRUE, :operator, :operator
            )
            ON CONFLICT (option_set_key) DO UPDATE SET
                option_set_name = EXCLUDED.option_set_name,
                description = EXCLUDED.description,
                is_shared = EXCLUDED.is_shared,
                sort_order = EXCLUDED.sort_order,
                is_active = TRUE,
                update_by = EXCLUDED.update_by,
                update_at = NOW()
            """
        ),
        {
            "option_set_key": option_set_key,
            "option_set_name": option_set_name,
            "description": description,
            "is_shared": is_shared,
            "sort_order": sort_order,
            "operator": operator or "system",
        },
    )

    for index, item in enumerate(options, start=1):
        label = str(item.get("label") or "").strip()
        value = str(item.get("value") or "").strip()
        if not label or not value:
            continue
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_question_option_item (
                    option_set_id, option_value, option_label, option_score,
                    sort_order, is_active, metadata, create_by, update_by
                ) VALUES (
                    (SELECT id FROM eam.avdm_question_option_set WHERE option_set_key = :option_set_key),
                    :option_value, :option_label, :option_score,
                    :sort_order, TRUE, '{}'::jsonb, :operator, :operator
                )
                ON CONFLICT (option_set_id, option_value) DO UPDATE SET
                    option_label = EXCLUDED.option_label,
                    option_score = EXCLUDED.option_score,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "option_set_key": option_set_key,
                "option_value": value,
                "option_label": label,
                "option_score": item.get("score"),
                "sort_order": index * 10,
                "operator": operator or "system",
            },
        )


async def load_questionnaire_config(db: AsyncSession) -> dict[str, Any]:
    config = _clone(DEFAULT_QUESTIONNAIRE_CONFIG)

    answer_type_rows = (
        await db.execute(
            text(
                """
                SELECT answer_type_key, answer_type_name, storage_kind, widget,
                       allows_multiple, allows_free_text, description, is_active
                FROM eam.avdm_question_answer_type
                WHERE is_active = TRUE
                ORDER BY answer_type_key
                """
            )
        )
    ).mappings().all()
    if answer_type_rows:
        config["answerTypes"] = [
            {
                "key": row["answer_type_key"],
                "name": row["answer_type_name"],
                "storageKind": row["storage_kind"],
                "widget": row["widget"],
                "allowsMultiple": bool(row.get("allows_multiple")),
                "allowsFreeText": bool(row.get("allows_free_text")),
                "description": row.get("description") or "",
            }
            for row in answer_type_rows
        ]

    category_rows = (
        await db.execute(
            text(
                """
                  SELECT c.category_key, c.category_name, c.description, c.sort_order,
                       g.group_key
                FROM eam.avdm_question_category c
                JOIN eam.avdm_question_group g ON g.id = c.group_id
                WHERE c.is_active = TRUE AND g.is_active = TRUE
                ORDER BY g.sort_order, c.sort_order, c.category_key
                """
            )
        )
    ).mappings().all()
    if category_rows:
        config["questionnaireCategories"] = [
            {
                "key": row["category_key"],
                "label": row["category_name"],
                "description": row.get("description") or "",
                "group": row["group_key"],
            }
            for row in category_rows
        ]

    option_rows = (
        await db.execute(
            text(
                """
                SELECT s.option_set_key, s.option_set_name, s.description, s.is_shared,
                       s.sort_order AS set_sort_order,
                       i.option_value, i.option_label, i.option_score, i.sort_order
                FROM eam.avdm_question_option_set s
                LEFT JOIN eam.avdm_question_option_item i ON i.option_set_id = s.id AND i.is_active = TRUE
                WHERE s.is_active = TRUE
                ORDER BY s.sort_order, s.option_set_key, i.sort_order, i.option_value
                """
            )
        )
    ).mappings().all()
    option_map: dict[str, list[dict[str, Any]]] = {}
    option_set_meta: dict[str, dict[str, Any]] = {}
    for row in option_rows:
        option_set_meta.setdefault(
            row["option_set_key"],
            {
                "key": row["option_set_key"],
                "name": row.get("option_set_name") or row["option_set_key"],
                "description": row.get("description") or "",
                "isShared": bool(row.get("is_shared")),
                "sortOrder": int(row.get("set_sort_order") or 0),
            },
        )
        if row.get("option_value") is not None:
            option_map.setdefault(row["option_set_key"], []).append(
                {
                    "label": row["option_label"],
                    "value": row["option_value"],
                    **({"score": float(row["option_score"])} if row.get("option_score") is not None else {}),
                }
            )
    if option_set_meta:
        config["optionSets"] = [
            {**meta, "options": option_map.get(option_set_key, [])}
            for option_set_key, meta in sorted(
                option_set_meta.items(),
                key=lambda item: (int(item[1].get("sortOrder") or 0), item[0]),
            )
        ]
    for option_key in QUESTIONNAIRE_OPTION_KEYS:
        if option_key in option_map:
            config[option_key] = option_map[option_key]

    question_rows = (
        await db.execute(
            text(
                """
                  SELECT q.stable_question_id, q.question_key, q.question_text, q.design_intent,
                      q.placeholder, q.source_scope, q.source_ref,
                      c.category_key, t.widget AS control, s.option_set_key
                FROM eam.avdm_question q
                JOIN eam.avdm_question_category c ON c.id = q.category_id
                JOIN eam.avdm_question_answer_type t ON t.id = q.answer_type_id
                LEFT JOIN eam.avdm_question_option_set s ON s.id = q.option_set_id
                WHERE q.is_active = TRUE AND c.is_active = TRUE AND t.is_active = TRUE
                ORDER BY c.sort_order, q.sort_order, q.stable_question_id
                """
            )
        )
    ).mappings().all()
    question_items: list[dict[str, Any]] = []
    if question_rows:
        for row in question_rows:
            option_set_key = row.get("option_set_key")
            item = {
                "id": int(row["stable_question_id"]),
                "text": row["question_text"],
                "category": row["category_key"],
                "control": row["control"],
                "sourceScope": row.get("source_scope") or "question_bank",
            }
            if row.get("question_key"):
                item["questionKey"] = row["question_key"]
            if row.get("source_ref"):
                item["sourceRef"] = row["source_ref"]
            if row.get("design_intent"):
                item["designIntent"] = row["design_intent"]
            if row.get("placeholder"):
                item["placeholder"] = row["placeholder"]
            if option_set_key:
                item["optionsSource"] = option_set_key
                item["options"] = option_map.get(option_set_key, [])
            question_items.append(item)
        config["questionBank"] = question_items
    config["assessmentMatrices"] = _build_assessment_matrices_from_questions(question_items)

    for config_key, document_key in STATIC_DOCUMENT_KEYS.items():
        if config_key in {"assessmentMatrices", "viewpointArtifactMapping", "projectTypeProfiles"}:
            continue
        config[config_key] = await _get_static_document(db, document_key=document_key)
    config["projectTypeProfiles"] = await _load_project_type_profiles_config(db)

    return config


async def save_questionnaire_config(
    db: AsyncSession,
    *,
    config: dict[str, Any],
    change_note: str | None,
    operator: str,
) -> dict[str, Any]:
    operator = operator or "system"
    await _seed_question_reference_data(db, operator=operator)
    await _set_all_questionnaire_records_inactive(db, operator=operator)

    answer_types = config.get("answerTypes") or []
    for answer_type in answer_types:
        answer_type_key = str(answer_type.get("key") or "").strip()
        if not answer_type_key:
            continue
        await _upsert_answer_type(
            db,
            answer_type_key=answer_type_key,
            answer_type_name=str(answer_type.get("name") or answer_type.get("label") or answer_type_key).strip(),
            storage_kind=str(answer_type.get("storageKind") or "single_choice").strip(),
            widget=str(answer_type.get("widget") or answer_type_key).strip(),
            allows_multiple=_normalize_bool(answer_type.get("allowsMultiple")),
            allows_free_text=_normalize_bool(answer_type.get("allowsFreeText")),
            description=str(answer_type.get("description") or "").strip(),
            operator=operator,
        )

    categories = config.get("questionnaireCategories") or []
    for index, category in enumerate(categories, start=1):
        group_key = str(category.get("group") or "change")
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_question_category (
                    group_id, category_key, category_name, description, sort_order,
                    is_active, create_by, update_by
                ) VALUES (
                    (SELECT id FROM eam.avdm_question_group WHERE group_key = :group_key),
                    :category_key, :category_name, :description, :sort_order,
                    TRUE, :operator, :operator
                )
                ON CONFLICT (category_key) DO UPDATE SET
                    group_id = EXCLUDED.group_id,
                    category_name = EXCLUDED.category_name,
                    description = EXCLUDED.description,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "group_key": group_key,
                "category_key": str(category.get("key") or "").strip(),
                "category_name": str(category.get("label") or "").strip(),
                "description": str(category.get("description") or "").strip(),
                "sort_order": index * 10,
                "operator": operator,
            },
        )

    option_sets_by_key: dict[str, dict[str, Any]] = {}
    for index, option_set in enumerate(config.get("optionSets") or [], start=1):
        option_set_key = str(option_set.get("key") or "").strip()
        if not option_set_key:
            continue
        option_sets_by_key[option_set_key] = {
            **option_set,
            "sortOrder": int(option_set.get("sortOrder") or index * 10),
        }

    for index, option_key in enumerate(QUESTIONNAIRE_OPTION_KEYS, start=1):
        if option_key not in option_sets_by_key and config.get(option_key):
            option_sets_by_key[option_key] = {
                "key": option_key,
                "name": option_key,
                "description": f"Managed option set for {option_key}",
                "isShared": True,
                "sortOrder": index * 10,
                "options": config.get(option_key) or [],
            }

    for option_set_key, option_set in option_sets_by_key.items():
        options = option_set.get("options") or []
        await _upsert_option_set(
            db,
            option_set_key=option_set_key,
            option_set_name=str(option_set.get("name") or option_set.get("label") or option_set_key).strip(),
            description=str(option_set.get("description") or "").strip(),
            is_shared=_normalize_bool(option_set.get("isShared"), default=True),
            sort_order=int(option_set.get("sortOrder") or 0),
            options=options,
            operator=operator,
        )

    questions = config.get("questionBank") or []
    for index, question in enumerate(questions, start=1):
        question_id = int(question.get("id") or 0)
        option_set_key = str(question.get("optionsSource") or "").strip() or None
        inline_options = question.get("options") or []
        if not option_set_key and inline_options:
            option_set_key = f"question:{question_id}"
            await _upsert_option_set(
                db,
                option_set_key=option_set_key,
                option_set_name=f"Question {question_id}",
                description=f"Inline answer options for question {question_id}",
                is_shared=False,
                sort_order=index * 10,
                options=inline_options,
                operator=operator,
            )

        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_question (
                    stable_question_id, question_key, category_id, answer_type_id, option_set_id,
                    question_text, design_intent, placeholder, source_scope, source_ref, sort_order,
                    is_active, create_by, update_by
                ) VALUES (
                    :stable_question_id, :question_key,
                    (SELECT id FROM eam.avdm_question_category WHERE category_key = :category_key),
                    (SELECT id FROM eam.avdm_question_answer_type WHERE answer_type_key = :answer_type_key),
                    CASE WHEN CAST(:option_set_key AS VARCHAR) IS NULL THEN NULL
                         ELSE (
                             SELECT id FROM eam.avdm_question_option_set
                             WHERE option_set_key = CAST(:option_set_key AS VARCHAR)
                         )
                    END,
                    :question_text, :design_intent, :placeholder, :source_scope, :source_ref, :sort_order,
                    TRUE, :operator, :operator
                )
                ON CONFLICT (stable_question_id) DO UPDATE SET
                    question_key = EXCLUDED.question_key,
                    category_id = EXCLUDED.category_id,
                    answer_type_id = EXCLUDED.answer_type_id,
                    option_set_id = EXCLUDED.option_set_id,
                    question_text = EXCLUDED.question_text,
                    design_intent = EXCLUDED.design_intent,
                    placeholder = EXCLUDED.placeholder,
                    source_scope = EXCLUDED.source_scope,
                    source_ref = EXCLUDED.source_ref,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "stable_question_id": question_id,
                "question_key": str(question.get("questionKey") or "").strip() or None,
                "category_key": str(question.get("category") or "").strip(),
                "answer_type_key": str(question.get("control") or "radio").strip(),
                "option_set_key": option_set_key,
                "question_text": str(question.get("text") or "").strip(),
                "design_intent": str(question.get("designIntent") or "").strip() or None,
                "placeholder": str(question.get("placeholder") or "").strip() or None,
                "source_scope": str(question.get("sourceScope") or "question_bank").strip() or "question_bank",
                "source_ref": str(question.get("sourceRef") or "").strip() or None,
                "sort_order": index * 10,
                "operator": operator,
            },
        )

    await _upsert_static_document(
        db,
        document_key=STATIC_DOCUMENT_KEYS["questionnaireSections"],
        payload=config.get("questionnaireSections") or _default_static_payload(STATIC_DOCUMENT_KEYS["questionnaireSections"]),
        operator=operator,
    )
    await _upsert_static_document(
        db,
        document_key=STATIC_DOCUMENT_KEYS["projectTypeGuide"],
        payload=config.get("projectTypeGuide") or _default_static_payload(STATIC_DOCUMENT_KEYS["projectTypeGuide"]),
        operator=operator,
    )
    await _save_project_type_profiles_config(
        db,
        profiles=config.get("projectTypeProfiles") or [],
        operator=operator,
    )

    revision = await _bump_revision(
        db,
        domain_key=QUESTIONNAIRE_DOMAIN,
        change_note=change_note,
        operator=operator,
    )
    await db.commit()
    return {"config": await load_questionnaire_config(db), **revision}


async def load_concern_mapping_config(db: AsyncSession) -> dict[str, Any]:
    config: dict[str, Any] = {"questionConcernMappings": [], "concernActivationRules": []}
    mapping_rows = (
        await db.execute(
            text(
                """
                SELECT q.stable_question_id, m.answer_value, c.concern_key,
                       m.mapping_score, m.severity, m.likelihood, m.hint_text,
                       m.sort_order
                FROM eam.avdm_question_answer_concern_mapping m
                JOIN eam.avdm_question q ON q.id = m.question_id
                JOIN eam.avdm_pact_concern c ON c.id = m.concern_id
                WHERE m.is_active = TRUE AND q.is_active = TRUE AND c.is_active = TRUE
                ORDER BY q.stable_question_id, m.answer_value, m.sort_order, c.concern_key
                """
            )
        )
    ).mappings().all()
    if mapping_rows:
        grouped: dict[tuple[int, str], dict[str, Any]] = {}
        for row in mapping_rows:
            key = (int(row["stable_question_id"]), str(row.get("answer_value") or ""))
            bucket = grouped.setdefault(
                key,
                {
                    "questionId": key[0],
                    "answer": key[1],
                    "concernScores": [],
                    "hints": [],
                },
            )
            if not any(score.get("concernKey") == row["concern_key"] for score in bucket["concernScores"]):
                bucket["concernScores"].append(
                    {
                        "concernKey": row["concern_key"],
                        "score": float(row.get("mapping_score") or 0),
                        **({"severity": float(row["severity"])} if row.get("severity") is not None else {}),
                        **({"likelihood": float(row["likelihood"])} if row.get("likelihood") is not None else {}),
                    }
                )
            if row.get("hint_text") and not bucket["hints"]:
                bucket["hints"] = [item for item in str(row["hint_text"]).split(" | ") if item]
        config["questionConcernMappings"] = list(grouped.values())

    rule_rows = (
        await db.execute(
            text(
                """
                SELECT r.rule_key, r.description, r.all_conditions, r.any_conditions,
                       c.concern_key, s.mapping_score, s.severity, s.likelihood, s.note_text,
                       r.sort_order, s.sort_order AS score_sort_order
                FROM eam.avdm_concern_activation_rule r
                LEFT JOIN eam.avdm_concern_activation_rule_score s ON s.rule_id = r.id AND s.is_active = TRUE
                LEFT JOIN eam.avdm_pact_concern c ON c.id = s.concern_id AND c.is_active = TRUE
                WHERE r.is_active = TRUE
                ORDER BY r.sort_order, r.rule_key, s.sort_order, c.concern_key
                """
            )
        )
    ).mappings().all()
    if rule_rows:
        grouped_rules: dict[str, dict[str, Any]] = {}
        for row in rule_rows:
            rule_key = row["rule_key"]
            bucket = grouped_rules.setdefault(
                rule_key,
                {
                    "id": rule_key,
                    "description": row.get("description") or "",
                    "all": row.get("all_conditions") or [],
                    "any": row.get("any_conditions") or [],
                    "concernScores": [],
                },
            )
            if row.get("concern_key"):
                if not any(score.get("concernKey") == row["concern_key"] for score in bucket["concernScores"]):
                    bucket["concernScores"].append(
                        {
                            "concernKey": row["concern_key"],
                            "score": float(row.get("mapping_score") or 0),
                            **({"severity": float(row["severity"])} if row.get("severity") is not None else {}),
                            **({"likelihood": float(row["likelihood"])} if row.get("likelihood") is not None else {}),
                            **({"note": row["note_text"]} if row.get("note_text") else {}),
                        }
                    )
        config["concernActivationRules"] = list(grouped_rules.values())
    return config


async def save_concern_mapping_config(
    db: AsyncSession,
    *,
    config: dict[str, Any],
    change_note: str | None,
    operator: str,
) -> dict[str, Any]:
    operator = operator or "system"
    await db.execute(text("DELETE FROM eam.avdm_question_answer_concern_mapping"))
    await db.execute(text("DELETE FROM eam.avdm_concern_activation_rule_score"))
    await db.execute(text("DELETE FROM eam.avdm_concern_activation_rule"))

    for item in config.get("questionConcernMappings") or []:
        question_id = int(item.get("questionId") or 0)
        answer = str(item.get("answer") or "").strip()
        hints = " | ".join([str(hint).strip() for hint in item.get("hints") or [] if str(hint).strip()]) or None
        unique_scores: dict[str, dict[str, Any]] = {}
        for score in item.get("concernScores") or []:
            concern_key = str(score.get("concernKey") or "").strip()
            if concern_key and concern_key not in unique_scores:
                unique_scores[concern_key] = score
        for index, score in enumerate(unique_scores.values(), start=1):
            await db.execute(
                text(
                    """
                    INSERT INTO eam.avdm_question_answer_concern_mapping (
                        question_id, concern_id, match_operator, answer_value,
                        mapping_score, severity, likelihood, hint_text, sort_order,
                        is_active, create_by, update_by
                    ) VALUES (
                        (SELECT id FROM eam.avdm_question WHERE stable_question_id = :question_id),
                        (SELECT id FROM eam.avdm_pact_concern WHERE concern_key = :concern_key),
                        'equals', :answer_value,
                        :mapping_score, :severity, :likelihood, :hint_text, :sort_order,
                        TRUE, :operator, :operator
                    )
                    """
                ),
                {
                    "question_id": question_id,
                    "concern_key": str(score.get("concernKey") or "").strip(),
                    "answer_value": answer,
                    "mapping_score": float(score.get("score") or 0),
                    "severity": score.get("severity"),
                    "likelihood": score.get("likelihood"),
                    "hint_text": hints,
                    "sort_order": index * 10,
                    "operator": operator,
                },
            )

    for index, rule in enumerate(config.get("concernActivationRules") or [], start=1):
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_concern_activation_rule (
                    rule_key, description, all_conditions, any_conditions,
                    sort_order, is_active, create_by, update_by
                ) VALUES (
                    :rule_key, :description, CAST(:all_conditions AS jsonb), CAST(:any_conditions AS jsonb),
                    :sort_order, TRUE, :operator, :operator
                )
                """
            ),
            {
                "rule_key": str(rule.get("id") or "").strip(),
                "description": str(rule.get("description") or "").strip(),
                "all_conditions": json.dumps(rule.get("all") or [], ensure_ascii=False),
                "any_conditions": json.dumps(rule.get("any") or [], ensure_ascii=False),
                "sort_order": index * 10,
                "operator": operator,
            },
        )
        unique_rule_scores: dict[str, dict[str, Any]] = {}
        for score in rule.get("concernScores") or []:
            concern_key = str(score.get("concernKey") or "").strip()
            if concern_key and concern_key not in unique_rule_scores:
                unique_rule_scores[concern_key] = score
        for score_index, score in enumerate(unique_rule_scores.values(), start=1):
            await db.execute(
                text(
                    """
                    INSERT INTO eam.avdm_concern_activation_rule_score (
                        rule_id, concern_id, mapping_score, severity, likelihood, note_text,
                        sort_order, is_active, create_by, update_by
                    ) VALUES (
                        (SELECT id FROM eam.avdm_concern_activation_rule WHERE rule_key = :rule_key),
                        (SELECT id FROM eam.avdm_pact_concern WHERE concern_key = :concern_key),
                        :mapping_score, :severity, :likelihood, :note_text,
                        :sort_order, TRUE, :operator, :operator
                    )
                    """
                ),
                {
                    "rule_key": str(rule.get("id") or "").strip(),
                    "concern_key": str(score.get("concernKey") or "").strip(),
                    "mapping_score": float(score.get("score") or 0),
                    "severity": score.get("severity"),
                    "likelihood": score.get("likelihood"),
                    "note_text": str(score.get("note") or "").strip() or None,
                    "sort_order": score_index * 10,
                    "operator": operator,
                },
            )

    revision = await _bump_revision(
        db,
        domain_key=CONCERN_MAPPING_DOMAIN,
        change_note=change_note,
        operator=operator,
    )
    await db.commit()
    return {"config": await load_concern_mapping_config(db), **revision}


async def _seed_artifact_categories(db: AsyncSession, *, operator: str) -> None:
    for item in ARTIFACT_CATEGORY_DEFINITIONS:
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_artifact_category (
                    category_key, category_name, description, sort_order,
                    is_active, create_by, update_by
                ) VALUES (
                    :category_key, :category_name, :description, :sort_order,
                    TRUE, :operator, :operator
                )
                ON CONFLICT (category_key) DO UPDATE SET
                    category_name = EXCLUDED.category_name,
                    description = EXCLUDED.description,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "category_key": item["key"],
                "category_name": item["name"],
                "description": item["description"],
                "sort_order": item["sortOrder"],
                "operator": operator or "system",
            },
        )


async def load_artifact_catalog_config(db: AsyncSession) -> dict[str, Any]:
    config: dict[str, Any] = {
        "catalogName": "Architecture Artifact Catalog",
        "stage": "Preparation",
        "artifactTypes": [],
    }
    rows = (
        await db.execute(
            text(
                """
                SELECT artifact_key, artifact_name, purpose, typical_contents, sort_order, is_active
                FROM eam.avdm_artifact
                WHERE is_active = TRUE
                ORDER BY sort_order, artifact_name
                """
            )
        )
    ).mappings().all()
    if rows:
        config["artifactTypes"] = [
            {
                "key": row["artifact_key"],
                "name": row["artifact_name"],
                "purpose": row.get("purpose") or "",
                "typicalContents": row.get("typical_contents") or [],
                "supportedViewpoints": [],
                "isActive": bool(row.get("is_active", True)),
                "sortOrder": int(row.get("sort_order") or 0),
            }
            for row in rows
        ]
    return config


async def save_artifact_catalog_config(
    db: AsyncSession,
    *,
    config: dict[str, Any],
    change_note: str | None,
    operator: str,
) -> dict[str, Any]:
    operator = operator or "system"
    await _seed_artifact_categories(db, operator=operator)
    await db.execute(
        text("UPDATE eam.avdm_artifact SET is_active = FALSE, update_by = :operator, update_at = NOW()"),
        {"operator": operator},
    )
    for index, item in enumerate(config.get("artifactTypes") or [], start=1):
        artifact_key = str(item.get("key") or "").strip()
        if not artifact_key:
            continue
        category_key = DEFAULT_ARTIFACT_CATEGORY_BY_KEY.get(artifact_key, "architecture_diagram")
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_artifact (
                    artifact_key, artifact_category_id, artifact_name, purpose, stage,
                    typical_contents, sort_order, is_active, create_by, update_by
                ) VALUES (
                    :artifact_key,
                    (SELECT id FROM eam.avdm_artifact_category WHERE category_key = :category_key),
                    :artifact_name, :purpose, :stage,
                    CAST(:typical_contents AS jsonb), :sort_order, TRUE, :operator, :operator
                )
                ON CONFLICT (artifact_key) DO UPDATE SET
                    artifact_category_id = EXCLUDED.artifact_category_id,
                    artifact_name = EXCLUDED.artifact_name,
                    purpose = EXCLUDED.purpose,
                    stage = EXCLUDED.stage,
                    typical_contents = EXCLUDED.typical_contents,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "artifact_key": artifact_key,
                "category_key": category_key,
                "artifact_name": str(item.get("name") or "").strip(),
                "purpose": str(item.get("purpose") or "").strip(),
                    "stage": str(config.get("stage") or "Preparation"),
                "typical_contents": json.dumps(item.get("typicalContents") or [], ensure_ascii=False),
                "sort_order": int(item.get("sortOrder") or index * 10),
                "operator": operator,
            },
        )
    revision = await _bump_revision(
        db,
        domain_key=ARTIFACT_CATALOG_DOMAIN,
        change_note=change_note,
        operator=operator,
    )
    await db.commit()
    return {"config": await load_artifact_catalog_config(db), **revision}


async def load_viewpoint_artifact_mapping_config(db: AsyncSession) -> dict[str, Any]:
    payload = await _get_static_document(
        db,
        document_key=STATIC_DOCUMENT_KEYS["viewpointArtifactMapping"],
    )
    config = payload if isinstance(payload, dict) else _default_static_payload(STATIC_DOCUMENT_KEYS["viewpointArtifactMapping"])
    rows = (
        await db.execute(
            text(
                """
                SELECT v.viewpoint_number, v.layer_name, v.viewpoint_name, v.logical_physical,
                       v.structure_behavior, v.purpose, v.example, v.primary_source, v.audience,
                       v.notes, v.sort_order AS viewpoint_sort_order,
                       c.concern_key, vc.sort_order AS concern_sort_order,
                       a.artifact_key, va.recommendation_status, va.sort_order AS artifact_sort_order
                FROM eam.avdm_viewpoint v
                LEFT JOIN eam.avdm_viewpoint_concern_mapping vc
                  ON vc.viewpoint_id = v.id AND vc.is_active = TRUE
                LEFT JOIN eam.avdm_pact_concern c
                  ON c.id = vc.concern_id AND c.is_active = TRUE
                LEFT JOIN eam.avdm_viewpoint_artifact_mapping va
                  ON va.viewpoint_id = v.id AND va.is_active = TRUE
                LEFT JOIN eam.avdm_artifact a
                  ON a.id = va.artifact_id AND a.is_active = TRUE
                WHERE v.is_active = TRUE
                ORDER BY v.sort_order, v.viewpoint_number, vc.sort_order, c.concern_key, va.sort_order, a.artifact_key
                """
            )
        )
    ).mappings().all()
    viewpoints_by_number: dict[int, dict[str, Any]] = {}
    concern_seen: dict[int, set[str]] = {}
    artifact_seen: dict[tuple[int, str], set[str]] = {}
    for row in rows:
        number = int(row["viewpoint_number"])
        viewpoint = viewpoints_by_number.setdefault(
            number,
            {
                "number": number,
                "layer": row.get("layer_name") or "",
                "viewpoint": row.get("viewpoint_name") or "",
                "concernKeys": [],
                "mandatoryArtifacts": [],
                "optionalArtifacts": [],
                "logicalPhysical": row.get("logical_physical") or "",
                "structureBehavior": row.get("structure_behavior") or "",
                "purpose": row.get("purpose") or "",
                "example": row.get("example") or "",
                "primarySource": row.get("primary_source") or "",
                "audience": row.get("audience") or "",
                "notes": row.get("notes") or "",
                "isActive": True,
                "sortOrder": int(row.get("viewpoint_sort_order") or number),
            },
        )
        concern_key = str(row.get("concern_key") or "").strip()
        if concern_key and concern_key not in concern_seen.setdefault(number, set()):
            concern_seen[number].add(concern_key)
            viewpoint["concernKeys"].append(concern_key)
        artifact_key = str(row.get("artifact_key") or "").strip()
        status = str(row.get("recommendation_status") or "").strip()
        target_key = "mandatoryArtifacts" if status == "Mandatory" else "optionalArtifacts" if status == "Optional" else ""
        if artifact_key and target_key and artifact_key not in artifact_seen.setdefault((number, target_key), set()):
            artifact_seen[(number, target_key)].add(artifact_key)
            viewpoint[target_key].append(artifact_key)
    config["viewpoints"] = list(viewpoints_by_number.values())
    return config


async def save_viewpoint_artifact_mapping_config(
    db: AsyncSession,
    *,
    config: dict[str, Any],
    change_note: str | None,
    operator: str,
) -> dict[str, Any]:
    operator = operator or "system"
    metadata = {key: value for key, value in config.items() if key != "viewpoints"}
    await _upsert_static_document(
        db,
        document_key=STATIC_DOCUMENT_KEYS["viewpointArtifactMapping"],
        payload=metadata,
        operator=operator,
    )
    await db.execute(
        text("UPDATE eam.avdm_viewpoint SET is_active = FALSE, update_by = :operator, update_at = NOW()"),
        {"operator": operator},
    )
    await db.execute(
        text("UPDATE eam.avdm_viewpoint_concern_mapping SET is_active = FALSE, update_by = :operator, update_at = NOW()"),
        {"operator": operator},
    )
    await db.execute(
        text("UPDATE eam.avdm_viewpoint_artifact_mapping SET is_active = FALSE, update_by = :operator, update_at = NOW()"),
        {"operator": operator},
    )
    for index, viewpoint in enumerate(config.get("viewpoints") or [], start=1):
        number = int(viewpoint.get("number") or index)
        await db.execute(
            text(
                """
                INSERT INTO eam.avdm_viewpoint (
                    viewpoint_number, layer_name, viewpoint_name, logical_physical, structure_behavior,
                    purpose, example, primary_source, audience, notes, sort_order,
                    is_active, create_by, update_by
                ) VALUES (
                    :viewpoint_number, :layer_name, :viewpoint_name, :logical_physical, :structure_behavior,
                    :purpose, :example, :primary_source, :audience, :notes, :sort_order,
                    TRUE, :operator, :operator
                )
                ON CONFLICT (viewpoint_number) DO UPDATE SET
                    layer_name = EXCLUDED.layer_name,
                    viewpoint_name = EXCLUDED.viewpoint_name,
                    logical_physical = EXCLUDED.logical_physical,
                    structure_behavior = EXCLUDED.structure_behavior,
                    purpose = EXCLUDED.purpose,
                    example = EXCLUDED.example,
                    primary_source = EXCLUDED.primary_source,
                    audience = EXCLUDED.audience,
                    notes = EXCLUDED.notes,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    update_by = EXCLUDED.update_by,
                    update_at = NOW()
                """
            ),
            {
                "viewpoint_number": number,
                "layer_name": str(viewpoint.get("layer") or "Unclassified").strip(),
                "viewpoint_name": str(viewpoint.get("viewpoint") or f"Viewpoint {number}").strip(),
                "logical_physical": str(viewpoint.get("logicalPhysical") or "").strip() or None,
                "structure_behavior": str(viewpoint.get("structureBehavior") or "").strip() or None,
                "purpose": str(viewpoint.get("purpose") or "").strip() or None,
                "example": str(viewpoint.get("example") or "").strip() or None,
                "primary_source": str(viewpoint.get("primarySource") or "").strip() or None,
                "audience": str(viewpoint.get("audience") or "").strip() or None,
                "notes": str(viewpoint.get("notes") or "").strip() or None,
                "sort_order": int(viewpoint.get("sortOrder") or number),
                "operator": operator,
            },
        )
        for concern_index, concern_key in enumerate(viewpoint.get("concernKeys") or [], start=1):
            normalized_concern_key = str(concern_key or "").strip().upper()
            if not normalized_concern_key:
                continue
            await db.execute(
                text(
                    """
                    INSERT INTO eam.avdm_viewpoint_concern_mapping (
                        viewpoint_id, concern_id, sort_order, is_active, create_by, update_by
                    ) VALUES (
                        (SELECT id FROM eam.avdm_viewpoint WHERE viewpoint_number = :viewpoint_number),
                        (SELECT id FROM eam.avdm_pact_concern WHERE concern_key = :concern_key),
                        :sort_order, TRUE, :operator, :operator
                    )
                    ON CONFLICT (viewpoint_id, concern_id) DO UPDATE SET
                        sort_order = EXCLUDED.sort_order,
                        is_active = TRUE,
                        update_by = EXCLUDED.update_by,
                        update_at = NOW()
                    """
                ),
                {
                    "viewpoint_number": number,
                    "concern_key": normalized_concern_key,
                    "sort_order": concern_index * 10,
                    "operator": operator,
                },
            )
        for status, field_name in (("Mandatory", "mandatoryArtifacts"), ("Optional", "optionalArtifacts")):
            for artifact_index, artifact_key in enumerate(viewpoint.get(field_name) or [], start=1):
                normalized_artifact_key = str(artifact_key or "").strip()
                if not normalized_artifact_key:
                    continue
                await db.execute(
                    text(
                        """
                        INSERT INTO eam.avdm_viewpoint_artifact_mapping (
                            viewpoint_id, artifact_id, recommendation_status, sort_order,
                            is_active, create_by, update_by
                        ) VALUES (
                            (SELECT id FROM eam.avdm_viewpoint WHERE viewpoint_number = :viewpoint_number),
                            (SELECT id FROM eam.avdm_artifact WHERE artifact_key = :artifact_key),
                            :recommendation_status, :sort_order, TRUE, :operator, :operator
                        )
                        ON CONFLICT (viewpoint_id, artifact_id, recommendation_status) DO UPDATE SET
                            sort_order = EXCLUDED.sort_order,
                            is_active = TRUE,
                            update_by = EXCLUDED.update_by,
                            update_at = NOW()
                        """
                    ),
                    {
                        "viewpoint_number": number,
                        "artifact_key": normalized_artifact_key,
                        "recommendation_status": status,
                        "sort_order": artifact_index * 10,
                        "operator": operator,
                    },
                )
    revision = await _bump_revision(
        db,
        domain_key=VIEWPOINT_ARTIFACT_MAPPING_DOMAIN,
        change_note=change_note,
        operator=operator,
    )
    await db.commit()
    return {"config": await load_viewpoint_artifact_mapping_config(db), **revision}


async def get_config_metadata(
    db: AsyncSession,
    *,
    domain_key: str,
    default_change_note: str,
) -> dict[str, Any]:
    return await _get_revision(db, domain_key=domain_key, default_change_note=default_change_note)


async def list_concern_artifact_recommendation_items(
    db: AsyncSession,
    *,
    decisions: list[dict[str, Any]],
) -> list[ArtifactRecommendationItem]:
    concern_keys = [
        str(item.get("concernKey") or "").strip().upper()
        for item in decisions
        if str(item.get("classification") or "") != "Optional" and str(item.get("concernKey") or "").strip()
    ]
    if not concern_keys:
        return []
    rows = (
        await db.execute(
            text(
                """
                SELECT c.concern_key, a.artifact_name, m.default_status, a.sort_order
                FROM eam.avdm_concern_artifact_mapping m
                JOIN eam.avdm_pact_concern c ON c.id = m.concern_id
                JOIN eam.avdm_artifact a ON a.id = m.artifact_id
                WHERE m.is_active = TRUE AND a.is_active = TRUE AND c.is_active = TRUE
                  AND c.concern_key = ANY(:concern_keys)
                ORDER BY c.concern_key, a.sort_order, a.artifact_name
                """
            ),
            {"concern_keys": concern_keys},
        )
    ).mappings().all()
    artifact_map: dict[str, list[str]] = {}
    for row in rows:
        artifact_map.setdefault(row["concern_key"], []).append(row["artifact_name"])

    items: list[ArtifactRecommendationItem] = []
    for decision in decisions:
        concern_key = str(decision.get("concernKey") or "").strip().upper()
        classification = str(decision.get("classification") or "")
        artifact_names = artifact_map.get(concern_key, [])
        if classification == "Optional" or not artifact_names:
            continue
        items.append(
            ArtifactRecommendationItem(
                concernKey=concern_key,
                concernName=str(decision.get("concernName") or concern_key),
                classification=classification,
                artifacts=artifact_names,
            )
        )
    return items