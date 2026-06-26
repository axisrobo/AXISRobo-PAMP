"""Normalized AVDM master-data models.

These models define the target relational shape for questionnaire, concern,
and artifact master data. They are intentionally independent from the current
JSON bootstrap config so the migration can proceed incrementally.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


QuestionSourceScope = Literal["question_bank", "questionnaire_section", "assessment_matrix"]
AnswerStorageKind = Literal["single_choice", "multi_choice", "text"]
AnswerMatchOperator = Literal["equals", "in", "contains", "non_empty", "regex"]
ArtifactRecommendationStatus = Literal["Mandatory", "Recommended", "Optional", "Not Required"]


@dataclass(frozen=True, slots=True)
class QuestionGroupModel:
    key: str
    name: str
    description: str = ""
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class QuestionCategoryModel:
    key: str
    group_key: str
    name: str
    description: str = ""
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class QuestionAnswerTypeModel:
    key: str
    name: str
    storage_kind: AnswerStorageKind
    widget: str
    allows_multiple: bool = False
    allows_free_text: bool = False
    description: str = ""
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class QuestionAnswerOptionSetModel:
    key: str
    name: str
    description: str = ""
    is_shared: bool = True
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class QuestionAnswerOptionItemModel:
    option_set_key: str
    value: str
    label: str
    score: float | None = None
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class QuestionModel:
    stable_id: int
    category_key: str
    answer_type_key: str
    prompt: str
    question_key: str | None = None
    design_intent: str = ""
    option_set_key: str | None = None
    placeholder: str | None = None
    source_scope: QuestionSourceScope = "question_bank"
    source_ref: str | None = None
    sort_order: int = 0
    is_active: bool = True
    requires_comment_on_answers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class QuestionAnswerConcernMappingModel:
    question_stable_id: int
    concern_key: str
    match_operator: AnswerMatchOperator = "equals"
    answer_value: str | None = None
    mapping_score: float = 0.0
    severity: float | None = None
    likelihood: float | None = None
    hint: str | None = None
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ArchitectureConcernCatalogModel:
    concern_key: str
    concern_name: str
    layer: str
    description: str = ""
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ArtifactCategoryModel:
    key: str
    name: str
    description: str = ""
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ArtifactModel:
    key: str
    category_key: str
    name: str
    purpose: str
    stage: str = "Preparation"
    typical_contents: tuple[str, ...] = field(default_factory=tuple)
    sort_order: int = 0
    is_active: bool = True