# AxisArch 全局优化建议与执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 AxisArch 项目进行架构、设计、API、安全、UI/UX、清晰度、业务流程完整度与一致性优化

**Architecture:** 3-Tier (Next.js 16 + FastAPI + PostgreSQL)，6 个可插拔业务模块 + RBAC。优化重点为消除文档/实现不一致、统一设计系统、强化安全纵深、补齐业务流程、提升可维护性。

**Tech Stack:** TypeScript/React 19, Next.js 16, Ant Design v6, Tailwind CSS 4, Python 3.12+, FastAPI, asyncpg

**范围说明:** 本次不涉及认证默认值、密钥泄露、TLS 校验三项（已单独处理）。

---

## 一、架构与设计

### 1.1 分层架构路线不清晰

**问题:** 代码中同时存在两种架构风格：
- 旧风格：router 内联 SQL（`app/architecture_review/`, `app/application_management/`）
- 新风格：Clean Architecture 分层（`app/application/`, `app/domain/`, `app/infrastructure/`, `app/plugins/`）

文档 `docs/module-splitting-plan.md` 和 `docs/ROADMAP.md` 仍以旧风格描述，但 `STATUS.md` 称 models/schemas 为空——明显已经迁移。

**建议:**
- 制定架构迁移路线图：新模块强制走分层架构，旧模块逐个迁移
- 在 `docs/architecture.md` 中明确两种风格并存的原因和迁移计划
- 建立模块架构检查清单

### 1.2 模块启用机制未贯通全栈

**问题:** 后端 `ENABLED_MODULES` 已控制路由注册，但前端菜单、路由可见性、文档列表未同步。

**建议:**
- 前端构建时注入模块清单，控制侧边栏菜单和路由注册
- 建立模块 Matrix 文档，字段包括：模块名、后端 key、前端菜单路径、API prefix、权限 resource、DB 表、是否默认启用

### 1.3 模块注册顺序不稳定

**问题:** `iter_enabled_module_registrations()` 遍历 `set`，路由注册顺序不确定（`backend/app/module_registry.py:45`）。

**建议:**
- 改为 `list` 或 `OrderedDict` 保证确定性顺序
- 有利于调试、OpenAPI 稳定性、CI 测试

---

## 二、API 一致性

### 2.1 文档与实现路由严重不一致

**问题:**

| 文档 (`docs/api.md`) | 实现 | 影响 |
|---|---|---|
| `/api/add/...` | `/api/avdm/...` | 前后端对接错误 |
| `/api/cmdb-applications` | `/api/cmdb` | 集成方误调用 |
| `/api/ea-requests/attachments` | `/api/ea-requests/attachments/upload` | 附件上传路径不同 |
| `/api/attachment/{id}/download` | `/api/ea-requests/attachments/{id}/file` | 下载路径不同 |

**建议:**
- 以 FastAPI OpenAPI (`/openapi.json`) 为唯一事实来源
- 重写 `docs/api.md` 为自动生成或 CI 校验
- OpenSpec 每个 capability 增加 `implementation_path` 字段

### 2.2 技术栈模块双路由前缀

**问题:** 同一 router 同时挂载 `/tech-stack` 和 `/technology-stack`（`backend/app/technology_stack_management/__init__.py`）。

**建议:**
- 确定正式 prefix（建议 `/api/technology-stack` 与文档对齐）
- 保留另一个为 deprecated，增加 `Deprecation` 响应头，计划 v2.0 移除

### 2.3 ADD vs AVDM 命名冲突

**问题:** 模块注册 key 为 `add`，路由 prefix 为 `/api/avdm`，文档写 `/api/add`。三处命名不同。

**建议:**
- 确定正式模块名（建议保留 `avdm` 作为路由名，模块 key 改为 `avdm` 或保持 `add` 但加别名）
- 同步更新 `module_registry.py`、`roles.py`、`docs/api.md`、OpenSpec、前端 API 调用

### 2.4 响应 envelope 规范不完整

**问题:** 全局 envelope 已统一 400/401/403/404/500，但 201/204 未明确处理。`enveloped_client.py` 只在 `code == 200` 时 unwrap。

**建议:**
- 明确所有 2xx 的 envelope 格式：`{code: HTTP_STATUS, message: "...", data: ...}`
- `enveloped_client.py` 支持所有 2xx unwrap
- 增加结构化错误码（`error_code`）和 `request_id`

---

## 三、安全（不含认证默认值、密钥、TLS）

### 3.1 ADD/AVDM 模块 RBAC 不完整

**问题:** `backend/app/add/routes.py` 中多个读写接口缺少 `require_permission`：
- `POST /api/avdm/evaluate`
- `POST /api/avdm/review`
- `POST /api/avdm/projects/{project_id}/questionnaire`
- `PUT /api/avdm/projects/{project_id}/artifacts`
- 多个 confirm 接口

**建议:**
- 读接口加 `require_permission("avdm", "read")`
- 写接口加 `require_permission("avdm", "write")`
- 管理接口加 `Depends(require_role(Role.EA_ADMIN))`
- 资源加入 `ROLE_PERMISSIONS` 矩阵

### 3.2 CORS 配置过宽

**问题:** `backend/app/main.py` 中 `allow_origins=["*"]` 且 `allow_credentials=True`——浏览器端该组合不可用且策略过宽。

**建议:**
- 增加 `CORS_ALLOWED_ORIGINS` 配置项，默认 `http://localhost:3000`
- 生产环境禁止 `*` + `credentials`
- `threat-model.md` 已记录此风险，需落地修复

### 3.3 JWT audience 未校验

**问题:** Keycloak JWT decode 设置了 `"verify_aud": False`（`backend/app/ee/auth/keycloak_provider.py`）。

**建议:**
- 开启 audience 校验，配置预期 `client_id`
- 校验 issuer、algorithms 白名单
- JWKS 获取失败时不 fallback 到不安全模式

### 3.4 日志泄露敏感信息

**问题:** `get_current_user()` 中 debug 记录 `dict(request.headers)`（`backend/app/auth/dependencies.py`）。

**建议:**
- 不打印完整 request headers
- Authorization、Cookie、Set-Cookie、token、secret 统一脱敏

### 3.5 SQLAlchemy echo 默认开启

**问题:** `backend/app/database.py` 中 `echo=True` 可能在生产日志中输出 SQL 和参数。

**建议:**
- 增加 `DB_ECHO` 配置项，默认 `False`
- 仅开发环境可开启

### 3.6 DB_SCHEMA 配置缺乏校验

**问题:** `SET search_path TO {settings.DB_SCHEMA}` 直接 f-string 拼接（`backend/app/database.py`）。

**建议:**
- 对 `DB_SCHEMA` 做白名单或正则校验（如 `^[a-zA-Z_][a-zA-Z0-9_]*$`）
- 文档统一 schema 命名策略

---

## 四、数据库与迁移

### 4.1 迁移机制不可靠

**问题:**
- `run_migrations()` 每次启动按文件名执行全部 SQL，无版本记录
- 迁移失败仅 warning，不阻断启动
- 存在重复编号：002 和 004 各有两个文件
- 部分 `ALTER TABLE` 不幂等，重复启动反复失败但被跳过

**建议:**
- 引入 Alembic 管理迁移
- 至少增加 `schema_migrations` 表（filename, hash, applied_at）
- 修正重复编号
- 所有 DDL 确保幂等（`IF NOT EXISTS` / `IF EXISTS`）
- 迁移失败阻断启动

### 4.2 数据库 schema 命名不一致

**问题:** `backend/.env.example` 和 `config.py` 使用 `DB_SCHEMA=axisarch`。代码和 OpenSpec 多处硬编码 `eam` 前缀（如 `eam.eam_request_attachment`、`eam.cmdb_application`）。

**建议:**
- 二选一：
  - 固定 schema 为 `eam`，更新配置和文档
  - 真正支持 `DB_SCHEMA`，代码中不硬编码 schema 前缀而是用 `search_path` 或安全注入

### 4.3 Team Members 写事务未提交

**问题:** `create_team_member`、`update_team_member`、`delete_team_member` 执行 DB 写入后未 commit（`backend/app/project_management/team_members.py`）。

**建议:**
- 写操作后 `await db.commit()`
- 异常路径 `await db.rollback()`
- 增加持久化验证测试

---

## 五、审计

### 5.1 审计实现与项目原则不符

**问题:** 项目规则声明 "append-only `eam_audit_log`"，但：
- `audit_allow` / `audit_deny` 仅写 logger（`backend/app/auth/audit.py`）
- 仅在 `EE_ENABLED` 时启用
- 无持久化存储

**建议:**
- 创建 `eam_audit_log` 表
- 字段：id, user_id, roles, resource, action, decision, reason, request_id, timestamp, client_ip
- `audit_allow()` / `audit_deny()` 同时写入该表
- 区分 `audit_log`（安全审计）、`eam_audit_log`（业务审计）、`tech_stack_operate_log`（操作日志）

---

## 六、前端 UI/UX

### 6.1 Tailwind 扫描范围不完整（Critical）

**问题:** `tailwind.config.ts` 的 `content` 只包含 `src/app`、`src/pages`、`src/components`。`src/shared` 和 `src/features` 中的大量 Tailwind class 在 production purge 时可能丢失。

**建议:**
- 将 content 改为 `./src/**/*.{js,ts,jsx,tsx,mdx}`
- 或用 `safelist` 保护关键动态 class
- 验证 production build 无样式缺失

### 6.2 设计系统不统一

**问题:** 同一类 UI 存在多种实现：
- 表格：`DataTable` vs 原生 `<table>`
- 抽屉：AntD `Drawer` vs 自定义 fixed overlay
- 按钮：AntD `Button` vs Tailwind `<button>` vs 图标裸按钮
- 颜色：AntD token vs Tailwind token vs 硬编码 hex

**建议:**
- 建立 UI 规范文档
- 表单/表格/抽屉/弹窗 统一使用 AntD
- Tailwind 仅用于布局和轻量样式
- 统一调色板，消除 `gray-*` / `slate-*` 混用

### 6.3 核心流程疑似断链（High）

**问题:** `RequestDetailView` 中 "Go to Questionnaire Submit" 跳转 `/request/create?id=...`，实际创建页路由为 `/ea-review/request/create`（`frontend/src/features/review/components/ea-review/RequestDetailView.tsx`）。

**建议:**
- 修正跳转路径为 `/ea-review/request/create?id=...`
- 全局搜索 `/request/create` 确保无其他残留
- 增加页面级 E2E 测试覆盖此链路

### 6.4 超大页面需拆分

**问题:** 多个页面文件过大，混合 API 调用、状态、表单校验、渲染：
- `request/create/page.tsx`：~2000+ 行
- `bcm/page.tsx`：~1000+ 行
- `ApplicationTechStackModal.tsx`：同时承载详情/目录/成员/日志/权限/多个弹窗

**建议拆分:**
- Request Create：`Step1ProjectForm`、`Step2Questionnaire`、`Step3Handoff`、`useCreateRequest` hook、validators
- BCM：`SearchPanel`、`BcmTable`、`BcmDrawer`、`BcCascader`
- TechStack Modal：`GeneralInfo`、`CatalogTab`、`TeamTab`、`LogTab`、`PermissionPanel`

### 6.5 可访问性不足

**问题:**
- 图标按钮缺少 `aria-label`（关闭、缩放、重置、收藏、帮助）
- `label` 元素缺少 `htmlFor`
- 自定义 drawer 缺少 `role="dialog"`、`aria-modal`、焦点陷阱
- BCM Cascader 仅支持 hover，无键盘操作
- Mindmap 仅鼠标拖拽/点击，无键盘替代路径

**建议:**
- 所有图标按钮加 `aria-label`
- 所有 label 加 `htmlFor` 关联 input
- 自定义 drawer 加 `role="dialog"`、`aria-modal`、Esc 关闭、焦点回收
- Cascader 支持键盘上下左右/Enter/Esc
- Mindmap 提供等价列表视图或键盘选择节点能力

### 6.6 移动端适配不系统

**问题:**
- 表格依赖横向滚动，列宽默认 150px
- 自定义抽屉 `max-w-lg` 在小屏缺少专门布局
- Mindmap 使用 `calc(100vh - 280px)` 固定视图
- SearchForm inline 模式在窄屏拥挤

**建议:**
- 复杂表格在移动端提供卡片列表视图
- 抽屉/Modal 在小屏全屏显示
- Mindmap 提供简化移动端视图
- 如果移动端正式支持，定义最小宽度和降级策略

### 6.7 表单体验不统一

**问题:**
- 混用 AntD Form、自定义 FieldLabel、裸 Input、ResourceAutoComplete
- required 提示在用户输入前即显示
- 多处只用 toast/message 提示错误，无字段级定位
- disabled 状态缺少原因说明

**建议:**
- 统一用 AntD `Form.Item` 或封装统一 `FormField` 组件
- 校验仅在触摸后或提交后触发（`validateTrigger="onBlur"`）
- 字段级错误通过 Form.Item 的 `help` / `validateStatus` 展示
- disabled 字段通过 tooltip 说明原因

### 6.8 状态管理分散

**问题:** 复杂客户端状态大量散布在页面/Modal 内（useState），缺少集中管理。

**建议:**
- 复杂多步流程考虑 useReducer 或 Zustand
- 跨组件共享状态用 Context + reducer
- Mindmap localStorage key 需增加用户/数据版本维度避免污染

---

## 七、文档与清晰度

### 7.1 版本矩阵严重冲突

**问题:**

| 来源 | Next.js | React | Python | 备注 |
|------|---------|-------|--------|------|
| README / architecture.md | 15 | 19 | ≥3.12 | |
| frontend/package.json | ^16.2.1 | ^19.2.4 | - | 实际版本 |
| docs/design.md | 14 | - | 3.11 | 严重过时 |
| .python-version | - | - | 3.14.3 | 与 pyproject.toml 不一致 |

**建议:**
- 在 `docs/architecture.md` 建立唯一 Runtime Matrix，包含：Node | npm | Python | Next.js | React | FastAPI | PostgreSQL | AntD
- 同步更新：`.nvmrc`、`.python-version`、`pyproject.toml`、`package.json`、`frontend/package.json`、README、design 文档

### 7.2 授权文档角色模型过时

**问题:**
- `docs/authorization.md` 只列 4 个角色（Normal_User, EA_Admin, EA_Reviewer, App_Owner）
- 实际有 5 个角色（含 Project_Owner）
- `docs/module-splitting-plan.md` 使用旧命名（admin, editor, viewer）

**建议:**
- 以 `backend/app/auth/models.py` 中的 `Role` enum 为准更新 `docs/authorization.md`
- 统一所有文档的角色模型为：Normal_User, EA_Admin, EA_Reviewer, App_Owner, Project_Owner

### 7.3 设计文档质量问题

**问题:**
- `docs/design.md` 多处编码损坏（乱码）
- `docs/design-En.md` 仅 85 行，不是完整英文版
- 两文档的架构版本（Next 14 vs 16) 已过时

**建议:**
- 重整 `docs/design.md` 到当前真实架构
- `docs/design-En.md` 要么补齐要么删除
- 标注最后更新日期

### 7.4 OpenSpec 组织不规范

**问题:** `openspec/specs/authorization/` 中同时包含 `proposal.md`、`tasks.md`、`spec.md`。`openspec/config.yaml` 几乎为空。

**建议:**
- 稳定 spec 保留在 `openspec/specs/`
- proposal/tasks 移到 `openspec/changes/` 或归档
- 填写 `openspec/config.yaml`：项目名、命名规范、归档规则

### 7.5 STATUS.md 可信度不足

**问题:** `docs/STATUS.md` 声称 Certification、Dashboard、Schedules、Dict Options 等完整，但当前后端未发现对应实现文件。测试目录虽有相关测试，但实现可能已被迁移或移除。

**建议:**
- 逐项核实每个功能模块的完成状态
- 更新 `STATUS.md` 反映真实情况
- 标记已移除/未实现的功能

### 7.6 部署资产缺失

**问题:** 当前仓库未发现 Dockerfile、docker-compose、CI workflow 文件。

**建议:**
- 提供 `docker-compose.yml`（PostgreSQL + backend + frontend）
- 提供 backend 和 frontend 的 Dockerfile
- 提供 GitHub Actions CI：lint、build、pytest、api-tests、Playwright

### 7.7 仓库结构杂乱

**问题:** 工作区存在未跟踪/未忽略的产物：
- `backend/venv/`
- `frontend/tsc_output.txt`、`tsc_errors.log`、`build_log.txt`
- `frontend/test-results/`

**建议:**
- 确认 `.gitignore` 覆盖这些路径
- 如果已被 Git 跟踪，移出版本控制
- 确认 `AGENTS.md` 不应被 `.gitignore` 忽略

---

## 八、业务流程完整度

### 8.1 EA Review 流程链路需端到端梳理

**问题:** 请求创建 → 详情 → 问卷回填 → 提交 → AI check → 审批链路中存在断链（见 6.3）。

**建议:**
- 绘制 EA Review 状态机（Draft → Submitted → Under Review → AI Check → Approved/Rejected）
- 验证每个状态转换的 API 和前端跳转
- 补 Playwright E2E 覆盖完整流程

### 8.2 模块间数据关系未文档化

**问题:** ADD/AVDM、EA Review、Technology Stack、Application Portfolio 之间的引用关系未在文档中说明。

**建议:**
- 在 `docs/architecture.md` 中增加模块间数据流图
- 标注哪些实体有跨模块引用（如 Project → Request、Application → TechStack）
- 每个模块明确生命周期状态机

### 8.3 关键业务流程缺少 E2E 测试

**建议补 E2E 覆盖:**
- EA Request 完整生命周期（创建 → 填写问卷 → 上传附件 → AI check → 审批）
- Technology Stack 生命周期（创建 → 审批 → 发布 → 废弃）
- CMDB 同步流程
- BCM 能力映射流程
- 项目团队管理流程

---

## 九、执行计划

### Phase 1: 止血修复（第 1-2 周，优先解决 Critical/High 问题）

#### Task 1: 修复 Tailwind content 配置

**Files:**
- Modify: `frontend/tailwind.config.ts`

- [ ] **Step 1: 修改 content 扫描范围**

```typescript
// tailwind.config.ts
content: [
  "./src/**/*.{js,ts,jsx,tsx,mdx}",
],
```

- [ ] **Step 2: 执行 production build 验证无样式缺失**

```bash
cd frontend && npm run build
```
验证：构建产物中关键 class 存在（sidebar, datatable, mindmap 等）

- [ ] **Step 3: Commit**

```bash
git add frontend/tailwind.config.ts
git commit -m "fix: expand Tailwind content scan to shared/features directories"
```

---

#### Task 2: 修复请求详情页断链路由

**Files:**
- Modify: `frontend/src/features/review/components/ea-review/RequestDetailView.tsx`

- [ ] **Step 1: 修正跳转路径**

将：
```tsx
router.push(`/request/create?id=${id}`)
```
改为：
```tsx
router.push(`/ea-review/request/create?id=${id}`)
```

- [ ] **Step 2: 全局搜索 `/request/create` 确保无其他残留**

```bash
rg "/request/create" frontend/src
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/review/components/ea-review/RequestDetailView.tsx
git commit -m "fix: correct EA request detail page navigation to create route"
```

---

#### Task 3: 修复 ADD/AVDM RBAC 缺失

**Files:**
- Modify: `backend/app/add/routes.py`
- Modify: `backend/app/auth/rbac.py`

- [ ] **Step 1: 为 ADD 路由补充权限依赖**

为每个路由端点添加适当的权限依赖：

```python
# 读接口示例
@router.get("/api/avdm/projects", dependencies=[Depends(require_permission("avdm", "read"))])
async def list_projects(...):
    ...

# 写接口示例
@router.post("/api/avdm/evaluate", dependencies=[Depends(require_permission("avdm", "write"))])
async def evaluate(...):
    ...

@router.post("/api/avdm/projects/{project_id}/questionnaire", dependencies=[Depends(require_permission("avdm", "write"))])
async def submit_questionnaire(...):
    ...
```

- [ ] **Step 2: 在 RBAC 矩阵中注册 avdm 资源**

在 `ROLE_PERMISSIONS` 中增加 `avdm` 资源的权限配置。

- [ ] **Step 3: 运行后端测试验证不引入回归**

```bash
cd backend && python -m pytest
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/add/routes.py backend/app/auth/rbac.py
git commit -m "fix: add RBAC permission dependencies to AVDM/ADD endpoints"
```

---

#### Task 4: 修复 Team Members 事务提交

**Files:**
- Modify: `backend/app/project_management/team_members.py`

- [ ] **Step 1: 为 create/update/delete 添加 commit/rollback**

```python
async def create_team_member(db: AsyncSession, ...):
    try:
        await db.execute(...)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

async def update_team_member(db: AsyncSession, ...):
    try:
        await db.execute(...)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

async def delete_team_member(db: AsyncSession, ...):
    try:
        await db.execute(...)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
```

- [ ] **Step 2: 运行测试验证持久化**

```bash
cd backend && python -m pytest tests/ -k "team_member"
cd api-tests && python -m pytest tests/ -k "team"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/project_management/team_members.py
git commit -m "fix: add transaction commit to team member write operations"
```

---

#### Task 5: 修复 CORS 配置

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/config.py`

- [ ] **Step 1: 增加 CORS 配置项**

```python
# config.py
CORS_ALLOWED_ORIGINS: list[str] = Field(default=["http://localhost:3000"])
```

- [ ] **Step 2: 修改 main.py CORS middleware**

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 3: 同步更新 .env.example**

```env
CORS_ALLOWED_ORIGINS=["http://localhost:3000"]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py backend/app/config.py backend/.env.example
git commit -m "fix: restrict CORS origins from wildcard to configured list"
```

---

#### Task 6: 日志脱敏

**Files:**
- Modify: `backend/app/auth/dependencies.py`

- [ ] **Step 1: 移除完整 headers 日志，改为只记录关键字段**

```python
# 修改前
logger.debug(f"Request headers: {dict(request.headers)}")

# 修改后（只记录非敏感字段）
safe_headers = {k: v for k, v in request.headers.items()
                if k.lower() not in ('authorization', 'cookie', 'set-cookie')}
logger.debug(f"Request headers: {safe_headers}")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/auth/dependencies.py
git commit -m "fix: redact sensitive headers from debug logging"
```

---

#### Task 7: SQLAlchemy echo 改为配置化

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/database.py`

- [ ] **Step 1: 增加 DB_ECHO 配置**

```python
# config.py
DB_ECHO: bool = Field(default=False)
```

- [ ] **Step 2: 修改 database.py**

```python
# database.py
engine = create_async_engine(..., echo=settings.DB_ECHO)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py backend/app/database.py
git commit -m "fix: make SQLAlchemy echo configurable, default off"
```

---

### Phase 2: 契约对齐（第 2-3 周）

#### Task 8: 统一 API prefix（AVDM/ADD）

**Files:**
- Modify: `backend/app/add/__init__.py`
- Modify: `backend/app/module_registry.py`
- Modify: `frontend/src/` (all API calls referencing `/api/add`)

- [ ] **Step 1: 确定正式 prefix**

决定：保持路由 prefix 为 `/api/avdm`，模块注册 key 保持 `add`，但在 `module_registry.py` 中记录 display_name 为 "ADD (AVDM)"。

- [ ] **Step 2: 更新前端所有 API 调用**

搜索并替换前端中所有 `/api/add` 为 `/api/avdm`（如果有残留旧路径）。

- [ ] **Step 3: 更新 docs/api.md**

同步文档路径。

- [ ] **Step 4: Commit**

```bash
git add ...
git commit -m "refactor: standardize AVDM module API prefix to /api/avdm"
```

---

#### Task 9: 统一技术栈双路由

**Files:**
- Modify: `backend/app/technology_stack_management/__init__.py`

- [ ] **Step 1: 决定保留 `/api/technology-stack`，标记 `/api/tech-stack` deprecated**

保留 `/api/technology-stack` 与文档一致；`/api/tech-stack` 加 Deprecation 头保留一版本。

- [ ] **Step 2: 更新前端调用**

前端统一使用 `/api/technology-stack`。

- [ ] **Step 3: Commit**

```bash
git add backend/app/technology_stack_management/__init__.py
git commit -m "refactor: standardize technology stack prefix, deprecate /api/tech-stack alias"
```

---

#### Task 10: 重建 API 文档

**Files:**
- Modify: `docs/api.md`

- [ ] **Step 1: 获取 FastAPI OpenAPI schema**

```bash
cd backend && python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json
```

- [ ] **Step 2: 基于 openapi.json 重写 docs/api.md**

按模块整理端点、路径、参数、响应格式。标注 OpenSpec capability 对应关系。

- [ ] **Step 3: Commit**

```bash
git add docs/api.md
git commit -m "docs: regenerate API reference from OpenAPI schema"
```

---

#### Task 11: 统一 DB schema 策略

**Files:**
- Modify: `backend/app/database.py`
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/app/architecture_review/attachments.py`
- Modify: `backend/app/application_management/cmdb.py`

- [ ] **Step 1: 决定 schema 名称**

确认正式 schema 名称。建议统一为 `axisarch` 或 `eam`。以下假设选择 `axisarch`。

- [ ] **Step 2: DB_SCHEMA 增加白名单校验**

```python
# config.py validator
@field_validator("DB_SCHEMA")
def validate_schema_name(cls, v):
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
        raise ValueError(f"Invalid schema name: {v}")
    return v
```

- [ ] **Step 3: 代码中硬编码的 eam 替换为动态 schema**

使用 `{DB_SCHEMA}.table_name` 动态拼接（已做白名单校验，安全性可控），或依赖 `search_path`。

- [ ] **Step 4: 更新配置和文档**

`.env.example` 和文档统一 schema 名称。

- [ ] **Step 5: Commit**

---

### Phase 3: 基础设施加固（第 3-4 周）

#### Task 12: 引入迁移版本管理

**Files:**
- Create: `backend/migrations/schema_migrations.sql`
- Modify: `backend/app/database.py`

- [ ] **Step 1: 创建迁移版本表**

```sql
-- migrations/000_schema_migrations.sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    hash VARCHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

- [ ] **Step 2: 修改 run_migrations 实现版本管理**

- 读取 `schema_migrations` 表
- 只执行未执行过的迁移文件
- 计算文件 SHA256 hash 并记录
- 执行失败阻断启动

- [ ] **Step 3: 修正重复编号**

将重复的 002 和 004 文件重命名为唯一编号。

- [ ] **Step 4: 确保所有迁移 DDL 幂等**

为所有 ALTER TABLE 添加 `IF EXISTS` / `IF NOT EXISTS`。

- [ ] **Step 5: Commit**

---

#### Task 13: 落地数据库审计

**Files:**
- Create: `backend/migrations/XXX_create_audit_log.sql`
- Modify: `backend/app/auth/audit.py`

- [ ] **Step 1: 创建 eam_audit_log 表**

```sql
CREATE TABLE IF NOT EXISTS eam_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    roles JSONB,
    resource VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    reason TEXT,
    request_id VARCHAR(64),
    client_ip VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

- [ ] **Step 2: 修改 audit_allow / audit_deny 写入数据库**

```python
async def audit_allow(db: AsyncSession, user, resource, action, ...):
    # Write to eam_audit_log
    await db.execute(
        text("INSERT INTO eam_audit_log (...) VALUES (...)"),
        {...}
    )

async def audit_deny(db: AsyncSession, user, resource, action, reason, ...):
    # Write to eam_audit_log
    await db.execute(
        text("INSERT INTO eam_audit_log (...) VALUES (...)"),
        {...}
    )
```

- [ ] **Step 3: Commit**

---

#### Task 14: JWT audience 校验

**Files:**
- Modify: `backend/app/ee/auth/keycloak_provider.py`

- [ ] **Step 1: 增加 AUDIENCE 配置**

```python
# config.py
JWT_AUDIENCE: str | None = Field(default=None)
```

- [ ] **Step 2: 开启 audience 校验**

```python
# keycloak_provider.py
payload = jwt.decode(
    token,
    key,
    algorithms=["RS256"],
    audience=settings.JWT_AUDIENCE or settings.KEYCLOAK_CLIENT_ID,
    options={"verify_aud": True, "verify_exp": True},
)
```

- [ ] **Step 3: JWKS 获取失败时拒绝，不 fallback**

- [ ] **Step 4: Commit**

---

#### Task 15: 增强 API 测试覆盖

**Files:**
- Create/Modify: `api-tests/tests/`

- [ ] **Step 1: 增加鉴权测试**

```python
# test_auth_enforcement.py
def test_unauthenticated_returns_401():
    response = client.get("/api/avdm/projects")
    assert response.status_code == 401

def test_insufficient_role_returns_403():
    response = normal_user_client.post("/api/avdm/evaluate", ...)
    assert response.status_code == 403
```

- [ ] **Step 2: 增加 Team Members 持久化测试**

```python
def test_create_team_member_persists():
    response = client.post("/api/projects/{id}/members", ...)
    assert response.status_code == 201
    # Verify GET returns the member
    get_response = client.get(f"/api/projects/{id}/members")
    assert member in get_response.json()["data"]
```

- [ ] **Step 3: 增加 envelope 契约测试（2xx/201/204）**

- [ ] **Step 4: Commit**

---

### Phase 4: 前端体验优化（第 4-6 周）

#### Task 16: 拆分超大页面

**Files (create/modify):**

Request Create 拆分：
- Create: `frontend/src/features/review/components/request-create/Step1ProjectForm.tsx`
- Create: `frontend/src/features/review/components/request-create/Step2Questionnaire.tsx`
- Create: `frontend/src/features/review/components/request-create/Step3Handoff.tsx`
- Create: `frontend/src/features/review/hooks/useCreateRequest.ts`
- Modify: `frontend/src/app/(architecture_review)/ea-review/(standalone)/request/create/page.tsx`

BCM 拆分：
- Create: `frontend/src/features/portfolio/components/bcm/SearchPanel.tsx`
- Create: `frontend/src/features/portfolio/components/bcm/BcmTable.tsx`
- Create: `frontend/src/features/portfolio/components/bcm/BcmDrawer.tsx`
- Modify: `frontend/src/app/(application_management)/app-management/bcm/page.tsx`

TechStack Modal 拆分：
- Create: `frontend/src/features/tech-stack/components/detail/GeneralInfoTab.tsx`
- Create: `frontend/src/features/tech-stack/components/detail/CatalogTab.tsx`
- Create: `frontend/src/features/tech-stack/components/detail/TeamTab.tsx`
- Create: `frontend/src/features/tech-stack/components/detail/LogTab.tsx`
- Modify: `frontend/src/features/tech-stack/components/lifecycle/ApplicationTechStackModal.tsx`

- [ ] **Step 1-N: 逐个拆分，每个拆分后运行 lint 和 build 验证**

```bash
cd frontend && npm run lint && npm run build
```

- [ ] **Commit after each component split**

---

#### Task 17: 统一设计系统规范

**Files:**
- Create: `docs/standards/ui-guidelines.md`

- [ ] **Step 1: 建立 UI 规范文档**

明确：
- 表单统一使用 AntD `Form.Item`
- 表格统一使用 `DataTable` 封装
- 抽屉/Modal 统一使用 AntD 组件
- Tailwind 仅用于布局（flex/grid/spacing）
- 颜色令牌从 AntD theme token 派生

- [ ] **Step 2: 逐步迁移不符合规范的组件**

- [ ] **Step 3: Commit**

---

#### Task 18: 补齐可访问性

**Files (modify: 多个文件)**

- [ ] **Step 1: 全局图标按钮加 aria-label**

搜索所有 `<Button icon={...} />` 和 `<button>` 图标按钮，添加 `aria-label`。

- [ ] **Step 2: 表单 label 加 htmlFor**

搜索所有 `<label>` 元素，确保有关联的 `htmlFor`。

- [ ] **Step 3: 自定义 drawer 加 ARIA 属性**

为自定义 overlay drawer 添加 `role="dialog"`, `aria-modal="true"`, Esc 关闭, 焦点陷阱。

- [ ] **Step 4: Mindmap 提供键盘支持或列表视图**

- [ ] **Step 5: 运行 lint 验证**

```bash
cd frontend && npm run lint
# 如果配置了 eslint-plugin-jsx-a11y
```

- [ ] **Commit after each category**

---

#### Task 19: 移动端适配策略

**Files:**
- Create: `docs/standards/mobile-guidelines.md`

- [ ] **Step 1: 建立移动端适配规范**

定义：
- 最小支持宽度：768px（平板）/ 375px（手机）
- 表格降级策略：复杂表格提供 Card List 视图
- 抽屉/Modal：小屏全屏
- Mindmap：移动端展示简化列表视图

- [ ] **Step 2: 为 DataTable 增加卡片视图模式**

```tsx
<DataTable
  mobileView="cards"  // 新增 prop
  columns={...}
  dataSource={...}
/>
```

- [ ] **Step 3: 核心页面逐步适配**

- [ ] **Commit**

---

### Phase 5: 文档与部署（第 6-8 周）

#### Task 20: 统一版本矩阵

**Files:**
- Modify: `docs/architecture.md`
- Modify: `README.md`
- Modify: `docs/design.md`
- Modify: `.python-version`
- Modify: `frontend/package.json` (如需要)

- [ ] **Step 1: 确定当前真实 Runtime 版本**

```bash
node --version
python --version
cd frontend && npm ls next react antd --depth=0
```

- [ ] **Step 2: 在 docs/architecture.md 增加 Runtime Matrix 表格**

```markdown
| Component | Version |
|-----------|---------|
| Node.js   | 22.x    |
| Python    | 3.12.x  |
| Next.js   | 16.x    |
| React     | 19.x    |
| AntD      | 6.x     |
| FastAPI   | 0.115.x |
| PostgreSQL| 16      |
```

- [ ] **Step 3: 同步所有文档和配置文件**

- [ ] **Step 4: Commit**

---

#### Task 21: 更新授权文档

**Files:**
- Modify: `docs/authorization.md`

- [ ] **Step 1: 以源码为准重写角色模型**

列出 5 个角色：Normal_User, EA_Admin, EA_Reviewer, App_Owner, Project_Owner，每种角色的权限矩阵、默认角色。

- [ ] **Step 2: Commit**

```bash
git add docs/authorization.md
git commit -m "docs: update authorization model to match Role enum"
```

---

#### Task 22: 重整设计文档

**Files:**
- Modify: `docs/design.md`
- Modify or Delete: `docs/design-En.md`

- [ ] **Step 1: 修复 design.md 编码问题，更新架构到当前版本**

- [ ] **Step 2: design-En.md 要么完整翻译，要么删除**

- [ ] **Step 3: Commit**

---

#### Task 23: 规范 OpenSpec 组织

**Files:**
- Move: `openspec/specs/authorization/proposal.md` → `openspec/changes/authorization/proposal.md`
- Move: `openspec/specs/authorization/tasks.md` → `openspec/changes/authorization/tasks.md`
- Modify: `openspec/config.yaml`

- [ ] **Step 1: 分离 proposal/tasks 到 changes 目录**

- [ ] **Step 2: 填写 openspec/config.yaml**

```yaml
project: AxisArch
description: Enterprise Architecture Management Platform
conventions:
  naming: kebab-case
  api_prefix: /api
  module_registration: module_registry.py
```

- [ ] **Step 3: Commit**

---

#### Task 24: 清理仓库结构

- [ ] **Step 1: 检查未忽略的构建产物**

```bash
git ls-files backend/venv
git ls-files frontend/tsc_output.txt
git ls-files frontend/tsc_errors.log
git ls-files frontend/build_log.txt
git ls-files frontend/test-results/
```

- [ ] **Step 2: 从 Git 移除不应跟踪的文件**

```bash
git rm --cached frontend/tsc_output.txt frontend/tsc_errors.log frontend/build_log.txt  # if tracked
```

- [ ] **Step 3: 完善 .gitignore**

```gitignore
backend/venv/
frontend/tsc_output.txt
frontend/tsc_errors.log
frontend/build_log.txt
frontend/test-results/
```

- [ ] **Step 4: Commit**

---

#### Task 25: 提供 Docker 部署方案

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`

- [ ] **Step 1: 创建 docker-compose.yml（PostgreSQL + backend + frontend）**

```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: axisarch
      POSTGRES_USER: axisarch
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://axisarch:${DB_PASSWORD}@db:5432/axisarch
    depends_on:
      - db
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend
    ports:
      - "3000:3000"

volumes:
  pgdata:
```

- [ ] **Step 2: 创建 backend/Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: 创建 frontend/Dockerfile**

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
CMD ["npm", "start"]
```

- [ ] **Step 4: Commit**

---

#### Task 26: 更新 STATUS.md 反映真实完成度

**Files:**
- Modify: `docs/STATUS.md`

- [ ] **Step 1: 逐模块核实实现文件存在性**

```bash
ls backend/app/architecture_review/
ls backend/app/application_management/
ls backend/app/add/
ls backend/app/technology_stack_management/
ls backend/app/project_management/
ls backend/app/data_management/
```

- [ ] **Step 2: 更新 STATUS.md**

以实际文件存在为准，标注每个功能的真实状态。移除不存在实现的功能声明。增加"需确认"标记的功能。

- [ ] **Step 3: Commit**

---

## 十、持续改进建议

1. **CI 流程:** 每个 PR 自动运行 `backend/pytest` + `api-tests/pytest` + `frontend/lint` + `frontend/build` + `frontend/playwright`
2. **API 文档自动校验:** CI 中对比 `openapi.json` vs `docs/api.md`，检测不一致
3. **定期安全审计:** 每季度审查 RBAC 配置、依赖漏洞、敏感信息扫描
4. **可访问性 CI:** 集成 `eslint-plugin-jsx-a11y` 和 `axe-core` 到 CI
5. **模块契约测试:** 新模块 PR 必须附带 `ENABLED_MODULES` 组合测试
6. **版本矩阵单一来源:** `docs/architecture.md` 的 Runtime Matrix 作为唯一来源，其他文档和配置文件引用它
