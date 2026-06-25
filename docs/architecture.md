# PAMF Architecture

## System Overview

PAMF is a 3-tier web application for enterprise architecture management and governance:
- **Frontend**: Next.js 16 (React 19, TypeScript) -- UI rendering, routing, state management
- **Backend**: FastAPI (Python 3.12+) -- API server, business logic, AI orchestration
- **Database**: PostgreSQL 14+ -- persistent storage, async access via asyncpg

## Runtime Matrix

| Component | Version |
|-----------|---------|
| Node.js | 22.x |
| npm | 10.x |
| Python | 3.12.x |
| Next.js | 16.x (Turbopack) |
| React | 19.x |
| Ant Design | 6.x |
| FastAPI | 0.115.x |
| PostgreSQL | 16 |

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend Framework | Next.js 16 (Turbopack) | SSR/CSR, App Router, API proxy |
| State Management | TanStack Query v5 + Zustand v5 | Server state + client state |
| Authentication | Pluggable (OSS Local JWT / Keycloak SSO) | Username+password or OIDC |
| Backend Framework | FastAPI | Async REST API |
| Database Driver | SQLAlchemy (async) + asyncpg | Connection pooling, raw SQL execution |
| AI Pipeline | LangChain + LangGraph | Architecture diagram review workflows |
| File Storage | S3-compatible (boto3) or Database | Attachment uploads/downloads |
| Scheduling | APScheduler | Periodic tasks (CMDB sync) |
| Email | Pluggable provider | Notification delivery |

## Module Topology

Seven independently deployable modules, controlled via `ENABLED_MODULES` env var:

```
                    Frontend (Next.js)
  review | portfolio | add | tech-stack | projects | data-management
                                |
                          REST /api/*
                                |
                    Backend (FastAPI)
  architecture_review | application_management | add | technology_stack
       project_management | data_management | ai_assessment
    +----------------------------------------------------------+
    | Auth | Audit | Export | Email | Storage | Scheduler      |
    +----------------------------------------------------------+
                                |
                             asyncpg
                                |
                    PostgreSQL (schema: eam)
                      98+ tables | 33 migrations
```

## Module Descriptions

| Module | Backend Key | Frontend Route Group | Description |
|--------|------------|---------------------|-------------|
| EA Review | `architecture_review` | `(architecture_review)` | Architecture review workflow: requests, meetings, actions, AI checks, reports |
| Application Portfolio | `application_management` | `(application_management)` | BCM, BizCapability, CMDB -- business capability mapping, application CRUD |
| ADD | `add` | `(add_config)` | Architecture Decision & Design: concern catalog, risk scoring, artifact mapping |
| Technology Stack | `technology_stack_management` | `(technology_stack_management)` | Tech stack lifecycle management, compliance checking |
| Project Management | `project_management` | `(project_management)` | Project CRUD, team member management |
| Data Management | `data_management` | `(data_management)` | Master data, resources, certifications, dict options |
| AI Self-Assessment | `ai_assessment` | `(ai_assessment)` | AI project self-assessment against AI Security Architecture Guideline v2.4 |

## AVDM Architecture Concerns

### Overview

Architecture Concerns are derived from the AVDM (Architecture Viewpoint Decision Model) questionnaire. When a requester submits a questionnaire, the system automatically evaluates which PACT architecture concerns are triggered and at what severity level.

### Data Flow

```
Questionnaire Submission
    |   POST /avdm/projects/{id}/questionnaire
    v
Risk Item Extraction
    |   questionnaire answers -> risk_items (code, severity, likelihood)
    v
Concern Evaluation (evaluate_avdm -- backend/app/add/service.py:148)
    |   For each of 52 PACT concerns (CONCERN_CATALOG):
    |
    |   +-- Direct Match: risk_items[concern_key] -> score = (severity/5) * (likelihood/5)
    |   +-- Tag Match: average score of risk_items matching concern.risk_tags[]
    |   +-- risk_score = max(direct_score, tagged_score)
    |   +-- final_score = min(1.0, risk_score + project_complexity * 0.15)
    |   +-- Classification: >=0.66 Mandatory | >=0.38 Recommended | else Optional
    v
Storage
    |   avdm_project_assessment.evaluation (JSONB) -> { decisions[], contributions{}, layerSummary[] }
    v
API Endpoint
    |   GET /ea-requests/{id}/concerns
    v
Frontend Display (AVDMConcernExpandSection)
    |   Expandable table: Concern Key, Concern Name, Layer, Classification, Total Score
    |   Expanded row: individual Questionnaire items with Severity, Likelihood, Item Score
```

### Concern Decision Structure

```json
{
  "concernKey": "B1",
  "concernName": "Business Capability View",
  "layer": "Business / Organization",
  "score": 0.85,
  "classification": "Mandatory",
  "rationale": "Risk-driven AVDM scoring...",
  "contributions": {
    "direct": [
      { "riskCode": "B1", "severity": 4, "likelihood": 0.8, "itemScore": 0.64 }
    ],
    "tagged": [
      { "riskCode": "B2", "severity": 3, "likelihood": 0.6, "itemScore": 0.36 }
    ],
    "rules": []
  }
}
```

### Concern Categories

| Classification | Score Range | Color | Action |
|---------------|------------|-------|--------|
| Mandatory | >= 0.66 | Red | Must be addressed in architecture review |
| Recommended | >= 0.38 | Gold | Should be considered |
| Optional | < 0.38 | Default | May be skipped |

### Key Files

| Layer | File | Purpose |
|-------|------|---------|
| Catalog | `backend/app/add/catalog.py` | 52 PACT concerns with risk_tags, layer mapping |
| Evaluation | `backend/app/add/service.py:148` | `evaluate_avdm()` -- score computation |
| Contributions | `backend/app/add/service.py` | `build_concern_contributions()` -- direct/tag/rule mapping |
| API | `backend/app/architecture_review/concerns.py` | `GET /ea-requests/{id}/concerns` |
| Frontend | `AVDMConcernExpandSection.tsx` | Expandable concern table with item breakdown |

## Data Flow -- EA Review Lifecycle

```
Create Request -> Upload Diagram -> AI Check -> Reviewer Assessment
       |                                             |
  [Status: Draft]                           [Status: Reviewed]
       |                                             |
       |      Meeting Scheduled -> Meeting Held -> Actions Assigned
       |
  [Status: Closed]
```

## Deployment Architecture

```
Browser -> Nginx (reverse proxy) -> Next.js :3000 -> FastAPI :4000 -> PostgreSQL :5432
                                               -> S3 / DB (attachments)
                                               -> LLM API (AI review)
                                               -> Email API (notifications)
```

## Cross-Cutting Concerns

| Concern | Implementation |
|---------|---------------|
| Auth | Middleware -> JWT extraction -> RBAC Depends() -> ownership checks |
| Audit | Append-only audit log, audit_allow()/audit_deny() |
| Logging | Python colorlog, structured key=value pairs |
| Error Handling | Global exception handlers -> {code, message, data} envelope |
| Pagination | paginate() helper -> {items, total, page, page_size} |

## Key Design Decisions

1. **Raw SQL over ORM**: Performance and migration simplicity. Pydantic schemas for request/response validation.
2. **All client-side rendering**: Pages use `'use client'` -- simpler state management, no SSR hydration issues.
3. **Auth via Depends()**: Zero business code intrusion. `require_permission("resource", "scope")` as FastAPI dependency.
4. **Selective module deployment**: `ENABLED_MODULES` env var controls which backend routers activate.
5. **Turbopack for dev**: Replaces Webpack -- lower memory usage, faster HMR.
