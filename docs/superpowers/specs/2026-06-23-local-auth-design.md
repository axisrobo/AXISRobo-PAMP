# OSS 本地用户名密码认证 + 用户管理

Date: 2026-06-23

## 概述

为 AxisArch OSS 版本添加本地用户名/密码认证系统，支持三种角色（Admin / Reviewer / Requestor），Admin 可管理用户 CRUD。OIDC/Keycloak 保留为企业版（EE）功能。

## 1. 数据库

### 新表 `eam.local_users` (migration `025`)

```sql
CREATE TABLE eam.local_users (
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
```

**种子数据**：Admin 默认用户 `admin / admin123`

### 角色权限映射

| local_users.role | 系统 Role | 权限 |
|---|---|---|
| `admin` | `EA_ADMIN` | `*:*` 全部 |
| `reviewer` | `EA_REVIEWER` | NORMAL_USER + meeting/action/bcm/scope 写权限 |
| `requestor` | `NORMAL_USER` | 创建/查看自己的 ea_request 和 project |

## 2. 配置

**新增 config** (`backend/app/config.py`):

```python
AUTH_MODE: str = "dev"           # dev | local | oidc
JWT_SECRET_KEY: str = ""         # local 模式必需
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_MINUTES: int = 480
```

`AUTH_MODE=dev` 保持向后兼容（开发默认）。

## 3. 后端 Auth

### Provider 工厂

```
AUTH_MODE=dev   → DevAuthProvider   (固定用户，开发用)
AUTH_MODE=local → LocalAuthProvider (用户名密码 + JWT)
AUTH_MODE=oidc  → KeycloakAuthProvider (EE only，需 EE_ENABLED=true)
```

### LocalAuthProvider

| 方法 | 逻辑 |
|---|---|
| `authenticate(request)` | 解析 `Authorization: Bearer <JWT>` → 解码 JWT → 查 local_users → 返回 AuthUser |
| `login(username, password)` | 查 local_users by username → bcrypt 验证 → 签发 JWT (HS256, 8h) |

### 新增端点

**`POST /api/auth/login`** — 公开接口。

Request: `{ username, password }`
Response: `{ access_token, user: { id, username, name, email, role } }`

### RBAC 生效

当 `AUTH_MODE=local` 时，`require_permission` / `require_role` / `require_auth` 全部生效（不再依赖 `EE_ENABLED`）。

### AuthUser 构建

Local 模式下从 `local_users` 表构建：
- `id` = username（向后兼容 existing itcode-based checks）
- `roles` = `[mapped_role, NORMAL_USER]`
- `permissions` = 从 RBAC 矩阵展开

## 4. 后端用户管理

**新模块** `backend/app/user_management/`，所有端点需 `admin` 角色。

| 端点 | 功能 |
|---|---|
| `GET /api/users` | 分页列表，`?q=keyword&page=1&pageSize=20` |
| `POST /api/users` | 创建: `{ username, password, name, email, role }` |
| `PUT /api/users/{id}` | 更新: name, email, role, is_active（不能改 username） |
| `DELETE /api/users/{id}` | 软删除: `is_active = false` |
| `PUT /api/users/{id}/password` | Admin 重置密码 |

`POST /api/users` 需验证 username 唯一性，password 最少 6 位。密码用 bcrypt hash。

## 5. 前端

### 环境变量

```
NEXT_PUBLIC_AUTH_MODE=local   # dev | local | oidc
```

### Login 页面 (`/login`)

- 用户名 + 密码表单
- `POST /api/auth/login` → 存 `access_token` 到 localStorage
- 调用 `/api/auth/me` 获取 user profile
- 成功后跳转首页

### AuthContext 改动

- 新增 `login(username, password)` 方法
- `AUTH_MODE=local` 时跳过 Keycloak 初始化
- `authHeaders()` 优先用 localStorage token → `Bearer <token>`
- `logout()` 清空 localStorage token + 重定向 `/login`

### 路由守卫

- 未登录 → `/login`
- 已登录访问 `/login` → `/`

## 6. .env.example 更新

```env
# 认证模式: dev | local | oidc
AUTH_MODE=dev
# local 模式 JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=change-me-in-production
```

## 7. 实现顺序

1. 迁移 `025_create_local_users.sql`
2. `LocalAuthProvider` + login 端点 + RBAC 开关
3. 用户管理 CRUD 模块
4. 前端 login 页面 + AuthContext 适配

## 8. 不予实现

- OIDC 改名（Keycloak 保持 EE only）
- 用户自己改密码（后续再加）
- 刷新 token / token 黑名单
- 前端注册页面
