# AxisRobo-PAMP — Enterprise Architecture Management Platform

A modular, extensible platform for enterprise architecture management — EA review workflows, application portfolio management, business capability analysis, architecture decision & design (ADD), PACT concern catalog, viewpoint/artifact mapping, and reporting.

AxisRobo-PAMP was sparked by the **PAMF series of papers** (PACT, AVDM, AADM, ARCM) and shaped by years of enterprise architecture practice. It is built not only around what ships today, but toward a long-term vision for architecture governance — spanning domain capability coverage and platform evolution through the v3.x horizon. See the [Roadmap](docs/ROADMAP.md) for that vision, beyond the currently implemented feature set.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16.2 (Turbopack), React 19, TanStack Query, Ant Design v6, Tailwind CSS |
| Backend | FastAPI (Python 3.12+), SQLAlchemy asyncpg, Raw SQL via `text()` |
| Database | PostgreSQL 14+, 98 tables in `eam` schema |
| Auth | Pluggable: OSS local (JWT + bcrypt), Keycloak SSO (EE), Dev mode. RBAC (3 roles, 24 resources) |
| Storage | Pluggable: S3-compatible or database-backed (`eam_file_storage`) |
| Testing | pytest (backend + API integration), Playwright (E2E) |

## Quick Start

### Prerequisites
- Node.js >= 22.0.0
- Python >= 3.12
- PostgreSQL 14+

### Setup

```bash
# Clone
git clone <repo-url>
cd AXISRobo-PAMP

# Install frontend
cd frontend && npm install

# Setup backend
cd ../backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure
cp backend/.env.example backend/.env
```

### Start Database

```bash
docker run -d --name axisarch-pg \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=axisarch \
  -p 5432:5432 postgres:16
```

### Initialize Schema & Seed Data

The database schema and AVDM seed data are maintained as SQL scripts under [`docs/SQL/`](docs/SQL/). Create the `eam` schema, load the table DDL, then load the AVDM seed data:

```bash
# Connection string matches the docker container above (db: axisarch)
PG="postgresql://postgres:postgres@localhost:5432/axisarch"

# 1. Create the eam schema
psql "$PG" -c "CREATE SCHEMA IF NOT EXISTS eam;"

# 2. Load all table definitions
psql "$PG" -f docs/SQL/eam_schema_ddl.sql

# 3. Load AVDM seed data (concerns, viewpoints, artifacts, mappings)
psql "$PG" -f docs/SQL/avdm_schema_seed.sql
```

### Run

```bash
# Backend (port 4000)
cd backend && python -m uvicorn app.main:app --port 4000 --reload

# Frontend (port 3000)
cd frontend && npm run dev
```

## Auth Configuration

| Mode | `AUTH_MODE` | Description |
|------|-------------|-------------|
| **Dev** | `dev` | Fixed admin user (`AUTH_DEV_USER`), no auth required |
| **Local (OSS)** | `local` | Username/password + JWT, users stored in `eam.local_users` |
| **OIDC (EE)** | `oidc` | Keycloak SSO with JWT validation |

### Local Auth (OSS)

```env
# backend/.env
AUTH_MODE=local
JWT_SECRET_KEY=change-me-in-production

# frontend/.env
NEXT_PUBLIC_AUTH_MODE=local
```

Default admin: `admin` / `admin123`

Admin can manage users at `/api/users` (CRUD endpoints) or via the Admin workspace.

### Dev Mode

Set `AUTH_MODE=dev` in backend/.env to skip authentication during development. All requests use the default admin user.

## Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access (`*:*`), user CRUD, all data management pages |
| **Reviewer** | Review assigned EA requests, manage meetings, actions, BCM |
| **Requestor** | Create and manage own EA requests and projects |

## Modules

| Module | Description |
|--------|-------------|
| **EA Review** | Architecture review workflow, meetings, actions, AI architecture checks, AVDM questionnaire |
| **ADD — Architecture Decision & Design** | PACT concern catalog, viewpoint catalog, concern-to-viewpoint mapping, viewpoint-to-artifact mapping, questionnaire config, risk scoring, architecture governance matrix |
| **AI Self-Assessment** | AI project self-assessment aligned with Enterprise AI Security Architecture Guideline v2.4 — AT0-AT8 adoption tier × L0-L4 governance maturity matrix, 11-section 49-item checklist, counterparty type (CP1-CP4) governance contexts |
| **Application Portfolio** | BCM, BizCapability, CMDB — business capability mapping |
| **Technology Stack** | Tech stack lifecycle, compliance checking |
| **Project Management** | Project CRUD, team management |
| **Data Management** | Enterprise data governance — master data, data classification, data flow, data-application mapping, resources, certifications |

Modules selectively enabled via `ENABLED_MODULES` env var.

## Architecture

```
Browser → Next.js :3000 → FastAPI :4000 → PostgreSQL :5432
                                         → S3 / eam_file_storage (attachments)
                                         → LLM API (AI architecture review)
```

### Key Design Principles

1. **Modular by contract** — Each module self-contained with own DB access
2. **Deny by default** — All 81+ API endpoints RBAC-gated via `require_permission(resource, scope)`
3. **Audit everything** — Append-only `eam_audit_log` with `audit_allow()` / `audit_deny()` hooks
4. **Plugin-first** — Auth providers, email services, CMDB connectors, and storage backends are abstracted behind interfaces
5. **Raw SQL over ORM** — SQLAlchemy `text()` for performance; Pydantic for request/response validation
6. **Storage abstraction** — S3-compatible when configured, database-backed (`eam_file_storage`) when not

### AVDM Decision Chain

AXISRobo-PAMP implements AVDM as a configurable decision chain:

```
Questionnaire Answer
    → Risk Signal / Architecture Concern Activation
    → Concern Score Aggregation
    → Viewpoint Classification
    → Artifact Recommendation
```

The questionnaire captures project scale, complexity, change scope, and architecture type. Selected answers activate architecture concerns through weighted mapping rules. Activated concerns are then projected onto the viewpoint taxonomy through concern-to-viewpoint mappings. Finally, each selected viewpoint is mapped to one or more supporting artifacts, such as diagrams, lists, or matrices.

Canonical chain: `Questionnaire → Concern → Viewpoint → Artifact`.

Multiple concerns may map to the same viewpoint, and a single concern may activate multiple viewpoints. Artifacts are derived exclusively through viewpoints — there is no direct concern-to-artifact mapping. The viewpoint layer is the single source of truth for which artifacts a concern requires.

## API

81+ endpoints, all RBAC-gated. Swagger UI at `http://localhost:4000/docs`.

See [docs/api.md](docs/api.md) for full reference.

## Storage

| Backend | Config | Use Case |
|---------|--------|----------|
| **S3** | Set `S3_ENDPOINT` | Production, enterprise deployments |
| **Database** | S3 not configured (default) | Local development, OSS deployments |

Files stored in `eam.eam_file_storage` table when S3 is unavailable.

## Database

98 tables across the `eam` schema. Complete documentation at [docs/database-schema.md](docs/database-schema.md).

```bash
# Generate fresh schema documentation
cd backend && python ../scripts/generate_db_schema_doc.py
```

## Testing

```bash
# API integration tests
cd api-tests && python -m pytest

# Backend unit tests
cd backend && python -m pytest

# Frontend E2E
cd frontend && npx playwright test
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/architecture.md](docs/architecture.md) | System architecture |
| [docs/api.md](docs/api.md) | API reference |
| [docs/STATUS.md](docs/STATUS.md) | Completion status |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Development roadmap |
| [docs/threat-model.md](docs/threat-model.md) | Security threat model |
| [docs/design.md](docs/design.md) | Detailed design (Chinese) |
| [docs/database-schema.md](docs/database-schema.md) | Complete DB schema (98 tables) |
| [docs/SQL/eam_schema_ddl.sql](docs/SQL/eam_schema_ddl.sql) | Complete schema DDL — `CREATE TABLE` definitions for all tables |
| [docs/SQL/avdm_schema_seed.sql](docs/SQL/avdm_schema_seed.sql) | AVDM schema + seed data (concerns, viewpoints, artifacts, mappings) |
| [docs/authorization.md](docs/authorization.md) | Auth model: RBAC + record-level ownership |
| [docs/standards/](docs/standards/) | Coding conventions |

## Superpowers Specs & Plans

| Doc | Description |
|-----|-------------|
| [docs/superpowers/specs/2026-06-23-local-auth-design.md](docs/superpowers/specs/2026-06-23-local-auth-design.md) | OSS local auth design |
| [docs/superpowers/specs/2026-06-23-concern-artifact-expand-design.md](docs/superpowers/specs/2026-06-23-concern-artifact-expand-design.md) | Concern & Artifact expandable view |
| [docs/superpowers/plans/2026-06-23-local-auth-plan.md](docs/superpowers/plans/2026-06-23-local-auth-plan.md) | Local auth implementation plan |
| [docs/superpowers/plans/2026-06-23-concern-artifact-expand-plan.md](docs/superpowers/plans/2026-06-23-concern-artifact-expand-plan.md) | Concern/Artifact expand implementation plan |
| [docs/superpowers/plans/2026-06-22-global-optimization.md](docs/superpowers/plans/2026-06-22-global-optimization.md) | Global optimization |

## Citing AXISRobo-PAMP

If you use AXISRobo-PAMP in your research, please cite the related papers:

**[1]** Han, H. *PACT: A Reference Viewpoint Taxonomy for Software-Intensive Systems*. Preprints 2026, 2026010720. [DOI: 10.20944/preprints202601.0720.v1](https://doi.org/10.20944/preprints202601.0720.v1)

**[2]** Han, H. *AVDM: A Risk-Informed Decision Model for Architecture Viewpoint Selection*. TechRxiv, 27 January 2026. [DOI: 10.36227/techrxiv.176948759.92525674/v1](https://doi.org/10.36227/techrxiv.176948759.92525674/v1)

**[3]** Han, H. *AADM: An Architecture Artifact Decision Model for Risk-Aware Documentation Scope*. TechRxiv, 27 January 2026. [DOI: 10.36227/techrxiv.176948904.46258539/v1](https://doi.org/10.36227/techrxiv.176948904.46258539/v1)

**[4]** Han, H. *ARCM: Responsibility Configuration in Multi-View Architecture Descriptions*. TechRxiv, 27 January 2026. [DOI: 10.36227/techrxiv.176948938.83267225/v1](https://doi.org/10.36227/techrxiv.176948938.83267225/v1)

**[5]** Han, H. *AXISRobo-PAMP: An Open-Source Enterprise Architecture Management Platform*. GitHub repository, 2026. [Online]. Available: https://github.com/axisrobo/AXISRobo-PAMP

## License

MIT
