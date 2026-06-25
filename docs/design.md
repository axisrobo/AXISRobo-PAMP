# AxisArch 系统详细设计文档

> **注意:** 本文档最后更新于 2026-03-26，部分内容已过时。以 docs/architecture.md 为当前架构参考。
>
> 版本: 2.0.0 | 生成日期: 2026-03-26

---

---

## 目录

1. [系统概览](#1-系统概览)
2. [技术栈](#2-技术栈)
3. [系统架构](#3-系统架构)
4. [后端详细设计](#4-后端详细设计)
   - 4.1 [应用入口与中间件](#41-应用入口与中间件)
   - 4.2 [认证与授权（Auth）](#42-认证与授权auth)
   - 4.3 [模块 A：EA Review（EA审查）](#43-模块-a-ea-reviewea审查)
   - 4.4 [模块 B：App Solution（应用管理）](#44-模块-b-app-solution应用管理)
   - 4.5 [模块 C：Reports & Analytics（报表分析）](#45-模块-c-reports--analytics报表分析)
   - 4.6 [模块 D：Auth & Users（用户管理）](#46-模块-d-auth--users用户管理)
   - 4.7 [模块 E：Config & Data（配置数据）](#47-模块-e-config--data配置数据)
   - 4.8 [模块 F：Shared Services（共享服务）](#48-模块-f-shared-services共享服务)
   - 4.9 [AI Agent（架构检查智能体）](#49-ai-agent架构检查智能体)
   - 4.10 [定时任务](#410-定时任务)
5. [数据库设计](#5-数据库设�?
   - 5.1 [Schema 概览](#51-schema-概览)
   - 5.2 [核心表结构](#52-核心表结�?
6. [前端详细设计](#6-前端详细设计)
   - 6.1 [整体结构](#61-整体结构)
   - 6.2 [路由设计](#62-路由设计)
   - 6.3 [页面模块详细说明](#63-页面模块详细说明)
   - 6.4 [公共组件库](#64-公共组件�?
   - 6.5 [核心工具层](#65-核心工具�?
7. [API 接口汇总](#7-api-接口汇�?
8. [安全设计](#8-安全设计)
9. [数据流转图](#9-数据流转�?

---

## 1. 系统概览

AxisArch 是一个通用的企业架构管理平台，主要承载以下核心业务�?

| 业务�?| 功能描述 |
|--------|----------|
| **EA Review（EA审查�?* | 管理项目 EA 审查请求的全生命周期，包括提交、受理、评审、完结、退回等状态流转，以及关联会议、行动项、日程、附件管�?|
| **App Solution（应用管理）** | 管理企业应用系统，维护业务能力映射（BCM），管理技术栈，对�?CMDB |
| **Reports & Analytics（报表分析）** | EA 审查数据统计与可视化，包括状态分布、月度趋势、架构评分分布、Lead Time 分析�?|
| **BC Visualization（业务能力可视化�?* | �?Heatmap/Mindmap 形式展示 BCPF（Business Capability Presentation Framework）与应用系统的映射关�?|
| **Certification（认证管理）** | 管理团队成员的技术认证，包括批量导入、提醒通知 |
| **Master Data（主数据�?* | 数据中心、数据分类、法律实体等参考数据管�?|
| **Settings（系统设置）** | 审计日志、团队成员管理、审查范围配�?|

---

## 2. 技术栈

### 后端

| 组件 | 版本/选型 |
|------|-----------|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| ORM/数据库驱�?| SQLAlchemy (AsyncIO) + asyncpg |
| 数据�?| PostgreSQL（Schema: `eam`�?|
| 认证 | Keycloak（JWT/OIDC�?|
| 数据迁移 | 自定�?SQL 文件（启动时执行�?|
| 定时任务 | APScheduler（AsyncIOScheduler�?|
| 文件存储 | S3 兼容对象存储 |
| AI 集成 | LangChain + 自定�?Workflow（架构图 AI 检查） |
| 邮件服务 | 企业邮件 API（异步发送） |
| Excel 导出 | openpyxl |

### 前端

| 组件 | 版本/选型 |
|------|-----------|
| 框架 | Next.js 14（App Router�?|
| 语言 | TypeScript（严格模式） |
| UI 组件�?| Ant Design v6 |
| 样式 | Tailwind CSS |
| 状态管�?| Zustand（全局�? React Query（服务器状态） |
| 认证 | Keycloak JS Adapter |
| 图表 | 自定�?Canvas/SVG 组件 |
| 端到端测�?| Playwright |

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────────────�?
�?                        浏览�?(Next.js SSR/CSR)                      �?
�? ┌──────────�? ┌──────────�? ┌──────────�? ┌───────────────────�? �?
�? �?EA Review�? �?  Apps   �? �?Reports  �? �? Settings / Data  �? �?
�? └────┬─────�? └────┬─────�? └────┬─────�? └─────────┬─────────�? �?
�?      └─────────────┴─────────────┴───────────────────�?           �?
�?                         API Layer (api.ts)                          �?
�?                   Authorization Header (Bearer JWT)                  �?
└────────────────────────────────┬────────────────────────────────────�?
                                 �?HTTPS
                                 �?
┌─────────────────────────────────────────────────────────────────────�?
�?                    FastAPI Backend (Port 4000)                       �?
�? ┌────────────�? ┌──────────────�? ┌──────────────────────────────�?�?
�? �?   CORS    �? �? AuthMiddle  �? �? ResponseEnvelopeMiddleware  �?�?
�? �?Middleware �? �?   ware      �? �? { code, message, data, ts } �?�?
�? └────────────�? └──────┬───────�? └──────────────────────────────�?�?
�?                        �?                                           �?
�? ┌──────────────────────▼───────────────────────────────────────�?  �?
�? �?                    Router Modules                            �?  �?
�? �? EA Review | App Solution | Reports | Auth | Config | Shared  �?  �?
�? └──────────────────────┬───────────────────────────────────────�?  �?
�?                        �?                                           �?
�? ┌──────────────────────▼───────────────────────────────────────�?  �?
�? �?             SQLAlchemy AsyncSession (asyncpg)                �?  �?
�? └──────────────────────┬───────────────────────────────────────�?  �?
└───────────────────────────────────────────────────────────────────  �?
                          �?                                           �?
         ┌────────────────┴─────────────────�?                        �?
         �?                                 �?                         �?
   ┌───────────�?                   ┌──────────────�?                 �?
   �?PostgreSQL�?                   �? S3 Storage  �?                 �?
   �? (eam.*)  �?                   �? (Attachments�?                 �?
   └───────────�?                   �?  /Decks)    �?                 �?
                                    └──────────────�?                 �?
         �?                                                            �?
         �?                                                            �?
   ┌─────┴──────�?         ┌──────────────────────�?                 �?
   �?APScheduler�?         �?   Keycloak (OIDC)    �?                 �?
   �?CMDB Sync  �?         �? Token Validation     �?                 �?
   �?Daily 02:00�?         └──────────────────────�?                 �?
   └────────────�?
```

---

## 4. 后端详细设计

### 4.1 应用入口与中间件

**文件**: `backend/app/main.py`

#### 启动流程

1. 执行 `run_migrations()` �?扫描 `migrations/` 目录，按文件名排序执行所�?`.sql` 文件
2. 启动 APScheduler �?注册 CMDB 同步任务（每�?02:00 CST�?
3. 加载所有路由模�?

#### 中间件栈（顺序由外到内）

| 顺序 | 中间�?| 作用 |
|------|--------|------|
| 1 | `CORSMiddleware` | 允许所有来源（`allow_origins=["*"]`），支持 Cookie |
| 2 | `AuthMiddleware` | 提取 JWT，解析用户身份，注入 `request.state.user` |
| 3 | `ResponseEnvelopeMiddleware` | 统一包装响应�?`{code, message, data, timestamp}` |

#### 统一响应格式

```json
{
  "code": 200,
  "message": "OK",
  "data": { ... },
  "timestamp": 1712345678000
}
```

#### 全局异常处理

| 异常类型 | HTTP 状态码 | 处理逻辑 |
|----------|-------------|----------|
| `HTTPException` | 原状态码 | 4xx 保留 detail�?xx 屏蔽细节 |
| `RequestValidationError` | 400 | 返回字段级错误详�?|
| `StarletteHTTPException` | 原状态码 | 处理 404/405 |
| `Exception` | 500 | 仅记录日志，不暴露错误细�?|

---

### 4.2 认证与授权（Auth�?

**目录**: `backend/app/auth/`

#### 4.2.1 认证流程

```
请求进入 AuthMiddleware
    �?
    ├─ 是否公开路径�?(/api/health, /docs �? �?直接放行
    �?
    └─ 调用 get_auth_provider()
           �?
           ├─ Keycloak Provider（生产）
           �?   └─ 验证 Bearer JWT Token
           �?        ├─ 提取 preferred_username (id), name, email
           �?        └─ 解析 Keycloak realm_access.roles
           �?
           └─ Dev Provider（开发模式，AUTH_DISABLED=true�?
                └─ 注入固定测试用户
           �?
           └─ resolve_scoped_roles(user, db)
                └─ 查询数据库中�?EA_Reviewer/App_Owner 角色分配
                     ├─ 是否�?eam_bigea_team_members 中？ �?EA_Reviewer
                     └─ 是否有关联应用所有权�?�?App_Owner
```

#### 4.2.2 角色模型

```python
class Role(str, Enum):
    EA_ADMIN    = "ea_admin"     # 平台管理员，无限�?
    NORMAL_USER = "normal_user"  # 所有认证用户的基础角色
    EA_REVIEWER = "ea_reviewer"  # EA 评审员（记录级作用域�?
    APP_OWNER   = "app_owner"    # 应用所有者（记录级作用域�?
```

#### 4.2.3 权限矩阵

| 资源 | EA_Admin | Normal_User | EA_Reviewer | App_Owner |
|------|----------|-------------|-------------|-----------|
| ea_request | read/write | read/write* | read/write* | read/write* |
| meeting | read/write | read | read/write* | read |
| action | read/write | read | read/write* | read |
| application | read/write | read | read | read/write* |
| bcm | read/write | read | read | read/write* |
| tech_stack | read/write | read | read | read/write* |
| report/dashboard | read/write | read | read | read |
| export | execute | - | execute | execute |
| master_data | read/write | read | read | read |

> `*` 表示仅限自己创建�?被分配的/拥有的记录（记录级作用域�?

#### 4.2.4 依赖注入

```python
# 任意认证用户
Depends(require_auth)

# 特定角色
Depends(require_role(Role.EA_ADMIN))

# 资源+操作权限（功能级�?
Depends(require_permission("ea_request", "write"))
```

#### 4.2.5 AuthUser 数据结构

```python
class AuthUser(BaseModel):
    id: str              # itcode（工号）
    name: str            # 姓名
    email: str           # 邮箱
    email_prefix: str    # 邮箱前缀（用于所有权匹配�?
    roles: list[Role]    # 所有角�?
    permissions: list[str]  # 扁平化权限列表，�?["ea_request:read", ...]

    @property
    def is_admin(self) -> bool: ...
    @property
    def is_reviewer(self) -> bool: ...
    @property
    def is_app_owner(self) -> bool: ...
```

---

### 4.3 模块 A: EA Review（EA审查�?

#### 4.3.1 EA Requests（EA审查请求�?

**文件**: `backend/app/architecture_review/ea_requests.py`  
**前缀**: `/api/ea-requests`

##### 数据模型（DB: `eam.eam_request`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| request_id | VARCHAR | 业务 ID，格式：`EA{FY年份}{4位序号}` �?`EAFY25260001` |
| project_id | VARCHAR | 关联项目 ID |
| review_scope | VARCHAR | 审查范围（EA Review, Architecture Review 等） |
| ws_phase_name | VARCHAR | 工作流阶段名�?|
| requester | VARCHAR | 申请�?itcode |
| status | VARCHAR | 状态（Draft/Submitted/In Progress/Completed/Deleted�?|
| assign_reviewer | VARCHAR[] | 指定评审�?itcode 数组 |
| review_result | VARCHAR | 评审结果（Approved/Approved with Exception/Not Passed/Returned by EA�?|
| organization | VARCHAR | 所属组�?|
| request_desc | TEXT | 申请描述 |
| link | VARCHAR | 相关链接 |
| status_remark | TEXT | 状态备�?|
| status_changed_by | VARCHAR | 状态变更人 |
| status_changed_at | TIMESTAMP | 状态变更时�?|
| create_by | VARCHAR | 创建�?|
| create_at | TIMESTAMP | 创建时间 |
| update_at | TIMESTAMP | 更新时间 |

##### API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/ea-requests` | ea_request:read | 分页列表，支持多维过滤、排�?|
| GET | `/api/ea-requests/dashboard` | ea_request:read | 17维度统计汇总数�?|
| GET | `/api/ea-requests/filter-options` | ea_request:read | 获取过滤下拉选项 |
| GET | `/api/ea-requests/{id}` | ea_request:read | 单条详情（含附件�?|
| POST | `/api/ea-requests` | ea_request:write | 创建新请�?|
| PUT | `/api/ea-requests/{id}` | ea_request:write | 更新请求（状态流�?记录级权限） |
| DELETE | `/api/ea-requests/{id}` | ea_request:write | 软删除（�?Draft 状态） |

##### 状态流�?

```
[Draft] ──(Submit)──�?[Submitted] ──(Accept)──�?[In Progress] ──(Complete)──�?[Completed]
   �?                      �?                                                    �?
   �?                      └──(Return)──────────────────────────────────────────�?
   �?
   └──(Delete)──�?[Deleted]
```

##### 状态流转业务规�?

| 动作 | 前置状�?| 操作人权�?| 后置状�?| 触发邮件 |
|------|----------|-----------|----------|---------|
| Submit | Draft | 请求创建�?| Submitted | 发给申请�?+ CC PM/DT Lead |
| Accept by EA | Submitted | EA_Admin | In Progress | 发给申请人（通知�? 评审员（提醒�?|
| Return by EA | Submitted | EA_Admin | Draft | 发给申请�?|
| Complete (Approved) | In Progress | EA_Admin 或已分配�?EA_Reviewer | Completed | 发给申请�?|
| Complete (Not Passed) | In Progress | EA_Admin 或已分配�?EA_Reviewer | Completed | 发给申请�?|
| Delete | Draft | 请求创建�?/ EA_Admin | Deleted | - |

##### 请求 ID 生成逻辑

```python
# 财年计算�?月开始（月份<4则使用上一年）
# 格式：EA + FY年份(4�? + 序号(4位补�?
# 示例：EAFY25260001

# 使用 eam.fiscal_year_sequences 表实现原子自�?
INSERT INTO eam.fiscal_year_sequences (sequence_name, fiscal_year, current_value)
VALUES ('EA_Request', 'FY2526', 1)
ON CONFLICT (sequence_name, fiscal_year)
DO UPDATE SET current_value = current_value + 1
RETURNING current_value
```

##### Dashboard 统计维度（`GET /dashboard`�?

1. `statusCounts` �?按状态计�?
2. `completedResultCounts` �?已完结请求按评审结果分布
3. `orgCounts` �?按组织计�?
4. `monthlyTrend` �?月度趋势（提交量 + 批准量）
5. `monthlyLeadTime` �?月度 Lead Time（min/avg/median/max�?
6. `monthlyByOrg` �?月度按组织分�?
7. `recentRequests` �?最�?10 条请�?
8. `architectByOrgType` �?架构师按组织&类型分布
9. `topArchitects` �?Top 10 工作量排�?
10. `monthlyReviewActivity` �?月度评审活动（会议数 + 行动项数�?
11. `monthlyOrgTypeTrend` �?月度组织类型趋势
12. `diagramScoreStats` �?架构�?AI 评分统计
13. `monthlyArchScore` �?月度架构评分趋势
14. `firstPassRate` �?一次通过�?
15. `scoreDistribution` �?评分分布（散点图数据�?
16. `monthlyFirstPass` �?月度一次通过趋势
17. `monthlyTopArchitects` �?月度 Top 10 架构师排�?
18. `monthlyRequestorReviewerTime` �?月度申请�?评审员时间分�?
19. `requestorReviewerTimeSplit` �?申请�?评审员时间总分�?

---

#### 4.3.2 Meetings（会议管理）

**文件**: （已迁移，历史路�?backend/app/routers/ea_review/meetings.py 已删除）  
**前缀**: `/api/meetings`

##### 数据模型（DB: `eam.eam_meetings`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| meeting_no | INTEGER | 会议序号 |
| meeting_title | VARCHAR | 会议标题 |
| project_id | VARCHAR | 关联项目 |
| request_id | VARCHAR | 关联 EA 请求 |
| start_time | TIMESTAMP | 开始时�?|
| end_time | TIMESTAMP | 结束时间 |
| presenter | VARCHAR | 主讲�?|
| participants | VARCHAR[] | 参会人列�?|
| meeting_link | VARCHAR | 会议链接 |
| status | VARCHAR | 状�?|
| remark | TEXT | 备注 |
| create_at | TIMESTAMP | 创建时间 |

##### API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/meetings` | meeting:read | 分页列表 |
| GET | `/api/meetings/{id}` | meeting:read | 单条详情 |
| POST | `/api/meetings` | meeting:write | 创建会议 |
| PUT | `/api/meetings/{id}` | meeting:write | 更新会议 |
| DELETE | `/api/meetings/{id}` | meeting:write | 删除会议 |
| POST | `/api/meetings/{id}/deck` | meeting:write | 上传会议 PPT �?S3 |
| GET | `/api/meetings/{id}/deck` | meeting:read | 下载/预览会议 PPT |
| GET | `/api/meetings/stats` | meeting:read | 会议统计 |
| POST | `/api/meetings/import` | meeting:write | CSV 批量导入 |

---

#### 4.3.3 Actions（行动项�?

**文件**: （已迁移，历史路�?backend/app/routers/ea_review/actions.py 已删除）  
**前缀**: `/api/actions`

##### 数据模型（DB: `eam.eam_actions`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| action_no | INTEGER | 行动项序�?|
| action_title | VARCHAR | 标题 |
| project_id | VARCHAR | 关联项目 |
| meeting_id | UUID | 关联会议 |
| request_id | VARCHAR | 关联 EA 请求 |
| priority | VARCHAR | 优先级（High/Medium/Low�?|
| due_date | DATE | 截止日期 |
| close_date | DATE | 关闭日期 |
| open_date | DATE | 开启日�?|
| assignee | VARCHAR | 执行�?itcode |
| assignee_name | VARCHAR | 执行人名�?|
| action_description | TEXT | 描述 |
| action_updates | TEXT | 进展记录 |
| status | VARCHAR | 状态（Open/Closed/In Progress�?|
| type | VARCHAR | 类型 |
| applicable_domain | VARCHAR | 适用领域 |
| requested_by | VARCHAR | 提出�?|

##### API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/actions` | action:read | 分页列表 |
| GET | `/api/actions/stats` | action:read | 行动项统�?|
| GET | `/api/actions/{id}` | action:read | 单条详情 |
| POST | `/api/actions` | action:write | 创建行动�?|
| PUT | `/api/actions/{id}` | action:write | 更新行动�?|
| DELETE | `/api/actions/{id}` | action:write | 删除行动�?|
| POST | `/api/actions/import` | action:write | CSV 批量导入 |
| POST | `/api/actions/{id}/send-reminder` | action:write | 发送逾期提醒邮件 |

---

#### 4.3.4 Schedules（日程安排）

**文件**: （已迁移，历史路�?backend/app/routers/ea_review/schedules.py 已删除）  
**前缀**: `/api/schedules`

##### 数据模型（DB: `eam.eam_schedules`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| schedule_no | INTEGER | 日程序号 |
| schedule_title | VARCHAR | 标题 |
| project_id | VARCHAR | 关联项目 |
| start_time | TIMESTAMP | 开始时�?|
| end_time | TIMESTAMP | 结束时间 |
| duration | NUMERIC | 时长（小时） |
| recurrence_pattern | VARCHAR | 重复模式（None/Daily/Weekly/Monthly�?|
| end_after | INTEGER | 重复次数 |
| owner | VARCHAR[] | 负责�?itcode 列表 |
| remark | TEXT | 备注 |
| status | VARCHAR | 状�?|
| for_project | BOOLEAN | 是否项目级日�?|
| for_meeting | BOOLEAN | 是否关联会议 |

##### API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/schedules` | schedule:read | 分页列表 |
| GET | `/api/schedules/stats` | schedule:read | 日程统计 |
| GET | `/api/schedules/{id}` | schedule:read | 单条详情 |
| POST | `/api/schedules` | schedule:write | 创建（支持重复日程自动展开�?|
| PUT | `/api/schedules/{id}` | schedule:write | 更新 |
| DELETE | `/api/schedules/{id}` | schedule:write | 删除 |

---

#### 4.3.5 Attachments（附件管理）

**文件**: `backend/app/architecture_review/attachments.py`  
**前缀**: `/api/ea-requests/attachments`

##### 附件类型（`biz_type`�?

| 类型 | 说明 |
|------|------|
| `App_Arch` | 应用架构图（支持 AI 评分�?|
| `Tech_Arch` | 技术架构图（支�?AI 评分�?|
| `Proj_Intro` | 项目介绍文档 |

##### 数据模型（DB: `eam.eam_request_attachment`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键（S3 Key 组成部分�?|
| request_id | VARCHAR | 关联 EA 请求 |
| attachment_name | VARCHAR | S3 存储路径 |
| biz_type | VARCHAR | 业务类型 |
| app_arch_type | VARCHAR | 架构图子类型 |
| create_by | VARCHAR | 上传�?|
| create_at | TIMESTAMP | 上传时间 |

##### 关联表（DB: `eam.eam_arch_ai_check`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| attachment_uuid | UUID | 关联附件 |
| result | JSONB | AI 评分结果（含 overall_evaluation.score�?|
| create_at | TIMESTAMP | 检查时�?|

##### API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/ea-requests/attachments/upload` | ea_request:write | 上传文件�?S3，自动触�?AI 检�?|
| GET | `/api/ea-requests/attachments/{id}/download` | ea_request:read | 生成 S3 预签�?URL |
| DELETE | `/api/ea-requests/attachments/{id}` | ea_request:write | 删除文件 |
| POST | `/api/ea-requests/attachments/{id}/ai-check` | ea_request:write | 手动触发 AI 检�?|
| GET | `/api/ea-requests/attachments/{id}/ai-result` | ea_request:read | 获取 AI 评分结果 |

---

#### 4.3.6 Scope（审查范围）

**文件**: （已迁移，历史路�?backend/app/routers/ea_review/scope.py 已删除）  
**前缀**: `/api`

提供两类数据�?
- **Scope of Change**（变更范围）：描述本次审查的变更内容条目
- **Scope Checklist**（检查清单）：结构化的审查问卷，包含分类/子分�?问题/答案/评论

##### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/scope-of-change` | 查询变更范围（按 projectId �?requestId�?|
| POST | `/api/scope-of-change` | 创建变更范围条目 |
| PUT | `/api/scope-of-change/{id}` | 更新变更范围条目 |
| DELETE | `/api/scope-of-change/{id}` | 删除 |
| GET | `/api/scope-checklist` | 查询检查清�?|
| POST | `/api/scope-checklist` | 创建检查清单条�?|
| PUT | `/api/scope-checklist/{id}` | 更新 |
| DELETE | `/api/scope-checklist/{id}` | 删除 |
| GET | `/api/scope-checklist/templates` | 查询模板 |
| POST | `/api/scope-checklist/from-template` | 从模板生成检查清�?|

---

#### 4.3.7 Architecture Check（架构检查）

**文件**: `backend/app/architecture_review/architecture_check.py`  
**前缀**: `/api/arch-check-apps`

管理 AI 架构检查结果中识别的应用列表，以及与标�?AppID 的关联�?

##### 数据模型（DB: `eam.eam_arch_ai_check_app`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ai_check_id | UUID | 关联 AI 检查记�?|
| app_id | VARCHAR | 应用 ID（AI 识别或手动输入） |
| app_name | VARCHAR | 应用名称 |
| id_is_standard | BOOLEAN | 是否为标�?ID |
| standard_id | VARCHAR | 标准化后�?AppID |
| functions | VARCHAR[] | 应用功能列表 |
| check_app_status | VARCHAR | 状态（confirmed/pending 等） |
| remark | TEXT | 备注 |

#### 4.3.8 Architecture Check Interactions（架构检查交互）

**文件**: `backend/app/architecture_review/architecture_check_interactions.py`  
**前缀**: `/api/arch-check-interactions`

管理架构图中识别的应用间交互关系�?

---

### 4.4 模块 B: App Solution（应用管理）

#### 4.4.1 Applications（应用列表）

**文件**: `backend/app/routers/app_solution/applications.py`  
**前缀**: `/api/applications`

##### 主要数据�?

- `eam.project_app` �?项目维度的应用信�?
- `eam.cmdb_application` �?�?CMDB 同步的应用基础信息
- `eam.biz_cap_map` �?业务能力映射（BCM�?
- `eam.bcpf_master_data` �?BizCapability 主数�?

##### API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/applications` | application:read | 分页列表 |
| GET | `/api/applications/cmdb` | application:read | CMDB 应用列表 |
| GET | `/api/applications/bcm/versions` | application:read | BCM 数据版本列表 |
| GET | `/api/applications/bcm/bc-tree` | application:read | BC 树形结构（级联选择用） |
| GET | `/api/applications/bcm/filter-options` | application:read | BCM 过滤选项 |
| GET | `/api/applications/bcm` | application:read | BCM 列表（多维过滤） |
| GET | `/api/applications/bcm/export` | application:read | BCM 导出 Excel |
| POST | `/api/applications/bcm` | bcm:write | 创建 BCM 记录 |
| PUT | `/api/applications/bcm/{id}` | bcm:write | 更新 BCM 记录 |
| DELETE | `/api/applications/bcm/{id}` | bcm:write | 删除 BCM 记录 |
| GET | `/api/applications/bcm/visualization` | bcm:read | BCM 可视化数�?|

---

#### 4.4.2 Technology Stack（技术栈�?

**文件**: `backend/app/routers/app_solution/technology_stack.py`  
**前缀**: `/api/technology-stack`

管理企业技术栈的生命周期状态，包括技术组件的应用绑定、EA 建议、导�?导出�?

##### 数据模型（DB: `eam.tech_key_stack_item`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| app_id | VARCHAR | 关联应用 |
| component | VARCHAR | 组件名称 |
| component_package | VARCHAR | �?版本 |
| category | VARCHAR | 分类 |
| ea_advice | VARCHAR | EA 建议（Adopt/Trial/Assess/Hold�?|
| lifecycle_status | VARCHAR | 生命周期状�?|
| end_of_life_date | DATE | 停止支持日期 |
| create_by | VARCHAR | 创建�?|
| create_at | TIMESTAMP | 创建时间 |

##### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/technology-stack` | 分页列表（多维过滤） |
| GET | `/api/technology-stack/export` | 导出 CSV |
| POST | `/api/technology-stack` | 创建 |
| PUT | `/api/technology-stack/{id}` | 更新（记录变更日志） |
| DELETE | `/api/technology-stack/{id}` | 删除 |
| POST | `/api/technology-stack/import` | 批量导入（支�?CSV/Excel/Word/PDF�?|

---

#### 4.4.3 CMDB（配置管理数据库�?

**文件**: `backend/app/application_management/cmdb.py`  
**前缀**: `/api/cmdb`

提供 CMDB 应用数据查询（只读），数据由定时任务每日同步�?

---

#### 4.4.4 BCPF（业务能力框架主数据�?

**文件**: `backend/app/routers/app_solution/BizCapability.py`  
**前缀**: `/api/BizCapability-master-data`

管理 BizCapability 主数据版本和条目（EA_Admin 专属写入权限）�?

---

### 4.5 模块 C: Reports & Analytics（报表分析）

#### 4.5.1 Reports（报表）

**文件**: `backend/app/routers/reports_analytics/reports.py`  
**前缀**: `/api/reports`

##### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reports/lead-time` | Lead Time 报表（含流程日志时间线） |

每条记录包含：EA 请求基础信息 + 完整流程日志（Created/Submitted/Accepted/Completed 等）

---

#### 4.5.2 Dashboard（仪表盘�?

**文件**: `backend/app/routers/reports_analytics/dashboard.py`  
**前缀**: `/api/dashboard`

提供整体应用管理视角的统计数据（�?EA Review Dashboard 互补）�?

---

#### 4.5.3 BC Visualization（业务能力可视化�?

**文件**: `backend/app/routers/reports_analytics/bc_visualization.py`  
**前缀**: `/api/applications`（复�?applications 前缀�?

##### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/applications/bcm/visualization` | BCM 可视化数据（按版本） |

返回结构�?
```json
{
  "capabilities": [...],  // BC 节点列表
  "applications": [...],  // 应用节点列表
  "mappings": [...],      // 映射关系列表
  "domains": [...],       // L1 域列�?
  "dataVersion": "..."    // 数据版本
}
```

---

### 4.6 模块 D: Auth & Users（用户管理）

#### 4.6.1 Auth（认证）

**文件**: `backend/app/auth/api.py`  
**前缀**: `/api/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/me` | 获取当前用户信息和权�?|
| GET | `/api/auth/permissions` | 获取当前用户扁平化权限列�?|

---

#### 4.6.2 Team Members（团队成员）

**文件**: `backend/app/routers/auth_users/team_members.py`  
**前缀**: `/api/team-members`

管理 BigEA 团队成员档案，包�?EA 评审员和领域架构师�?

##### 数据模型（DB: `eam.eam_bigea_team_members`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| itcode | VARCHAR | 主键（工号） |
| name | VARCHAR | 姓名 |
| email | VARCHAR | 邮箱 |
| worker_type | VARCHAR | 类型（EA Office/Domain Architect�?|
| country | VARCHAR | 国家 |
| primary_skill | VARCHAR | 主要技�?|
| job_role | VARCHAR | 职位 |
| manager_itcode | VARCHAR | 上级工号 |
| ea_admin_status | VARCHAR | EA 管理员状�?|

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/team-members` | team_member:read | 分页列表 |
| GET | `/api/team-members/{itcode}` | team_member:read | 单条详情 |
| POST | `/api/team-members` | EA_ADMIN | 创建 |
| PUT | `/api/team-members/{itcode}` | EA_ADMIN | 更新 |
| DELETE | `/api/team-members/{itcode}` | EA_ADMIN | 删除 |

---

#### 4.6.3 Resources（资源池�?

**文件**: `backend/app/data_management/resources.py`  
**前缀**: `/api/resources`

企业人员资源库，用于自动补全搜索（Requester/Reviewer 选择等）�?

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/resources/search` | 模糊搜索（by name/itcode�?|
| GET | `/api/resources` | 分页列表 |

---

### 4.7 模块 E: Config & Data（配置数据）

#### 4.7.1 Projects（项目）

**文件**: `backend/app/project_management/projects.py`  
**前缀**: `/api/projects`

管理 IT 项目信息，是 EA 审查请求的核心关联对象�?

##### 数据模型（DB: `eam.project`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| project_id | VARCHAR | 项目 ID |
| project_name | VARCHAR | 项目名称 |
| type | VARCHAR | 项目类型 |
| start_date | DATE | 开始日�?|
| go_live_date | DATE | 上线日期 |
| pps_exit_date | DATE | PPS 退出日�?|
| end_date | DATE | 结束日期 |
| pm / pm_itcode | VARCHAR | 项目经理（姓�?工号�?|
| dt_lead / dt_lead_itcode | VARCHAR | DT Lead（姓�?工号�?|
| it_lead / it_lead_itcode | VARCHAR | IT Lead（姓�?工号�?|
| duration | INTEGER | 工期（天�?|
| investment_cost | NUMERIC | 投资成本 |
| yearly_ma_cost | NUMERIC | 年度 MA 成本 |
| currency | VARCHAR | 货币类型 |
| status | VARCHAR | 状�?|
| ea_review_type | VARCHAR | EA 审查类型 |
| ai_related | BOOLEAN | 是否 AI 相关项目 |
| favourite | BOOLEAN | 是否标记为关�?|

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects` | 分页列表（多维过滤） |
| GET | `/api/projects/search` | 快速搜索（自动补全�?|
| GET | `/api/projects/{id}` | 单条详情 |
| POST | `/api/projects` | 创建项目 |
| PUT | `/api/projects/{id}` | 更新项目 |
| DELETE | `/api/projects/{id}` | 删除（EA_Admin�?|
| GET | `/api/projects/{id}/tasks` | 获取项目任务列表 |
| POST | `/api/projects/{id}/tasks` | 创建项目任务 |
| PUT | `/api/projects/{id}/tasks/{taskId}` | 更新任务 |
| DELETE | `/api/projects/{id}/tasks/{taskId}` | 删除任务 |
| GET | `/api/projects/favourite` | 获取关注项目列表 |
| PUT | `/api/projects/{id}/favourite` | 标记关注状�?|

---

#### 4.7.2 Master Data（主数据�?

**文件**: `backend/app/routers/config_data/master_data.py`  
**前缀**: `/api/master-data`

| API | DB �?| 说明 |
|-----|-------|------|
| GET `/data-classification` | `eam.data_classification` | 数据分类（树形，有层级） |
| GET `/data-centers` | `eam.data_center` | 数据中心列表 |
| GET `/legal-entities` | `eam.legal_entity` | 法律实体列表 |
| POST/PUT/DELETE `/data-centers/{id}` | `eam.data_center` | 数据中心 CRUD（EA_Admin�?|
| POST/PUT/DELETE `/legal-entities/{id}` | `eam.legal_entity` | 法律实体 CRUD（EA_Admin�?|

---

#### 4.7.3 Certifications（认证）

**文件**: `backend/app/routers/config_data/certifications.py`  
**前缀**: `/api/certifications`

管理团队成员技术认证，支持批量 CSV 导入和到期提醒邮件�?

##### 数据模型（DB: `eam.certifications`�?

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| simple_id | VARCHAR | 业务序号 |
| exam_name | VARCHAR | 认证名称 |
| certificate_type | VARCHAR | 认证类型 |
| itcode | VARCHAR | 持证人工�?|
| user_name | VARCHAR | 持证人姓�?|
| issue_date | DATE | 颁发日期 |
| expiration_date | DATE/TIMESTAMP | 到期日期 |
| duration | VARCHAR | 有效期描�?|

状态自动计算：`Valid`（未过期�? `Expired`（已过期�?

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/certifications` | 分页列表 |
| POST | `/api/certifications` | 单条创建 |
| PUT | `/api/certifications/{id}` | 更新 |
| DELETE | `/api/certifications/{id}` | 删除 |
| POST | `/api/certifications/import` | CSV 批量导入 |
| GET | `/api/certifications/export` | CSV 导出 |
| POST | `/api/certifications/send-reminder` | 发送到期提醒邮�?|

---

#### 4.7.4 Dict Options（字典选项�?

**文件**: `backend/app/routers/config_data/dict_options.py`  
**前缀**: `/api/dict-options`

提供系统中各种下拉选项（Review Scope、WS Phase、Organization 等）的动态配置�?

---

### 4.8 模块 F: Shared Services（共享服务）

#### 4.8.1 Audit Log（审计日志）

**文件**: `backend/app/routers/shared_services/audit_log.py`  
**前缀**: `/api`

| API | 说明 |
|-----|------|
| GET `/api/audit-log` | 字段级变更日志（项目/配置变更�?|
| GET `/api/process-log/{requestId}` | EA 请求流程日志 |
| GET `/api/email-log` | 邮件发送日志（EA_Admin�?|

---

#### 4.8.2 Export（导出）

**文件**: `backend/app/routers/shared_services/export.py`  
**前缀**: `/api/export`

通用 CSV 导出端点，按实体类型生成导出文件�?

| API | 说明 |
|-----|------|
| GET `/api/export/{entity}` | 导出指定实体（ea-requests/meetings/actions/bcm/technology-stack 等） |

权限要求：`export:execute`（EA_Reviewer �?App_Owner 以上�?

---

#### 4.8.3 EA Review Logs（评审日志）

**文件**: `backend/app/routers/shared_services/ea_review_logs.py`  
**前缀**: `/api/ea-review-logs`

查询 EA 评审过程中的操作日志（AI 检查记录、状态变更等）�?

---

### 4.9 AI Agent（架构检查智能体�?

**目录**: `backend/app/architecture_review/ai/`

当用户上传架构图（App_Arch / Tech_Arch 类型附件）后，系统自动触�?AI 检查流程�?

#### 处理流程

```
文件上传�?S3
    �?
    └─�?process_attachment_ai_check(attachment_id, db, user)
              �?
              ├─ �?S3 下载文件
              ├─ 通过 LangChain Workflow 调用 LLM
              �?   ├─ 内容提取（识别应用、接口、交互）
              �?   └─ 架构评估（生�?overall_evaluation.score�?
              �?
              ├─ 保存结果�?eam.eam_arch_ai_check
              �?   └─ result (JSONB): {
              �?        "overall_evaluation": {"score": 85, "summary": "..."},
              �?        "applications": [...],
              �?        "interactions": [...]
              �?      }
              �?
              └─ 保存识别到的应用�?eam.eam_arch_ai_check_app
```

#### AI 检查结果数据结�?

```json
{
  "overall_evaluation": {
    "score": 85,
    "summary": "架构设计较合�?..",
    "findings": ["..."],
    "recommendations": ["..."]
  },
  "applications": [
    {"app_id": "APP001", "app_name": "...", "functions": ["..."]}
  ],
  "interactions": [
    {"source": "APP001", "target": "APP002", "protocol": "REST"}
  ]
}
```

---

### 4.10 定时任务

**文件**: `backend/app/tasks/cmdb_sync.py`

| 任务 | 触发时间 | 说明 |
|------|----------|------|
| CMDB 应用同步 | 每日 02:00 (Asia/Shanghai) | �?CMDB API 全量拉取应用数据，upsert �?`eam.cmdb_application` |

同步字段：应�?ID、名称、全称、状态、Owner、DT Owner、应用分类、解决方案类型、Portfolio 管理等（�?18 个字段）

---

## 5. 数据库设�?

### 5.1 Schema 概览

所有表位于 `eam` schema（PostgreSQL），连接时通过 `SET search_path TO eam` 自动设置�?

### 5.2 核心表结�?

#### `eam.eam_request` �?EA 审查请求

```sql
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
request_id        VARCHAR UNIQUE   -- 业务 ID（EAFY25260001�?
project_id        VARCHAR          -- 关联 project.project_id
review_scope      VARCHAR
ws_phase_name     VARCHAR
requester         VARCHAR          -- 申请�?itcode
status            VARCHAR          -- Draft/Submitted/In Progress/Completed/Deleted
assign_reviewer   VARCHAR[]        -- 评审�?itcode 数组
review_result     VARCHAR          -- Approved/Approved with Exception/Not Passed/Returned by EA
organization      VARCHAR
request_desc      TEXT
link              VARCHAR
status_remark     TEXT
status_changed_by VARCHAR
status_changed_at TIMESTAMP(6)
process_id        VARCHAR
create_by         VARCHAR
create_at         TIMESTAMP(6)
update_at         TIMESTAMP(6)
update_by         VARCHAR
```

#### `eam.eam_request_process_log` �?请求流程日志

```sql
id          UUID PRIMARY KEY
request_id  VARCHAR          -- 关联 eam_request.request_id
action      VARCHAR          -- Created/Submitted/Accepted by EA/Returned by EA/Approved/Not Passed
comment     TEXT
operator    VARCHAR
create_at   TIMESTAMP(6)
```

#### `eam.eam_request_attachment` �?请求附件

```sql
id               UUID PRIMARY KEY
request_id       VARCHAR
attachment_name  VARCHAR          -- S3 路径
biz_type         VARCHAR          -- App_Arch/Tech_Arch/Proj_Intro
app_arch_type    VARCHAR
create_by        VARCHAR
create_at        TIMESTAMP(6)
```

#### `eam.eam_arch_ai_check` �?AI 架构检查结�?

```sql
id               UUID PRIMARY KEY
attachment_uuid  UUID             -- 关联 eam_request_attachment.id
result           JSONB            -- AI 评分结果
create_at        TIMESTAMP(6)
```

#### `eam.eam_arch_ai_check_app` �?AI 识别的应�?

```sql
id               UUID PRIMARY KEY
ai_check_id      UUID             -- 关联 eam_arch_ai_check.id
app_id           VARCHAR
app_name         VARCHAR
id_is_standard   BOOLEAN
standard_id      VARCHAR
functions        VARCHAR[]
check_app_status VARCHAR
remark           TEXT
create_by        VARCHAR
create_at        TIMESTAMP(6)
```

#### `eam.eam_meetings` �?会议

```sql
id                     UUID PRIMARY KEY
meeting_no             INTEGER
meeting_title          VARCHAR
project_id             VARCHAR
request_id             VARCHAR
start_time             TIMESTAMP(6)
end_time               TIMESTAMP(6)
presenter              VARCHAR
participants           VARCHAR[]
meeting_link           VARCHAR
status                 VARCHAR
remark                 TEXT
project_objectives     TEXT
available_ea_schedule  VARCHAR
create_at              TIMESTAMP(6)
```

#### `eam.eam_actions` �?行动�?

```sql
id                  UUID PRIMARY KEY
action_no           INTEGER
action_title        VARCHAR
project_id          VARCHAR
meeting_id          UUID
request_id          VARCHAR
priority            VARCHAR
due_date            DATE
close_date          DATE
open_date           DATE
start_date          DATE
assignee            VARCHAR
assignee_name       VARCHAR
action_description  TEXT
action_updates      TEXT
status              VARCHAR
type                VARCHAR
applicable_domain   VARCHAR
requested_by        VARCHAR
requested_by_name   VARCHAR
create_at           TIMESTAMP(6)
update_at           TIMESTAMP(6)
```

#### `eam.eam_schedules` �?日程

```sql
id                  UUID PRIMARY KEY
schedule_no         INTEGER
schedule_title      VARCHAR
project_id          VARCHAR
start_time          TIMESTAMP(6)
end_time            TIMESTAMP(6)
duration            NUMERIC
recurrence_pattern  VARCHAR
end_after           INTEGER
owner               VARCHAR[]
remark              TEXT
status              VARCHAR
for_project         BOOLEAN
for_meeting         BOOLEAN
```

#### `eam.project` �?IT 项目

```sql
id                UUID PRIMARY KEY
project_id        VARCHAR UNIQUE
project_name      VARCHAR
type              VARCHAR
start_date        DATE
go_live_date      DATE
pps_exit_date     DATE
end_date          DATE
pm                VARCHAR
pm_itcode         VARCHAR
dt_lead           VARCHAR
dt_lead_itcode    VARCHAR
it_lead           VARCHAR
it_lead_itcode    VARCHAR
duration          INTEGER
objectives        TEXT
investment_cost   NUMERIC
yearly_ma_cost    NUMERIC
currency          VARCHAR
status            VARCHAR
comment           TEXT
ea_review_type    VARCHAR
domain_ea_reviewer VARCHAR
favourite         BOOLEAN
overall_status    VARCHAR
approved_time     TIMESTAMP
source            VARCHAR
ea_approval_dt    DATE
ai_related        BOOLEAN
create_by         VARCHAR
create_at         TIMESTAMP(6)
update_at         TIMESTAMP(6)
```

#### `eam.project_app` �?项目关联应用

```sql
id               UUID PRIMARY KEY
app_id           VARCHAR
project_id       VARCHAR
app_name         VARCHAR
app_full_name    VARCHAR
app_it_owner     VARCHAR
current_state    VARCHAR
app_tech_id_in_cmdb VARCHAR
app_description  TEXT
business_function VARCHAR
create_by        VARCHAR
create_at        TIMESTAMP(6)
```

#### `eam.cmdb_application` �?CMDB 应用（定时同步）

```sql
app_id              VARCHAR PRIMARY KEY
name                VARCHAR
app_full_name       VARCHAR
u_status            VARCHAR
short_description   TEXT
owned_by            VARCHAR
app_it_owner        VARCHAR
app_dt_owner        VARCHAR
app_ownership       VARCHAR
portfolio_mgt       VARCHAR
app_solution_type   VARCHAR
app_classification  VARCHAR
app_owner_tower     VARCHAR
app_owner_domain    VARCHAR
app_operation_owner VARCHAR
```

#### `eam.biz_cap_map` �?业务能力映射

```sql
id              UUID PRIMARY KEY
app_id          VARCHAR
bcpf_master_id  INTEGER    -- 关联 bcpf_master_data.id
create_by       VARCHAR
create_at       TIMESTAMP(6)
```

#### `eam.bcpf_master_data` �?BizCapability 主数�?

```sql
id                  INTEGER PRIMARY KEY
bc_id               VARCHAR
bc_name             VARCHAR
bc_name_cn          VARCHAR
lv1_domain          VARCHAR
lv2_sub_domain      VARCHAR
lv3_capability_group VARCHAR
parent_bc_id        VARCHAR
bc_description      TEXT
biz_group           VARCHAR
geo                 VARCHAR
level               INTEGER
alias               VARCHAR
data_version        VARCHAR
```

#### `eam.eam_bigea_team_members` �?EA 团队成员

```sql
itcode          VARCHAR PRIMARY KEY
name            VARCHAR
email           VARCHAR
worker          VARCHAR
worker_type     VARCHAR    -- EA Office / Domain Architect
country         VARCHAR
location        VARCHAR
primary_skill   VARCHAR
skill_level     VARCHAR
job_role        VARCHAR
track_focal     VARCHAR
manager_itcode  VARCHAR
manager_name    VARCHAR
email_option    VARCHAR
ea_admin_status VARCHAR
tier_1_org      VARCHAR
tier_2_org      VARCHAR
```

#### `eam.certifications` �?技术认�?

```sql
id               UUID PRIMARY KEY
simple_id        VARCHAR
exam_name        VARCHAR
certificate_type VARCHAR
itcode           VARCHAR
user_name        VARCHAR
issue_date       DATE
expiration_date  TIMESTAMP/DATE
duration         VARCHAR
```

#### `eam.tech_key_stack_item` �?技术栈条目

```sql
id               UUID PRIMARY KEY
app_id           VARCHAR
component        VARCHAR
component_package VARCHAR
category         VARCHAR
ea_advice        VARCHAR    -- Adopt/Trial/Assess/Hold
lifecycle_status VARCHAR
end_of_life_date DATE
create_by        VARCHAR
create_at        TIMESTAMP(6)
```

#### `eam.tech_stack_operate_log` �?技术栈变更日志（Migration 001�?

```sql
id        UUID PRIMARY KEY
app_id    VARCHAR
stack_id  VARCHAR
field     VARCHAR
old_value TEXT
new_value TEXT
create_by VARCHAR
create_at TIMESTAMP(6)
```

#### `eam.fiscal_year_sequences` �?财年序列�?

```sql
sequence_name  VARCHAR
fiscal_year    VARCHAR
current_value  INTEGER
UNIQUE(sequence_name, fiscal_year)
```

#### `eam.data_classification` / `eam.data_center` / `eam.legal_entity` �?主数据参考表

---

## 6. 前端详细设计

### 6.1 整体结构

```
frontend/src/
├── app/                          # Next.js App Router 路由
�?  ├── layout.tsx                # 根布局（注�?Providers�?
�?  ├── providers.tsx             # React Query + Ant Design + Auth 等全局 Provider
�?  ├── page.tsx                  # 根页面（重定向到 /ea-review�?
�?  ├── (sidebar)/                # 带侧边栏布局的页面组
�?  �?  ├── layout.tsx            # Sidebar + Header 布局
�?  �?  ├── settings/             # 系统设置
�?  �?  ├── master-data/          # 主数据管�?
�?  �?  ├── reports/              # 报表
�?  �?  ├── resources/            # 资源�?
�?  �?  ├── platform-engineering/ # 平台工程
�?  �?  ├── data-privacy/         # 数据隐私
�?  �?  └── help/                 # 帮助
�?  ├── ea-review/                # EA 审查（双布局�?
�?  �?  ├── (managed)/            # 带侧边栏（列�?管理类）
�?  �?  �?  ├── actions/          # 行动项列�?
�?  �?  �?  ├── calendar/         # 日历视图
�?  �?  �?  ├── meetings/         # 会议列表
�?  �?  �?  ├── request-summary/  # 请求汇�?
�?  �?  �?  └── request/          # 请求列表
�?  �?  └── (standalone)/         # 独立布局（请求详情）
�?  �?      └── request/[id]/     # 请求详情�?
�?  ├── projects/                 # 项目管理
�?  �?  ├── page.tsx              # 项目列表
�?  �?  ├── new/                  # 新建项目
�?  �?  └── [projectId]/          # 项目详情
�?  ├── request/                  # 请求相关（独立路由）
�?  ├── tech-stack/               # 技术栈
�?  ├── certification/            # 认证管理
�?  ├── app-management/           # 应用管理（BCM�?
�?  └── ea-review/                # EA Review Dashboard
�?
├── components/
�?  ├── layout/                   # 布局组件
�?  �?  ├── Header.tsx
�?  �?  ├── Footer.tsx
�?  �?  ├── Sidebar.tsx
�?  �?  ├── HomeLayout.tsx
�?  �?  └── PageLayout.tsx
�?  ├── ui/                       # 通用 UI 组件�?4个）
�?  ├── bc-visualization/         # BC 可视化组�?
�?  └── ea-review/                # EA 审查专用组件
�?
└── lib/
    ├── api.ts                    # HTTP 客户端（统一封装�?
    ├── auth-context.tsx          # 认证上下�?React Context
    ├── auth-token.ts             # Token 管理
    ├── keycloak-config.ts        # Keycloak 配置
    ├── keycloak-provider.tsx     # Keycloak Provider
    ├── keycloak-service.ts       # Keycloak 服务（登�?刷新/登出�?
    ├── constants.ts              # 全局常量
    ├── locale.tsx                # 国际�?
    └── useMediaQuery.ts          # 响应式媒体查�?Hook
```

---

### 6.2 路由设计

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | 根页�?| 重定向到 `/ea-review` |
| `/ea-review` | EA Review Dashboard | 统计仪表�?|
| `/ea-review/request` | EA 请求列表 | 分页搜索列表 |
| `/ea-review/request/[id]` | EA 请求详情 | 详情+状态流转操�?|
| `/ea-review/request-summary` | 请求汇�?| 汇总视�?|
| `/ea-review/meetings` | 会议列表 | |
| `/ea-review/actions` | 行动项列�?| |
| `/ea-review/calendar` | 日历视图 | 会议+日程日历 |
| `/projects` | 项目列表 | |
| `/projects/new` | 新建项目 | |
| `/projects/[projectId]` | 项目详情 | |
| `/app-management` | 应用管理（BCM�?| |
| `/tech-stack` | 技术栈管理 | |
| `/certification` | 认证管理 | |
| `/(sidebar)/reports/lead-time` | Lead Time 报表 | |
| `/(sidebar)/reports/ea-review-dashboard` | EA Review 统计 | |
| `/(sidebar)/reports/email-log` | 邮件日志 | |
| `/(sidebar)/master-data/data-classification` | 数据分类 | |
| `/(sidebar)/master-data/data-center` | 数据中心 | |
| `/(sidebar)/master-data/legal-entities` | 法律实体 | |
| `/(sidebar)/settings/team-members` | 团队成员管理 | |
| `/(sidebar)/settings/audit-log` | 审计日志 | |
| `/(sidebar)/settings/scope-change` | 审查范围变更 | |
| `/(sidebar)/settings/scope-checklist` | 审查清单模板 | |
| `/(sidebar)/resources` | 资源�?| |
| `/forbidden` | 无权限页�?| |

---

### 6.3 页面模块详细说明

#### EA Review Dashboard

**核心功能**�?
- 多维度统计数据可视化�?9 个维度）
- 支持日期范围、组织、架构师类型筛�?
- 图表类型：柱状图、折线图、饼图、散点图、热力图

**数据�?*�?
```
筛选条件变�?
    �?React Query useQuery('ea-requests-dashboard', filters)
    �?GET /api/ea-requests/dashboard?from=...&to=...&org=...
    �?图表组件渲染
```

---

#### EA 请求列表页（`/ea-review/request`�?

**核心功能**�?
- 分页列表，支持多列过滤（requestId/status/reviewer/dateRange 等）
- 状�?Tab 快速切换（All / Draft / Submitted / In Progress / Completed�?
- 行内操作：查看详情、删除（Draft 状态）
- 新建请求入口
- 导出 CSV

**关键组件**�?
- `SearchForm` �?多条件搜索表�?
- `StatusTabs` �?状态分�?Tab
- `DataTable` �?分页表格
- `ExportButton` �?导出按钮（调�?`/api/export/ea-requests`�?

---

#### EA 请求详情页（`/ea-review/request/[id]`�?

**核心功能**�?
- 展示请求完整信息（基本信息、申请人、评审员、附件）
- 状态流转操作按钮（Submit/Accept/Return/Complete�?
- 附件上传/下载（含 AI 评分展示�?
- 关联会议/行动�?日程列表
- 变更范围（Scope of Change）和检查清单（Scope Checklist�?
- 流程日志时间�?

**权限控制**�?
- `PermissionGate` 组件包裹操作按钮，按角色显示/隐藏

---

#### BC Visualization（业务能力可视化�?

**核心功能**�?
- Heatmap 视图：BC 节点按域/子域组织，色块显示关联应用数�?
- Mindmap 视图：树状展�?BC 层次结构
- 应用面板：点�?BC 节点展示关联应用列表
- 版本切换

**组件**�?
- `CapabilityDashboard.tsx` �?主视图容�?
- `CapabilityMindmap.tsx` �?Mindmap 渲染
- `NodeRenderer.tsx` / `EdgeRenderer.tsx` �?自定�?Canvas 节点/边渲�?
- `DomainFilter.tsx` �?L1 域过滤器
- `DetailPanel.tsx` �?侧边详情面板

---

#### 技术栈管理（`/tech-stack`�?

**核心功能**�?
- 按应�?组件/EA建议分类展示技术栈
- 生命周期状态管理（EOL 日期跟踪�?
- 批量导入（CSV/Excel/Word/PDF�?
- 变更历史记录

---

#### 认证管理（`/certification`�?

**核心功能**�?
- 认证列表（含有效/过期状态）
- CSV 批量导入
- 到期提醒邮件发�?
- 导出

---

### 6.4 公共组件�?

**目录**: `frontend/src/components/ui/`

| 组件 | 说明 |
|------|------|
| `DataTable.tsx` | 通用数据表格，支持分页、排序、行选择 |
| `SearchForm.tsx` | 多条件搜索表单容�?|
| `StatusBadge.tsx` | 状态标签（带颜色映射） |
| `StatusTabs.tsx` | 状态分�?Tab 切换 |
| `StatsCard.tsx` | 统计数字卡片 |
| `Pagination.tsx` | 分页控件 |
| `PermissionGate.tsx` | 权限门控组件（按角色/权限显示/隐藏子元素） |
| `ExportButton.tsx` | 导出按钮（fetchBlob 下载�?|
| `FileUpload.tsx` | 文件上传组件（multipart/form-data�?|
| `DiagramUploadCard.tsx` | 架构图上传卡片（�?AI 评分展示�?|
| `RichTextEditor.tsx` | 富文本编辑器 |
| `RichTextContent.tsx` | 富文本内容渲�?|
| `MultiSelect.tsx` | 多选下拉组�?|
| `DateRangePicker.tsx` | 日期范围选择�?|
| `ResourceSearch.tsx` | 人员资源搜索（防抖自动补全） |
| `ResourceAutoComplete.tsx` | 资源自动补全 |
| `ResourceSingleSelect.tsx` | 单选人�?|
| `ResourceMultiSelect.tsx` | 多选人�?|
| `ConfirmDialog.tsx` | 确认对话�?|
| `ActionBar.tsx` | 操作按钮�?|
| `AuthButton.tsx` | 认证状态按钮（登录/登出�?|
| `LoginGate.tsx` | 登录拦截（未认证时展示登录提示） |
| `RiskLevelBadge.tsx` | 风险等级徽章 |
| `Toast.tsx` | 消息提示 |

---

### 6.5 核心工具�?

#### `lib/api.ts` �?HTTP 客户�?

- 封装 `GET / POST / PUT / PATCH / DELETE / postForm` 方法
- 统一处理响应信封（`{code, message, data, timestamp}`�?
- **401 自动刷新**：遇�?401 时调�?`keycloakService.refreshToken()`，刷新成功后重试一�?
- **403 重定�?*：跳转到 `/forbidden` 页面（带 15 秒冷却防止循环）
- `fetchBlob()` �?带认证头的文件下�?
- `authFetch()` �?通用认证 fetch 封装

#### `lib/keycloak-service.ts` �?Keycloak 服务

- 封装 Keycloak JS Adapter
- 提供 `login()` / `logout()` / `refreshToken()` 方法
- Token 存储�?sessionStorage

#### `lib/auth-context.tsx` �?认证上下�?

- 提供 `useAuth()` Hook
- 暴露 `user`、`isAdmin`、`isReviewer`、`hasPermission()` �?

---

## 7. API 接口汇�?

### 按模块汇�?

| 模块 | 接口前缀 | 接口数量（约�?|
|------|----------|-------------|
| EA Requests | `/api/ea-requests` | 7 |
| EA Attachments | `/api/ea-requests/attachments` | 5 |
| Meetings | `/api/meetings` | 9 |
| Actions | `/api/actions` | 8 |
| Schedules | `/api/schedules` | 6 |
| Scope | `/api/scope-of-change`, `/api/scope-checklist` | 10 |
| Architecture Check | `/api/arch-check-apps`, `/api/arch-check-interactions` | 8 |
| Meeting Decks | `/api/meeting-decks` | 4 |
| Applications / BCM | `/api/applications` | 12 |
| Technology Stack | `/api/technology-stack` | 7 |
| CMDB | `/api/cmdb` | 3 |
| BizCapability | `/api/BizCapability-master-data` | 5 |
| BC Visualization | `/api/applications/bcm/visualization` | 1 |
| Reports | `/api/reports` | 2 |
| Dashboard | `/api/dashboard` | 2 |
| Auth | `/api/auth` | 2 |
| Team Members | `/api/team-members` | 5 |
| Resources | `/api/resources` | 3 |
| Projects | `/api/projects` | 11 |
| Master Data | `/api/master-data` | 8 |
| Certifications | `/api/certifications` | 7 |
| Dict Options | `/api/dict-options` | 3 |
| Audit Log | `/api/audit-log`, `/api/process-log`, `/api/email-log` | 5 |
| Export | `/api/export` | 1 |
| EA Review Logs | `/api/ea-review-logs` | 3 |
| Health | `/api/health` | 1 |

### 通用分页参数

所有列表接口均支持以下分页参数（通过 `PaginationParams` 依赖注入）：

| 参数 | 类型 | 默认�?| 说明 |
|------|------|--------|------|
| `page` | int | 1 | 当前页码 |
| `pageSize` | int | 20 | 每页条数（最�?200�?|
| `sortField` | string | - | 排序字段（前端字段名，映射到 DB 列） |
| `sortOrder` | string | desc | 排序方向（asc/desc�?|

---

## 8. 安全设计

### 认证

- **生产环境**：Keycloak OIDC，JWT Bearer Token 验证
- **开发模�?*：环境变�?`AUTH_DISABLED=true` 注入固定测试用户

### 授权（双层设计）

```
第一层：功能级权限检查（require_permission�?
    └─ 检查角色是否有 resource:scope 权限
         例：require_permission("ea_request", "write")

第二层：记录级所有权检查（在路由逻辑中）
    ├─ check_request_creator(user, request_id, db)
    �?   └─ 非管理员必须�?create_by 字段的�?
    ├─ check_request_draft_status(request_data, operation)
    �?   └─ 非管理员只能删除 Draft 状态的请求
    ├─ check_reviewer_assignment(user, request_id, db)
    �?   └─ 非管理员必须�?assign_reviewer 数组�?
    └─ check_app_ownership(user, app_id, db)
         └─ 非管理员必须是应�?IT Owner
```

### SQL 注入防护

- 所有动态查询使�?SQLAlchemy `text()` + 命名参数（`:param_name`�?
- 排序字段通过白名单（`SORT_FIELD_MAP`）映射，防止注入

### 文件安全

- 附件最�?10MB
- 文件存储�?S3，前端通过预签�?URL 访问
- 文件类型：支�?PNG/JPG/PDF/PPT 等，不直接执行上传文�?

---

## 9. 数据流转�?

### EA 审查请求完整生命周期

```
用户（申请人�?       EA Admin              EA Reviewer
     �?                  �?                     �?
     ├─ POST /ea-requests �?                     �?
     �?  (status: Draft)  �?                     �?
     �?                  �?                     �?
     ├─ 上传附件          �?                     �?
     �?  POST /attachments/upload               �?
     �?  └─ 触发 AI 架构检�?                   �?
     �?                  �?                     �?
     ├─ PUT /ea-requests/{id}                   �?
     �?  (status: Submitted)                    �?
     �?  └─ 发送邮件通知（申请人+CC�?           �?
     �?                  �?                     �?
     �?                  ├─ PUT /ea-requests/{id}�?
     �?                  �?  (status: Accepted) �?
     �?                  �?  assignReviewer=[...]�?
     �?                  �?  └─ 发送邮件→申请�? �?
     �?                  �?  └─ 发送邮件→评审�? �?
     �?                  �?                     �?
     �?                  �?                     ├─ 创建会议 POST /meetings
     �?                  �?                     ├─ 创建行动�?POST /actions
     �?                  �?                     �?
     �?                  �?                     ├─ PUT /ea-requests/{id}
     �?                  �?                     �?  (reviewResult: Approved)
     �?                  �?                     �?  └─ 发送邮件→申请�?
     �?                  �?                     �?
     └─────────────────────────────────────────�?
```

### BCM 数据�?

```
CMDB API (每日 02:00)
    └─ cmdb_sync.py �?eam.cmdb_application

用户手动维护
    └─ eam.project_app (项目应用信息)

BizCapability 主数据（EA Admin 导入�?
    └─ eam.bcpf_master_data

BCM 创建（App Owner�?
    └─ POST /applications/bcm
         └─ eam.biz_cap_map (app_id + bcpf_master_id)

可视化展�?
    └─ GET /applications/bcm/visualization
         └─ JOIN biz_cap_map + bcpf_master_data + project_app + cmdb_application
```

---

*文档生成自代码扫描，如需更新请重新扫描工程代码�?

