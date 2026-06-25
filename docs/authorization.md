# Authorization Model

## Overview

AxisArch uses a hybrid baseline + scoped authorization model. Every authenticated
user receives a baseline role. Scoped business roles are resolved at login
and grant additional authority over specific record categories.

The backend is the final enforcement point. Frontend gating hides or disables
UI elements but does not replace server-side checks.

> **Auth modes:** Setting `AUTH_MODE=local` enables the OSS local JWT provider
> (backed by the `local_users` table) with three built-in roles and full RBAC
> enforcement — `EE_ENABLED` is **not** required. The Keycloak OIDC provider is
> used in EE deployments, and `AUTH_MODE=disabled` bypasses RBAC entirely for
> local development.

## Roles

| Role | Type | Source | Description |
|------|------|--------|-------------|
| `Normal_User` | Baseline | Automatic | Granted to every authenticated user |
| `EA_Admin` | Baseline | Keycloak group/claim | Unrestricted platform access |
| `EA_Reviewer` | Scoped | `eam_bigea_team_members` table | Can complete reviews on assigned EA requests |
| `App_Owner` | Scoped | `cmdb_application` + `application_member` | Can maintain BCM and lifecycle data for owned applications |
| `Project_Owner` | Scoped | `eam_project` table | Can maintain owned project data |

Scoped roles are additive. A user with `EA_Reviewer` also has all
`Normal_User` permissions.

## Role Resolution Pipeline

1. **Keycloak JWT** is decoded by `AuthMiddleware`
2. **Baseline roles** are assigned:
   - `Normal_User` is always added
   - `EA_Admin` is added if the user's Keycloak claims include the admin group
3. **Scoped roles** are resolved from the database by `role_resolver.resolve_scoped_roles()`:
   - `EA_Reviewer`: user's itcode exists in `eam_bigea_team_members`
   - `App_Owner`: user's itcode matches `cmdb_application.app_dt_owner`,
     `cmdb_application.app_operation_owner`, `cmdb_application.app_it_owner`,
     or `application_member.itcode` (matched by lowercase email prefix)
4. The final `AuthUser` is attached to `request.state.user`

## Two-Layer Authorization

### Layer 1: Feature-Level RBAC

Defined in `app/auth/rbac.py` as a static permission matrix.

Enforced by the `require_permission(resource, scope)` dependency on router
endpoints. This checks whether any of the user's roles grant the requested
`resource:scope` pair.

Key rules:
- `EA_Admin` has wildcard `*:*` (all resources, all scopes)
- `Normal_User` has `read` on everything, `write` only on `ea_request`
- `EA_Reviewer` adds `write` on EA review resources (`meeting`, `action`, `scope`, etc.)
- `App_Owner` adds `write` on `application`, `bcm`, `tech_stack`

### Layer 2: Record-Level Ownership

Enforced by helpers in `app/auth/ownership.py`, called inside router
endpoint handlers after the RBAC gate passes.

| Check | Function | When Used |
|-------|----------|-----------|
| Creator ownership | `check_request_creator()` | Update/submit/delete own EA request |
| Draft status | `check_request_draft_status()` | Submit or delete (must be Draft) |
| Reviewer assignment | `check_reviewer_assignment()` | Review actions on assigned request |
| App ownership | `check_app_ownership()` | BCM and lifecycle mutations |
| Project access | `check_request_access_by_project()` | EA review sub-resources (actions, meetings, scope) |
| Request access | `check_request_access_by_request_id()` | EA review sub-resources by request key |

All ownership checks:
- Return the record or `True` on success
- Raise `HTTPException(403)` on denial (which triggers `audit_deny` in the
  helper's logging)
- Allow `EA_Admin` to bypass unconditionally

## Audit Logging

Write operations are audited via `app/auth/audit.py` in both log and database:

- `audit_allow(user, action, resource_type, resource_id, scope_basis)` — logged at
  `INFO` level and written to `eam.eam_audit_log` table on successful write operations
- `audit_deny(user, action, resource_type, resource_id, reason)` — logged at
  `WARNING` level and written to `eam.eam_audit_log` table on authorization failures

Audit events are persisted in the append-only `eam.eam_audit_log` database table
with fields: `id` (UUID), `user_id`, `roles` (JSONB), `resource`, `action`,
`decision` (allow/deny), `reason`, `created_at`.

## Frontend Authorization

The frontend uses the `useAuth()` hook from `lib/auth-context.tsx` which
provides:

- `hasPermission(resource, scope)` — checks the user's permission list
- `hasRole(...roles)` — checks if the user has any of the listed roles

Mutation buttons (Add, Edit, Delete, etc.) are conditionally rendered:

```tsx
const { hasPermission } = useAuth();
const canWrite = hasPermission('bcm', 'write');

{canWrite && <button>Add</button>}
```

The `PermissionGate` component provides declarative gating:

```tsx
<PermissionGate resource="bcm" scope="write">
  <button>Add</button>
</PermissionGate>
```

## Adding a New Protected Endpoint

1. Add `require_permission("resource", "scope")` as a dependency on the route
2. Inside the handler, call the appropriate ownership check if record-level
   authorization is needed
3. Use `user.id` as `create_by` instead of accepting it from the request body
4. Call `audit_allow()` after a successful write operation
5. On the frontend, gate mutation buttons with `hasPermission()` or
   `PermissionGate`

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

The test suite covers:
- RBAC permission matrix for all five roles
- AuthUser model properties and multi-role behavior
- All ownership check functions with mocked database sessions
- Draft-only submit and delete enforcement
- Reviewer assignment validation
- Application ownership via owner fields and member itcode
- Audit log output format and levels
