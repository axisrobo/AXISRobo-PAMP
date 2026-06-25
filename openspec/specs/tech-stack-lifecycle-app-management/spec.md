## ADDED Requirements

### Requirement: Register Application to Tech Stack
具有 `tech_stack` write 权限的用户 SHALL 能通过 "Add an Application" 按钮，用 Application ID 搜索 CMDB，将应用登记到 `tech_stack_app` 表。后端 SHALL 校验 app_id 唯一性，已登记的应用不可重复添加。

#### Scenario: 打开新建 Modal
- **WHEN** 用户点击 Lifecycle 列表页的 "Add an Application" 按钮
- **THEN** 弹出 "Application Technology Stack" Modal，Application ID 字段为空，其余字段均为空

#### Scenario: 通过 Application ID 查询 CMDB
- **WHEN** 用户在 Application ID 输入框输入后点击搜索按钮
- **THEN** 调用 `GET /api/technology-stack/cmdb-lookup?appId=xxx`，返回匹配的 CMDB 记录，并自动填充 Application Name、Ownership、Classification、Function (Value Chain)、IT Owner、Portfolio Management、Solution Type、Application Status、Created By、Created At 字段（均为只读）

#### Scenario: CMDB lookup 不返回已登记的 App
- **WHEN** 调用 `GET /api/technology-stack/cmdb-lookup`
- **THEN** 结果中不包含已在 `tech_stack_app` 中存在的 app_id（后端过滤）

#### Scenario: 保存新登记成功
- **WHEN** 用户填写 Application ID 并点击 Save
- **THEN** 调用 `POST /api/technology-stack/apps`，后端校验 app_id 不存在于 `tech_stack_app`，创建记录，返回 201，Modal 切换为详情模式，Lifecycle 列表刷新

#### Scenario: 重复登记被拒绝
- **WHEN** 用户尝试保存一个已登记的 app_id
- **THEN** 后端返回 409 Conflict，前端显示错误提示 "This application has already been registered"

#### Scenario: 权限控制
- **WHEN** 用户没有 `tech_stack` write 权限
- **THEN** "Add an Application" 按钮不显示

---

### Requirement: View Application Tech Stack Detail
任意具有 `tech_stack` read 权限的用户 SHALL 能通过点击 Lifecycle 列表中的 Application ID 链接，打开 Application Technology Stack 详情 Modal。

#### Scenario: 打开详情 Modal
- **WHEN** 用户点击 Lifecycle 列表中某行的 Application ID 链接
- **THEN** 弹出 "Application Technology Stack" Modal，顶部显示只读 General Data，默认激活 "Key Technology Stack Catalog" Tab

#### Scenario: General Data 字段只读
- **WHEN** 详情 Modal 打开
- **THEN** Application ID、Application Name、Application Ownership、Application Classification、Function (Value Chain)、Application IT Owner、Application Portfolio Management、Application Solution Type、Application Status、Created By、Created At 均为只读展示，不可编辑

#### Scenario: Delete 按钮可见性
- **WHEN** 用户具有 `tech_stack` write 权限打开详情 Modal
- **THEN** 右上角显示 Delete 按钮

#### Scenario: Delete 删除登记
- **WHEN** 用户点击 Delete 并确认
- **THEN** 调用 `DELETE /api/technology-stack/apps/{app_id}`，删除 `tech_stack_app` 记录，Modal 关闭，Lifecycle 列表刷新

---

### Requirement: Manage Key Technology Stack Catalog
具有 `tech_stack` write 权限的用户 SHALL 能在 "Key Technology Stack Catalog" Tab 中对该 Application 的 `tech_key_stack_item` 进行增删改查。

#### Scenario: 查看 Catalog 列表
- **WHEN** 用户打开 Key Technology Stack Catalog Tab
- **THEN** 调用 `GET /api/technology-stack/apps/{app_id}/catalog`，展示分页表格，列包含：Stack ID、Security Risk Level（带颜色标签）、EOL Date、EOL Interval Time、Maintainability Risk Level、Category、Sub Category、Technology Component、Component Package Name、Major Version、Minor Version、Patch Version、Operation

#### Scenario: 按条件过滤 Catalog
- **WHEN** 用户选择 Category、Sub Category、Technology Component 或 Use Status 过滤器
- **THEN** 表格仅展示匹配的条目

#### Scenario: 新增 Catalog 条目
- **WHEN** 用户点击 "+ Add" 按钮
- **THEN** 弹出 "Key Technology Stack Catalog" 子 Modal，包含字段：Category（必填下拉）、Sub Category（必填下拉，联动 Category）、Technology Component（必填文本）、Component Package Name（必填文本）、Major Version（必填数字下拉）、Minor Version（必填数字下拉）、Patch Version（文本）、Use Status（下拉）、Standard（只读，从 Master Data 带入）、Comments（文本）

#### Scenario: 新增时联动 Master Data 填充风险字段
- **WHEN** 用户选择 Category/SubCategory/Component/ComponentPackage 和版本后
- **THEN** 前端查询匹配的 Master Data，自动填充 EOL Date、EOL Interval Time、Maintainability Risk Level、Security Risk Level、CVSS v3 Score、Standard、master_no（均为只读展示）

#### Scenario: 保存新增 Catalog 条目
- **WHEN** 用户填写必填项并点击 Save
- **THEN** 调用 `POST /api/technology-stack/apps/{app_id}/catalog`，创建 `tech_key_stack_item` 记录，stack_id 由数据库序列自动生成，后端将字段变更逐字段写入 `tech_stack_operate_log`，列表刷新

#### Scenario: 编辑 Catalog 条目
- **WHEN** 用户点击行内 ✏️ 按钮
- **THEN** 弹出预填的子 Modal，修改保存后调用 `PUT /api/technology-stack/apps/{app_id}/catalog/{item_id}`，变更字段写入 `tech_stack_operate_log`

#### Scenario: 删除 Catalog 条目
- **WHEN** 用户点击行内 🗑 按钮并确认
- **THEN** 调用 `DELETE /api/technology-stack/apps/{app_id}/catalog/{item_id}`，记录从列表消失

---

### Requirement: View Team Members
任意具有 `tech_stack` read 权限的用户 SHALL 能在 "Team Members" Tab 中查看该 Application 关联项目的团队成员列表。

#### Scenario: 查看 Team Members
- **WHEN** 用户切换到 Team Members Tab
- **THEN** 调用 `GET /api/technology-stack/apps/{app_id}/team-members`，展示成员列表（IT Code、Name、Worker Type、Manager IT Code）

#### Scenario: 无团队成员时展示空状态
- **WHEN** 该 Application 无关联项目或项目无成员
- **THEN** 展示 "No Data"

---

### Requirement: View Changed Log
任意具有 `tech_stack` read 权限的用户 SHALL 能在 "Changed Log" Tab 中查看该 Application 下 Catalog 条目的字段级变更历史。

#### Scenario: 查看 Changed Log
- **WHEN** 用户切换到 Changed Log Tab
- **THEN** 调用 `GET /api/technology-stack/apps/{app_id}/operate-log`，展示变更列表（Stack ID、Field、Old Value、New Value、Changed By、Changed At），按时间倒序

#### Scenario: 无变更记录展示空状态
- **WHEN** 无任何变更记录
- **THEN** 展示 "No Data"

---

### Requirement: Checking — Sync Catalog with Master Data
具有 `tech_stack` write 权限的用户 SHALL 能点击 "Checking" 按钮触发合规检查，系统自动对比 Master Data 更新，同步 Catalog 条目的 EOL/Security 风险字段。

#### Scenario: 触发 Checking
- **WHEN** 用户点击 "Checking" 按钮
- **THEN** 调用 `POST /api/technology-stack/apps/{app_id}/checking`，后端执行同步逻辑

#### Scenario: 1小时内限频
- **WHEN** 该 App 最近一次 Checking 距今不足 1 小时
- **THEN** 返回 `{ "alreadyUpToDate": false, "message": "The last inspection was conducted at <time>，You can only perform an inspection once within the next 1 hour!" }`，前端显示提示

#### Scenario: Master Data 无更新
- **WHEN** 自上次 Checking 以来 Master Data 无变更
- **THEN** 返回 `{ "alreadyUpToDate": true, "message": "The associated master data information is already up-to-date." }`，前端显示提示

#### Scenario: Checking 成功更新 Catalog
- **WHEN** Master Data 有更新，且该 App 有匹配的 Catalog 条目
- **THEN** 后端根据 category/sub_category/component/component_package/major_version/minor_version（patch_version 为"*"或空时宽松匹配）找到对应 Catalog 条目，更新 eol_date、eol_interval_time、maintainability_risk_level/light、cvss_v3_score、security_risk_level/light、standard、master_no，写入 `tech_key_stack_auto_checking_log`，前端刷新 Catalog 列表

#### Scenario: 风险字段计算规则 — EOL
- **WHEN** Master Data 的 eol_date 不为空
- **THEN** 根据距今时长：已过期→ `Very Critical`；0-6月→ `Very Critical`；6-12月→ `Critical`；12-24月→ `High`；24月以上→ `Low`

#### Scenario: 风险字段计算规则 — Security
- **WHEN** Master Data 的 cvss_v3_score 不为空
- **THEN** 0→空；0.1-3.9→ `Low`；4.0-6.9→ `Medium`；7.0-8.9→ `High`；9.0-10.0→ `Very Critical`

---

### Requirement: Backend POST /api/technology-stack/apps
后端 SHALL 提供注册 Application 的接口，校验唯一性。

#### Scenario: 注册成功
- **WHEN** 发送有效 POST 请求，app_id 不在 `tech_stack_app` 中
- **THEN** 在 `eam.tech_stack_app` 创建记录，返回 201

#### Scenario: 重复注册
- **WHEN** app_id 已存在于 `tech_stack_app`
- **THEN** 返回 409 Conflict

---

### Requirement: Backend GET /api/technology-stack/apps/{app_id}
后端 SHALL 提供获取 Application 详情的接口，合并 `tech_stack_app` 与 `cmdb_application` 数据。

#### Scenario: 获取成功
- **WHEN** 发送 GET 请求，app_id 存在于 `tech_stack_app`
- **THEN** 返回合并后的 General Data（含 CMDB 字段）

#### Scenario: 不存在
- **WHEN** app_id 不存在于 `tech_stack_app`
- **THEN** 返回 404

---

### Requirement: Backend Catalog CRUD APIs
后端 SHALL 提供 Catalog 条目的增删改查接口，写操作需记录 `tech_stack_operate_log`。

#### Scenario: 获取 Catalog 列表
- **WHEN** 发送 GET /catalog，支持 category/subCategory/component/useStatus 过滤参数
- **THEN** 返回分页的 `tech_key_stack_item` 列表

#### Scenario: 新增 Catalog 条目
- **WHEN** 发送有效 POST /catalog 请求
- **THEN** 在 `tech_key_stack_item` 创建记录（stack_id 自动生成），逐字段写 `tech_stack_operate_log`（old_value = null），返回 201

#### Scenario: 更新 Catalog 条目
- **WHEN** 发送有效 PUT /catalog/{item_id} 请求
- **THEN** 更新 `tech_key_stack_item`，对每个变更字段写 `tech_stack_operate_log`（记录 old_value 和 new_value），返回 200

#### Scenario: 删除 Catalog 条目
- **WHEN** 发送 DELETE /catalog/{item_id}
- **THEN** 删除 `tech_key_stack_item` 记录，返回 200

---

### Requirement: Backend GET /api/technology-stack/cmdb-lookup
后端 SHALL 提供 CMDB Application 搜索接口，结果排除已登记的 app_id。

#### Scenario: 搜索成功
- **WHEN** 发送 GET /cmdb-lookup?appId=xxx
- **THEN** 返回匹配的 cmdb_application 记录，不包含已在 tech_stack_app 中的 app_id
