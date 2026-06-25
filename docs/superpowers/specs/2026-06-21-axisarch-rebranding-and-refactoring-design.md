# AxisArch: Rebranding, Documentation & Architecture Refactoring

**Date**: 2026-06-21
**Status**: Design Approved
**Product**: AxisArch (formerly Lenovo EAM)

---

## 1. Overview

Transform the current Lenovo EAM enterprise application into **AxisArch** — a generic, modular Enterprise Architecture Management platform. This spec covers four phases:

| Phase | Scope | Goal |
|-------|-------|------|
| P1: De-brand | Naming, config, test data | Zero Lenovo/EAM references in codebase |
| P2: Documentation | architecture.md, STATUS.md, ROADMAP.md, threat-model.md, api.md | Complete project documentation suite |
| P3: Harness | AGENTS.md, CLAUDE.md, OpenCode agents | Harness aligned with actual project |
| P4: Architecture | Clean Architecture layers, plugin system | Backend/frontend refactored to Clean Architecture |

---

## 2. Naming Map

| Category | Old | New |
|----------|-----|-----|
| Product | Lenovo EAM | AxisArch |
| Module | AVDM | ADD (Architecture Decision & Design) |
| DB Schema | `eam` | `axisarch` |
| DB Table prefix | `eam_` | `axisarch_` |
| Package name (root) | `eam` | `axisarch` |
| Package name (frontend) | `eam-frontend` | `axisarch-frontend` |
| Package name (api-tests) | `eam-api-tests` | `axisarch-api-tests` |
| Logo asset | `lenovo.png` | `axisarch.png` |
| Description | Lenovo Enterprise Architecture Management | Enterprise Architecture Management Platform |

---

## 3. Phase 1 — De-Branding

### 3.1 Files by Category

#### Configuration Files (6 files)

| File | Changes |
|------|---------|
| `backend/app/config.py` | Remove Lenovo defaults (S3_ENDPOINT, S3_BUCKET, EMAIL_*, CMDB_*, EAM_SITE_URL, BCT_*) → empty strings or generic placeholders; rename EAM_SITE_URL → SITE_URL |
| `backend/.env` | Remove Lenovo URLs; replace with placeholder comments |
| `backend/.env.example` | Same treatment |
| `frontend/.env` | Remove Keycloak URL; branding vars → generic |
| `frontend/.env.example` | Same treatment |
| `api-tests/.env.test.example` | Remove Keycloak URL |
| `pyproject.toml` | name: axisarch, update description |

#### Root Configuration (2 files)

| File | Changes |
|------|---------|
| `package.json` | name: axisarch, description: generic |
| `README.md` | Full rewrite: AxisArch branding, generic setup instructions |

#### Documentation (7 files)

| File | Changes |
|------|---------|
| `docs/design.md` | Replace Lenovo/EAM → AxisArch; update architecture description |
| `docs/design-En.md` | Same treatment |
| `docs/authorization.md` | Generic role descriptions |
| `docs/module-splitting-plan.md` | Replace project name |
| `docs/schema.prisma` | Schema eam → axisarch |
| `docs/standards/*` | Keep as-is (coding conventions are generic) |
| `docs/version-management-strategy.md` | Keep as-is |

#### Backend Code (10 files)

| File | Changes |
|------|---------|
| `backend/app/main.py` | FastAPI title: "AxisArch API" |
| `backend/app/config.py` | Settings class: remove enterprise defaults |
| `backend/app/architecture_review/ea_requests.py` | Email subjects: `[AxisArch]` |
| `backend/app/architecture_review/ai/service_common.py` | scenario: "AxisArch" |
| `backend/app/architecture_review/ai/workflow_common.py` | scenario: "AxisArch" |
| `backend/app/architecture_review/ai/prompts/tech_architect_review.md` | Remove LenovoID references → generic SSO provider |
| `backend/app/avdm/*` | Module rename: avdm → add, AVDM → ADD (handled in P4) |
| `backend/app/auth/__init__.py` | Docstring: AxisArch Authentication |
| `backend/app/auth/models.py` | Docstring: AxisArch authorization roles |
| `backend/app/module_registry.py` | Module key: avdm → add |

#### Frontend Code (4 files)

| File | Changes |
|------|---------|
| `frontend/src/components/ui/LoginGate.tsx` | "Welcome to the AxisArch system" |
| `frontend/src/app/(data_management)/help/page.tsx` | Reference update |
| `frontend/src/modules/technology_stack_management/components/lifecycle/ApplicationTechStackModal.tsx` | Role name reference |
| `frontend/public/lenovo.png` | Rename to `axisarch.png` |

#### OpenSpec (7 files)

| File | Changes |
|------|---------|
| All 10 spec files | Replace Lenovo/EAM references |
| Config references | Replace enterprise URLs with placeholders |

#### Database Migrations (4 files)

| File | Changes |
|------|---------|
| `015_normalize_avdm_questionnaire_wording.sql` | LenovoID → generic SSO |
| `017_seed_avdm_master_data.sql` | Company seed data → generic; LenovoID → generic SSO |
| `019_normalize_avdm_questionnaire_questions.sql` | Lenovo references → generic |
| `backend/app/avdm/questionnaire_config.py` | Lenovo options → generic |

#### Integration Docs (2 files)

| File | Changes |
|------|---------|
| `integration/ai-architecture-review-api.md` | Title + URLs + example data → generic |
| `integration/cmdb-applicaiton-api.md` | URL reference generic |

#### Test Files (3 files)

| File | Changes |
|------|---------|
| `backend/tests/routers/test_master_data.py` | test data: CN01 → generic company |
| `api-tests/tests/test_email.py` | email address → generic |
| `api-tests/helpers/keycloak_auth.py` | default URL → empty |

#### Scripts (1 file)

| File | Changes |
|------|---------|
| `scripts/upsert-apps.sql` | LENOVO BID PLATFORM → generic app name |

### 3.2 De-Branding Principles

1. **Env vars with enterprise defaults**: Remove defaults from `config.py`, use empty strings. Users configure their own values.
2. **Seed data**: Replace real company names with generic examples (e.g., "Acme Corp", "GlobalTech").
3. **Hardcoded references in prompts/SQL**: Replace "LenovoID" → "SSO Provider", "ADFS" → "Enterprise IDP", etc.
4. **Email subjects**: `[EAM]` → `[AxisArch]`.

---

## 4. Phase 2 — Documentation

### 4.1 New Documents

#### `docs/architecture.md` (~300 lines)

Sections:
- System Overview (3-tier: Frontend → Backend → PostgreSQL/S3)
- Technology Stack (Next.js, FastAPI, PostgreSQL, Keycloak, LangGraph)
- Module Topology (6 modules with dependency graph)
- Data Flow (request lifecycle, AI review pipeline, CMDB sync)
- Deployment Architecture (Nginx → Next.js → FastAPI → PostgreSQL)
- Cross-Cutting Concerns (auth, audit, logging, error handling)
- Design Decisions (raw SQL rationale, why Turbopack, why Zustand, why React 19)

#### `docs/STATUS.md` (~200 lines)

Sections:
- Module Completion Matrix (backend source lines, frontend source lines, test coverage per module)
- API Coverage (81 endpoints breakdown by module)
- Test Coverage (201 API tests, 4 E2E specs, backend unit tests)
- Known Limitations
  - Raw SQL without ORM mapping layer
  - No automated DB migration rollback
  - Frontend lacks SSR (all 'use client')
  - No i18n key extraction tooling
  - Email service not abstracted
  - CMDB sync hardcoded to one provider
- Tech Debt Items
  - ea_requests.py >1100 lines (needs splitting)
  - Mixed concerns in some frontend pages
  - No API versioning strategy
  - Hardcoded credentials in config.py (P1 will fix)

#### `docs/ROADMAP.md` (~150 lines)

| Version | Theme | Key Deliverables |
|---------|-------|------------------|
| v1.0 | De-brand + Docs | P1 + P2 complete, AxisArch release |
| v1.1 | Clean Architecture | P4 backend layers, plugin system |
| v1.2 | Frontend Restructure | Feature-based folders, shared component library extraction |
| v1.3 | Multi-tenancy | Schema-level or row-level multi-tenant support |
| v2.0 | Plugin Marketplace | External plugin SDK, hot-reload modules |
| v2.1 | i18n Framework | Extract all strings, zh/en/es localization packs |
| v2.2 | Observability | OpenTelemetry tracing, structured logging, metrics dashboard |

#### `docs/threat-model.md` (~200 lines)

Sections:
- Trust Boundaries
  - Boundary 1: Browser ↔ Next.js (CSRF, XSS)
  - Boundary 2: Next.js ↔ FastAPI (JWT tampering, MITM)
  - Boundary 3: FastAPI ↔ PostgreSQL (SQL injection, credential leak)
  - Boundary 4: FastAPI ↔ External APIs (Keycloak, LLM, S3, Email) — token leak, SSRF
- STRIDE Analysis per boundary
- Known Gaps
  - No CSRF protection on API endpoints (JWT Bearer only)
  - No rate limiting on AI review endpoint
  - S3 credentials in env vars (should use IAM roles or Vault)
  - No audit log tamper detection (hash chain)
  - Email service uses long-lived API tokens
- Mitigations Planned
  - API rate limiting (v1.1)
  - Secrets manager integration (v1.2)
  - Audit log integrity hashing (v1.2)

#### `docs/api.md` (~250 lines)

Sections:
- Base URL: `/api`
- Auth: Bearer JWT
- Response Envelope: `{code, message, data, timestamp}`
- Endpoints Index (81 endpoints organized by module)
  - Auth (2): GET /auth/me, GET /auth/permissions
  - EA Review (12): CRUD for requests, attachments, AI check, stages
  - Meetings (5): CRUD, decks
  - Actions (4): CRUD
  - Applications (8): BCM, BizCapability, CMDB, BC visualization
  - Tech Stack (6): CRUD, lifecycle, compliance
  - ADD (12): Questionnaire, concern catalog, evaluation, artifacts
  - Projects (4): CRUD
  - Data Management (8): Master data, resources, certifications, dict options
  - Reports (4): Dashboard, reports, export
  - Shared (4): Audit log, email log, health
  - Admin (12): Team members, scope, schedules
- Error Codes
  - 401: Unauthenticated
  - 403: Forbidden
  - 404: Not found
  - 422: Validation error
  - 500: Internal error
- Pagination: `?page=1&page_size=20` → `{items, total, page, page_size}`

### 4.2 Updated Documents

| Document | Changes |
|----------|---------|
| `README.md` | AxisArch branding, updated architecture diagram, simplified setup |
| `docs/design.md` | De-branded, updated architecture, module renames |
| `docs/design-En.md` | Same |
| `docs/authorization.md` | Generic role names, updated RBAC matrix |
| `docs/module-splitting-plan.md` | Project name updated, module boundaries preserved |

---

## 5. Phase 3 — Harness Alignment

### 5.1 AGENTS.md Rewrite

Replace the entire 7-layer AxisRobo Agent template with actual AxisArch content:

- Product Identity: AxisArch
- Architecture: 3 Tiers (Frontend / Backend / Database)
- 6 Modules with descriptions
- Auth Model: Pluggable RBAC
- Development Verification commands: `npm run build` (frontend), `pytest` (backend)
- Documentation links: the actual files that exist
- Key Principles: Modular, RBAC-gated, auditable, plugin-first

### 5.2 CLAUDE.md

Sync with AGENTS.md (keep both aligned per convention).

### 5.3 OpenCode Agents

Create `.opencode/agents/` definitions:
- `code-reviewer.md`: Code review agent for AxisArch (TypeScript + Python conventions)
- `test-runner.md`: Test runner (pytest + Playwright)

### 5.4 Verification Commands

```sh
# Frontend build + lint
cd frontend && npm run lint && npm run build

# Backend tests
cd backend && python -m pytest

# API integration tests
cd api-tests && python -m pytest

# E2E tests
cd frontend && npx playwright test
```

---

## 6. Phase 4 — Clean Architecture Refactoring

### 6.1 Backend Layer Structure

```
backend/app/
├── domain/                    # Domain Layer (no dependencies)
│   ├── __init__.py
│   ├── review/                # EA Review domain
│   │   ├── entities.py        # ReviewRequest, Meeting, Action, Attachment
│   │   ├── value_objects.py   # ReviewStatus, ReviewResult, ArchitectureScore
│   │   └── repository.py      # ReviewRepository (abstract interface)
│   ├── application/           # App Management domain
│   │   ├── entities.py        # Application, BCMapping, BizCapability
│   │   └── repository.py
│   ├── add/                   # ADD domain (formerly AVDM)
│   │   ├── entities.py        # Concern, Viewpoint, Artifact, Assessment
│   │   └── repository.py
│   ├── project/               # Project domain
│   │   ├── entities.py        # Project, TeamMember
│   │   └── repository.py
│   ├── technology/            # Technology Stack domain
│   │   ├── entities.py        # TechStackItem, LifecycleStage
│   │   └── repository.py
│   └── shared/                # Shared domain
│       ├── base_entity.py     # BaseEntity (id, created_at, updated_at)
│       └── base_repository.py # Repository[T] generic interface
│
├── application/               # Application Layer (use cases)
│   ├── review/
│   │   ├── dto.py             # CreateRequestDTO, UpdateMeetingDTO, etc.
│   │   ├── services.py        # ReviewService, MeetingService, ActionService
│   │   └── workflows.py       # AIReviewWorkflow, StageTransitionWorkflow
│   ├── application/
│   │   ├── dto.py
│   │   └── services.py        # AppService, BCMService, CMDBService
│   ├── add/
│   │   ├── dto.py
│   │   └── services.py        # QuestionnaireService, AssessmentService
│   ├── project/
│   │   ├── dto.py
│   │   └── services.py
│   ├── technology/
│   │   ├── dto.py
│   │   └── services.py
│   └── shared/
│       ├── dto.py             # PaginationDTO, FilterDTO
│       └── services.py        # ExportService, AuditService
│
├── infrastructure/            # Infrastructure Layer (adapters)
│   ├── database/
│   │   ├── session.py         # Async SQLAlchemy session factory
│   │   ├── migrations.py      # Migration runner
│   │   └── repositories/      # Concrete repository implementations
│   │       ├── review_repo.py
│   │       ├── application_repo.py
│   │       ├── add_repo.py
│   │       └── ...
│   ├── storage/
│   │   ├── provider.py        # StorageProvider (abstract)
│   │   └── s3_provider.py     # S3StorageProvider (concrete)
│   ├── email/
│   │   ├── provider.py        # EmailProvider (abstract)
│   │   └── smtp_provider.py   # SMTPEmailProvider (concrete)
│   └── auth/
│       ├── provider.py        # AuthProvider (abstract)
│       ├── keycloak_provider.py
│       └── dev_provider.py
│
├── interfaces/                # Interface Layer (API, middleware)
│   ├── api/
│   │   ├── router.py          # Central router aggregator
│   │   ├── review_routes.py
│   │   ├── application_routes.py
│   │   ├── add_routes.py
│   │   └── ...
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── cors.py
│   │   └── envelope.py
│   └── schemas/
│       ├── request.py         # Pydantic request schemas
│       ├── response.py        # Pydantic response schemas
│       └── envelope.py        # ResponseEnvelope
│
├── plugins/                   # Enterprise Integration Plugins
│   ├── cmdb/
│   │   ├── provider.py        # CMDBProvider (abstract)
│   │   ├── lenovo_cmdb.py     # Lenovo CMDB adapter (example plugin)
│   │   └── scheduler.py       # CMDB sync scheduler
│   ├── email/
│   │   ├── provider.py        # Advanced Email Provider
│   │   └── bct_provider.py    # BCT Message API adapter (example)
│   ├── auth/
│   │   └── keycloak_plugin.py # Keycloak-specific extensions
│   └── agent_watch/
│       └── provider.py        # Agent Watch telemetry adapter
│
└── main.py                    # App entry point (DI wiring, lifespan)
```

### 6.2 Dependency Rule (Inward)

```
interfaces → application → domain ← infrastructure
                  ↓
              plugins (outward, optional)
```

- `domain/` depends on nothing
- `application/` depends on `domain/`
- `infrastructure/` depends on `domain/` (implements repository interfaces)
- `interfaces/` depends on `application/` and `domain/`
- `plugins/` depends on `infrastructure/` abstractions

### 6.3 Frontend Feature Structure

```
frontend/src/
├── features/                  # Feature modules (self-contained)
│   ├── review/                # EA Review feature
│   │   ├── pages/             # Page components
│   │   ├── components/        # Feature-specific components
│   │   ├── hooks/             # Feature-specific hooks
│   │   ├── api.ts             # Feature API client
│   │   ├── types.ts           # Feature types
│   │   └── index.ts           # Public exports
│   ├── portfolio/             # Application Portfolio (BCM/BizCapability/CMDB)
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── add/                   # Architecture Decision & Design
│   │   └── ...
│   ├── tech-stack/            # Technology Stack
│   │   └── ...
│   ├── projects/              # Project Management
│   │   └── ...
│   └── data-management/       # Master Data, Resources, Certifications
│       └── ...
│
├── shared/                    # Shared across features
│   ├── components/            # Design system components
│   │   ├── DataTable/
│   │   ├── StatusBadge/
│   │   ├── PermissionGate/
│   │   └── ...
│   ├── hooks/                 # Shared hooks
│   │   ├── useAuth.ts
│   │   ├── usePermission.ts
│   │   └── useMediaQuery.ts
│   ├── lib/                   # Utilities, API client, i18n
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── i18n.ts
│   └── types/                 # Shared TypeScript types
│
├── app/                       # Next.js App Router (thin routing layer)
│   ├── layout.tsx
│   ├── providers.tsx
│   ├── (review)/
│   │   ├── ea-review/page.tsx     → imports from features/review
│   │   └── reviewer/page.tsx
│   ├── (portfolio)/
│   │   └── app-management/page.tsx → imports from features/portfolio
│   └── ...
│
└── styles/
    └── globals.css
```

### 6.4 Plugin System Design

Plugins are optional integrations abstracted behind interfaces. Loaded at startup based on configuration.

```python
# plugins/__init__.py
class PluginRegistry:
    """Discovers and registers plugins based on settings."""
    
    def __init__(self, settings: Settings):
        self._providers: dict[str, Any] = {}
    
    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider
    
    def get(self, name: str) -> Any | None:
        return self._providers.get(name)

# In main.py lifespan:
plugin_registry = PluginRegistry(settings)

if settings.CMDB_API_URL:
    plugin_registry.register("cmdb", LenovoCMDBProvider(settings))
else:
    plugin_registry.register("cmdb", NoopCMDBProvider())

if settings.EMAIL_SERVICE_URL:
    plugin_registry.register("email", BCTEmailProvider(settings))
else:
    plugin_registry.register("email", SMTPEmailProvider(settings))
```

### 6.5 Migration Strategy (Incremental)

Per module, bottom-up:

1. **Extract domain entities** (no behavior change, just type definitions)
2. **Create repository interface** (abstract over raw SQL)
3. **Implement repository** (wrap existing SQL queries)
4. **Create application service** (move business logic out of router)
5. **Update router** (thin layer, delegates to service)
6. **Add tests** at each layer
7. **Repeat** for next module

Risk mitigation:
- Existing API contract preserved throughout
- All 201 API tests must continue passing after each module migration
- Database schema unchanged during P4 (table renames in a future migration)

---

## 7. File Inventory

### Files to Create

| File | Phase |
|------|-------|
| `docs/architecture.md` | P2 |
| `docs/STATUS.md` | P2 |
| `docs/ROADMAP.md` | P2 |
| `docs/threat-model.md` | P2 |
| `docs/api.md` | P2 |
| `.opencode/agents/code-reviewer.md` | P3 |
| `.opencode/agents/test-runner.md` | P3 |

### Files to Modify (by Phase)

| Phase | Count | Key Files |
|-------|-------|-----------|
| P1 | ~30 | config.py, README.md, .env files, main.py, all docs, all openspec specs |
| P2 | 5 | docs/design.md, docs/authorization.md, etc. (update existing docs) |
| P3 | 3 | AGENTS.md, CLAUDE.md, .opencode/** |
| P4 | ~50+ | All backend modules restructured, all frontend features reorganized |

### Files to Rename

| Old Path | New Path |
|----------|----------|
| `backend/app/avdm/` | `backend/app/domain/add/` (incrementally during P4) |
| `frontend/public/lenovo.png` | `frontend/public/axisarch.png` |
| `frontend/src/modules/architecture_review/` | `frontend/src/features/review/` (P4) |

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Renames break imports | Build failures | Use IDE refactoring tools; verify with `npm run build` + `pytest` after each batch |
| DB table rename breaks data | Data loss | Keep existing schema; only rename in new code/docs; create new migration for rename in P4 |
| P4 restructuring introduces bugs | Regression | Incremental per-module; run full test suite after each module |
| Config changes break local devs | Dev environment issues | Provide clear migration guide in `.env.example`; backward-compat fallbacks for old var names |
| OpenSpec specs become stale | Spec-code gap | Update specs alongside code changes; audit after each phase |
