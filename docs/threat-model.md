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
| CSRF on state changes | Medium | JWT Bearer (not vulnerable to CSRF); SameSite cookies recommended |
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
| Credential leak | High | Env vars; rotate DB passwords |
| Excessive privileges | Medium | Least-privilege DB user |

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
| Rate limit bypass | Medium | Concurrency limiter (EA_AGENT_CONCURRENCY_LIMIT) |

### Boundary 4c: FastAPI ↔ S3 / Email
| Threat | Severity | Mitigation |
|--------|----------|------------|
| Unauthenticated file upload | High | RBAC-gated upload endpoint |
| File type bypass | Medium | Content-Type validation on upload |
| Email spoofing | Low | Fixed sender, no user-controlled From header |
| API token leak | High | Env vars, rotate regularly |

## Known Gaps

1. **No CSRF tokens**: API uses JWT Bearer — not CSRF-vulnerable by default, but double-submit cookie adds defense-in-depth
2. **No rate limiting**: AI review endpoint can be abused for resource exhaustion
3. **Plain-text audit log**: No hash chain or tamper detection
4. **Secrets in environment**: Should use Vault/Secrets Manager
5. **No WAF**: No web application firewall for injection protection
6. **Long-lived API tokens**: No automated rotation

## Planned Mitigations (v1.1+)
- API rate limiting per user + per endpoint
- Secrets manager integration (HashiCorp Vault or cloud-native)
- Audit log Merkle-tree integrity verification
- File upload malware scanning integration
- Automated secret rotation
