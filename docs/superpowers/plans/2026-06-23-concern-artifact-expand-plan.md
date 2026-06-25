# Concern & Artifact Expandable View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace flat Concern list with two expandable sections showing contribution breakdowns (Questionnaire items → Concern, Concern → Artifact) via two new request-scoped endpoints.

**Architecture:** Two new backend endpoints (`/ea-requests/{id}/concerns`, `/ea-requests/{id}/artifacts`) compute contribution mappings from existing AVDM assessment data. Frontend replaces `AVDMConcernListSection` with two new expandable-table sections.

**Tech Stack:** FastAPI, SQLAlchemy async, Ant Design expandable Table

---

### Task 1: Extract concern contributions from evaluation logic

**Files:**
- Modify: `backend/app/add/service.py`

Add a new function `build_concern_contributions()` that computes which questionnaire items contributed to each concern's score, and return this data alongside the existing `decisions`.

- [ ] **Step 1: Add `build_concern_contributions` function to service.py**

After the `_classify` function (line 145), add:

```python
def build_concern_contributions(
    risk_items: list,
    concern_catalog: list[dict[str, object]] | None = None,
) -> dict[str, dict]:
    """For each concern, list which risk items contributed (direct/tag/rule)."""
    risk_map = _risk_score_by_code(risk_items)
    catalog = concern_catalog or CONCERN_CATALOG

    # Build lookup: risk_code -> risk_item details
    risk_item_map: dict[str, dict] = {}
    for item in risk_items:
        code = item.code.strip().lower()
        if not code:
            continue
        if code not in risk_item_map:
            risk_item_map[code] = {
                "riskCode": item.code.strip(),
                "severity": float(item.severity),
                "likelihood": float(item.likelihood),
                "itemScore": round((float(item.severity) / 5.0) * (float(item.likelihood) / 5.0), 4),
                "question": getattr(item, "question", ""),
                "note": getattr(item, "note", ""),
            }

    result: dict[str, dict] = {}
    for concern in catalog:
        ck = str(concern["key"]).lower()
        tags = [str(t).lower() for t in concern.get("risk_tags", [])]

        direct: list[dict] = []
        tagged: list[dict] = []
        rules: list[dict] = []

        # Direct match
        if ck in risk_item_map:
            direct.append({**risk_item_map[ck], "matchType": "direct"})

        # Tag matches
        for tag in tags:
            if tag in risk_item_map and tag != ck:
                tagged.append({**risk_item_map[tag], "matchType": "tagged"})

        result[str(concern["key"])] = {
            "direct": direct,
            "tagged": tagged,
            "rules": rules,
        }

    return result
```

- [ ] **Step 2: Modify `evaluate_avdm` to return contributions**

Change the return at line 211-215 to include contributions:

```python
    contributions = build_concern_contributions(payload.riskItems, catalog)

    return AVDMEvaluateResponse(
        projectId=payload.projectId,
        decisions=decisions,
        layerSummary=layer_summary,
        contributions=contributions,
    )
```

- [ ] **Step 3: Add `contributions` field to `AVDMEvaluateResponse` model**

**File:** `backend/app/add/models.py`

Add the field to the class (around line 58):

```python
class AVDMEvaluateResponse(BaseModel):
    projectId: str
    decisions: list[ConcernDecision]
    layerSummary: list[LayerSummary]
    contributions: dict | None = None   # <-- add this
```

- [ ] **Step 4: Update route to return contributions in assessment response**

**File:** `backend/app/add/routes.py`

Find the GET endpoint that returns `ProjectAssessmentRecord` (around line 438). Ensure `evaluation` field includes `contributions` when serializing. The `evaluation` dict comes from `AVDMEvaluateResponse.model_dump()`, so the field should serialize automatically.

- [ ] **Step 5: Commit**

```bash
git add backend/app/add/service.py backend/app/add/models.py
git commit -m "feat(avdm): extract concern contributions with direct/tag/rule mapping from risk items"
```

---

### Task 2: Create GET /ea-requests/{id}/concerns endpoint

**Files:**
- Create: `backend/app/architecture_review/concerns.py`

- [ ] **Step 1: Create concerns.py**

```python
"""EA Request Concerns — per-request concern list with contribution breakdown."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

router = APIRouter()


@router.get("/{request_id}/concerns", dependencies=[Depends(require_permission("ea_request", "read"))])
async def get_request_concerns(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    req_result = await db.execute(
        text("SELECT request_id, project_id FROM eam.eam_request WHERE request_id = :rid OR id::text = :rid LIMIT 1"),
        {"rid": request_id},
    )
    req_row = req_result.mappings().first()
    if not req_row:
        raise HTTPException(status_code=404, detail="EA request not found")

    project_id = req_row["project_id"]
    if not project_id:
        raise HTTPException(status_code=404, detail="No project associated with this request")

    assessment_result = await db.execute(
        text(
            "SELECT project_id, evaluation, concern_requirement_confirmed_at, "
            "artifact_requirement_confirmed_at, artifact_submitted_at, "
            "questionnaire, risk_items, status "
            "FROM eam.avdm_project_assessment WHERE project_id = :pid"
        ),
        {"pid": project_id},
    )
    assessment = assessment_result.mappings().first()

    if not assessment or not assessment.get("evaluation"):
        return {
            "requestId": req_row["request_id"],
            "projectId": project_id,
            "workflowStatus": "request_created",
            "concerns": [],
        }

    evaluation = assessment["evaluation"]
    if isinstance(evaluation, str):
        import json
        evaluation = json.loads(evaluation)

    decisions = evaluation.get("decisions", [])
    contributions = evaluation.get("contributions") or {}

    def _status_from_timestamps(row) -> str:
        if row.get("artifact_submitted_at"):
            return "artifact_submitted"
        if row.get("artifact_requirement_confirmed_at"):
            return "artifact_requirement_confirmed"
        if row.get("concern_requirement_confirmed_at"):
            return "concern_requirement_confirmed"
        return _infer_from_questionnaire(row)

    def _infer_from_questionnaire(row) -> str:
        q = row.get("questionnaire") or {}
        if isinstance(q, str):
            import json
            q = json.loads(q)
        if q and isinstance(q, dict) and q.get("checkpoint1"):
            return "questionnaire_confirmed"
        return "questionnaire_submitted"

    workflow_status = _status_from_timestamps(assessment)

    concerns = []
    for d in decisions:
        ck = d.get("concernKey", "")
        concerns.append({
            "concernKey": ck,
            "concernName": d.get("concernName", ""),
            "layer": d.get("layer", ""),
            "classification": d.get("classification", "Optional"),
            "totalScore": d.get("score", 0),
            "rationale": d.get("rationale", ""),
            "contributions": contributions.get(ck, {"direct": [], "tagged": [], "rules": []}),
        })

    concerns.sort(key=lambda c: (
        {"Mandatory": 0, "Recommended": 1, "Optional": 2}.get(c["classification"], 3),
        -c["totalScore"],
        c["concernKey"],
    ))

    return {
        "requestId": req_row["request_id"],
        "projectId": project_id,
        "workflowStatus": workflow_status,
        "concerns": concerns,
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/architecture_review/concerns.py
git commit -m "feat(ea-review): add GET /ea-requests/{id}/concerns endpoint with contribution breakdown"
```

---

### Task 3: Create GET /ea-requests/{id}/artifacts endpoint

**Files:**
- Create: `backend/app/architecture_review/artifacts.py`

- [ ] **Step 1: Create artifacts.py**

```python
"""EA Request Artifacts — per-request artifact list with concern contributions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth import require_permission, get_current_user
from app.auth.models import AuthUser

router = APIRouter()


@router.get("/{request_id}/artifacts", dependencies=[Depends(require_permission("ea_request", "read"))])
async def get_request_artifacts(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    req_result = await db.execute(
        text("SELECT request_id, project_id FROM eam.eam_request WHERE request_id = :rid OR id::text = :rid LIMIT 1"),
        {"rid": request_id},
    )
    req_row = req_result.mappings().first()
    if not req_row:
        raise HTTPException(status_code=404, detail="EA request not found")

    project_id = req_row["project_id"]
    if not project_id:
        raise HTTPException(status_code=404, detail="No project associated with this request")

    assessment_result = await db.execute(
        text(
            "SELECT project_id, evaluation, artifact_selection, concern_requirement_confirmed_at, "
            "artifact_requirement_confirmed_at, artifact_submitted_at, status "
            "FROM eam.avdm_project_assessment WHERE project_id = :pid"
        ),
        {"pid": project_id},
    )
    assessment = assessment_result.mappings().first()

    if not assessment or not assessment.get("evaluation"):
        return {
            "requestId": req_row["request_id"],
            "projectId": project_id,
            "artifacts": [],
        }

    evaluation = assessment["evaluation"]
    if isinstance(evaluation, str):
        import json
        evaluation = json.loads(evaluation)

    decisions = {d.get("concernKey", ""): d for d in evaluation.get("decisions", [])}
    contributions = evaluation.get("contributions") or {}
    artifact_selections = assessment.get("artifact_selection") or []
    if isinstance(artifact_selections, str):
        import json
        artifact_selections = json.loads(artifact_selections) or []

    selected_keys = set()
    for sel in artifact_selections:
        if isinstance(sel, dict):
            selected_keys.add((sel.get("concernKey", ""), sel.get("artifactName", "")))

    artifacts = []
    for d in evaluation.get("decisions", []):
        ck = d.get("concernKey", "")
        cn = d.get("concernName", "")
        cl = d.get("classification", "Optional")
        score = d.get("score", 0)
        concern_contrib = contributions.get(ck, {"direct": [], "tagged": [], "rules": []})

        artifact_names = _get_artifacts_for_concern(ck)
        for aname in artifact_names:
            sel_status = "selected" if (ck, aname) in selected_keys else "recommended"
            artifacts.append({
                "artifactId": f"{ck}_{aname}",
                "artifactName": aname,
                "associatedConcernKey": ck,
                "associatedConcernName": cn,
                "classification": cl,
                "totalScore": score,
                "status": sel_status,
                "contributions": concern_contrib,
            })

    return {
        "requestId": req_row["request_id"],
        "projectId": project_id,
        "artifacts": artifacts,
    }


def _get_artifacts_for_concern(concern_key: str) -> list[str]:
    from app.add.service import CONCERN_CATALOG
    for concern in CONCERN_CATALOG:
        if str(concern.get("key")) == concern_key:
            artifacts = concern.get("deliverables") or concern.get("artifacts") or []
            return [str(a) for a in artifacts]
    return []
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/architecture_review/artifacts.py
git commit -m "feat(ea-review): add GET /ea-requests/{id}/artifacts endpoint with concern association"
```

---

### Task 4: Register new routes + fix AVDMEvaluateResponse model

**Files:**
- Modify: `backend/app/architecture_review/stages/preparation.py`
- Modify: `backend/app/add/models.py` (if needed)
- Modify: `backend/app/add/routes.py` (if needed)

- [ ] **Step 1: Register new routes in preparation.py**

```python
"""Architecture Preparation stage routes."""

from fastapi import APIRouter

from .. import attachments as ea_attachments
from .. import concerns as ea_concerns
from .. import artifacts as ea_artifacts
from .. import ea_requests

router = APIRouter()

router.include_router(ea_requests.router, prefix="/ea-requests", tags=["EA Requests"])
router.include_router(ea_concerns.router, prefix="/ea-requests", tags=["EA Concerns"])
router.include_router(ea_artifacts.router, prefix="/ea-requests", tags=["EA Artifacts"])
router.include_router(ea_attachments.router, prefix="/ea-requests/attachments", tags=["EA Attachments"])
```

- [ ] **Step 2: Verify AVDMEvaluateResponse model has contributions field**

Read `backend/app/add/models.py` to confirm the field exists. If the model already has it from Task 1, skip.

- [ ] **Step 3: Commit**

```bash
git add backend/app/architecture_review/stages/preparation.py
git commit -m "feat(ea-review): register concerns and artifacts routes in preparation stage"
```

---

### Task 5: Create AVDMConcernExpandSection frontend component

**Files:**
- Create: `frontend/src/features/review/components/ea-review/request-detail/AVDMConcernExpandSection.tsx`

- [ ] **Step 1: Create component**

```tsx
'use client';

import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { RequestDetailSection } from './RequestDetailSection';

type ContributionItem = {
  riskCode: string;
  severity: number;
  likelihood: number;
  itemScore: number;
  question: string;
  note: string;
  matchType: string;
};

type ConcernItem = {
  concernKey: string;
  concernName: string;
  layer: string;
  classification: string;
  totalScore: number;
  rationale: string;
  contributions: {
    direct: ContributionItem[];
    tagged: ContributionItem[];
    rules: ContributionItem[];
  };
};

const classificationColor: Record<string, string> = {
  Mandatory: 'red',
  Recommended: 'gold',
  Optional: 'default',
};

function flattenContributions(contributions: ConcernItem['contributions']): ContributionItem[] {
  return [
    ...(contributions.direct || []),
    ...(contributions.tagged || []),
    ...(contributions.rules || []),
  ];
}

export function AVDMConcernExpandSection({
  concerns,
  loading,
}: {
  concerns: ConcernItem[];
  loading: boolean;
}) {
  const outerColumns: ColumnsType<ConcernItem> = [
    { title: 'Concern', dataIndex: 'concernKey', key: 'concernKey', width: 100, render: (v: string) => <strong>{v}</strong> },
    { title: 'Viewpoint Name', dataIndex: 'concernName', key: 'concernName', width: 240 },
    { title: 'Layer', dataIndex: 'layer', key: 'layer', width: 180 },
    {
      title: 'Classification', dataIndex: 'classification', key: 'classification', width: 130,
      render: (v: string) => <Tag color={classificationColor[v] || 'default'}>{v}</Tag>,
    },
    {
      title: 'Total Score', dataIndex: 'totalScore', key: 'totalScore', width: 100,
      render: (v: number) => v.toFixed(3),
    },
  ];

  const innerColumns: ColumnsType<ContributionItem> = [
    { title: 'Risk Code', dataIndex: 'riskCode', key: 'riskCode', width: 100 },
    { title: 'Severity', dataIndex: 'severity', key: 'severity', width: 80 },
    { title: 'Likelihood', dataIndex: 'likelihood', key: 'likelihood', width: 90 },
    {
      title: 'Item Score', dataIndex: 'itemScore', key: 'itemScore', width: 90,
      render: (v: number) => v.toFixed(4),
    },
    { title: 'Question', dataIndex: 'question', key: 'question', ellipsis: true },
    { title: 'Note', dataIndex: 'note', key: 'note', ellipsis: true },
    {
      title: 'Type', dataIndex: 'matchType', key: 'matchType', width: 80,
      render: (v: string) => <Tag>{v}</Tag>,
    },
  ];

  const summary = {
    mandatory: concerns.filter(c => c.classification === 'Mandatory').length,
    recommended: concerns.filter(c => c.classification === 'Recommended').length,
    optional: concerns.filter(c => c.classification === 'Optional').length,
  };

  return (
    <RequestDetailSection title="Architecture Concerns" defaultOpen>
      <div className="mb-3 flex gap-3 text-xs">
        <Tag color="red">Mandatory: {summary.mandatory}</Tag>
        <Tag color="gold">Recommended: {summary.recommended}</Tag>
        <Tag>Optional: {summary.optional}</Tag>
      </div>
      <Table
        columns={outerColumns}
        dataSource={concerns}
        rowKey="concernKey"
        loading={loading}
        expandable={{
          expandedRowRender: (record) => {
            const items = flattenContributions(record.contributions);
            if (items.length === 0) return <div className="text-xs text-text-secondary px-4 py-2">No questionnaire item contributions</div>;
            return (
              <Table
                columns={innerColumns}
                dataSource={items}
                rowKey={(r, i) => `${record.concernKey}-${r.riskCode}-${i}`}
                pagination={false}
                size="small"
              />
            );
          },
          rowExpandable: (record) => flattenContributions(record.contributions).length > 0,
        }}
        pagination={false}
        size="small"
      />
    </RequestDetailSection>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/review/components/ea-review/request-detail/AVDMConcernExpandSection.tsx
git commit -m "feat(frontend): add expandable concern section with questionnaire item breakdown"
```

---

### Task 6: Create AVDMArtifactExpandSection frontend component

**Files:**
- Create: `frontend/src/features/review/components/ea-review/request-detail/AVDMArtifactExpandSection.tsx`

- [ ] **Step 1: Create component**

```tsx
'use client';

import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { RequestDetailSection } from './RequestDetailSection';

type ConcernContribution = {
  direct: Array<{ riskCode: string; itemScore: number }>;
  tagged: Array<{ riskCode: string; itemScore: number }>;
  rules: Array<{ riskCode: string; score: number }>;
};

type ArtifactItem = {
  artifactId: string;
  artifactName: string;
  associatedConcernKey: string;
  associatedConcernName: string;
  classification: string;
  totalScore: number;
  status: string;
  contributions: ConcernContribution;
};

type ScoreBreakdown = {
  concernKey: string;
  directScore: number;
  taggedScore: number;
  ruleScore: number;
  finalScore: number;
};

const classificationColor: Record<string, string> = {
  Mandatory: 'red',
  Recommended: 'gold',
  Optional: 'default',
};

export function AVDMArtifactExpandSection({
  artifacts,
  loading,
}: {
  artifacts: ArtifactItem[];
  loading: boolean;
}) {
  const outerColumns: ColumnsType<ArtifactItem> = [
    { title: 'Artifact', dataIndex: 'artifactName', key: 'artifactName', width: 280, render: (v: string) => <strong>{v}</strong> },
    {
      title: 'Concern', dataIndex: 'associatedConcernName', key: 'associatedConcernName', width: 240,
      render: (v: string, r: ArtifactItem) => <span>{r.associatedConcernKey}: {v}</span>,
    },
    {
      title: 'Classification', dataIndex: 'classification', key: 'classification', width: 130,
      render: (v: string) => <Tag color={classificationColor[v] || 'default'}>{v}</Tag>,
    },
    {
      title: 'Total Score', dataIndex: 'totalScore', key: 'totalScore', width: 100,
      render: (v: number) => v.toFixed(3),
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={v === 'selected' ? 'blue' : 'default'}>{v}</Tag>,
    },
  ];

  const innerColumns: ColumnsType<ScoreBreakdown> = [
    { title: 'Concern', dataIndex: 'concernKey', key: 'concernKey', width: 100 },
    { title: 'Direct Score', dataIndex: 'directScore', key: 'directScore', width: 100, render: (v: number) => v.toFixed(4) },
    { title: 'Tag Score', dataIndex: 'taggedScore', key: 'taggedScore', width: 100, render: (v: number) => v.toFixed(4) },
    { title: 'Rule Score', dataIndex: 'ruleScore', key: 'ruleScore', width: 100, render: (v: number) => v.toFixed(4) },
    { title: 'Final Score', dataIndex: 'finalScore', key: 'finalScore', width: 100, render: (v: number) => v.toFixed(3) },
  ];

  function buildBreakdown(record: ArtifactItem): ScoreBreakdown[] {
    const contrib = record.contributions;
    const directScore = (contrib.direct || []).reduce((s, i) => s + (i.itemScore || 0), 0);
    const taggedScore = (contrib.tagged || []).reduce((s, i) => s + (i.itemScore || 0), 0);
    const ruleScore = (contrib.rules || []).reduce((s, i) => s + (i.score || 0), 0);

    return [{
      concernKey: record.associatedConcernKey,
      directScore,
      taggedScore,
      ruleScore,
      finalScore: record.totalScore,
    }];
  }

  return (
    <RequestDetailSection title="Architecture Artifacts" defaultOpen>
      <Table
        columns={outerColumns}
        dataSource={artifacts}
        rowKey="artifactId"
        loading={loading}
        expandable={{
          expandedRowRender: (record) => (
            <Table
              columns={innerColumns}
              dataSource={buildBreakdown(record)}
              rowKey="concernKey"
              pagination={false}
              size="small"
            />
          ),
        }}
        pagination={false}
        size="small"
      />
    </RequestDetailSection>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/review/components/ea-review/request-detail/AVDMArtifactExpandSection.tsx
git commit -m "feat(frontend): add expandable artifact section with concern score breakdown"
```

---

### Task 7: Update RequestDetailView to use new sections + wire endpoints

**Files:**
- Modify: `frontend/src/features/review/components/ea-review/RequestDetailView.tsx`

- [ ] **Step 1: Add imports**

```typescript
import { AVDMConcernExpandSection } from '@/features/review/components/ea-review/request-detail/AVDMConcernExpandSection';
import { AVDMArtifactExpandSection } from '@/features/review/components/ea-review/request-detail/AVDMArtifactExpandSection';
```

- [ ] **Step 2: Add two new useQuery hooks for concerns and artifacts data**

After the existing `useQuery` blocks (around line 121), add:

```typescript
  const { data: concernsData, isLoading: concernsLoading } = useQuery({
    queryKey: ['eaRequestConcerns', id],
    queryFn: () => api.get<any>(`/ea-requests/${id}/concerns`),
    enabled: !!id,
  });

  const { data: artifactsData, isLoading: artifactsLoading } = useQuery({
    queryKey: ['eaRequestArtifacts', id],
    queryFn: () => api.get<any>(`/ea-requests/${id}/artifacts`),
    enabled: !!id,
  });
```

- [ ] **Step 3: Replace AVDMLifecycleStageSection + AVDMConcernListSection with new sections**

Replace lines 266-295 (the `AVDMLifecycleStageSection` and `AVDMConcernListSection` and `canGoToQuestionnaireSubmit` block) with:

```tsx
      <AVDMLifecycleStageSection
        workflowStatus={workflowStatus ? {
          ...workflowStatus,
          concernRequirementConfirmedAt: avdmAssessment?.concernRequirementConfirmedAt ?? null,
        } : undefined}
        loading={workflowStatusLoading}
        canConfirmConcerns={canConfirmConcerns}
        confirmingConcerns={confirmConcernsMutation.isPending}
        onConfirmConcerns={() => confirmConcernsMutation.mutate()}
        canConfirmArtifactRequirements={canConfirmArtifactRequirements}
        confirmingArtifactRequirements={confirmArtifactRequirementsMutation.isPending}
        onConfirmArtifactRequirements={() => confirmArtifactRequirementsMutation.mutate()}
        canSubmitArtifacts={canSubmitArtifacts}
        submittingArtifacts={submitArtifactsMutation.isPending}
        onSubmitArtifacts={() => submitArtifactsMutation.mutate()}
        canConfirmQuestionnaire={canConfirmQuestionnaire}
        confirmingQuestionnaire={confirmQuestionnaireMutation.isPending}
        onConfirmQuestionnaire={() => confirmQuestionnaireMutation.mutate()}
      />

      {canGoToQuestionnaireSubmit && (
        <div className="mt-3 mb-4 flex items-center justify-between rounded-md border border-blue-200 bg-blue-50 px-3 py-2">
          <div className="text-xs text-text-secondary">
            Questionnaire is not submitted yet. Project team should complete Step 2 before review team confirmation.
          </div>
          <Button type="primary" size="small" onClick={() => router.push(`/ea-review/request/create?id=${id}`)}>
            Go to Questionnaire Submit
          </Button>
        </div>
      )}

      <AVDMConcernExpandSection
        concerns={concernsData?.concerns ?? []}
        loading={concernsLoading}
      />

      <AVDMArtifactExpandSection
        artifacts={artifactsData?.artifacts ?? []}
        loading={artifactsLoading}
      />
```

- [ ] **Step 4: Remove the old AVDMConcernListSection import** (line 17) — keep it but the component is no longer used in this file. Remove or keep (no harm).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/review/components/ea-review/RequestDetailView.tsx
git commit -m "feat(frontend): integrate concern and artifact expandable sections into request detail view"
```
