# AxisArch API Reference

> **Last verified:** 2026-06-27  |  **Source:** FastAPI OpenAPI (backend/app)

## Base
- Base URL: `/api`
- Auth: Bearer JWT (Keycloak OIDC in EE mode, local JWT when `AUTH_MODE=local`) or Dev-mode fixed user
- Content-Type: `application/json`
- Envelope: `{"code": <http_status>, "message": "...", "data": {...}}`

## Authentication

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/auth/me` | Current user info + roles + permissions | Login |
| GET | `/api/auth/permissions` | Flat permission list for current user | Login |

## EA Review

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/ea-requests` | List requests (paginated, filterable) | `ea_request:read` |
| POST | `/api/ea-requests` | Create request | `ea_request:write` |
| GET | `/api/ea-requests/{id}` | Get request detail | `ea_request:read` |
| PUT | `/api/ea-requests/{id}` | Update request | `ea_request:write` |
| DELETE | `/api/ea-requests/{id}` | Delete request | `ea_request:write` |
| GET | `/api/ea-requests/dashboard` | Dashboard aggregations | `ea_request:read` |
| POST | `/api/ea-requests/attachments/upload` | Upload attachment | `ea_request:write` |
| GET | `/api/ea-requests/attachments/{id}/file` | Download attachment file | `ea_request:read` |
| GET | `/api/ea-requests/attachments/{id}/download` | Download attachment (alt) | `ea_request:read` |
| DELETE | `/api/ea-requests/attachments/{id}` | Delete attachment | `ea_request:write` |
| POST | `/api/ea-requests/attachments/ai-check` | Trigger AI architecture check | `ea_request:write` |
| GET | `/api/ea-requests/filter-options` | Distinct filter option values | `ea_request:read` |
| GET | `/api/ea-requests/{id}/concerns` | AVDM concerns derived for an EA request | `ea_request:read` |
| GET | `/api/ea-requests/{id}/viewpoints` | AVDM viewpoints derived through concern-to-viewpoint mapping | `ea_request:read` |

## Meetings & Decks

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/meetings` | List meetings | `meeting:read` |
| POST | `/api/meetings` | Create meeting | `meeting:write` |
| GET | `/api/meetings/{meeting_no}` | Get meeting detail | `meeting:read` |
| PUT | `/api/meetings/{meeting_no}` | Update meeting | `meeting:write` |
| DELETE | `/api/meetings/{meeting_no}` | Delete meeting | `meeting:write` |
| POST | `/api/meetings/{meeting_no}/cancel` | Cancel meeting | `meeting:write` |
| POST | `/api/meetings/{meeting_no}/set-ea-review-result` | Set EA review result | `meeting:write` |
| POST | `/api/meetings/{meeting_no}/send-minute` | Send meeting minutes | `meeting:write` |
| GET | `/api/meetings/{meeting_no}/decks` | List meeting decks | `meeting_deck:read` |
| POST | `/api/meetings/{meeting_no}/decks` | Add deck file | `meeting_deck:write` |
| DELETE | `/api/meetings/{meeting_no}/decks/{deck_id}` | Delete deck file | `meeting_deck:write` |
| GET | `/api/meetings/attendees-template` | Download attendees template | `meeting:read` |
| POST | `/api/meetings/parse-attendees` | Parse attendees from file | `meeting:write` |

## Actions

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/actions` | List actions | `action:read` |
| POST | `/api/actions` | Create action | `action:write` |
| PUT | `/api/actions/{id}` | Update action | `action:write` |
| DELETE | `/api/actions/{id}` | Delete action | `action:write` |
| GET | `/api/actions/{id}/comments` | List action comments | `action:read` |
| POST | `/api/actions/{id}/comments` | Add action comment | `action_comment:write` |
| GET | `/api/actions/{id}/audit-logs` | Action audit trail | `action:read` |

## Architecture Check (AI)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/arch-check-apps` | List AI-checked apps | `ea_request:read` |
| POST | `/api/arch-check-apps/confirm` | Confirm arch check apps | `ea_request:write` |
| PUT | `/api/arch-check-apps/{uuid}` | Update arch check app | `ea_request:write` |
| DELETE | `/api/arch-check-apps/{uuid}` | Delete arch check app | `ea_request:write` |
| GET | `/api/arch-check-interactions` | List AI-checked interactions | `ea_request:read` |
| POST | `/api/arch-check-interactions/confirm` | Confirm arch check interactions | `ea_request:write` |
| PUT | `/api/arch-check-interactions/{uuid}` | Update arch check interaction | `ea_request:write` |
| DELETE | `/api/arch-check-interactions/{uuid}` | Delete arch check interaction | `ea_request:write` |

## ADD / AVDM

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/avdm/questionnaire-config` | Get questionnaire config | `avdm:read` |
| PUT | `/api/avdm/questionnaire-config` | Update questionnaire config | EA_ADMIN |
| GET | `/api/avdm/concern-mapping-config` | Get concern mapping config | `avdm:read` |
| PUT | `/api/avdm/concern-mapping-config` | Update concern mapping config | EA_ADMIN |
| GET | `/api/avdm/artifact-catalog-config` | Get artifact catalog config | `avdm:read` |
| PUT | `/api/avdm/artifact-catalog-config` | Update artifact catalog config | EA_ADMIN |
| GET | `/api/avdm/viewpoint-artifact-mapping-config` | Get viewpoint-artifact mapping | `avdm:read` |
| PUT | `/api/avdm/viewpoint-artifact-mapping-config` | Update viewpoint-artifact mapping | EA_ADMIN |
| GET | `/api/avdm/concern-viewpoint-mapping` | List concern-to-viewpoint mappings, or unmapped concerns with `includeUnmapped=true` | `avdm:read` |
| GET | `/api/avdm/viewpoints` | List viewpoint catalog | `avdm:read` |
| GET | `/api/avdm/concerns` | List concern catalog | `avdm:read` |
| PUT | `/api/avdm/concerns` | Upsert concern | EA_ADMIN |
| GET | `/api/avdm/concerns/export` | Export concern catalog | `avdm:read` |
| POST | `/api/avdm/evaluate` | Evaluate project risks | `avdm:write` |
| POST | `/api/avdm/review` | Apply review overrides | `avdm:write` |
| GET | `/api/avdm/statistics` | AVDM assessment statistics | `avdm:read` |
| GET | `/api/avdm/projects/{projectId}` | Get project assessment | `avdm:read` |
| POST | `/api/avdm/projects/{projectId}/questionnaire` | Submit questionnaire | `avdm:write` |
| POST | `/api/avdm/projects/{projectId}/judge` | Judge AVDM need | `avdm:write` |
| GET | `/api/avdm/projects/{projectId}/workflow-status` | Get workflow status | `avdm:read` |
| GET | `/api/avdm/projects/{projectId}/artifacts/recommendation` | Get artifact recommendations | `avdm:read` |
| PUT | `/api/avdm/projects/{projectId}/artifacts` | Save artifact selection | `avdm:write` |
| POST | `/api/avdm/projects/{projectId}/questionnaire/confirm` | Confirm questionnaire | `avdm:write` |
| POST | `/api/avdm/projects/{projectId}/concerns/confirm` | Confirm concern requirements | `avdm:write` |
| POST | `/api/avdm/projects/{projectId}/artifacts/requirements/confirm` | Confirm artifact requirements | `avdm:write` |

## AI Assessment

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/ai-assessment` | List assessments (paginated) | `avdm:read` |
| GET | `/api/ai-assessment/meta` | Self-assessment metadata | `avdm:read` |
| POST | `/api/ai-assessment` | Create assessment | `avdm:write` |
| GET | `/api/ai-assessment/{id}` | Get assessment with self-assessment + checklist | `avdm:read` |
| PUT | `/api/ai-assessment/{id}/self-assessment` | Save self-assessment | `avdm:write` |
| PUT | `/api/ai-assessment/{id}/checklist` | Save review checklist | `avdm:write` |
| DELETE | `/api/ai-assessment/{id}` | Delete assessment (admin) | EA_ADMIN |

## AI Model Registry

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/ai-models/meta` | Registry metadata (types, statuses, provenance sources) | `avdm:read` |
| GET | `/api/ai-models` | List models (paginated, `q` / `status` filters) | `avdm:read` |
| POST | `/api/ai-models` | Register a model | `avdm:write` |
| GET | `/api/ai-models/{id}` | Get model with versions | `avdm:read` |
| PUT | `/api/ai-models/{id}` | Update model metadata | `avdm:write` |
| DELETE | `/api/ai-models/{id}` | Delete model (admin, cascades versions) | EA_ADMIN |
| POST | `/api/ai-models/{id}/versions` | Add a model version (provenance + production gating) | `avdm:write` |
| PUT | `/api/ai-models/{id}/versions/{versionId}` | Update a model version | `avdm:write` |
| DELETE | `/api/ai-models/{id}/versions/{versionId}` | Delete a model version (admin) | EA_ADMIN |

## AI Agent Registry

Design-time registration & governance of AI agents as governed architecture elements (NOT runtime agent identity).

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/ai-agents/meta` | Registry metadata (types, autonomy, trust, capabilities, lethal trifecta) | `avdm:read` |
| GET | `/api/ai-agents` | List agents (paginated, `q` / `status` filters) | `avdm:read` |
| POST | `/api/ai-agents` | Register an agent | `avdm:write` |
| GET | `/api/ai-agents/{id}` | Get agent governance record | `avdm:read` |
| PUT | `/api/ai-agents/{id}` | Update agent (lethal-trifecta HITL approval gate) | `avdm:write` |
| DELETE | `/api/ai-agents/{id}` | Delete agent (admin) | EA_ADMIN |

## MCP Governance

Registration, approval, and provenance governance for MCP servers and their tools.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/mcp-servers/meta` | Registry metadata (transports, auth methods, tool lifecycle) | `avdm:read` |
| GET | `/api/mcp-servers` | List MCP servers (paginated, `q` / `status` filters) | `avdm:read` |
| POST | `/api/mcp-servers` | Register an MCP server | `avdm:write` |
| GET | `/api/mcp-servers/{id}` | Get server with tools | `avdm:read` |
| PUT | `/api/mcp-servers/{id}` | Update server (provenance approval gate) | `avdm:write` |
| DELETE | `/api/mcp-servers/{id}` | Delete server (admin, cascades tools) | EA_ADMIN |
| POST | `/api/mcp-servers/{id}/tools` | Add a tool (hash-pinned + production gate) | `avdm:write` |
| PUT | `/api/mcp-servers/{id}/tools/{toolId}` | Update a tool | `avdm:write` |
| DELETE | `/api/mcp-servers/{id}/tools/{toolId}` | Delete a tool (admin) | EA_ADMIN |

## Application Portfolio

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/applications/bcm` | Business capability mapping list | `bcm:read` |
| POST | `/api/applications/bcm` | Create BCM entry | `bcm:write` |
| PUT | `/api/applications/bcm/{id}` | Update BCM entry | `bcm:write` |
| DELETE | `/api/applications/bcm/{id}` | Delete BCM entry | `bcm:write` |
| GET | `/api/applications/bcm/visualization` | BC analysis data | `bcm:read` |
| GET | `/api/applications/bcm/app/{appId}` | BCM entries for an application | `bcm:read` |
| GET | `/api/applications/bcm/bc-tree` | BC tree structure | `bcm:read` |
| GET | `/api/applications/bcm/filter-options` | BCM filter option values | `bcm:read` |
| GET | `/api/applications/bcm/versions` | BCM data versions | `bcm:read` |
| GET | `/api/applications/bcm/export` | Export BCM to XLSX | `bcm:read` |
| GET | `/api/applications/cmdb` | CMDB application list (alt) | `cmdb:read` |
| GET | `/api/biz-capability` | BizCapability master data | `biz_capability:read` |
| POST | `/api/biz-capability` | Create BizCapability | `biz_capability:write` |
| GET | `/api/biz-capability/filter-options` | BizCapability filter values | `biz_capability:read` |
| GET | `/api/biz-capability/versions` | BizCapability data versions | `biz_capability:read` |
| GET | `/api/biz-capability/export` | Export BizCapability to XLSX | `biz_capability:read` |
| POST | `/api/biz-capability/import/validate` | Validate import data | `biz_capability:write` |
| POST | `/api/biz-capability/import` | Import BizCapability data | `biz_capability:write` |
| GET | `/api/cmdb` | CMDB application list / search | `cmdb:read` |
| GET | `/api/cmdb/{app_id}` | CMDB application detail | `cmdb:read` |
| POST | `/api/cmdb/sync` | Trigger CMDB sync manually | EA_ADMIN |

## Technology Stack

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/technology-stack` | List tech stack master data | `tech_stack_master:read` |
| POST | `/api/technology-stack` | Create tech stack entry | `tech_stack_master:write` |
| PUT | `/api/technology-stack/{id}` | Update tech stack entry | `tech_stack_master:write` |
| DELETE | `/api/technology-stack/{id}` | Soft delete entry | `tech_stack_master:write` |
| GET | `/api/technology-stack/categories` | Category/subcategory options | `tech_stack_master:read` |
| GET | `/api/technology-stack/lifecycle` | Lifecycle management list | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/apps/{appId}` | App tech stack detail | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/apps/{appId}/catalog` | App catalog items | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/apps/{appId}/team-members` | App team members | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/apps/{appId}/operate-log` | App operation log | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/resource-pool` | Resource pool lookup | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/cmdb-lookup` | CMDB app lookup | `tech_stack_lifecycle:read` |
| GET | `/api/technology-stack/master-options` | Master data options | `tech_stack_lifecycle:read` |
| POST | `/api/technology-stack/apps` | Register app in tech stack | `tech_stack_lifecycle:write` |
| DELETE | `/api/technology-stack/apps/{appId}` | Remove app from tech stack | `tech_stack_lifecycle:write` |
| POST | `/api/technology-stack/apps/{appId}/catalog` | Add catalog item | `tech_stack_lifecycle:write` |
| PUT | `/api/technology-stack/apps/{appId}/catalog/{itemId}` | Update catalog item | `tech_stack_lifecycle:write` |
| DELETE | `/api/technology-stack/apps/{appId}/catalog/{itemId}` | Delete catalog item | `tech_stack_lifecycle:write` |
| POST | `/api/technology-stack/apps/{appId}/checking` | Trigger compliance check | `tech_stack_lifecycle:write` |
| POST | `/api/technology-stack/apps/{appId}/team-members` | Add team member | `tech_stack_lifecycle:write` |
| DELETE | `/api/technology-stack/apps/{appId}/team-members/{memberId}` | Remove team member | `tech_stack_lifecycle:write` |
| POST | `/api/technology-stack/import` | Import master data (CSV) | `tech_stack_master:write` |

## Projects

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/projects` | List projects | `project:read` |
| POST | `/api/projects` | Create project | `project:write` |
| GET | `/api/projects/{projectId}` | Get project detail | `project:read` |
| PUT | `/api/projects/{projectId}` | Update project | `project:write` |
| POST | `/api/projects/change-favourite` | Toggle project favourite | `project:write` |
| GET | `/api/projects/{projectId}/applications` | Project applications | `project:read` |
| POST | `/api/projects/{projectId}/applications/{appId}` | Link application to project | `project:write` |
| DELETE | `/api/projects/{projectId}/applications/{appId}` | Unlink application from project | `project:write` |
| GET | `/api/projects/{projectId}/tasks` | Project tasks / EA requests | `project:read` |

## Team Members

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/team-members` | List team members (paginated) | `team_member:read` |
| POST | `/api/team-members` | Add team member | `team_member:write` |
| PUT | `/api/team-members/{itcode}` | Update team member | `team_member:write` |
| DELETE | `/api/team-members/{itcode}` | Delete team member | `team_member:write` |

## Data Management

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/master-data/{type}` | Get master data by type | `master_data:read` |
| POST | `/api/master-data/{type}` | Create master data entry | `master_data:write` |
| GET | `/api/master-data/companies` | Company master data | `master_data:read` |
| GET | `/api/master-data/data-centers` | Data center master data | `master_data:read` |
| GET | `/api/master-data/data-classification` | Data classification master data | `master_data:read` |
| GET | `/api/master-data/legal-entities` | Legal entity master data | `master_data:read` |
| GET | `/api/master-data/help-files` | Help/documentation files | `master_data:read` |
| GET | `/api/resources` | Resource pool lookup | `resource:read` |
| GET | `/api/resources/search` | Resource search by keyword | `resource:read` |

## Reports & Export

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/reports/lead-time` | Lead time report data | `report:read` |
| GET | `/api/reports/{type}` | Report data by type | `report:read` |
| GET | `/api/export/{entity}` | CSV/Excel export | `export:execute` |

## EA Review Logs

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/ea-review-logs` | EA review process logs | `ea_review_log:read` |

## Shared

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (no auth) |

## Pagination

All list endpoints support: `?page=1&pageSize=20`

Response format: `{"code": 200, "message": "success", "data": {"items": [...], "total": 150, "page": 1, "pageSize": 20}}`

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation) |
| 401 | Unauthenticated — missing/invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 500 | Internal server error |

## Notes

- The `ENABLED_MODULES` env var controls which module routers are registered at startup.
- With `AUTH_MODE=local` (OSS), local JWT auth is enabled with three roles and RBAC permission checks are enforced — no `EE_ENABLED` required.
- When auth is fully disabled (`AUTH_MODE=disabled` / `EE_ENABLED=false`), RBAC permission checks are bypassed and any user can access all endpoints.
- In EE mode, the Auth column above indicates the required `resource:scope` permission. Wildcard (`*`) role (EA_ADMIN) bypasses all checks.
- The `ADD` module is registered under the key `add` in `ENABLED_MODULES` but served at prefix `/api/avdm`.
- The `/api/tech-stack` prefix was removed in favor of `/api/technology-stack` for API calls. Frontend page navigation still uses `/tech-stack` (Next.js routes).
