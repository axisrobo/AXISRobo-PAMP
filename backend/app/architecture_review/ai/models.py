"""Pydantic models for EA Review agent results."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ScoreDimension(BaseModel):
    score: float
    max: float


class TechScoreBreakdown(BaseModel):
    cloud_network_completeness: ScoreDimension
    connectivity: ScoreDimension
    technical_component_completeness: ScoreDimension
    interaction_integration: ScoreDimension
    security_compliance: ScoreDimension
    terminology_expression: ScoreDimension


class TechIssue(BaseModel):
    id: str
    description: str
    dimension: str
    related_entities: str
    related_relationships: Optional[str] = ""
    priority: str
    impact: str
    issue_type: str
    suggestion: str


class OverallEvaluation(BaseModel):
    score: float
    summary: str


class ArchitectureReviewResult(BaseModel):
    title: str = ""
    overall_evaluation: OverallEvaluation
    score_breakdown: Optional[TechScoreBreakdown] = None
    issues: list[TechIssue] = []
    recommendations: list[str] = []
    content_extract_result: Optional[Any] = None


class AppScoreBreakdown(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    application_information_completion: float
    relationship_completion: float
    relationship_accuracy: float
    template_matching_rate: float


class AppIssue(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    description: str
    dimension: str
    related_entities: str | list[str] | None = ""
    related_relationshipes: str | list[str] | None = ""
    priority: str
    impact: str
    issue_type: str
    suggestion: str

    @field_validator("related_entities", "related_relationshipes", mode="before")
    @classmethod
    def _normalize_list_to_string(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item is not None)
        return str(value)


class AppArchitectureReviewResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    title: str = ""
    overall_evaluation: OverallEvaluation
    score_breakdown: Optional[AppScoreBreakdown] = None
    issues: list[AppIssue] = []
    recommendations: list[str] = []
    content_extract_result: Optional[Any] = None


class ReviewHistoryRecord(BaseModel):
    id: int
    itcode: str
    file_name: str
    s3_url: str
    created_at: Any
    title: str | None = None
    score: float | None = None
    review_type: str | None = None
    code: str | None = None
    scenario: str | None = None
    review_result: dict[str, Any] | None = None
