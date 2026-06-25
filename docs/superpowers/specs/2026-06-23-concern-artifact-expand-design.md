# Request Detail Concern & Artifact Expandable View

Date: 2026-06-23

## 概述

将 `/request/{id}` 页面重新设计为上下两个展开式 Section：
1. **Architecture Concerns** — 每个 Concern 展开显示关联 Questionnaire items 及细分 Score
2. **Architecture Artifacts** — 每个 Artifact 展开显示关联 Concerns 及细分 Score

数据基于 request（非 project），新增两个后端端点供给数据。

## 1. 后端端点

### `GET /api/ea-requests/{request_id}/concerns`

根据 request_id 查 project_id → 读 AVDM assessment → 返回 Concern 列表含贡献明细。

**Response:**

```json
{
  "requestId": "EA260039",
  "projectId": "xxx",
  "workflowStatus": "concern_requirement_confirmed",
  "concerns": [
    {
      "concernKey": "B1",
      "concernName": "Business Capability View",
      "layer": "Business",
      "classification": "Mandatory",
      "totalScore": 0.85,
      "rationale": "...",
      "contributions": {
        "direct": [
          { "riskCode": "B1", "severity": 4, "likelihood": 0.8,
            "itemScore": 0.64, "question": "Does the project involve...", "note": "" }
        ],
        "tagged": [
          { "riskCode": "B2", "severity": 3, "likelihood": 0.6,
            "itemScore": 0.36, "question": "...", "note": "" }
        ],
        "rules": [
          { "ruleName": "DataSensitivity-Combo", "riskCodes": ["D1","D3"],
            "score": 0.5, "description": "Combined D1+D3 triggers D4" }
        ]
      }
    }
  ]
}
```

**Score 计算逻辑**（从 `evaluate_avdm` 提取）：
- `direct`: risk_code 精确匹配 concern key
- `tagged`: risk_code 匹配 concern 的 `risk_tags[]` 中任意标签
- `rules`: concern_mapping_config 联合规则
- `risk_score = max(direct_avg, tagged_avg)`
- `totalScore = min(1.0, risk_score + complexity_boost)`

### `GET /api/ea-requests/{request_id}/artifacts`

根据 request_id 查 project_id → 读 artifact recommendations（`/avdm/projects/{id}/artifacts/recommendation`）+ artifactSelection → 每个 Artifact 关联其 Concern 的贡献明细。

**Response:**

```json
{
  "requestId": "EA260039",
  "projectId": "xxx",
  "artifacts": [
    {
      "artifactId": "arch_business_01",
      "artifactName": "Business Architecture Document",
      "associatedConcernKey": "B1",
      "associatedConcernName": "Business Capability View",
      "classification": "Mandatory",
      "totalScore": 0.85,
      "status": "selected",
      "contributions": {
        "direct": [...],
        "tagged": [...],
        "rules": [...]
      }
    }
  ]
}
```

## 2. 前端页面

### 布局

`/request/{id}` 页面，保留现有 `GeneralDataSection` + `AVDMLifecycleStageSection`，替换 `AVDMConcernListSection` 为两个新 Section：

```
┌─ GeneralDataSection ─────────────────────┐
├─ AVDMLifecycleStageSection ──────────────┤
├─ Architecture Concerns (expandable) ─────┤
│  ┌─ Concern B1 ═══════════════════════┐  │
│  │  Risk Code │ Sev │ Lkl │ Score │ Q │  │
│  │  B1        │ 4   │ 0.8 │ 0.64  │.. │  │
│  │  B2        │ 3   │ 0.6 │ 0.36  │.. │  │
│  └────────────────────────────────────┘  │
├─ Architecture Artifacts (expandable) ────┤
│  ┌─ Artifact Business Arch Doc ═══════┐  │
│  │  Concern │ Direct │ Tag │ Final   │  │
│  │  B1      │ 0.64   │ 0.36│ 0.85    │  │
│  └────────────────────────────────────┘  │
├─ AttachmentsSection ─────────────────────┤
└─ Diagrams ───────────────────────────────┘
```

### Concerns Section

展开式表格，外层列：

| # | Concern | Viewpoint | Layer | Classification | Total Score |
|---|---------|-----------|-------|---------------|-------------|

Classification 用 Tag 颜色：Mandatory=red, Recommended=gold, Optional=default

展开行内表：

| Risk Code | Severity | Likelihood | Item Score | Question Text | Note | Match Type |
|-----------|----------|------------|------------|---------------|------|------------|

Match Type: direct / tagged / rule

### Artifacts Section

展开式表格，外层列：

| # | Artifact | Concern | Classification | Total Score | Status |
|---|----------|---------|---------------|-------------|--------|

展开行内表：

| Concern Key | Direct Score | Tagged Score | Rule Score | Final Score |

## 3. 实现文件

**后端：**
- 新增: `backend/app/architecture_review/concerns.py` — `GET /ea-requests/{id}/concerns`
- 新增: `backend/app/architecture_review/artifacts.py` — `GET /ea-requests/{id}/artifacts`
- 修改: `backend/app/add/service.py` — 提取贡献明细到 response
- 修改: `backend/app/architecture_review/stages/preparation.py` — 注册新路由

**前端：**
- 新增: `frontend/src/features/review/components/ea-review/request-detail/AVDMConcernExpandSection.tsx`
- 新增: `frontend/src/features/review/components/ea-review/request-detail/AVDMArtifactExpandSection.tsx`
- 修改: `frontend/src/features/review/components/ea-review/RequestDetailView.tsx` — 替换 section

## 4. 不予实现
- 前端不修改 `AVDMConcernListSection.tsx`（保留给其他页面使用）
- 不修改 artifact recommendation 端点
- 不修改 concern_mapping_config 规则引擎
