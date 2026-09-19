# AxisArch 模块划分与开发管理建�?

## 背景

AxisArch 系统采用前后端分离架构：`frontend`（Next.js 15�? `backend`（FastAPI + SQLAlchemy async）。后端已�?TypeScript (Express + Prisma) 完整迁移�?Python，共 23 �?router 模块（含 auth）、~6,100+ �?Python 代码。认证授权框架已建设完成（RBAC + AuthMiddleware + 81 个端点权限接入）。数据库 schema 文档保留�?`docs/schema.prisma`�?

当前所有开发在 `main` 分支上进行，�?CI/CD 流水线。团队成员各自使�?Claude Code / Codex 模式开发，需要模块边界清晰、冲突最小化�?

---

## 一、模块划分建�?

基于代码耦合度分析，建议划分�?**5 个功能模�?+ 1 个通用支持�?*，每人负责一个模块（前后端一体），模块间通过数据�?schema �?API 契约协调�?

### 模块 A：EA Review 流程核心 ⭐（最复杂，建�?人）

**范围�?* EA 评审全流�?�?申请、评审、会议、行动项、日�?

| �?| 文件 | 行数 |
|---|------|------|
| Backend | `app/routers/ea_requests.py` | 979 |
| Backend | `app/routers/scope.py` | 445 |
| Backend | `app/routers/actions.py` | 412 |
| Backend | `app/routers/meetings.py` | 352 |
| Backend | `app/routers/schedules.py` | 330 |
| Backend | `app/routers/meeting_decks.py` | 104 |
| Frontend | `ea-review/request-summary/page.tsx` | 111 |
| Frontend | `ea-review/request/[id]/page.tsx` | 878 |
| Frontend | `ea-review/request/create/page.tsx` | 349 |
| Frontend | `ea-review/request/[id]/create-meeting/page.tsx` | 356 |
| Frontend | `ea-review/meetings/page.tsx` + `[meetingNo]/page.tsx` | 343 |
| Frontend | `ea-review/actions/page.tsx` + `[actionId]/page.tsx` | 538 |
| Frontend | `ea-review/calendar/page.tsx` | 95 |
| **后端小计** | | **2,622 �?* |
| **前端小计** | | **~2,670 �?* |

**DB Tables�?* `pamp_request`, `pamp_request_attachment`, `pamp_arch_ai_check`, `pamp_actions`, `pamp_meetings`, `pamp_ea_calendar`, `pamp_scope_of_change`, `pamp_scope_check_list`

**耦合说明�?* 这是系统的核心聚合根，`pamp_request` 表是枢纽，actions/meetings/scope 都通过 request_id 关联�?

**两人分工建议�?*
- 人员 A1：Request 生命周期 + Scope（`ea_requests.py` 979�? `scope.py` 445�? 前端 request 相关页面�?
- 人员 A2：Meeting + Action + Calendar（`meetings.py` 352�? `actions.py` 412�? `schedules.py` 330�? `meeting_decks.py` 104�? 前端对应页面�?

---

### 模块 B：App Solution 维护

**范围�?* 应用数据维护 �?BCM 数据管理、Business Capability Master Data、CMDB、技术栈（纯 CRUD 维护，不含分析）

| �?| 文件 | 行数 |
|---|------|------|
| Backend | `app/routers/applications.py`（BCM CRUD 部分�?| ~350 |
| Backend | `app/routers/cmdb.py` | 169 |
| Backend | `app/routers/BizCapability.py` | 123 |
| Backend | `app/routers/technology_stack.py` | 116 |
| Frontend | `app-management/bcm/page.tsx` | 675 |
| Frontend | `app-management/cmdb/page.tsx` | 260 |
| Frontend | `app-management/BizCapability/page.tsx` | 86 |
| Frontend | `tech-stack/page.tsx` + `master-data/page.tsx` | 194 |
| **后端小计** | | **~758 �?* |
| **前端小计** | | **~1,215 �?* |

**DB Tables�?* `project_app`, `cmdb_application`, `bcpf_master_data`, `tech_stack_*`

**耦合度：�?* �?主要是独立的 master data CRUD，与 EA Review 模块仅通过 `project_app` 表有弱关联�?

**测试覆盖�?* �?已有 3 �?Playwright E2E 测试（`cmdb.spec.ts`, `bcm.spec.ts`, `BizCapability.spec.ts`�?

---

### 模块 C：业务分析与报表

**范围�?* Dashboard、Reports、业务能力分析可视化（纯分析视角，不含日志和导出�?

| �?| 文件 | 行数 |
|---|------|------|
| Backend | `app/routers/reports.py` | 126 |
| Backend | `app/routers/dashboard.py` | 61 |
| Backend | `app/routers/applications.py`（BCM visualization 部分�?| ~153 |
| Frontend | `(sidebar)/reports/ea-review-dashboard/page.tsx` | 1,482 |
| Frontend | `(sidebar)/reports/ea-review-dashboard/` 子页�?(6�? | ~1,522 |
| Frontend | `(sidebar)/reports/lead-time/page.tsx` | 72 |
| Frontend | 首页 `page.tsx` (Dashboard) | 194 |
| Frontend | `app-management/bc-visualization/page.tsx` | 99 |
| Frontend | `components/bc-visualization/` (12 files，含 MindMap/Dashboard/Layout) | ~800 |
| **后端小计** | | **~340 �?* |
| **前端小计** | | **~4,169 �?* |

**DB Tables�?* 只读聚合查询，不拥有独立表；BC Visualization 读取 `project_app` + `cmdb_application` + `bcpf_master_data` 做分�?

**耦合说明�?* 纯读取型模块，依赖其他模块的表做聚合统计�?*不会与其他模块产生写冲突**。BC Visualization 的数据来源由模块 B 维护，本模块只做分析展示�?

**注意�?* `ea-review-dashboard/page.tsx` 是全项目最大文件（1,482行），建议拆分为独立组件�?

**测试覆盖�?* �?已有 1 �?Playwright E2E 测试（`bc-visualization.spec.ts`�?

---

### 通用支持�?F：日志、导出、通用服务

**范围�?* Audit Log、EA Review Log、Email Log、CSV 导出 �?供各模块共同调用

| �?| 文件 | 行数 |
|---|------|------|
| Backend | `app/routers/export.py` | 341 |
| Backend | `app/routers/audit_log.py` | 275 |
| Backend | `app/routers/ea_review_logs.py` | 84 |
| Backend | `app/utils/csv_export.py` | 31 |
| Frontend | `(sidebar)/reports/email-log/page.tsx` | 80 |
| Frontend | `(sidebar)/settings/audit-log/page.tsx` | 66 |
| Frontend | `components/ui/ExportButton.tsx` | 通用组件 |
| **后端小计** | | **731 �?* |
| **前端小计** | | **~146 �?* |

**定位�?* 横切关注点，不属于任何业务模块，各模块按需调用�?
- **CSV 导出**：`export.py` 根据 entity 参数导出不同模块数据（ea-requests, bcm, meetings 等），各模块新增实体时只需在此扩展
- **审计日志**：`audit_log.py` 记录所有模块的字段变更和操作日�?
- **邮件日志**：actions/meetings 发送邮件的记录查询

**归属建议�?* 可由模块 D（用户权限）负责人兼管，因日�?权限天然关联；也可单独指定一人负责�?

---

### 模块 D：用户与权限 �?已建设完�?

**范围�?* 认证中间件、RBAC 权限矩阵、SSO 集成、用户管理、团队成�?

| �?| 文件 | 行数 | 状�?|
|---|------|------|------|
| Backend | `app/auth/__init__.py` | 6 | �?新建 |
| Backend | `app/auth/models.py` | ~30 | �?新建 �?Role enum + AuthUser |
| Backend | `app/auth/rbac.py` | ~60 | �?新建 �?ROLE_PERMISSIONS 矩阵 |
| Backend | `app/auth/providers.py` | ~200 | �?新建 �?DevAuthProvider + KeycloakAuthProvider (JWKS 验签) |
| Backend | `app/auth/middleware.py` | ~76 | �?新建 �?AuthMiddleware |
| Backend | `app/auth/dependencies.py` | ~97 | �?新建 �?require_auth / require_role / require_permission |
| Backend | `app/routers/auth.py` | ~40 | �?新建 �?/api/auth/me + /api/auth/permissions |
| Backend | `app/routers/team_members.py` | 233 | 已有 |
| Backend | `app/routers/resources.py` | 148 | 已有 |
| Frontend | `src/lib/auth-context.tsx` | ~132 | �?新建 �?AuthProvider + useAuth + usePermission |
| Frontend | `src/lib/auth-token.ts` | ~30 | �?新建 �?Token 管理 (setAuthToken / authHeaders) |
| Frontend | `src/components/ui/PermissionGate.tsx` | ~35 | �?新建 �?权限门控组件 |
| Frontend | `(sidebar)/settings/team-members/page.tsx` | 173 | 已有 |
| Frontend | `(sidebar)/resources/page.tsx` | 66 | 已有 |
| **后端小计** | | **~890 �?* |
| **前端小计** | | **~436 �?* |

**DB Tables�?* `resource_pool`, `pamp_bigea_team_members`, `user_profile`

**认证架构（已实现）：**

```
AUTH_DISABLED=true  �?DevAuthProvider（固�?dev_admin 用户，开发模式）
AUTH_DISABLED=false �?KeycloakAuthProvider（JWKS 签名验证，生产模式）
                      �?
              AuthMiddleware �?request.state.user
                      �?
              Depends(require_permission("resource", "scope"))
```

**RBAC 角色体系�? 角色）：**

| 角色 | 旧系统对�?| 说明 |
|------|-----------|------|
| `admin` | `_SYS_ADMIN` | 全部权限 `*:*` |
| `ea_reviewer` | 新增 | 评审流程读写，其余只�?|
| `editor` | `_SYS_DEVELOPER` | 数据维护读写，评审只�?|
| `viewer` | `_SYS_BASIC` | 只读 |

**接入状态：** 全部 22 �?router�?1 个端点已通过 `Depends(require_permission(...))` 接入 RBAC，对业务代码零侵入�?

**待完成：** Keycloak 生产对接（前�?keycloak-js 适配�?+ 端到端测试），详�?`plans/buzzing-dancing-mist.md` Phase 5�?

---

### 模块 E：基础数据与配�?

**范围�?* Master Data、字典选项、Certification、Projects、Help

| �?| 文件 | 行数 |
|---|------|------|
| Backend | `app/routers/projects.py` | 301 |
| Backend | `app/routers/master_data.py` | 163 |
| Backend | `app/routers/certifications.py` | 103 |
| Backend | `app/routers/dict_options.py` | 76 |
| Frontend | `projects/page.tsx` | 96 |
| Frontend | `certification/page.tsx` | 91 |
| Frontend | `(sidebar)/master-data/page.tsx` | 144 |
| Frontend | `(sidebar)/data-privacy/page.tsx` | 120 |
| Frontend | `(sidebar)/help/page.tsx` | 77 |
| Frontend | `(sidebar)/settings/scope-change/page.tsx` | 68 |
| Frontend | `(sidebar)/settings/scope-checklist/page.tsx` | 91 |
| **后端小计** | | **643 �?* |
| **前端小计** | | **~687 �?* |

**DB Tables�?* `dict_option`, `data_classification`, `company`, `data_center`, `project`, `certification`, `help_file`

**耦合度：�?* �?提供基础数据给其他模块消费。`projects.py` �?EA Review 引用但仅通过 `project_id` FK�?

---

### 模块依赖关系�?

```
    ┌──────────────────�?  ┌─────────────────────�?
    �? D: 用户权限 �?   �?  �?F: 通用支持 (日志/导出)�?
    �? AuthMiddleware   �?  └──────────┬──────────�?
    �? RBAC + Depends() �?             �?各模块调�?
    └──────┬───────────�?  ┌───────────�?
           �?81端点已接�?   �?
    ┌──────┴───────────────┴───────────�?
    �?                                  �?
┌───┴────────�? ┌──────────�? ┌────────┴──────�?
�?A: EA Review│←→│E: 基础数据�? �?B: App维护     �?
�? (核心流程) �? �?(projects)�? �?(CRUD/MasterData)�?
└───┬────────�? └──────────�? └──────┬────────�?
    �?只读                           �?数据供给
    �?                               �?
┌────────────────────────────────────────�?
�? C: 业务分析/报表 (只读聚合 + BC可视�?  �?
└────────────────────────────────────────�?
```

### 各模块代码量汇�?

| 模块 | 后端 (Python) | 前端 (TSX) | 合计 | 建议人数 |
|------|--------------|-----------|------|---------|
| A: EA Review 流程核心 | 2,622 �?| ~2,670 �?| ~5,292 �?| 2 �?|
| B: App Solution 维护 | ~758 �?| ~1,215 �?| ~1,973 �?| 1 �?|
| C: 业务分析与报�?| ~340 �?| ~4,169 �?| ~4,509 �?| 1 �?|
| D: 用户与权�?�?| ~890 �?| ~436 �?| ~1,326 �?| 1 �?|
| E: 基础数据与配�?| 643 �?| ~687 �?| ~1,330 �?| 1 �?|
| F: 通用支持 (日志/导出) | 731 �?| ~146 �?| ~877 �?| D兼管或独�?�?|
| **共享基础设施** | 175 �?| ~450 �?| ~625 �?| �?|

---

## 二、共享基础设施（所有模块共用）

### 后端共享文件（修改需全员协调�?

| 文件 | 行数 | 说明 |
|------|------|------|
| `app/main.py` | ~80 | Router 注册、CORS 配置、AuthMiddleware 注册 |
| `app/database.py` | 26 | 数据库连接池、schema 切换 |
| `app/config.py` | ~28 | 环境变量配置（含 AUTH_*、KEYCLOAK_* 配置�?|
| `app/auth/` | ~510 | 认证授权模块（models / rbac / providers / middleware / dependencies�?|
| `app/utils/pagination.py` | 34 | 分页参数和响应构�?|
| `app/utils/filters.py` | 25 | 多值过滤条件构�?|
| `app/utils/csv_export.py` | 31 | CSV 导出和注入防�?|

### 前端共享文件（修改需全员协调�?

| 文件/目录 | 说明 |
|----------|------|
| `src/lib/api.ts` | 通用 API 客户�?+ fetchBlob（~50行，�?authHeaders 自动注入�?|
| `src/lib/auth-context.tsx` | AuthProvider + useAuth / usePermission hooks |
| `src/lib/auth-token.ts` | Token 管理（getAuthToken / setAuthToken / authHeaders�?|
| `src/components/ui/` | 19 个通用 UI 组件（含 PermissionGate、SearchForm 等） |
| `src/components/layout/` | 5 个布局组件（Header, Sidebar 含权限过滤等�?|

---

## 三、代码管理：Git 分支工作�?

### 推荐�?*必须使用 Pull/Merge Request**

Claude Code / Codex 生成的代码量大、速度快，**没有 code review 极易引入隐蔽问题**�?

### 分支规范

```
main (受保�? 不可直接 push)
  �?
  ├── feature/module-a/request-lifecycle    �?人员 A1
  ├── feature/module-a/meetings-actions     �?人员 A2
  ├── feature/module-b/BizCapability-crud           �?人员 B
  ├── feature/module-c/dashboard-reports   �?人员 C
  ├── feature/module-d/auth-middleware     �?人员 D
  └── feature/module-e/master-data        �?人员 E
```

| 规则 | 说明 |
|-----|------|
| **分支命名** | `feature/module-X/功能描述` |
| **保护 main** | Settings �?Protected Branches �?禁止直接 push |
| **MR/PR 必须** | 至少 1 �?approve（模�?owner 互审�?|
| **合并策略** | Squash merge（保�?main 历史整洁�?|
| **冲突解决** | 每天�?main rebase 一次，避免大冲�?|

### 冲突高危文件（修改时需通知全员�?

| 文件 | 原因 |
|------|------|
| `backend/app/main.py` | Router 注册 + 中间件注册，新增模块必改 |
| `backend/app/config.py` | 环境变量，新增配置项必改 |
| `backend/app/auth/rbac.py` | 权限矩阵，新增资�?角色时需修改 |
| `backend/app/database.py` | 数据库配�?|
| `backend/app/utils/*.py` | 共享工具函数 |
| `frontend/src/lib/api.ts` | API 客户端（�?auth header 注入�?|
| `frontend/src/lib/auth-context.tsx` | Auth Provider，权限判断逻辑 |
| `frontend/src/lib/constants.ts` | 导航定义 + 权限配置（requiredResource�?|
| `frontend/src/components/ui/*` | 共享 UI 组件（含 PermissionGate�?|
| `frontend/src/components/layout/*` | 导航菜单（Sidebar 含权限过滤） |
| `docs/schema.prisma` | 数据库模型文�?|

### 针对 Claude Code 的特别建�?

1. **每个 session 开始前** `git pull --rebase origin main`
2. **频繁小提�?*，不要等一个大功能做完再提�?
3. **PR 描述**�?Claude Code 自动生成，人工审核关键变�?
4. **后端新增 router** 需�?`main.py` 注册 �?容易冲突，及时合�?

---

## 四、测试策�?

### 现有测试资产

| 测试类型 | 位置 | 覆盖范围 |
|---------|------|---------|
| Python API 测试 | `api-tests/` | 19 个模块（�?auth），覆盖全部 23 �?backend router，共 201 个测�?|
| Playwright E2E | `frontend/e2e/` | 4 个文件：bcpf, bc-visualization, bcm, cmdb |
| 后端单元测试 | �?不存�?| 需要建�?|

### 测试优先�?

| 优先�?| 内容 | 方式 | 状�?|
|-------|------|------|------|
| 🔴 P0 | 每次 PR 必须通过 | Python API 测试 + 前端编译检�?| �?|
| 🔴 P0 | 模块 D 认证中间�?| API 测试覆盖 auth/me + permissions | �?4 个测�?|
| 🟡 P1 | 模块 A EA Request 状态机 | API 测试覆盖所有状态转�?| �?|
| 🟡 P1 | 模块 C 报表数据准确�?| API 测试对比聚合结果 | �?|
| 🟢 P2 | 前端交互 | Playwright E2E 覆盖关键路径 | �?|
| 🟢 P2 | 后端单元测试 | 复杂计算逻辑（评分、统计） | �?|

### CI 建议配置

每次 PR 自动运行�?
1. Python API 测试（`cd api-tests && pytest`�?
2. 前端编译检查（`cd frontend && npm run build`�?
3. Playwright E2E 测试（`cd frontend && npx playwright test`�?

---

## 五、Python 后端特有的架构改进建�?

### 当前状�?

1. **�?Model/Schema �?* �?`app/models/` �?`app/schemas/` 目录存在但为空，所有逻辑内联�?router �?
2. **原始 SQL** �?直接�?`text()` �?SQL，无 ORM model
3. ~~**无认证中间件**~~ �?�?已完成：AuthMiddleware + RBAC + 全部 81 个端点接�?`Depends(require_permission(...))`

### 建议的渐进式改进

```
阶段1（当前）：直接在 router 中写 SQL + 手动字段映射
    �?各模块独立推进，不阻�?
阶段2：抽�?Pydantic schemas �?app/schemas/（类型安�?+ 自动文档�?
    �?
阶段3：✅ 已完�?�?认证中间�?+ RBAC 权限矩阵 + 前端 PermissionGate
    �?
阶段4（可选）：SQLAlchemy ORM models（如�?SQL 维护成本过高�?
    �?
阶段5（待做）：Keycloak SSO 生产对接（前�?keycloak-js + 端到端测试）
```

**FastAPI 自动文档优势�?* 后端启动后访�?`http://localhost:4000/docs` 即可查看所�?API �?Swagger 文档，无需额外维护�?

**权限接入方式�?* 各模�?router 通过 `Depends()` 零侵入接入，新增端点只需在装饰器中声明所需资源�?scope�?
```python
@router.post("", dependencies=[Depends(require_permission("ea_request", "write"))])
```
新增资源类型时需修改 `app/auth/rbac.py` �?`ROLE_PERMISSIONS` 矩阵�?

---

## 六、实施建议时间线

| 阶段 | 动作 | 负责�?|
|-----|------|-------|
| **�?�?* | Git 配置：保�?main 分支，开�?PR 必须审批 | 项目负责�?|
| **�?�?* | 每人 fork 自己�?feature 分支 | 全员 |
| **�?�?* | 搭建 CI 基础配置（API 测试 + 前端编译�?| 模块 D 负责�?|
| **�?�?* | 确认共享文件的修改流程（PR + 全员通知�?| 全员 |
| **持续** | 每天 rebase main，小步提交，及时 PR | 全员 |
