# PAMF Enterprise Edition (EE)

> Enterprise features subject to commercial license. Contact for license terms.

## EE Features

The following features are enterprise-only, gated behind `EE_ENABLED=true`:

| Feature | Module | Description |
|---------|--------|-------------|
| **Keycloak SSO** | `backend/app/ee/auth/` | OIDC-based single sign-on with JWT validation, RBAC enforcement, scoped role resolution |
| **CMDB Sync** | `backend/app/ee/cmdb/` | Automated CMDB application synchronization |
| **BCT Email** | `backend/app/ee/email/` | Enterprise email via BCT Message API |
| **Agent Watch Telemetry** | `backend/app/ee/telemetry/` | AI agent observability and monitoring |
| **Role Resolution** | `backend/app/ee/role_resolver.py` | Database-sourced role resolution (EA_ADMIN, EA_REVIEWER, APP_OWNER, PROJECT_OWNER) |
| **Full RBAC** | `backend/app/auth/` | Complete role-based access control with ownership checks and audit logging |

## Configuration

Set in `backend/.env`:

```env
EE_ENABLED=true
AUTH_MODE=oidc
KEYCLOAK_SERVER_URL=https://your-keycloak-server.com/
KEYCLOAK_REALM=myapp
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

## Contact

For enterprise licensing inquiries, contact the PAMF team.
