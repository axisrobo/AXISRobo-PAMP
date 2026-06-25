"""Pydantic models for AVDM evaluation APIs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkflowStatus = Literal[
    "request_created",
    "questionnaire_submitted",
    "questionnaire_confirmed",
    "concern_requirement_confirmed",
    "artifact_requirement_confirmed",
    "artifact_submitted",
]

ArchitectureLifecycleStage = Literal[
    "Preparation",
    "Design",
    "Review",
    "Execution & Operations",
]


class RiskItem(BaseModel):
    code: str = Field(..., description="Risk code, e.g. compliance, data, operations")
    severity: float = Field(..., ge=0, le=5)
    likelihood: float = Field(..., ge=0, le=5)
    note: str | None = None


class AVDMEvaluateRequest(BaseModel):
    projectId: str = Field(..., min_length=1)
    projectType: str | None = None
    projectComplexity: float = Field(0.5, ge=0, le=1)
    riskItems: list[RiskItem] = Field(default_factory=list)


class ConcernDecision(BaseModel):
    concernKey: str
    concernName: str
    layer: str
    score: float
    classification: str
    rationale: str


class LayerSummary(BaseModel):
    layer: str
    mandatory: int
    recommended: int
    optional: int


class AVDMEvaluateResponse(BaseModel):
    projectId: str
    decisions: list[ConcernDecision]
    layerSummary: list[LayerSummary]
    contributions: dict | None = None


class ReviewOverrideItem(BaseModel):
    concernKey: str
    classification: str = Field(..., pattern="^(Mandatory|Recommended|Optional)$")
    reviewerComment: str | None = None


class AVDMReviewRequest(BaseModel):
    evaluation: AVDMEvaluateResponse
    overrides: list[ReviewOverrideItem] = Field(default_factory=list)


class AVDMReviewResponse(BaseModel):
    projectId: str
    decisions: list[ConcernDecision]
    changeCount: int


class PactConcern(BaseModel):
    id: str
    concernKey: str
    concernName: str
    layer: str
    riskTags: list[str] = Field(default_factory=list)
    description: str = ""
    isActive: bool = True
    updatedAt: datetime | None = None
    updatedBy: str | None = None


class PactConcernCatalogResponse(BaseModel):
    layers: list[str] = Field(default_factory=list)
    items: list[PactConcern] = Field(default_factory=list)


class PactConcernCatalogExportResponse(BaseModel):
    catalogName: str = "PACT Concern Catalog"
    version: int = 1
    exportedAt: datetime
    includeInactive: bool = True
    total: int
    layers: list[str] = Field(default_factory=list)
    items: list[PactConcern] = Field(default_factory=list)


class PactConcernUpsertRequest(BaseModel):
    concernKey: str = Field(..., min_length=2)
    concernName: str = Field(..., min_length=2)
    layer: str = Field(..., min_length=2)
    riskTags: list[str] = Field(default_factory=list)
    description: str = ""
    isActive: bool = True
    operator: str = "system"


class QuestionnaireRiskAnswer(BaseModel):
    riskCode: str = Field(..., min_length=1)
    severity: float = Field(..., ge=0, le=5)
    likelihood: float = Field(..., ge=0, le=5)
    note: str | None = None


class ProjectQuestionnaireUpsertRequest(BaseModel):
    projectType: str | None = None
    projectComplexity: float = Field(0.5, ge=0, le=1)
    questionnaire: dict = Field(default_factory=dict)
    answers: list[QuestionnaireRiskAnswer] = Field(default_factory=list)
    status: str = "draft"
    operator: str = "system"


class AVDMNeedJudgement(BaseModel):
    needsAVDM: bool
    confidence: float
    rationale: str


class ProjectAssessmentRecord(BaseModel):
    id: str
    projectId: str
    projectType: str | None = None
    projectComplexity: float
    questionnaire: dict = Field(default_factory=dict)
    riskItems: list[dict] = Field(default_factory=list)
    evaluation: dict | None = None
    reviewResult: dict | None = None
    artifactSelection: list[dict] | None = None
    needsAVDM: bool | None = None
    judgementReason: str | None = None
    version: int
    status: str
    questionnaireSubmittedAt: datetime | None = None
    questionnaireConfirmedAt: datetime | None = None
    concernRequirementConfirmedAt: datetime | None = None
    artifactRequirementConfirmedAt: datetime | None = None
    artifactSubmittedAt: datetime | None = None


class ProjectAssessmentUpsertResponse(BaseModel):
    assessment: ProjectAssessmentRecord
    judgement: AVDMNeedJudgement


class AVDMTrendPoint(BaseModel):
    month: str
    total: int
    needsAVDM: int


class AVDMStatisticsOverview(BaseModel):
    totalProjects: int
    needsAVDMProjects: int
    needsRatio: float
    avgMandatory: float
    avgRecommended: float
    avgOptional: float
    dataBlindSpotRatio: float
    operationsBlindSpotRatio: float


class AVDMStatisticsResponse(BaseModel):
    overview: AVDMStatisticsOverview
    trend: list[AVDMTrendPoint]


class ArtifactRecommendationItem(BaseModel):
    concernKey: str
    concernName: str
    classification: str
    artifacts: list[str] = Field(default_factory=list)


class ArtifactRecommendationResponse(BaseModel):
    projectId: str
    items: list[ArtifactRecommendationItem] = Field(default_factory=list)


class ArtifactSelectionItem(BaseModel):
    concernKey: str
    artifactName: str
    rationale: str | None = None


class ArtifactSelectionUpsertRequest(BaseModel):
    selections: list[ArtifactSelectionItem] = Field(default_factory=list)
    operator: str = "system"


class WorkflowStageConfirmRequest(BaseModel):
    operator: str = "system"


class AVDMWorkflowStatusResponse(BaseModel):
    projectId: str
    currentStatus: WorkflowStatus
    availableStatuses: list[WorkflowStatus] = Field(default_factory=list)
    architectureLifecycleStage: ArchitectureLifecycleStage
    architectureLifecycleStages: list[ArchitectureLifecycleStage] = Field(default_factory=list)
    questionnaireCompleted: bool
    concernIdentificationCompleted: bool
    artifactSelectionCompleted: bool
    diagramUploadAllowed: bool
    stage: WorkflowStatus


class QuestionnaireConfigResponse(BaseModel):
    configKey: str
    version: int
    config: dict = Field(default_factory=dict)
    changeNote: str | None = None
    updatedBy: str | None = None
    updatedAt: datetime | None = None
    source: Literal["db", "default"] = "db"


class QuestionnaireConfigUpsertRequest(BaseModel):
    config: dict = Field(default_factory=dict)
    changeNote: str | None = None
    operator: str = "system"
