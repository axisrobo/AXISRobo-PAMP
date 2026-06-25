# OSS 本地用户名密码认证 + 用户管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local username/password authentication with JWT, user CRUD for Admin, and login page for OSS mode.

**Architecture:** New `AUTH_MODE` config drives provider selection. `LocalAuthProvider` authenticates via Bearer JWT. `POST /api/auth/login` issues JWTs. New `user_management` module provides Admin-only CRUD on `eam.local_users`. Frontend login page stores token in localStorage, AuthContext adapted for local mode.

**Tech Stack:** PyJWT, bcrypt, Next.js App Router, React Context

---

### Task 1: Add bcrypt dependency + migration for local_users table

**Files:**
- Create: `backend/migrations/025_create_local_users.sql`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Create migration file**

```sql
CREATE TABLE IF NOT EXISTS eam.local_users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(255) NOT NULL DEFAULT '',
    email         VARCHAR(255) NOT NULL DEFAULT '',
    role          VARCHAR(50)  NOT NULL DEFAULT 'requestor'
                  CHECK (role IN ('admin', 'reviewer', 'requestor')),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default admin user: admin / admin123
-- bcrypt hash generated with 12 rounds
INSERT INTO eam.local_users (username, password_hash, name, email, role)
VALUES (
    'admin',
    '$2b$12$LJ3m4ys3LwOXBVBkvh//kO6FMR3LpGxPb0E2XFFoT4bIebBkVsVKu',
    'Administrator',
    'admin@axisarch.local',
    'admin'
) ON CONFLICT (username) DO NOTHING;
```

- [ ] **Step 2: Add bcrypt to requirements.txt**

```
bcrypt>=4.1.0
```

- [ ] **Step 3: Install bcrypt**

```bash
pip install bcrypt>=4.1.0
```

- [ ] **Step 4: Commit**

```bash
git add backend/migrations/025_create_local_users.sql backend/requirements.txt
git commit -m "feat(auth): add local_users table migration with admin seed + bcrypt dependency"
```

---

### Task 2: Add AUTH_MODE and JWT config

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add new config fields after existing auth config**

After line 41 (`AUTH_DEV_ROLE`), add:

```python
    # Auth mode: dev (fixed user), local (username/password + JWT), oidc (Keycloak SSO, EE only)
    AUTH_MODE: str = "dev"  # dev | local | oidc

    # Local auth JWT configuration (used when AUTH_MODE=local)
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480  # 8 hours
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/config.py
git commit -m "feat(auth): add AUTH_MODE and JWT config settings"
```

---

### Task 3: Add LocalAuthProvider

**Files:**
- Modify: `backend/app/auth/providers.py`

- [ ] **Step 1: Add imports at top of providers.py**

After line 13 (`from fastapi import Request`):

```python
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from sqlalchemy import text
```

- [ ] **Step 2: Add LocalAuthProvider class after DevAuthProvider class (before the factory function)**

```python
# ---------------------------------------------------------------------------
# Local auth — username + password, JWT tokens
# ---------------------------------------------------------------------------

class LocalAuthProvider(AuthProvider):
    """Authenticate users from eam.local_users table with JWT bearer tokens.

    Login issues a JWT access token containing the user's identity and role.
    Subsequent requests validate the token via JWTHS256 signature verification.
    """

    def __init__(self, _settings=None):
        pass

    def _create_token(self, user_id: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def authenticate(self, request: Request) -> AuthUser | None:
        """Decode JWT from Authorization: Bearer header, look up user."""
        from app.database import AsyncSessionLocal

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

        username = payload.get("sub")
        if not username:
            return None

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT username, name, email, role FROM eam.local_users "
                    "WHERE username = :un AND is_active = TRUE"
                ),
                {"un": username},
            )
            row = result.mappings().first()

        if not row:
            return None

        role_value = row["role"]
        if role_value == "admin":
            roles = [Role.EA_ADMIN, Role.NORMAL_USER]
        elif role_value == "reviewer":
            roles = [Role.NORMAL_USER, Role.EA_REVIEWER]
        else:
            roles = [Role.NORMAL_USER]

        return AuthUser(
            id=row["username"],
            name=row["name"] or row["username"],
            email=row["email"] or f"{row['username']}@local",
            email_prefix=row["username"].lower(),
            roles=roles,
            permissions=build_permission_list(roles),
        )

    async def refresh_token(self, refresh_token: str) -> dict | None:
        return None

    @staticmethod
    async def login(username: str, password: str) -> tuple[str, AuthUser] | None:
        """Verify credentials and return (access_token, AuthUser) or None."""
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT username, password_hash, name, email, role "
                    "FROM eam.local_users "
                    "WHERE username = :un AND is_active = TRUE"
                ),
                {"un": username},
            )
            row = result.mappings().first()

        if not row:
            return None

        if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            return None

        provider = LocalAuthProvider()
        token = provider._create_token(username, row["role"])

        role_value = row["role"]
        if role_value == "admin":
            roles = [Role.EA_ADMIN, Role.NORMAL_USER]
        elif role_value == "reviewer":
            roles = [Role.NORMAL_USER, Role.EA_REVIEWER]
        else:
            roles = [Role.NORMAL_USER]

        user = AuthUser(
            id=row["username"],
            name=row["name"] or row["username"],
            email=row["email"] or f"{row['username']}@local",
            email_prefix=row["username"].lower(),
            roles=roles,
            permissions=build_permission_list(roles),
        )
        return token, user
```

- [ ] **Step 3: Update factory function get_auth_provider()**

Replace lines 72-77:

```python
def get_auth_provider() -> AuthProvider:
    """Return the configured auth provider based on AUTH_MODE setting."""
    if settings.AUTH_MODE == "dev" or settings.AUTH_DISABLED:
        return DevAuthProvider()
    if settings.AUTH_MODE == "local":
        return LocalAuthProvider()
    if settings.AUTH_MODE == "oidc":
        from app.ee.auth.keycloak_provider import KeycloakAuthProvider
        return KeycloakAuthProvider()
    logger.warning("Unknown AUTH_MODE=%s, falling back to DevAuthProvider", settings.AUTH_MODE)
    return DevAuthProvider()
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/auth/providers.py
git commit -m "feat(auth): add LocalAuthProvider with JWT token generation and bcrypt verification"
```

---

### Task 4: Add POST /api/auth/login endpoint

**Files:**
- Modify: `backend/app/auth/api.py`

- [ ] **Step 1: Add login endpoint and imports**

Add after line 5 (`from fastapi import APIRouter, Depends`):

```python
from pydantic import BaseModel
```

Add at end of file (after line 59):

```python
# ---------------------------------------------------------------------------
# POST /login — Local username/password authentication
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def auth_login(body: LoginRequest):
    """Authenticate with local username/password.  Returns a JWT access token.

    Only works when AUTH_MODE=local.
    """
    from app.config import settings
    if settings.AUTH_MODE != "local":
        raise HTTPException(status_code=400, detail="Login is only available in local auth mode")

    from app.auth.providers import LocalAuthProvider
    result = await LocalAuthProvider.login(body.username, body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token, user = result
    primary_role = "ea_admin" if user.is_admin else (
        "ea_reviewer" if user.is_reviewer else "normal_user"
    )
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.id,
            "name": user.name,
            "email": user.email,
            "role": primary_role,
            "roles": [r.value for r in user.roles],
            "permissions": user.permissions,
        },
    }
```

Need to import HTTPException:

```python
from fastapi import APIRouter, Depends, HTTPException
```

- [ ] **Step 2: Add /login to public paths in middleware.py**

In `backend/app/auth/middleware.py`, add to PUBLIC_PATHS:

```python
PUBLIC_PATHS: set[str] = {
    "/api/health",
    "/api/health/check",
    "/api/auth/login",   # <-- add this line
    "/docs",
    "/redoc",
    "/openapi.json",
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/auth/api.py backend/app/auth/middleware.py
git commit -m "feat(auth): add POST /api/auth/login endpoint for local auth"
```

---

### Task 5: Enable RBAC enforcement in local mode

**Files:**
- Modify: `backend/app/auth/dependencies.py`

- [ ] **Step 1: Add local mode check to require_role**

Change line 75 from `if not settings.EE_ENABLED:` to include local mode:

```python
        from app.config import settings
        if not settings.EE_ENABLED and settings.AUTH_MODE != "local":
            return user
```

- [ ] **Step 2: Same for require_permission**

Change line 102 from `if not settings.EE_ENABLED:` to:

```python
        from app.config import settings
        if not settings.EE_ENABLED and settings.AUTH_MODE != "local":
            return user
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/auth/dependencies.py
git commit -m "fix(auth): enable RBAC enforcement in local auth mode"
```

---

### Task 6: Update main.py auth plugin registration for AUTH_MODE

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update auth provider registration in lifespan**

Replace lines 66-77:

```python
    # Auth provider registration
    if _cfg2.AUTH_MODE == "dev" or _cfg2.AUTH_DISABLED:
        from app.auth.providers import DevAuthProvider
        plugin_registry.register("auth", DevAuthProvider(_cfg2))
        logger.info("Plugin: auth -> DevAuthProvider (dev mode)")
    elif _cfg2.AUTH_MODE == "local":
        from app.auth.providers import LocalAuthProvider
        plugin_registry.register("auth", LocalAuthProvider(_cfg2))
        logger.info("Plugin: auth -> LocalAuthProvider (local mode)")
    elif _cfg2.AUTH_MODE == "oidc" and _cfg2.EE_ENABLED and _cfg2.KEYCLOAK_SERVER_URL:
        from app.ee.auth.keycloak_provider import KeycloakAuthProvider
        plugin_registry.register("auth", KeycloakAuthProvider(_cfg2))
        logger.info("Plugin: auth -> KeycloakAuthProvider (EE)")
    else:
        from app.auth.providers import DevAuthProvider
        plugin_registry.register("auth", DevAuthProvider(_cfg2))
        logger.info("Plugin: auth -> DevAuthProvider (OSS fallback)")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "fix(main): update auth plugin registration for AUTH_MODE setting"
```

---

### Task 7: User management CRUD module

**Files:**
- Create: `backend/app/user_management/__init__.py`
- Create: `backend/app/user_management/users.py`
- Modify: `backend/app/module_registry.py` (or `backend/app/main.py` to register router)

- [ ] **Step 1: Create __init__.py**

```python
"""User management module — local user CRUD for admin."""
```

- [ ] **Step 2: Create users.py**

```python
"""User CRUD — admin only.  Manages eam.local_users table."""
from __future__ import annotations

import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_role, get_current_user, Role
from app.auth.models import AuthUser
from app.config import settings

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    email: str = ""
    role: str = "requestor"


class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    password: str


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _assert_local_mode():
    if settings.AUTH_MODE != "local":
        raise HTTPException(status_code=400, detail="User management is only available in local auth mode")


def _validate_role(role: str):
    if role not in ("admin", "reviewer", "requestor"):
        raise HTTPException(status_code=400, detail="Role must be admin, reviewer, or requestor")


# ── GET /api/users ──────────────────────────────────────────────────

@router.get("", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def list_users(
    q: str = Query("", description="Search by username or name"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _assert_local_mode()

    where = ""
    params: dict = {}
    if q.strip():
        where = "WHERE username ILIKE :q OR name ILIKE :q"
        params["q"] = f"%{q.strip()}%"

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM eam.local_users {where}"), params
    )
    total = count_result.scalar()

    offset = (page - 1) * pageSize
    result = await db.execute(
        text(
            f"SELECT id::text, username, name, email, role, is_active, "
            f"created_at, updated_at FROM eam.local_users {where} "
            f"ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": pageSize, "offset": offset},
    )
    rows = result.mappings().all()

    return {
        "data": [
            {
                "id": r["id"],
                "username": r["username"],
                "name": r["name"],
                "email": r["email"],
                "role": r["role"],
                "isActive": r["is_active"],
                "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
                "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


# ── POST /api/users ─────────────────────────────────────────────────

@router.post("", status_code=201, dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def create_user(
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()
    _validate_role(body.role)

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await db.execute(
        text("SELECT 1 FROM eam.local_users WHERE username = :un"),
        {"un": body.username},
    )
    if existing.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO eam.local_users (id, username, password_hash, name, email, role) "
            "VALUES (:id, :un, :ph, :name, :email, :role)"
        ),
        {
            "id": user_id,
            "un": body.username,
            "ph": _hash_password(body.password),
            "name": body.name or body.username,
            "email": body.email or "",
            "role": body.role,
        },
    )
    await db.commit()

    return {
        "id": user_id,
        "username": body.username,
        "name": body.name or body.username,
        "email": body.email or "",
        "role": body.role,
    }


# ── PUT /api/users/{id} ─────────────────────────────────────────────

@router.put("/{user_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()

    existing = await db.execute(
        text("SELECT id FROM eam.local_users WHERE id = :id::uuid"),
        {"id": user_id},
    )
    if not existing.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        _validate_role(body.role)

    sets = []
    params: dict = {"id": user_id}
    if body.name is not None:
        sets.append("name = :name")
        params["name"] = body.name
    if body.email is not None:
        sets.append("email = :email")
        params["email"] = body.email
    if body.role is not None:
        sets.append("role = :role")
        params["role"] = body.role
    if body.is_active is not None:
        sets.append("is_active = :is_active")
        params["is_active"] = body.is_active

    if sets:
        sets.append("updated_at = NOW()")
        await db.execute(
            text(f"UPDATE eam.local_users SET {', '.join(sets)} WHERE id = :id::uuid"),
            params,
        )
        await db.commit()

    result = await db.execute(
        text("SELECT id::text, username, name, email, role, is_active FROM eam.local_users WHERE id = :id::uuid"),
        {"id": user_id},
    )
    row = result.mappings().first()
    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "isActive": row["is_active"],
    }


# ── DELETE /api/users/{id} ──────────────────────────────────────────

@router.delete("/{user_id}", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()

    result = await db.execute(
        text("DELETE FROM eam.local_users WHERE id = :id::uuid"),
        {"id": user_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return {"message": "deleted"}


# ── PUT /api/users/{id}/password ────────────────────────────────────

@router.put("/{user_id}/password", dependencies=[Depends(require_role(Role.EA_ADMIN))])
async def reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    _assert_local_mode()

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    result = await db.execute(
        text("UPDATE eam.local_users SET password_hash = :ph, updated_at = NOW() WHERE id = :id::uuid"),
        {"ph": _hash_password(body.password), "id": user_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return {"message": "password updated"}
```

- [ ] **Step 3: Register user management router in main.py**

In `backend/app/main.py`, add after line 27 (the auth import):

```python
from app.user_management import users as user_management
```

Add after line 149 (the auth router registration):

```python
app.include_router(user_management.router, prefix="/api/users", tags=["Users"])
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/user_management/__init__.py backend/app/user_management/users.py backend/app/main.py
git commit -m "feat(users): add admin-only user CRUD endpoints for local_users table"
```

---

### Task 8: Adapt frontend auth-context for local mode

**Files:**
- Modify: `frontend/src/shared/lib/auth-context.tsx`
- Modify: `frontend/src/shared/lib/auth-token.ts`

- [ ] **Step 1: Update auth-token.ts to persist token in localStorage**

Replace the file:

```typescript
let _token: string | null = null;

const TOKEN_KEY = 'axisarch_token';

function loadToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function saveToken(token: string | null): void {
  if (typeof window === 'undefined') return;
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch { /* noop */ }
}

/** Store the access token. */
export function setAuthToken(token: string | null): void {
  _token = token;
  saveToken(token);
}

/** Retrieve the current access token. */
export function getAuthToken(): string | null {
  if (_token) return _token;
  _token = loadToken();
  return _token;
}

/** Clear stored token. */
export function clearAuthToken(): void {
  _token = null;
  saveToken(null);
}

/**
 * Build the Authorization header object.
 * Returns an empty object when no token is available (dev mode),
 * so it can be spread into a headers object safely.
 */
export function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
```

- [ ] **Step 2: Update auth-context.tsx**

Add AUTH_MODE detection. Replace lines 51-52:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';
const AUTH_DISABLED = process.env.NEXT_PUBLIC_AUTH_DISABLED === 'true';
const AUTH_MODE = (process.env.NEXT_PUBLIC_AUTH_MODE as string) || 'dev';
```

Replace the `login` and `logout` callbacks (lines 172-188):

```typescript
  const login = useCallback(async (username?: string, password?: string) => {
    try {
      if (AUTH_MODE === 'local' && username && password) {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.message || body.detail || 'Login failed');
        }
        const body = await res.json();
        const data = body.data || body;
        if (data.access_token) {
          setAuthToken(data.access_token);
        }
        if (data.user) {
          setUser(decodeUser(data.user));
        }
        setLoading(false);
        setError(null);
        return;
      }
      await keycloakService.login();
    } catch (error) {
      console.error('Login failed:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      if (AUTH_MODE === 'local') {
        clearAuthToken();
        setUser(null);
        return;
      }
      await keycloakService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, []);
```

Add import for `clearAuthToken` at top:

```typescript
import { authHeaders, setAuthToken, clearAuthToken } from '@/shared/lib/auth-token';
```

Replace the initialization useEffect (lines 132-170):

```typescript
  // Initialize authentication.
  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);

        if (AUTH_MODE === 'dev' || AUTH_DISABLED) {
          // Development mode: skip auth and fetch the dev user directly.
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Content-Type': 'application/json' },
          });
          if (res.ok) {
            const body = await res.json();
            setUser(decodeUser(body));
          } else {
            setError('Failed to load the development user');
            setSuppressAutoLogin(true);
          }
          setLoading(false);
          return;
        }

        if (AUTH_MODE === 'local') {
          const token = getAuthToken();
          if (!token) {
            setLoading(false);
            return;
          }
          await fetchUser();
          return;
        }

        // Production mode: initialize Keycloak SSO.
        const authenticated = await keycloakService.init();
        if (authenticated) {
          await fetchUser();
        } else {
          setLoading(false);
        }
      } catch (error) {
        console.error('Authentication initialization failed:', error);
        setError('Failed to initialize the authentication system');
        setSuppressAutoLogin(true);
        setLoading(false);
      }
    };

    initAuth();
  }, [fetchUser]);
```

Update the `fetchUser` function to not require keycloak auth in local mode (lines 74-129):

Change line 75-78 from:

```typescript
    if (!keycloakService.isAuthenticated()) {
      setUser(null);
      setLoading(false);
      setSuppressAutoLogin(false);
      return;
    }
```

to:

```typescript
    const hasToken = !!getAuthToken();
    if (AUTH_MODE === 'oidc' && !keycloakService.isAuthenticated()) {
      setUser(null);
      setLoading(false);
      setSuppressAutoLogin(false);
      return;
    }
    if (AUTH_MODE === 'local' && !hasToken) {
      setUser(null);
      setLoading(false);
      setSuppressAutoLogin(false);
      return;
    }
```

- [ ] **Step 3: Add AUTH_MODE to auth context interface**

Add `login(username?, password?)` signature change:

```typescript
  /** Log in — local: username+password; oidc: Keycloak redirect */
  login: (username?: string, password?: string) => Promise<void>;
```

- [ ] **Step 4: Create .env file for frontend (or update existing)**

Create `frontend/.env`:

```
NEXT_PUBLIC_AUTH_MODE=local
NEXT_PUBLIC_API_URL=http://localhost:4000/api
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/shared/lib/auth-token.ts frontend/src/shared/lib/auth-context.tsx frontend/.env
git commit -m "feat(frontend): adapt auth-context for local auth mode with token persistence"
```

---

### Task 9: Create login page

**Files:**
- Create: `frontend/src/app/login/page.tsx`

- [ ] **Step 1: Create login page**

```tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Input, Button, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@/shared/lib/auth-context';
import { getAuthToken } from '@/shared/lib/auth-token';

const { Title, Text } = Typography;

export default function LoginPage() {
  const router = useRouter();
  const { login, user, loading: authLoading, error: authError } = useAuth();
  const [messageApi, contextHolder] = message.useMessage();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && user && getAuthToken()) {
      router.replace('/');
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (authError) {
      messageApi.error(authError);
    }
  }, [authError, messageApi]);

  const handleSubmit = async () => {
    if (!username.trim()) {
      messageApi.error('Please enter username');
      return;
    }
    if (!password) {
      messageApi.error('Please enter password');
      return;
    }
    setSubmitting(true);
    try {
      await login(username.trim(), password);
    } catch {
      // error handled by authError effect
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      {contextHolder}
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8 space-y-6">
        <div className="text-center space-y-2">
          <Title level={3} style={{ marginBottom: 0 }}>AxisArch</Title>
          <Text type="secondary">Enterprise Architecture Management</Text>
        </div>

        <div className="space-y-4">
          <Input
            size="large"
            prefix={<UserOutlined />}
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onPressEnter={handleSubmit}
          />
          <Input.Password
            size="large"
            prefix={<LockOutlined />}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onPressEnter={handleSubmit}
          />
          <Button
            type="primary"
            size="large"
            block
            loading={submitting || authLoading}
            onClick={handleSubmit}
          >
            Sign in
          </Button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/login/page.tsx
git commit -m "feat(frontend): add login page with username/password form"
```

---

### Task 10: Add route guard — redirect unauthenticated to /login

**Files:**
- Modify: `frontend/src/app/layout.tsx` (or `frontend/src/app/providers.tsx`)
- Create: `frontend/src/shared/lib/AuthGuard.tsx`

- [ ] **Step 1: Create AuthGuard component**

```tsx
'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/shared/lib/auth-context';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const AUTH_MODE = (process.env.NEXT_PUBLIC_AUTH_MODE as string) || 'dev';

  useEffect(() => {
    if (AUTH_MODE !== 'local') return;
    if (loading) return;
    if (!user && pathname !== '/login') {
      router.replace('/login');
    }
    if (user && pathname === '/login') {
      router.replace('/');
    }
  }, [user, loading, pathname, router]);

  if (AUTH_MODE !== 'local') return <>{children}</>;

  if (loading && pathname !== '/login') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Wrap children with AuthGuard in providers.tsx**

Add import:

```typescript
import { AuthGuard } from '@/shared/lib/AuthGuard';
```

Wrap children:

```tsx
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LocaleProvider>
          <ToastProvider>
            <AuthGuard>{children}</AuthGuard>
          </ToastProvider>
        </LocaleProvider>
      </AuthProvider>
    </QueryClientProvider>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/lib/AuthGuard.tsx frontend/src/app/providers.tsx
git commit -m "feat(frontend): add AuthGuard to redirect unauthenticated users to /login"
```

---

### Task 11: Update backend .env.example and verify

**Files:**
- Modify: `backend/.env.example`

- [ ] **Step 1: Update .env.example**

Add after AUTH_DEV_ROLE line:

```env
# Auth mode: dev (fixed dev user), local (username/password + JWT), oidc (Keycloak SSO, EE only)
AUTH_MODE=dev
# JWT secret for local auth (production: use a strong random key)
JWT_SECRET_KEY=change-me-in-production
```

- [ ] **Step 2: Run backend tests to verify nothing breaks**

```bash
cd backend && python -m pytest -x -q
```

- [ ] **Step 3: Commit**

```bash
git add backend/.env.example
git commit -m "docs: update .env.example with AUTH_MODE and JWT config"
```
