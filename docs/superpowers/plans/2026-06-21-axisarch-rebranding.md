# AxisArch Rebranding, Documentation & Harness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Lenovo EAM into AxisArch — zero enterprise branding, complete documentation suite, harness aligned with actual codebase.

**Architecture:** Three parallel workstreams. Workstream A (de-branding) by file count — batch configs, docs, code, tests. Workstream B (docs) creates 5 new documents. Workstream C (harness) rewrites AGENTS.md + CLAUDE.md + OpenCode agents. All verifiable via build + test.

**Tech Stack:** Python/FastAPI, TypeScript/Next.js, PostgreSQL, Markdown

---

## Workstream A: De-Branding (P1)

### Task A1: Root Configuration Files

**Files:**
- Modify: `package.json`
- Modify: `pyproject.toml`

- [ ] **Step 1: Update root package.json**

Change `package.json`:
```json
{
  "name": "axisarch",
  "version": "1.0.0",
  "private": true,
  "description": "AxisArch — Enterprise Architecture Management Platform",
  ...
}
```

- [ ] **Step 2: Update pyproject.toml**

Change `pyproject.toml`:
```toml
[project]
name = "axisarch"
version = "0.1.0"
description = "AxisArch — Enterprise Architecture Management Platform"
requires-python = ">=3.12"
```

- [ ] **Step 3: Verify**

```powershell
node -e "const p = require('./package.json'); console.log(p.name, p.description)"
python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['name'])"
```

- [ ] **Step 4: Commit**

```bash
git add package.json pyproject.toml
git commit -m "chore: rename project to AxisArch in root configs"
```

---

### Task A2: Backend Config — De-Brand

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Rewrite backend/app/config.py defaults**

All Lenovo-specific defaults become empty strings or generic placeholders:

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/axisarch"
    DB_SCHEMA: str = "axisarch"
    PORT: int = 4000
    HOST: str = "0.0.0.0"
    ENABLED_MODULES: str = (
        "add,architecture_review,application_management,"
        "data_management,project_management,technology_stack_management"
    )
    ENABLE_CMDB_SYNC: bool = False

    AUTH_DISABLED: bool = True
    AUTH_DEV_USER: str = "dev_admin"
    AUTH_DEV_ROLE: str = "admin"

    KEYCLOAK_SERVER_URL: str = ""
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = ""
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ALGORITHMS: str = "RS256"

    S3_ENDPOINT: str = ""
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_PREFIX: str = "axisarch/app"

    EA_AGENT_LLM_BASE_URL: str = ""
    EA_AGENT_LLM_API_KEY: str = ""
    EA_AGENT_LLM_MODEL: str = ""
    EA_AGENT_VISION_MODEL: str = ""
    EA_AGENT_LLM_TIMEOUT_SECONDS: int = 180
    EA_AGENT_LLM_MAX_RETRIES: int = 1
    EA_AGENT_APP_ARCH_RULE_NAME: str = "New_App"
    EA_AGENT_CONCURRENCY_LIMIT: int = 2

    AGENT_WATCH_ENABLED: bool = False
    AGENT_WATCH_APPLICATION_NAME: str = "AxisArch Review Assistant"
    AGENT_WATCH_CHATBOT_NAME: str = "AxisArch Review Assistant"
    AGENT_WATCH_TOKEN: str = ""
    AGENT_WATCH_COLLECTOR_URL: str = ""
    AGENT_WATCH_APIH_TOKEN_URL: str = ""
    AGENT_WATCH_APIH_ACCOUNT: str = ""
    AGENT_WATCH_APIH_KEY: str = ""
    AGENT_WATCH_APIH_SECRET: str = ""

    EMAIL_SERVICE_URL: str = ""
    EMAIL_FROM: str = "noreply@axisarch.local"
    EMAIL_DOMAIN: str = ""
    EMAIL_DEFAULT_CC: str = ""

    CMDB_API_URL: str = ""
    CMDB_API_TOKEN: str = ""

    SITE_URL: str = "http://localhost:3000"

    BCT_MS_URL: str = ""
    BCT_TOKEN_URL: str = ""
    BCT_APP_CODE: str = ""
    BCT_SDK_KEY: str = ""

    LOG_LEVEL: str = "DEBUG"

    class Config:
        _backend_env = Path(__file__).resolve().parents[1] / ".env"
        _root_env = Path(__file__).resolve().parents[2] / ".env"
        env_file = str(_backend_env) if _backend_env.exists() else str(_root_env)

settings = Settings()
```

- [ ] **Step 2: Update backend/.env.example**

Rewrite to generic:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/axisarch
DB_SCHEMA=axisarch
PORT=4000
HOST=0.0.0.0
AUTH_DISABLED=true
AUTH_DEV_USER=dev_admin
AUTH_DEV_ROLE=admin
KEYCLOAK_SERVER_URL=
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=
KEYCLOAK_CLIENT_SECRET=
EA_AGENT_LLM_BASE_URL=
EA_AGENT_LLM_API_KEY=
EA_AGENT_LLM_MODEL=
EA_AGENT_VISION_MODEL=
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
EMAIL_SERVICE_URL=
EMAIL_FROM=noreply@axisarch.local
CMDB_API_URL=
CMDB_API_TOKEN=
SITE_URL=http://localhost:3000
ENABLE_CMDB_SYNC=false
```

- [ ] **Step 3: Update references in config consumers**

Grep for `EAM_SITE_URL` in backend code and replace with `SITE_URL`:

```bash
rg "EAM_SITE_URL" backend/ --files-with-matches
```

For each match, replace `settings.EAM_SITE_URL` with `settings.SITE_URL`.

Expected files: `backend/app/architecture_review/ea_requests.py` (email link construction)

- [ ] **Step 4: Commit**

```bash
git add backend/app/config.py backend/.env.example
git commit -m "chore: de-brand backend config, remove enterprise defaults"
```

---

### Task A3: Frontend Config — De-Brand

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/.env.example`
- Modify: `frontend/src/lib/app-config.ts`

- [ ] **Step 1: Update frontend/package.json**

```json
{
  "name": "axisarch-frontend",
  "version": "1.0.0",
  "private": true,
  ...
}
```

- [ ] **Step 2: Rewrite frontend/.env.example**

```
NEXT_PUBLIC_API_URL=http://localhost:4000/api
NEXT_PUBLIC_KEYCLOAK_URL=
NEXT_PUBLIC_KEYCLOAK_REALM=master
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=
NEXT_PUBLIC_BRAND_NAME=AxisArch
NEXT_PUBLIC_APP_TITLE=AxisArch
NEXT_PUBLIC_APP_DESCRIPTION=Enterprise Architecture Management Platform
NEXT_PUBLIC_LOGO_SRC=/axisarch.png
NEXT_PUBLIC_LOGO_ALT=AxisArch
NEXT_PUBLIC_SUPPORT_EMAIL=
NEXT_PUBLIC_SUPPORT_CONTACTS=
NEXT_PUBLIC_CONFLUENCE_URL=
NEXT_PUBLIC_MSPO_URL=
NEXT_PUBLIC_CERT_TYPE_CLSA=CLSA
NEXT_PUBLIC_CERT_TYPE_CLTA=CLTA
NODE_ENV=development
NEXT_TELEMETRY_DISABLED=1
```

- [ ] **Step 3: Update app-config.ts defaults**

In `frontend/src/lib/app-config.ts`, ensure all `process.env.NEXT_PUBLIC_*` references have empty string fallbacks:

```typescript
export const appConfig = {
  brandName: process.env.NEXT_PUBLIC_BRAND_NAME || "AxisArch",
  appTitle: process.env.NEXT_PUBLIC_APP_TITLE || "AxisArch",
  appDescription: process.env.NEXT_PUBLIC_APP_DESCRIPTION || "Enterprise Architecture Management Platform",
  logoSrc: process.env.NEXT_PUBLIC_LOGO_SRC || "/axisarch.png",
  logoAlt: process.env.NEXT_PUBLIC_LOGO_ALT || "AxisArch",
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || "",
  supportContacts: process.env.NEXT_PUBLIC_SUPPORT_CONTACTS || "",
  confluenceUrl: process.env.NEXT_PUBLIC_CONFLUENCE_URL || "",
  mspoUrl: process.env.NEXT_PUBLIC_MSPO_URL || "",
  certTypeCLSA: process.env.NEXT_PUBLIC_CERT_TYPE_CLSA || "CLSA",
  certTypeCLTA: process.env.NEXT_PUBLIC_CERT_TYPE_CLTA || "CLTA",
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/.env.example frontend/src/lib/app-config.ts
git commit -m "chore: de-brand frontend config, generic branding defaults"
```

---

### Task A4: Backend Code — De-Brand

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/architecture_review/ea_requests.py`
- Modify: `backend/app/architecture_review/ai/service_common.py`
- Modify: `backend/app/architecture_review/ai/workflow_common.py`
- Modify: `backend/app/architecture_review/ai/prompts/tech_architect_review.md`
- Modify: `backend/app/auth/__init__.py`
- Modify: `backend/app/auth/models.py`
- Modify: `backend/app/module_registry.py`

- [ ] **Step 1: Update main.py**

In `backend/app/main.py`, change:
```python
app = FastAPI(title="AxisArch API", version="2.0.0", lifespan=lifespan)
```

- [ ] **Step 2: Update email subjects in ea_requests.py**

In `backend/app/architecture_review/ea_requests.py`, replace all `[EAM]` with `[AxisArch]`:

Search for `subject=f"[EAM]"` → `subject=f"[AxisArch]"` (expected ~5 occurrences around lines 1565, 1581, 1644, 1712, 1786)

- [ ] **Step 3: Update AI service scenario names**

In `backend/app/architecture_review/ai/service_common.py`:
```python
scenario="AxisArch"  # was "EAM"
```

In `backend/app/architecture_review/ai/workflow_common.py`:
```python
scenario=kwargs.get("scenario", "AxisArch")  # was "EAM"
```

- [ ] **Step 4: Update tech architect review prompt**

In `backend/app/architecture_review/ai/prompts/tech_architect_review.md`:
- Line ~103: `LenovoID (外部用户)` → `SSO Provider (external users)`
- Line ~148: `内部用户访问需要使用ADFS,外部用户访问需要使用Lenovo` → `Internal users authenticate via enterprise IDP, external users via SSO Provider`

- [ ] **Step 5: Update auth module docstrings**

In `backend/app/auth/__init__.py`:
```python
"""AxisArch Authentication & Authorization module."""
```

In `backend/app/auth/models.py`:
```python
"""AxisArch authorization roles — baseline RBAC + scoped business roles."""
```

- [ ] **Step 6: Update module_registry.py**

In `backend/app/module_registry.py`, change module key:
```python
"add": add_router,  # was "avdm"
```

And update the comment to reference `add` instead of `avdm`.

- [ ] **Step 7: Verify**

```powershell
cd backend; python -c "from app.main import app; print(app.title)"
```

Expected: "AxisArch API"

- [ ] **Step 8: Commit**

```bash
git add backend/app/main.py backend/app/architecture_review/ea_requests.py backend/app/architecture_review/ai/ backend/app/auth/ backend/app/module_registry.py
git commit -m "chore: de-brand backend code — AxisArch naming, generic prompts"
```

---

### Task A5: Frontend Code — De-Brand

**Files:**
- Modify: `frontend/src/components/ui/LoginGate.tsx`
- Modify: `frontend/public/lenovo.png` → `frontend/public/axisarch.png`
- Modify: `frontend/src/app/(data_management)/help/page.tsx`
- Modify: `frontend/src/modules/technology_stack_management/components/lifecycle/ApplicationTechStackModal.tsx`

- [ ] **Step 1: Update LoginGate welcome text**

In `frontend/src/components/ui/LoginGate.tsx`, line ~64:
```tsx
Welcome to the AxisArch system
```

- [ ] **Step 2: Rename logo asset**

```powershell
Rename-Item frontend/public/lenovo.png frontend/public/axisarch.png
```

- [ ] **Step 3: Update help page reference**

In `frontend/src/app/(data_management)/help/page.tsx`, replace `for EAM Review` with `for AxisArch Review`.

- [ ] **Step 4: Update tech stack modal role reference**

In `frontend/src/modules/technology_stack_management/components/lifecycle/ApplicationTechStackModal.tsx`, replace `EAM Admin` with `AxisArch Admin`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/LoginGate.tsx frontend/public/axisarch.png frontend/public/lenovo.png frontend/src/app/\(data_management\)/help/page.tsx frontend/src/modules/technology_stack_management/
git commit -m "chore: de-brand frontend code and assets"
```

---

### Task A6: OpenSpec Specs — De-Brand

**Files:**
- Modify: `openspec/specs/authorization/spec.md`
- Modify: `openspec/specs/certification-management/spec.md`
- Modify: `openspec/specs/ea-request-flow/spec.md`
- Modify: `openspec/specs/shared-services/spec.md`
- Modify: `openspec/specs/sync-cmdb-application/spec.md`
- Modify: `openspec/changes/ea-review-ai-agent-integration/specs/ea-request-flow/spec.md`

- [ ] **Step 1: Update authorization spec**

In `openspec/specs/authorization/spec.md`:
- Replace all `Lenovo` references with generic descriptions
- Replace `EAM` with `AxisArch`

- [ ] **Step 2: Update certification-management spec**

In `openspec/specs/certification-management/spec.md`:
- `CLSA(Certified Lenovo Solution Architect)` → `CLSA (Certified Solution Architect)`
- `CLTA(Certified Lenovo Technical Architect)` → `CLTA (Certified Technical Architect)`

- [ ] **Step 3: Update ea-request-flow spec**

In `openspec/specs/ea-request-flow/spec.md`:
- `https://eam.lenovo.com/ea-review/request/` → generic URL placeholder
- `-CIO_EA@lenovo.com` → generic email placeholder

- [ ] **Step 4: Update shared-services spec**

In `openspec/specs/shared-services/spec.md`:
- Replace enterprise URLs with `<configured-endpoint>` placeholders
- Replace enterprise emails with `<configured-email>`
- `Subject: EAM -` → `Subject: AxisArch -`

- [ ] **Step 5: Update sync-cmdb-application spec**

In `openspec/specs/sync-cmdb-application/spec.md`:
- Replace `Lenovo CMDB API` with `external CMDB API`
- Replace enterprise URL with placeholder

- [ ] **Step 6: Update change proposal specs**

Same treatment for `openspec/changes/` files.

- [ ] **Step 7: Commit**

```bash
git add openspec/
git commit -m "chore: de-brand openspec specs — generic references"
```

---

### Task A7: Database Migrations — De-Brand

**Files:**
- Modify: `backend/migrations/015_normalize_avdm_questionnaire_wording.sql`
- Modify: `backend/migrations/017_seed_avdm_master_data.sql`
- Modify: `backend/migrations/019_normalize_avdm_questionnaire_questions.sql`
- Modify: `backend/app/avdm/questionnaire_config.py`
- Modify: `backend/app/avdm/master_data_seeds.py`

- [ ] **Step 1: Update questionnaire wording migration**

In `015_normalize_avdm_questionnaire_wording.sql`:
- Replace `LenovoID or ADFS` → `SSO Provider or Enterprise IDP`

- [ ] **Step 2: Update master data seed migration**

In `017_seed_avdm_master_data.sql`:
- Replace `LenovoID or ADFS` → `SSO Provider or Enterprise IDP`

- [ ] **Step 3: Update questionnaire questions migration**

In `019_normalize_avdm_questionnaire_questions.sql`:
- `Lenovo subsidiary / JV / holding data` → `Subsidiary / JV / holding data`
- `Have existing solution in Lenovo` → `Have existing solution in organization`
- `Solution uses existing technologies within Lenovo portfolio` → `Solution uses existing technologies within organizational portfolio`

- [ ] **Step 4: Update questionnaire_config.py**

In `backend/app/avdm/questionnaire_config.py`:
- line 189: `"Subsidiary / JV / holding data",`
- line 192: `{"label": "Example Corp", "value": "example_corp"},`

- [ ] **Step 5: Update master_data_seeds.py**

In `backend/app/avdm/master_data_seeds.py`:
- Replace LenovoID reference with generic SSO

- [ ] **Step 6: Commit**

```bash
git add backend/migrations/ backend/app/avdm/questionnaire_config.py backend/app/avdm/master_data_seeds.py
git commit -m "chore: de-brand seed data and migrations — generic references"
```

---

### Task A8: Tests & Scripts — De-Brand

**Files:**
- Modify: `backend/tests/routers/test_master_data.py`
- Modify: `api-tests/tests/test_email.py`
- Modify: `api-tests/helpers/keycloak_auth.py`
- Modify: `api-tests/.env.test.example`
- Modify: `scripts/upsert-apps.sql`
- Modify: `test-data/uat/features/ea-request/ea-request-creation.feature`

- [ ] **Step 1: Update backend test data**

In `backend/tests/routers/test_master_data.py`:
```python
# line 18: replace
{"id": 1, "company_code": "CN01", "company_name": "Example Corp"},
# line 82: replace
resp = client.get("/api/master-data/companies?search=example")
```

- [ ] **Step 2: Update API test email**

In `api-tests/tests/test_email.py`:
- Replace `hongbw2@lenovo.com` → `testuser@example.com`

- [ ] **Step 3: Update Keycloak auth helper**

In `api-tests/helpers/keycloak_auth.py`:
```python
self.server_url = os.environ.get("KEYCLOAK_SERVER_URL", "")
```

- [ ] **Step 4: Update API test env example**

In `api-tests/.env.test.example`:
```
KEYCLOAK_SERVER_URL=
```

- [ ] **Step 5: Update upsert SQL script**

In `scripts/upsert-apps.sql`:
- `LENOVO BID PLATFORM (LBP)` → `Example Platform (EXP)`
- `EAM` app entry → `AxisArch` app entry

- [ ] **Step 6: Update UAT test data**

In `test-data/uat/features/ea-request/ea-request-creation.feature`:
- Replace enterprise URL with `http://localhost:3000`

- [ ] **Step 7: Commit**

```bash
git add backend/tests/ api-tests/ scripts/ test-data/
git commit -m "chore: de-brand tests and scripts — generic test data"
```

---

### Task A9: Integration Docs & README — De-Brand

**Files:**
- Modify: `integration/ai-architecture-review-api.md`
- Modify: `integration/cmdb-applicaiton-api.md`
- Rewrite: `README.md`

- [ ] **Step 1: De-brand AI review API doc**

In `integration/ai-architecture-review-api.md`:
- Title: `# AI Architecture Review API Documentation`
- Remove Lenovo APIHub references → generic
- Replace example URLs with placeholders
- Replace `"title": "Lenovo Multi-Data Center..."` → generic example

- [ ] **Step 2: De-brand CMDB API doc**

In `integration/cmdb-applicaiton-api.md`:
- Replace enterprise URL with placeholder

- [ ] **Step 3: Rewrite README.md**

Full rewrite to AxisArch:

```markdown
# AxisArch — Enterprise Architecture Management Platform

A modular, extensible platform for enterprise architecture management — EA review workflows, application portfolio management, business capability analysis, architecture decision & design (ADD), and reporting.

## Tech Stack
...
## Development
...
## Modules
...
## License
MIT
```

Use the de-branded content from the existing README but replace all branding and enterprise-specific instructions with generic setup.

- [ ] **Step 4: Commit**

```bash
git add integration/ README.md
git commit -m "chore: de-brand integration docs, AxisArch README"
```

---

## Workstream B: Documentation (P2)

### Task B1: Create docs/architecture.md

**Files:**
- Create: `docs/architecture.md`

- [ ] **Step 1: Write architecture document**

```markdown
# AxisArch Architecture

## System Overview

AxisArch is a 3-tier web application:
- **Frontend**: Next.js 15 (React 19, TypeScript) — UI rendering, routing, state management
- **Backend**: FastAPI (Python 3.12+) — API server, business logic, AI orchestration
- **Database**: PostgreSQL 14+ — persistent storage, async access via asyncpg

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend Framework | Next.js 15 (Turbopack) | SSR/CSR, App Router, API proxy |
| UI Library | Ant Design v6 + Tailwind CSS | Component library + utility CSS |
| State Management | TanStack Query v5 + Zustand v5 | Server state + client state |
| Authentication | Pluggable (Keycloak/Dev) | OIDC SSO or dev-mode bypass |
| Backend Framework | FastAPI | Async REST API |
| Database Driver | SQLAlchemy (async) + asyncpg | Connection pooling, raw SQL execution |
| AI Pipeline | LangChain + LangGraph | Architecture diagram review workflows |
| File Storage | S3-compatible (boto3) | Attachment uploads/downloads |
| Scheduling | APScheduler | Periodic tasks (CMDB sync) |
| Email | Pluggable provider | Notification delivery |

## Module Topology

Six independently deployable modules:

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                  │
│  review │ portfolio │ add │ tech-stack │ projects   │
│                       │ data-management             │
└──────────────────────┬──────────────────────────────┘
                       │ REST /api/*
┌──────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                   │
│  architecture_review │ application_management        │
│  add │ technology_stack │ project │ data_management │
│  ┌──────────────────────────────────────────────┐   │
│  │  Auth │ Audit │ Export │ Email │ Storage     │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │ asyncpg
┌──────────────────────▼──────────────────────────────┐
│              PostgreSQL (schema: axisarch)            │
│  20+ tables │ 22 migrations │ async access          │
└─────────────────────────────────────────────────────┘
```

## Module Descriptions

| Module | Backend Key | Frontend Route Group | Description |
|--------|------------|---------------------|-------------|
| EA Review | `architecture_review` | `(architecture_review)` | Architecture review workflow: requests, meetings, actions, AI checks, reports |
| Application Portfolio | `application_management` | `(application_management)` | BCM, BizCapability, CMDB — business capability mapping, application CRUD |
| ADD | `add` | `(data_management)` | Architecture Decision & Design: concern catalog, risk scoring, artifact mapping |
| Technology Stack | `technology_stack_management` | `(technology_stack_management)` | Tech stack lifecycle management, compliance checking |
| Project Management | `project_management` | `(project_management)` | Project CRUD, team member management |
| Data Management | `data_management` | `(data_management)` | Master data, resources, certifications, dict options |

## Data Flow — EA Review Lifecycle

```
Create Request → Upload Diagram → AI Check → Reviewer Assessment
       ↓                                               ↓
  [Status: Draft]                              [Status: Reviewed]
       ↓                                               ↓
  Meeting Scheduled → Meeting Held → Actions Assigned
       ↓
  [Status: Closed]
```

## Deployment Architecture

```
Browser → Nginx (reverse proxy) → Next.js :3000 → FastAPI :4000 → PostgreSQL :5432
                                              → S3 (attachments)
                                              → LLM API (AI review)
                                              → Email API (notifications)
```

## Cross-Cutting Concerns

| Concern | Implementation |
|---------|---------------|
| Auth | Middleware → JWT extraction → RBAC Depends() → ownership checks |
| Audit | Append-only eam_audit_log table, audit_allow()/audit_deny() |
| Logging | Python colorlog, structured key=value pairs |
| Error Handling | Global exception handlers → {code, message, data} envelope |
| Pagination | paginate() helper → {items, total, page, page_size} |

## Key Design Decisions

1. **Raw SQL over ORM**: Performance and migration simplicity. Pydantic schemas for request/response validation.
2. **All client-side rendering**: Pages use `'use client'` — simpler state management, no SSR hydration issues.
3. **Auth via Depends()**: Zero business code intrusion. `require_permission("resource", "scope")` as FastAPI dependency.
4. **Selective module deployment**: `ENABLED_MODULES` env var controls which backend routers activate.
5. **Turbopack for dev**: Replaces Webpack — lower memory usage, faster HMR.
```

- [ ] **Step 2: Commit**

```bash
git add docs/architecture.md
git commit -m "docs: add architecture overview"
```

---

### Task B2: Create docs/STATUS.md

**Files:**
- Create: `docs/STATUS.md`

- [ ] **Step 1: Write status document**

```markdown
# AxisArch — Project Status

## Module Completion

| Module | Backend (lines) | Frontend (lines) | API Endpoints | Tests | Status |
|--------|----------------|------------------|---------------|-------|--------|
| Auth & RBAC | ~890 | ~436 | 2 | 7 auth tests | Complete |
| EA Review | ~2,622 | ~2,670 | 12 | Router + API tests | Complete |
| Application Portfolio | ~758 | ~1,215 | 8 | Router + API tests | Complete |
| ADD (AVDM) | ~643 | ~687 | 12 | Roundtrip + API tests | Complete |
| Technology Stack | ~400 | ~800 | 6 | Router + API tests | Complete |
| Project Management | ~200 | ~400 | 4 | API tests | Complete |
| Data Management | ~443 | ~500 | 8 | Router + API tests | Complete |
| Shared Services | ~731 | ~146 | 4 | API tests | Complete |
| AI Review Agent | ~800 | ~200 | 2 | 2 agent tests | Complete |

Total: ~81 API endpoints, 201 API integration tests, 4 E2E specs

## Test Coverage

| Layer | Framework | Tests | Coverage |
|-------|-----------|-------|----------|
| API Integration | pytest | 201 tests, 27 files | All 23 routers |
| Backend Unit | pytest | ~50 tests | Auth, ADD, Utils |
| Frontend E2E | Playwright | 4 specs | BCM, CMDB, BizCapability, BC Visualization |
| Frontend Unit | (none) | 0 | No Vitest setup |

## Known Limitations

1. **Raw SQL without ORM**: Backend uses `text()` queries directly — no migration rollback, no type-safe queries
2. **No API versioning**: No `/api/v1/` prefix or version negotiation
3. **Frontend lacks SSR**: All pages are `'use client'` — no SEO benefits, slower initial load
4. **Large router files**: `ea_requests.py` exceeds 1100 lines — needs decomposition
5. **No i18n extraction**: Strings are inline in JSX — no key-based extraction tooling
6. **Email service coupled**: Hardcoded to BCT Message API — not abstracted
7. **CMDB sync single-provider**: Only one CMDB API implementation
8. **No CSRF protection**: JWT Bearer only — no double-submit cookie pattern
9. **No rate limiting**: AI review endpoint has no request throttling
10. **Sensitive data in env**: S3 credentials, API tokens in plain env vars

## Tech Debt

| Item | Severity | Effort |
|------|----------|--------|
| ea_requests.py split | Medium | 2 days |
| Frontend unit test setup | Medium | 1 day |
| API versioning | Low | 3 days |
| i18n extraction framework | Low | 5 days |
| Secrets management (Vault) | Medium | 3 days |
| Rate limiting on AI endpoint | Medium | 1 day |
```

- [ ] **Step 2: Commit**

```bash
git add docs/STATUS.md
git commit -m "docs: add project status and limitations"
```

---

### Task B3: Create docs/ROADMAP.md

**Files:**
- Create: `docs/ROADMAP.md`

- [ ] **Step 1: Write roadmap document**

```markdown
# AxisArch — Roadmap

## v1.0 — De-brand & Document (Current)
- [x] Remove all enterprise branding
- [x] Add architecture, status, roadmap, threat model, API docs
- [x] Align development harness (AGENTS.md, OpenCode)
- [ ] Verify build + test suite passes

## v1.1 — Clean Architecture Refactoring
- [ ] Extract domain layer (entities, value objects, repository interfaces)
- [ ] Create application service layer (use cases, DTOs)
- [ ] Implement repository layer (wrap raw SQL)
- [ ] Thin API routers (delegate to services)
- [ ] Plugin system for enterprise integrations (auth, email, CMDB, storage)
- [ ] Frontend feature-folder restructuring

## v1.2 — Frontend Modernization
- [ ] Unit test setup (Vitest + React Testing Library)
- [ ] Shared component library extraction
- [ ] API versioning (v1 → v2 with deprecation)
- [ ] Error boundary pages
- [ ] Loading skeleton patterns

## v1.3 — Multi-Tenancy
- [ ] Schema-level or row-level tenant isolation
- [ ] Tenant-aware auth (Keycloak realm per tenant)
- [ ] Tenant-scoped master data
- [ ] Tenant admin dashboard

## v2.0 — Plugin Marketplace
- [ ] Plugin SDK specification
- [ ] Hot-reload module system
- [ ] Plugin registry with versioning
- [ ] Community plugin templates

## v2.1 — Internationalization
- [ ] i18n key extraction tooling
- [ ] zh/en/es localization packs
- [ ] RTL layout support
- [ ] Locale-aware date/number formatting

## v2.2 — Observability
- [ ] OpenTelemetry tracing
- [ ] Structured logging (JSON format)
- [ ] Metrics dashboard (Prometheus + Grafana)
- [ ] Audit log integrity hashing
```

- [ ] **Step 2: Commit**

```bash
git add docs/ROADMAP.md
git commit -m "docs: add development roadmap"
```

---

### Task B4: Create docs/threat-model.md

**Files:**
- Create: `docs/threat-model.md`

- [ ] **Step 1: Write threat model document**

```markdown
# AxisArch — Security Threat Model

## Trust Boundaries

```
┌──────────┐     ┌──────────┐     ┌───────────┐     ┌────────────┐
│ Browser  │────▶│ Next.js  │────▶│  FastAPI  │────▶│ PostgreSQL │
│  (TB0)   │     │ :3000    │     │  :4000    │     │  (TB3)     │
└──────────┘     └──────────┘     └─────┬─────┘     └────────────┘
                                        │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Keycloak │ │ LLM API  │ │ S3/Email │
                    │  (TB4a)  │ │  (TB4b)  │ │  (TB4c)  │
                    └──────────┘ └──────────┘ └──────────┘
```

## STRIDE Analysis

### Boundary 1: Browser ↔ Next.js
| Threat | Severity | Mitigation |
|--------|----------|------------|
| XSS via user input | High | React auto-escaping, CSP headers |
| CSRF on state changes | Medium | JWT Bearer (not vulnerable to CSRF); add SameSite cookies |
| Token theft via XSS | High | httpOnly cookie option (currently localStorage) |

### Boundary 2: Next.js ↔ FastAPI
| Threat | Severity | Mitigation |
|--------|----------|------------|
| JWT tampering | High | JWKS signature verification |
| Token replay | Medium | Short token expiry (5min access, 30min refresh) |
| MITM | Medium | HTTPS in production |

### Boundary 3: FastAPI ↔ PostgreSQL
| Threat | Severity | Mitigation |
|--------|----------|------------|
| SQL injection | Critical | Parameterized queries via SQLAlchemy `text().bindparams()` |
| Credential leak | High | Env vars (not in code); rotate DB passwords |
| Excessive privileges | Medium | Least-privilege DB user (read/write only, no DDL from app) |

### Boundary 4a: FastAPI ↔ Keycloak
| Threat | Severity | Mitigation |
|--------|----------|------------|
| Token forgery | Critical | JWKS verification with 1-hour cache refresh |
| Keycloak downtime | Medium | Dev-mode fallback for local dev only |

### Boundary 4b: FastAPI ↔ LLM API
| Threat | Severity | Mitigation |
|--------|----------|------------|
| Prompt injection via uploaded diagrams | High | No user text in prompts; only extracted image data |
| Sensitive data in prompts | Medium | Review prompts for data minimization |
| API key leak | High | Env var, never logged |
| Rate limit bypass | Medium | Not implemented — need concurrency limiter (EA_AGENT_CONCURRENCY_LIMIT) |

### Boundary 4c: FastAPI ↔ S3 / Email
| Threat | Severity | Mitigation |
|--------|----------|------------|
| Unauthenticated file upload | High | RBAC-gated upload endpoint |
| File type bypass | Medium | Content-Type validation on upload |
| Email spoofing | Low | Fixed sender, no user-controlled From header |
| API token leak | High | Env vars, rotate regularly |

## Known Gaps

1. **No CSRF tokens**: API uses JWT Bearer → not CSRF-vulnerable by default, but double-submit cookie adds defense-in-depth
2. **No rate limiting**: AI review endpoint can be abused for resource exhaustion
3. **Plain-text audit log**: No hash chain or tamper detection on `eam_audit_log`
4. **Secrets in environment**: S3 keys, CMDB tokens, email tokens in plain env vars — should use Vault/Secrets Manager
5. **No WAF**: No web application firewall for injection/shellshock protection
6. **Email tokens long-lived**: BCT tokens have extended expiry without rotation automation

## Planned Mitigations (v1.1+)
- API rate limiting per user + per endpoint
- Secrets manager integration (HashiCorp Vault or cloud-native)
- Audit log Merkle-tree integrity verification
- File upload malware scanning integration
- Automated secret rotation
```

- [ ] **Step 2: Commit**

```bash
git add docs/threat-model.md
git commit -m "docs: add security threat model"
```

---

### Task B5: Create docs/api.md

**Files:**
- Create: `docs/api.md`

- [ ] **Step 1: Write API reference document**

```markdown
# AxisArch API Reference

## Base
- URL: `/api`
- Auth: Bearer JWT (Keycloak OIDC or Dev)
- Content-Type: `application/json`
- Envelope: `{"code": 200, "message": "success", "data": {...}, "timestamp": "..."}`

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/me` | Current user info + roles |
| GET | `/api/auth/permissions` | Full permission list for current user |

## EA Review

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ea-requests` | List requests (paginated, filterable) |
| POST | `/api/ea-requests` | Create request |
| GET | `/api/ea-requests/{id}` | Get request detail |
| PUT | `/api/ea-requests/{id}` | Update request |
| DELETE | `/api/ea-requests/{id}` | Delete request |
| GET | `/api/ea-requests/dashboard` | Dashboard aggregations |
| POST | `/api/ea-requests/attachments` | Upload attachment |
| GET | `/api/ea-requests/attachments/{id}` | Download attachment |
| DELETE | `/api/ea-requests/attachments/{id}` | Delete attachment |
| POST | `/api/ea-requests/attachments/ai-check` | Trigger AI architecture check |

## Meetings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/meetings` | List meetings |
| POST | `/api/meetings` | Create meeting |
| GET | `/api/meetings/{id}` | Get meeting detail |
| PUT | `/api/meetings/{id}` | Update meeting |
| DELETE | `/api/meetings/{id}` | Delete meeting |

## Actions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/actions` | List actions |
| POST | `/api/actions` | Create action |
| PUT | `/api/actions/{id}` | Update action |
| DELETE | `/api/actions/{id}` | Delete action |

## Architecture Check

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/architecture-checks` | List architecture checks |
| POST | `/api/architecture-checks` | Create check |
| GET | `/api/architecture-checks/{id}` | Get check detail |

## Applications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/applications/bcm` | Business capability mapping |
| POST | `/api/applications/bcm` | Create BCM entry |
| PUT | `/api/applications/bcm/{id}` | Update BCM entry |
| GET | `/api/applications/bcm/visualization` | BC analysis data |
| GET | `/api/biz-capability` | BizCapability master data |
| POST | `/api/biz-capability` | Create BizCapability entry |
| GET | `/api/cmdb-applications` | CMDB application list |

## ADD (Architecture Decision & Design)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/add/questionnaire` | Get questionnaire config |
| PUT | `/api/add/questionnaire` | Update questionnaire config |
| GET | `/api/add/concerns` | List concern catalog |
| POST | `/api/add/concerns` | Create concern |
| GET | `/api/add/assessments` | List project assessments |
| POST | `/api/add/assessments` | Create assessment |
| GET | `/api/add/assessments/{id}` | Get assessment detail |
| PUT | `/api/add/assessments/{id}` | Update assessment |
| GET | `/api/add/artifacts/recommendations` | Get artifact recommendations |
| GET | `/api/add/master-data/viewpoints` | Viewpoint master data |
| GET | `/api/add/master-data/artifacts` | Artifact master data |

## Technology Stack

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/technology-stack` | List tech stack items |
| POST | `/api/technology-stack` | Create item |
| PUT | `/api/technology-stack/{id}` | Update item |
| DELETE | `/api/technology-stack/{id}` | Soft delete |
| GET | `/api/technology-stack/{id}/lifecycle` | Lifecycle history |
| GET | `/api/technology-stack/compliance-check` | Compliance sync |

## Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Get project detail |
| PUT | `/api/projects/{id}` | Update project |

## Data Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/master-data/{type}` | Get master data by type |
| POST | `/api/master-data/{type}` | Create master data entry |
| GET | `/api/dict-options/{type}` | Get dictionary options |
| GET | `/api/certifications` | List certifications |
| POST | `/api/certifications` | Create certification |
| PUT | `/api/certifications/{id}` | Update certification |
| GET | `/api/resources` | Resource pool |

## Reports & Export

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports/{type}` | Report data |
| GET | `/api/dashboard` | Dashboard aggregations |
| GET | `/api/export/{entity}` | CSV export |

## Shared

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/audit-log` | Audit log queries |
| GET | `/api/email-log` | Email send history |
| GET | `/api/health` | Health check |

## Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/team-members` | Team member list |
| POST | `/api/team-members` | Add team member |
| GET | `/api/schedules` | Calendar/schedule |
| POST | `/api/schedules` | Create schedule entry |
| GET | `/api/scope` | Scope of change config |
| POST | `/api/scope` | Create scope entry |

## Pagination
All list endpoints support: `?page=1&page_size=20`
Response includes: `{"items": [...], "total": 150, "page": 1, "page_size": 20}`

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation) |
| 401 | Unauthenticated — missing/invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 422 | Validation error (Pydantic) |
| 500 | Internal server error |
```

- [ ] **Step 2: Commit**

```bash
git add docs/api.md
git commit -m "docs: add API reference"
```

---

### Task B6: Update Existing Documentation

**Files:**
- Modify: `docs/design.md`
- Modify: `docs/design-En.md`
- Modify: `docs/authorization.md`
- Modify: `docs/module-splitting-plan.md`

- [ ] **Step 1: De-brand design docs**

In `docs/design.md` and `docs/design-En.md`:
- Replace all Lenovo/EAM references with AxisArch
- Update architecture descriptions to match new naming

- [ ] **Step 2: Update authorization doc**

In `docs/authorization.md`:
- Replace `EAM uses` → `AxisArch uses`
- Replace enterprise-specific role descriptions with generic ones

- [ ] **Step 3: Update module splitting plan**

In `docs/module-splitting-plan.md`:
- Replace project name references
- Keep module structure intact (it's organizational, not branding)

- [ ] **Step 4: Commit**

```bash
git add docs/design.md docs/design-En.md docs/authorization.md docs/module-splitting-plan.md
git commit -m "docs: de-brand existing documentation"
```

---

## Workstream C: Harness Alignment (P3)

### Task C1: Rewrite AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Write new AGENTS.md**

```markdown
# AxisArch — Enterprise Architecture Management Platform

OpenCode project rules file. Claude Code reads `CLAUDE.md`. Keep both aligned.

## Product Identity

- **Product**: AxisArch
- **Tagline**: A modular enterprise architecture management platform.

## Harness

Use Superpowers as the project development harness.

Superpowers lives in `superpowers/` and is enabled via `.opencode/`. All 14 skills are instrumented with proc workflow templates.

Use Superpowers workflows for planning, TDD, debugging, verification, and code review.

## Architecture (3 Tiers + Plugin System)

```
Frontend (Next.js 15 + React 19)  →  Backend (FastAPI + Python 3.12)  →  PostgreSQL / S3
    ↑ AntD v6 + Zustand                ↑ 6 pluggable modules + RBAC       ↑ asyncpg + boto3
```

## Component Projects

| Project | Language | Responsibility |
|---------|----------|----------------|
| `frontend/` | TypeScript/React | Next.js 15 UI, App Router, Ant Design v6 components |
| `backend/` | Python | FastAPI server, 6 business modules, AI review pipeline |
| `api-tests/` | Python/pytest | API integration tests (201 tests) |

## Modules

| Module | Backend Key | Description |
|--------|------------|-------------|
| EA Review | `architecture_review` | Architecture review workflow, meetings, actions, AI checks, reports |
| Application Portfolio | `application_management` | BCM, BizCapability, CMDB — business capability mapping |
| ADD | `add` | Architecture Decision & Design — concern catalog, risk scoring |
| Technology Stack | `technology_stack_management` | Tech stack lifecycle, compliance checking |
| Project Management | `project_management` | Project CRUD, team management |
| Data Management | `data_management` | Master data, resources, certifications |

Selective deployment via `ENABLED_MODULES` env var:
```env
ENABLED_MODULES=add,architecture_review,application_management,data_management,project_management,technology_stack_management
```

## Key Principles

1. **Modular by contract**: Modules enabled/disabled via `ENABLED_MODULES` env var. Each module self-contained with its own DB access.
2. **Deny by default**: All 81 API endpoints are RBAC-gated via `require_permission(resource, scope)`. Zero business code intrusion.
3. **Audit everything**: Append-only `eam_audit_log` with `audit_allow()` / `audit_deny()` hooks.
4. **Plugin-first**: Auth providers, email services, CMDB connectors, and storage backends are abstracted behind interfaces. Default to dev-mode stubs, plug in enterprise adapters via config.
5. **Raw SQL over ORM**: Backend uses SQLAlchemy `text()` for performance. Pydantic models for request/response validation. DB schema tracked in migration SQL files under `backend/migrations/`.

## Documentation

| Doc | Content |
|-----|---------|
| `docs/architecture.md` | System architecture, data model, module topology |
| `docs/threat-model.md` | Security threat model (trust boundaries, STRIDE, known gaps) |
| `docs/api.md` | API reference (81 endpoints, auth, pagination, error codes) |
| `docs/STATUS.md` | Current completion status, limitations, tech debt |
| `docs/ROADMAP.md` | v1.0 through v2.2 feature roadmap |
| `docs/design.md` | Detailed system design (Chinese) |
| `docs/authorization.md` | Auth model: RBAC + record-level ownership |
| `docs/module-splitting-plan.md` | Multi-team module boundaries |
| `docs/standards/` | Coding conventions (8 standards documents) |
| `openspec/specs/` | Feature specs (10 specs, 2 active changes) |

## Development Verification

```sh
# Frontend build + lint
cd frontend && npm run lint && npm run build

# Backend tests
cd backend && python -m pytest

# API integration tests
cd api-tests && python -m pytest

# Frontend E2E tests
cd frontend && npx playwright test
```
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: align AGENTS.md with actual AxisArch architecture"
```

---

### Task C2: Rewrite CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write synced CLAUDE.md**

```markdown
# AxisArch — Enterprise Architecture Management Platform

Claude Code project rules file. OpenCode reads `AGENTS.md`. Keep both aligned.

## Harness

Use Superpowers as the project development harness. Superpowers lives in `superpowers/`.

## Architecture (3 Tiers)

Frontend (Next.js 15, React 19, TypeScript) → Backend (FastAPI, Python 3.12) → PostgreSQL + S3

6 pluggable backend modules: architecture_review, application_management, add, technology_stack_management, project_management, data_management.

## Key Technologies

- Next.js 15 (Turbopack) + React 19 + Ant Design v6 + TanStack Query + Zustand
- FastAPI + SQLAlchemy async + asyncpg
- LangChain + LangGraph (AI architecture review)
- Keycloak OIDC (pluggable) / DevAuthProvider

## Documentation

| Doc | Content |
|-----|---------|
| `docs/architecture.md` | Architecture, modules, data flow |
| `docs/STATUS.md` | Status, limitations, test coverage |
| `docs/ROADMAP.md` | v1.0 through v2.2 |
| `docs/api.md` | API reference (81 endpoints) |
| `docs/threat-model.md` | Security threat model |
| `docs/design.md` | Detailed system design |

## Verification

```sh
cd frontend && npm run build
cd backend && python -m pytest
cd api-tests && python -m pytest
```
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: align CLAUDE.md with AxisArch"
```

---

### Task C3: Create OpenCode Agents

**Files:**
- Create: `.opencode/agents/code-reviewer.md`
- Create: `.opencode/agents/test-runner.md`

- [ ] **Step 1: Create code-reviewer agent**

```markdown
# AxisArch Code Reviewer

Review code changes against AxisArch conventions.

## Backend (Python/FastAPI)
- Raw SQL via `text()` with parameterized queries
- FastAPI `Depends(require_permission(...))` for all endpoints
- Response envelope: `{"code", "message", "data", "timestamp"}`
- Pydantic settings from environment
- All DB access via async session

## Frontend (TypeScript/React)
- Next.js App Router with route groups
- Ant Design v6 components (no custom replacements)
- TanStack Query for server state, Zustand for client state
- `usePermission()` / `<PermissionGate>` for auth-gated UI
- `'use client'` directive on all pages
- API client from `@/lib/api` — auto-unwraps envelope, handles 401/403

## Common Issues to Flag
- Missing RBAC check on new endpoints
- Unwrapped API responses
- Hardcoded credentials or URLs
- SQL injection through string concatenation
- Missing pagination on list endpoints
- Tight coupling between modules
```

- [ ] **Step 2: Create test-runner agent**

```markdown
# AxisArch Test Runner

Run tests and interpret results.

## Commands

```sh
# Backend unit tests
cd backend && python -m pytest tests/ -v

# Backend single test
cd backend && python -m pytest tests/routers/test_ea_requests.py::test_create_request -v

# API integration tests
cd api-tests && python -m pytest tests/ -v

# API single test
cd api-tests && python -m pytest tests/test_ea_requests.py -v

# Frontend build check
cd frontend && npm run build

# Frontend E2E tests
cd frontend && npx playwright test

# Frontend E2E single spec
cd frontend && npx playwright test e2e/bcm.spec.ts
```

## Interpreting Failures
- 401: JWT token expired or missing — check AUTH_DISABLED setting
- 403: RBAC permission missing — check user role assignment
- 404: Route not registered — check ENABLED_MODULES includes the module
- 422: Request validation failed — check Pydantic schema vs request body
- Connection refused: Backend not running on port 4000
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/agents/
git commit -m "chore: add OpenCode agent definitions"
```

---

## Workstream D: Final Verification

### Task D1: Full Build + Test Verification

- [ ] **Step 1: Frontend build**

```powershell
cd frontend; npm run build
```

Expected: Build succeeds with no TypeScript or import errors.

- [ ] **Step 2: Backend import check**

```powershell
cd backend; python -c "from app.main import app; print('OK')"
```

Expected: `OK` with no import errors.

- [ ] **Step 3: Backend tests**

```powershell
cd backend; python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

- [ ] **Step 4: API integration tests**

```powershell
cd api-tests; python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

- [ ] **Step 5: Fix any failures**

If tests fail due to naming changes (e.g., `EAM` references in test assertions), fix them and re-run.

Common expected failures:
- Tests referencing `EAM` in assertions → replace with `AxisArch`
- Tests with hardcoded enterprise URLs → replace with generic placeholders
- Tests with `Lenovo` seed data → replace with generic data

- [ ] **Step 6: Final commit**

```bash
git add -A
git diff --cached --stat
git commit -m "chore: final verification fixes after de-branding"
```

---

## Summary

| Workstream | Tasks | Files Created | Files Modified |
|------------|-------|---------------|----------------|
| A: De-Brand | A1-A9 | 0 | ~30 |
| B: Documentation | B1-B6 | 5 | 4 |
| C: Harness | C1-C3 | 2 | 2 |
| D: Verification | D1 | 0 | ~5 (fixes) |
| **Total** | **19 tasks** | **7** | **~41** |
