# PAMF Project Status

> Last verified: 2026-06-24

## Module Completion

| Module | Backend | Frontend | API Endpoints | Status |
|--------|---------|----------|---------------|--------|
| Auth & RBAC | `app/auth/` | `shared/lib/auth-context.tsx` | 3 | Complete |
| EA Review | `app/architecture_review/` | `(architecture_review)/` | ~15 | Complete |
| Application Portfolio | `app/application_management/` | `(application_management)/` | ~12 | Complete |
| ADD (AVDM) | `app/add/` | `(add_config)/` | 28 | Complete |
| AI Assessment | `app/ai_assessment/` | `(add_config)/ai-assessment/` | 7 | Complete |
| Technology Stack | `app/technology_stack_management/` | `(technology_stack_management)/` | ~22 | Complete |
| Project Management | `app/project_management/` | `(project_management)/` | 6 | Complete |
| Data Management | `app/data_management/` | `(data_management)/` | ~4 | Complete |
| AI Review Agent | `app/architecture_review/ai.py` | review components | 2 | Complete |

Total: ~95 API endpoints, 160+ FastAPI routes.

## Recent Changes (2026-06-24)

- **AI Self-Assessment**: Full AI project self-assessment module — AT0-AT8 adoption tier × L0-L4 governance maturity matrix, 11-section 49-item architecture review checklist, counterparty type (CP1-CP4) governance contexts, automated matrix positioning with go/no-go guidance. Aligned with *Enterprise AI Security Architecture Guideline v2.4*.
- **Auth**: OSS local auth mode (`AUTH_MODE=local`) with username/password + JWT, 3 roles (admin/reviewer/requestor), `eam.local_users` table, user CRUD endpoints
- **Storage**: Database-backed file storage (`eam.eam_file_storage`) as fallback when S3 not configured
- **AVDM Data Chain**: Populated 45 viewpoints (from CSV), 76 concern→artifact direct mappings, 74 viewpoint→artifact mappings, 57 B-class question concern mappings. Three-tier question ID scheme (A1-A25, B1-B29, C1-C15).
- **Frontend**: OSS login page, AVDM config pages moved to `(add_config)` route group, expandable concern/artifact views in EA Review, concern-artifact/concern-viewpoint mapping pages
- **DB**: Renumbered `stable_question_id` to contiguous 1-69, `avdm_pact_concern` column restore, search_path fix for asyncpg
- **Docs**: README updated with local auth/DB storage/AVDM chain, roadmap v2.0-v3.0 for EA governance platform, database schema doc (98 tables), AI security guideline integration

## Known Gaps

- Concern→viewpoint mapping: CSV data source UUID mismatch prevents import; 0 rows until source DB concern table exported
- Dual project table architecture (`eam.project` vs `eam.eam_project`): GET unified via COALESCE fallback; UPDATE/DELETE still use legacy `eam.project` only
- CSRF protection: not implemented (JWT Bearer only)
- Rate limiting: AI review endpoint has no throttling
- Frontend unit tests: no Vitest setup
- i18n extraction: strings inline in JSX, no key-based tooling

## Tech Debt (prioritized)

| Item | Effort | Priority |
|------|--------|----------|
| Unify dual-project-table architecture | 2 days | High |
| Frontend unit test setup (Vitest) | 1 day | High |
| AI Self-Assessment: add counterparty-specific checklist sections | 0.5 day | Medium |
| Rate limiting on AI endpoint | 1 day | Medium |
| i18n extraction framework | 5 days | Low |
