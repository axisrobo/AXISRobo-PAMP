"""AVDM API routes for Phase 2 concern decision workflow."""
from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Role, require_permission, require_role
from app.database import get_db

from .catalog import CONCERN_CATALOG, PACT_LAYERS
from .models import (
    AVDMEvaluateRequest,
    AVDMEvaluateResponse,
    AVDMNeedJudgement,
    ArtifactRecommendationResponse,
    ArtifactSelectionUpsertRequest,
    AVDMReviewRequest,
    AVDMReviewResponse,
    AVDMStatisticsResponse,
    AVDMWorkflowStatusResponse,
    WorkflowStageConfirmRequest,
    PactConcern,
    PactConcernCatalogExportResponse,
    PactConcernCatalogResponse,
    PactConcernUpsertRequest,
    ProjectAssessmentRecord,
    ProjectAssessmentUpsertResponse,
    ProjectQuestionnaireUpsertRequest,
    QuestionnaireConfigResponse,
    QuestionnaireConfigUpsertRequest,
    RiskItem,
)
from .questionnaire_config import (
    DEFAULT_ARTIFACT_CATALOG_CONFIG_KEY,
    DEFAULT_CONFIG_KEY,
    DEFAULT_MAPPING_CONFIG_KEY,
    DEFAULT_VIEWPOINT_ARTIFACT_MAPPING_CONFIG_KEY,
)
from .master_data_repository import (
    ARTIFACT_CATALOG_DOMAIN,
    CONCERN_MAPPING_DOMAIN,
    QUESTIONNAIRE_DOMAIN,
    VIEWPOINT_ARTIFACT_MAPPING_DOMAIN,
    get_config_metadata,
    list_viewpoint_artifact_recommendation_items,
    load_artifact_catalog_config,
    load_concern_mapping_config,
    load_questionnaire_config,
    load_viewpoint_artifact_mapping_config,
    save_artifact_catalog_config,
    save_concern_mapping_config,
    save_questionnaire_config,
    save_viewpoint_artifact_mapping_config,
)
from app.infrastructure.database.repositories.add_repo import PostgresConcernRepository
from app.application.add.services import ConcernService

from .repository import (
    get_assessment_by_project,
    list_assessment_records_for_stats,
    list_concerns,
    upsert_concern,
    upsert_project_assessment,
)
from .service import apply_review_overrides, build_statistics, evaluate_avdm, judge_avdm_need
from .service import recommend_artifacts_from_config


router = APIRouter()


def _build_config_response(config_key: str, config: dict, metadata: dict) -> QuestionnaireConfigResponse:
    return QuestionnaireConfigResponse(
        configKey=config_key,
        version=int(metadata.get("version") or 1),
        config=config,
        changeNote=metadata.get("changeNote"),
        updatedBy=metadata.get("updatedBy"),
        updatedAt=metadata.get("updatedAt"),
        source=metadata.get("source") or "db",
    )


@router.get("/questionnaire-config", response_model=QuestionnaireConfigResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_questionnaire_config(
    configKey: str = Query(DEFAULT_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    config = await load_questionnaire_config(db)
    metadata = await get_config_metadata(
        db,
        domain_key=QUESTIONNAIRE_DOMAIN,
        default_change_note="normalized questionnaire master data",
    )
    return _build_config_response(configKey, config, metadata)


@router.put(
    "/questionnaire-config",
    response_model=QuestionnaireConfigResponse,
    dependencies=[Depends(require_role(Role.EA_ADMIN))],
)
async def put_questionnaire_config(
    payload: QuestionnaireConfigUpsertRequest,
    configKey: str = Query(DEFAULT_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    operator = payload.operator.strip() or "system"
    result = await save_questionnaire_config(
        db,
        config=payload.config,
        change_note=payload.changeNote,
        operator=operator,
    )
    return _build_config_response(configKey, result["config"], result)


@router.get("/concern-mapping-config", response_model=QuestionnaireConfigResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_concern_mapping_config(
    configKey: str = Query(DEFAULT_MAPPING_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    config = await load_concern_mapping_config(db)
    metadata = await get_config_metadata(
        db,
        domain_key=CONCERN_MAPPING_DOMAIN,
        default_change_note="normalized question-to-concern mapping",
    )
    return _build_config_response(configKey, config, metadata)


@router.put(
    "/concern-mapping-config",
    response_model=QuestionnaireConfigResponse,
    dependencies=[Depends(require_role(Role.EA_ADMIN))],
)
async def put_concern_mapping_config(
    payload: QuestionnaireConfigUpsertRequest,
    configKey: str = Query(DEFAULT_MAPPING_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    operator = payload.operator.strip() or "system"
    result = await save_concern_mapping_config(
        db,
        config=payload.config,
        change_note=payload.changeNote,
        operator=operator,
    )
    return _build_config_response(configKey, result["config"], result)


@router.get("/artifact-catalog-config", response_model=QuestionnaireConfigResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_artifact_catalog_config(
    configKey: str = Query(DEFAULT_ARTIFACT_CATALOG_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    config = await load_artifact_catalog_config(db)
    metadata = await get_config_metadata(
        db,
        domain_key=ARTIFACT_CATALOG_DOMAIN,
        default_change_note="normalized architecture artifact catalog",
    )
    return _build_config_response(configKey, config, metadata)


@router.put(
    "/artifact-catalog-config",
    response_model=QuestionnaireConfigResponse,
    dependencies=[Depends(require_role(Role.EA_ADMIN))],
)
async def put_artifact_catalog_config(
    payload: QuestionnaireConfigUpsertRequest,
    configKey: str = Query(DEFAULT_ARTIFACT_CATALOG_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    operator = payload.operator.strip() or "system"
    result = await save_artifact_catalog_config(
        db,
        config=payload.config,
        change_note=payload.changeNote,
        operator=operator,
    )
    return _build_config_response(configKey, result["config"], result)


@router.get("/viewpoint-artifact-mapping-config", response_model=QuestionnaireConfigResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_viewpoint_artifact_mapping_config(
    configKey: str = Query(DEFAULT_VIEWPOINT_ARTIFACT_MAPPING_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    config = await load_viewpoint_artifact_mapping_config(db)
    metadata = await get_config_metadata(
        db,
        domain_key=VIEWPOINT_ARTIFACT_MAPPING_DOMAIN,
        default_change_note="viewpoint to artifact mapping guide",
    )
    return _build_config_response(configKey, config, metadata)


@router.put(
    "/viewpoint-artifact-mapping-config",
    response_model=QuestionnaireConfigResponse,
    dependencies=[Depends(require_role(Role.EA_ADMIN))],
)
async def put_viewpoint_artifact_mapping_config(
    payload: QuestionnaireConfigUpsertRequest,
    configKey: str = Query(DEFAULT_VIEWPOINT_ARTIFACT_MAPPING_CONFIG_KEY),
    db: AsyncSession = Depends(get_db),
):
    operator = payload.operator.strip() or "system"
    result = await save_viewpoint_artifact_mapping_config(
        db,
        config=payload.config,
        change_note=payload.changeNote,
        operator=operator,
    )
    return _build_config_response(configKey, result["config"], result)


@router.get("/concern-viewpoint-mapping", dependencies=[Depends(require_permission("avdm", "read"))])
async def get_concern_viewpoint_mapping(
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text(
            "SELECT c.concern_key, c.concern_name, c.layer, vp.viewpoint_number, vp.viewpoint_name, vp.layer_name "
            "FROM eam.avdm_viewpoint_concern_mapping m "
            "JOIN eam.avdm_pact_concern c ON c.id = m.concern_id AND c.is_active = TRUE "
            "JOIN eam.avdm_viewpoint vp ON vp.id = m.viewpoint_id AND vp.is_active = TRUE "
            "WHERE m.is_active = TRUE ORDER BY vp.layer_name, vp.viewpoint_number, c.concern_key"
        )
    )
    items = []
    for row in rows.mappings().all():
        items.append({
            "concernKey": row["concern_key"],
            "concernName": row["concern_name"],
            "concernLayer": row["layer"],
            "viewpointNumber": row["viewpoint_number"],
            "viewpointName": row["viewpoint_name"],
            "viewpointLayer": row["layer_name"],
        })
    return {"data": items, "total": len(items)}


@router.get("/viewpoints", dependencies=[Depends(require_permission("avdm", "read"))])
async def list_viewpoints(
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text(
            "SELECT id, viewpoint_number, layer_name, viewpoint_name, logical_physical, structure_behavior, "
            "purpose, example, primary_source, audience, notes, sort_order, is_active "
            "FROM eam.avdm_viewpoint ORDER BY sort_order, viewpoint_number"
        )
    )
    items = []
    for row in rows.mappings().all():
        items.append({
            "id": str(row["id"]),
            "viewpointNumber": row["viewpoint_number"],
            "layerName": row["layer_name"],
            "viewpointName": row["viewpoint_name"],
            "logicalPhysical": row["logical_physical"],
            "structureBehavior": row["structure_behavior"],
            "purpose": row["purpose"],
            "example": row["example"],
            "primarySource": row["primary_source"],
            "audience": row["audience"],
            "notes": row["notes"],
            "sortOrder": row["sort_order"],
            "isActive": row["is_active"],
        })
    return {"data": items, "total": len(items)}


WORKFLOW_STATUSES = [
    "request_created",
    "questionnaire_submitted",
    "questionnaire_confirmed",
    "concern_requirement_confirmed",
    "artifact_requirement_confirmed",
    "artifact_submitted",
]

ARCHITECTURE_LIFECYCLE_STAGES = [
    "Preparation",
    "Design",
    "Review",
    "Execution & Operations",
]

WORKFLOW_STATUS_ALIAS: dict[str, str] = {
    "requestcreated": "request_created",
    "request_created": "request_created",
    "questionnairesubmitted": "questionnaire_submitted",
    "questionnaire_submitted": "questionnaire_submitted",
    "questionnaresubmited": "questionnaire_submitted",
    "questionnairesubmited": "questionnaire_submitted",
    "questionnare_submited": "questionnaire_submitted",
    "questionnaireconfirmed": "questionnaire_confirmed",
    "questionnaire_confirmed": "questionnaire_confirmed",
    "questionnareconfirmed": "questionnaire_confirmed",
    "concernrequirementconfirmed": "concern_requirement_confirmed",
    "concern_requirement_confirmed": "concern_requirement_confirmed",
    "concernrequiremendconfirmed": "concern_requirement_confirmed",
    "artifactrequirementconfirmed": "artifact_requirement_confirmed",
    "artifact_requirement_confirmed": "artifact_requirement_confirmed",
    "artifactrequiremendconfirmed": "artifact_requirement_confirmed",
    "artifactsubmitted": "artifact_submitted",
    "artifact_submitted": "artifact_submitted",
}


def _normalize_workflow_status(raw_status: str | None) -> str | None:
    if not raw_status:
        return None
    compact = "".join(ch for ch in raw_status.strip().lower() if ch.isalnum() or ch == "_")
    compact = compact.replace("-", "")
    return WORKFLOW_STATUS_ALIAS.get(compact)


def _build_workflow_status(project_id: str, record: dict | None) -> AVDMWorkflowStatusResponse:
    if not record:
        return AVDMWorkflowStatusResponse(
            projectId=project_id,
            currentStatus="request_created",
            availableStatuses=WORKFLOW_STATUSES,
            architectureLifecycleStage="Preparation",
            architectureLifecycleStages=ARCHITECTURE_LIFECYCLE_STAGES,
            questionnaireCompleted=False,
            concernIdentificationCompleted=False,
            artifactSelectionCompleted=False,
            diagramUploadAllowed=False,
            stage="request_created",
        )

    questionnaire = record.get("questionnaire") or {}
    evaluation = record.get("evaluation") or {}
    artifact_selection = record.get("artifactSelection") or []

    questionnaire_submitted = bool(questionnaire) or bool(record.get("questionnaireSubmittedAt"))
    questionnaire_confirmed = bool(record.get("questionnaireConfirmedAt"))
    concern_confirmed = bool(record.get("concernRequirementConfirmedAt"))
    artifact_requirement_confirmed = bool(record.get("artifactRequirementConfirmedAt"))
    artifact_submitted = bool(artifact_selection) or bool(record.get("artifactSubmittedAt"))

    if artifact_submitted:
        current_status = "artifact_submitted"
    elif artifact_requirement_confirmed:
        current_status = "artifact_requirement_confirmed"
    elif concern_confirmed:
        current_status = "concern_requirement_confirmed"
    elif questionnaire_confirmed:
        current_status = "questionnaire_confirmed"
    elif questionnaire_submitted:
        current_status = "questionnaire_submitted"
    else:
        current_status = "request_created"

    mapped_status = _normalize_workflow_status(record.get("status"))
    if mapped_status:
        status_rank = {status: idx for idx, status in enumerate(WORKFLOW_STATUSES)}
        current_idx = status_rank.get(current_status, 0)
        mapped_idx = status_rank.get(mapped_status, 0)
        if mapped_idx > current_idx:
            current_status = mapped_status

    return AVDMWorkflowStatusResponse(
        projectId=project_id,
        currentStatus=current_status,
        availableStatuses=WORKFLOW_STATUSES,
        architectureLifecycleStage="Preparation",
        architectureLifecycleStages=ARCHITECTURE_LIFECYCLE_STAGES,
        questionnaireCompleted=questionnaire_submitted,
        concernIdentificationCompleted=bool(evaluation),
        artifactSelectionCompleted=bool(artifact_selection),
        diagramUploadAllowed=artifact_submitted,
        stage=current_status,
    )


@router.get("/concerns", response_model=PactConcernCatalogResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_pact_concerns(
    layer: str | None = Query(None),
    includeInactive: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    concern_repo = PostgresConcernRepository(db)
    concern_service = ConcernService(concern_repo)
    entities, total = await concern_service.list_concerns(page=page, page_size=page_size)

    if entities:
        mapped = [
            PactConcern(
                id=str(entity.id),
                concernKey=entity.code,
                concernName=entity.name,
                layer=entity.category,
                riskTags=[],
                description=entity.description,
                isActive=True,
                updatedBy="system",
            )
            for entity in entities
        ]
        if layer:
            mapped = [item for item in mapped if item.layer.lower() == layer.strip().lower()]
        return PactConcernCatalogResponse(layers=PACT_LAYERS, items=mapped)

    if not layer and not includeInactive:
        return PactConcernCatalogResponse(
            layers=PACT_LAYERS,
            items=[
                PactConcern(
                    id=str(item["key"]),
                    concernKey=str(item["key"]),
                    concernName=str(item["name"]),
                    layer=str(item["layer"]),
                    riskTags=[str(tag) for tag in item.get("risk_tags", [])],
                    description=str(item.get("description", "")),
                    isActive=True,
                    updatedBy="system",
                )
                for item in CONCERN_CATALOG
            ],
        )
    return PactConcernCatalogResponse(layers=PACT_LAYERS, items=[])


@router.get("/concerns/export", response_model=PactConcernCatalogExportResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def export_pact_concerns(
    includeInactive: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    items = await list_concerns(db, include_inactive=includeInactive)
    concerns = [PactConcern(**item) for item in items]
    return PactConcernCatalogExportResponse(
        exportedAt=datetime.now(timezone.utc),
        includeInactive=includeInactive,
        total=len(concerns),
        layers=PACT_LAYERS,
        items=concerns,
    )


@router.put(
    "/concerns",
    response_model=PactConcern,
    dependencies=[Depends(require_role(Role.EA_ADMIN))],
)
async def put_pact_concern(payload: PactConcernUpsertRequest, db: AsyncSession = Depends(get_db)):
    concern = await upsert_concern(
        db,
        concern_key=payload.concernKey.strip(),
        concern_name=payload.concernName.strip(),
        layer=payload.layer.strip(),
        risk_tags=[item.strip() for item in payload.riskTags if item.strip()],
        description=payload.description.strip(),
        is_active=payload.isActive,
        operator=payload.operator.strip() or "system",
    )
    return PactConcern(**concern)


def _to_catalog(items: list[dict]) -> list[dict[str, object]]:
    return [
        {
            "key": item["concernKey"],
            "name": item["concernName"],
            "layer": item["layer"],
            "risk_tags": item.get("riskTags", []),
            "description": item.get("description", ""),
        }
        for item in items
    ]


@router.post("/evaluate", response_model=AVDMEvaluateResponse, dependencies=[Depends(require_permission("avdm", "write"))])
async def evaluate(payload: AVDMEvaluateRequest, db: AsyncSession = Depends(get_db)):
    concerns = await list_concerns(db, include_inactive=False)
    catalog = _to_catalog(concerns) if concerns else CONCERN_CATALOG
    return evaluate_avdm(payload, concern_catalog=catalog)


@router.post("/review", response_model=AVDMReviewResponse, dependencies=[Depends(require_permission("avdm", "write"))])
async def review(payload: AVDMReviewRequest):
    return apply_review_overrides(payload)


@router.get("/projects/{project_id}", response_model=ProjectAssessmentRecord, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_project_assessment(project_id: str, db: AsyncSession = Depends(get_db)):
    record = await get_assessment_by_project(db, project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project questionnaire not found")
    return ProjectAssessmentRecord(**record)


@router.post("/projects/{project_id}/questionnaire", response_model=ProjectAssessmentUpsertResponse, dependencies=[Depends(require_permission("avdm", "write"))])
async def upsert_project_questionnaire(
    project_id: str,
    payload: ProjectQuestionnaireUpsertRequest,
    db: AsyncSession = Depends(get_db),
):
    concerns = await list_concerns(db, include_inactive=False)
    catalog = _to_catalog(concerns) if concerns else CONCERN_CATALOG

    risk_items = [
        RiskItem(
            code=item.riskCode,
            severity=item.severity,
            likelihood=item.likelihood,
            note=item.note,
        )
        for item in payload.answers
    ]

    evaluation = evaluate_avdm(
        AVDMEvaluateRequest(
            projectId=project_id,
            projectType=payload.projectType,
            projectComplexity=payload.projectComplexity,
            riskItems=risk_items,
        ),
        concern_catalog=catalog,
    )
    judgement = judge_avdm_need(evaluation)

    assessment = await upsert_project_assessment(
        db,
        project_id=project_id,
        project_type=payload.projectType,
        project_complexity=payload.projectComplexity,
        questionnaire=payload.questionnaire,
        risk_items=[item.model_dump() for item in payload.answers],
        evaluation=evaluation.model_dump(),
        review_result=None,
        artifact_selection=None,
        needs_avdm=judgement.needsAVDM,
        judgement_reason=judgement.rationale,
        status=payload.status,
        operator=payload.operator,
    )

    return ProjectAssessmentUpsertResponse(
        assessment=ProjectAssessmentRecord(**assessment),
        judgement=judgement,
    )


@router.post("/projects/{project_id}/judge", response_model=AVDMNeedJudgement, dependencies=[Depends(require_permission("avdm", "write"))])
async def judge_project_need(project_id: str, db: AsyncSession = Depends(get_db)):
    record = await get_assessment_by_project(db, project_id)
    if not record or not record.get("evaluation"):
        raise HTTPException(status_code=404, detail="Project evaluation not found")

    evaluation_payload = record["evaluation"]
    evaluation = AVDMEvaluateResponse(**evaluation_payload)
    judgement = judge_avdm_need(evaluation)

    await upsert_project_assessment(
        db,
        project_id=project_id,
        project_type=record.get("projectType"),
        project_complexity=float(record.get("projectComplexity") or 0.5),
        questionnaire=record.get("questionnaire") or {},
        risk_items=record.get("riskItems") or [],
        evaluation=evaluation_payload,
        review_result=record.get("reviewResult"),
        artifact_selection=record.get("artifactSelection"),
        needs_avdm=judgement.needsAVDM,
        judgement_reason=judgement.rationale,
        status=record.get("status") or "draft",
        operator="system",
    )

    return judgement


@router.get("/statistics", response_model=AVDMStatisticsResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_avdm_statistics(
    status: str | None = Query(None, description="Optional status filter, e.g. draft/submitted"),
    db: AsyncSession = Depends(get_db),
):
    records = await list_assessment_records_for_stats(db, status=status)
    return build_statistics(records)


@router.get("/projects/{project_id}/artifacts/recommendation", response_model=ArtifactRecommendationResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_artifact_recommendation(project_id: str, db: AsyncSession = Depends(get_db)):
    record = await get_assessment_by_project(db, project_id)
    if not record or not record.get("evaluation"):
        raise HTTPException(status_code=404, detail="Project evaluation not found")
    evaluation = AVDMEvaluateResponse(**record["evaluation"])
    artifact_catalog_config = await load_artifact_catalog_config(db)
    questionnaire_config = await load_questionnaire_config(db)
    baseline = recommend_artifacts_from_config(
        project_id,
        evaluation,
        project_type=record.get("projectType"),
        artifact_catalog_config=artifact_catalog_config,
        viewpoint_mapping_config={"viewpoints": []},
        questionnaire_config=questionnaire_config,
    )
    concern_items = await list_viewpoint_artifact_recommendation_items(
        db,
        decisions=[item.model_dump() for item in evaluation.decisions],
    )
    return ArtifactRecommendationResponse(projectId=project_id, items=baseline.items + concern_items)


@router.put("/projects/{project_id}/artifacts", response_model=ProjectAssessmentRecord, dependencies=[Depends(require_permission("avdm", "write"))])
async def upsert_artifact_selection(
    project_id: str,
    payload: ArtifactSelectionUpsertRequest,
    db: AsyncSession = Depends(get_db),
):
    record = await get_assessment_by_project(db, project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project questionnaire not found")
    if not record.get("evaluation"):
        raise HTTPException(status_code=400, detail="Questionnaire must be completed before selecting artifacts")

    updated = await upsert_project_assessment(
        db,
        project_id=project_id,
        project_type=record.get("projectType"),
        project_complexity=float(record.get("projectComplexity") or 0.5),
        questionnaire=record.get("questionnaire") or {},
        risk_items=record.get("riskItems") or [],
        evaluation=record.get("evaluation"),
        review_result=record.get("reviewResult"),
        artifact_selection=[item.model_dump() for item in payload.selections],
        needs_avdm=record.get("needsAVDM"),
        judgement_reason=record.get("judgementReason"),
        status="artifact_submitted",
        operator=payload.operator,
    )
    return ProjectAssessmentRecord(**updated)


@router.get("/projects/{project_id}/workflow-status", response_model=AVDMWorkflowStatusResponse, dependencies=[Depends(require_permission("avdm", "read"))])
async def get_workflow_status(project_id: str, db: AsyncSession = Depends(get_db)):
    record = await get_assessment_by_project(db, project_id)
    return _build_workflow_status(project_id, record)


@router.post("/projects/{project_id}/questionnaire/confirm", response_model=AVDMWorkflowStatusResponse, dependencies=[Depends(require_permission("avdm", "write"))])
async def confirm_questionnaire(
    project_id: str,
    payload: WorkflowStageConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    record = await get_assessment_by_project(db, project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project questionnaire not found")
    if not (record.get("questionnaire") or {}):
        raise HTTPException(status_code=400, detail="Questionnaire must be submitted before confirmation")

    await db.execute(
        text(
            "UPDATE eam.avdm_project_assessment "
            "SET questionnaire_confirmed_at = NOW(), update_at = NOW(), update_by = :operator "
            "WHERE project_id = :project_id"
        ),
        {"project_id": project_id, "operator": payload.operator},
    )
    await db.commit()
    updated = await get_assessment_by_project(db, project_id)
    return _build_workflow_status(project_id, updated)


@router.post("/projects/{project_id}/concerns/confirm", response_model=AVDMWorkflowStatusResponse, dependencies=[Depends(require_permission("avdm", "write"))])
async def confirm_concern_requirement(
    project_id: str,
    payload: WorkflowStageConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    record = await get_assessment_by_project(db, project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project questionnaire not found")
    if not record.get("evaluation"):
        raise HTTPException(status_code=400, detail="Concern identification must be completed before confirmation")

    await db.execute(
        text(
            "UPDATE eam.avdm_project_assessment "
            "SET concern_requirement_confirmed_at = NOW(), update_at = NOW(), update_by = :operator "
            "WHERE project_id = :project_id"
        ),
        {"project_id": project_id, "operator": payload.operator},
    )
    await db.commit()
    updated = await get_assessment_by_project(db, project_id)
    return _build_workflow_status(project_id, updated)


@router.post("/projects/{project_id}/artifacts/requirements/confirm", response_model=AVDMWorkflowStatusResponse, dependencies=[Depends(require_permission("avdm", "write"))])
async def confirm_artifact_requirement(
    project_id: str,
    payload: WorkflowStageConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    record = await get_assessment_by_project(db, project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project questionnaire not found")
    if not record.get("evaluation"):
        raise HTTPException(status_code=400, detail="Concern identification must be completed before artifact requirement confirmation")

    await db.execute(
        text(
            "UPDATE eam.avdm_project_assessment "
            "SET artifact_requirement_confirmed_at = NOW(), artifact_confirmed_at = NOW(), update_at = NOW(), update_by = :operator "
            "WHERE project_id = :project_id"
        ),
        {"project_id": project_id, "operator": payload.operator},
    )
    await db.commit()
    updated = await get_assessment_by_project(db, project_id)
    return _build_workflow_status(project_id, updated)
