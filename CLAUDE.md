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
