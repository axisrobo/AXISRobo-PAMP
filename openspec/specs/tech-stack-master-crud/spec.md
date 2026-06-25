## ADDED Requirements

### Requirement: Fix column key mapping
前端 Master Data 表格中 Technology Component 和 Component Package Name 列的 key 必须与 API 响应字段名一致。

#### Scenario: Technology Component 列正常显示
- **WHEN** 列表加载完成
- **THEN** Technology Component 列显示来自 API 的 `component` 字段值，不为空

#### Scenario: Component Package Name 列正常显示
- **WHEN** 列表加载完成
- **THEN** Component Package Name 列显示来自 API 的 `componentPackage` 字段值，不为空

---

### Requirement: Create master data record
具有 `tech_stack` write 权限的用户 SHALL 能通过点击 New 按钮，在 Modal 表单中填写字段并保存，创建一条新的 Tech Stack Master Data 记录。

#### Scenario: 打开新建表单
- **WHEN** 用户点击 New 按钮
- **THEN** 弹出 Modal 表单，字段均为空，Category、Sub Category、Technology Component、Component Package Name、Version、EA Advice 为必填项

#### Scenario: 保存成功
- **WHEN** 用户填写所有必填项并点击 Save
- **THEN** 调用 `POST /api/technology-stack`，成功后 Modal 关闭，列表刷新，新记录出现在列表中

#### Scenario: 保存失败（必填项为空）
- **WHEN** 用户未填写必填项点击 Save
- **THEN** 必填项高亮显示错误提示，不发起请求

#### Scenario: 权限控制
- **WHEN** 用户没有 `tech_stack` write 权限
- **THEN** New 按钮不显示

---

### Requirement: Edit master data record
具有 `tech_stack` write 权限的用户 SHALL 能通过点击行内编辑按钮，在 Modal 表单中修改字段并保存，更新已有 Tech Stack Master Data 记录。

#### Scenario: 打开编辑表单
- **WHEN** 用户点击行内 ✏️ 按钮
- **THEN** 弹出 Modal 表单，字段预填当前记录数据

#### Scenario: 保存更新成功
- **WHEN** 用户修改字段后点击 Save
- **THEN** 调用 `PUT /api/technology-stack/{id}`，成功后 Modal 关闭，列表显示更新后的值

---

### Requirement: Delete master data record
具有 `tech_stack` write 权限的用户 SHALL 能通过点击行内删除按钮，确认后软删除一条 Tech Stack Master Data 记录。

#### Scenario: 确认删除弹框
- **WHEN** 用户点击行内 🗑 按钮
- **THEN** 弹出确认对话框，说明将要删除的记录

#### Scenario: 确认后删除成功
- **WHEN** 用户在确认框中点击 Confirm
- **THEN** 调用 `DELETE /api/technology-stack/{id}`，后端将 status 设为 'Deleted'，列表中该记录消失

#### Scenario: 取消删除
- **WHEN** 用户在确认框中点击 Cancel
- **THEN** 对话框关闭，记录不受影响

---

### Requirement: Export master data
任意具有 `tech_stack` read 权限的用户 SHALL 能点击 Export 按钮，将当前过滤条件下的全部 Master Data 导出为 CSV 文件下载。

#### Scenario: 导出成功
- **WHEN** 用户点击 Export 按钮
- **THEN** 浏览器触发 CSV 文件下载，文件包含当前过滤条件下的所有记录

#### Scenario: 无权限时 Export 仍可用
- **WHEN** 用户仅有 `tech_stack` read 权限（无 write 权限）
- **THEN** Export 按钮仍显示且可用（不需要 write 权限）

---

### Requirement: Backend POST /api/technology-stack
后端 SHALL 提供创建 Tech Stack Master Data 的接口。

#### Scenario: 创建成功
- **WHEN** 发送有效的 POST 请求到 `/api/technology-stack`，携带必填字段
- **THEN** 在 `eam.tech_stack_master_data` 表创建新记录，返回 201 和新记录 ID

#### Scenario: 缺少必填字段
- **WHEN** 发送 POST 请求缺少必填字段（category / component / version 等）
- **THEN** 返回 422 错误

---

### Requirement: Backend PUT /api/technology-stack/{id}
后端 SHALL 提供更新 Tech Stack Master Data 的接口。

#### Scenario: 更新成功
- **WHEN** 发送有效的 PUT 请求到 `/api/technology-stack/{id}`
- **THEN** 更新 `eam.tech_stack_master_data` 中对应记录，返回 200 和更新后的记录

#### Scenario: 记录不存在
- **WHEN** id 不存在
- **THEN** 返回 404

---

### Requirement: Backend DELETE /api/technology-stack/{id}
后端 SHALL 提供软删除 Tech Stack Master Data 记录的接口。

#### Scenario: 软删除成功
- **WHEN** 发送 DELETE 请求到 `/api/technology-stack/{id}`
- **THEN** 该记录的 `status` 字段被设为 `'Deleted'`，返回 200

#### Scenario: 记录不存在
- **WHEN** id 不存在
- **THEN** 返回 404

---

### Requirement: Backend GET /api/technology-stack/export
后端 SHALL 提供导出 Tech Stack Master Data 为 CSV 的接口，支持相同的过滤参数。

#### Scenario: 导出全部数据
- **WHEN** 发送带过滤参数的 GET 请求到 `/api/technology-stack/export`
- **THEN** 返回 Content-Type: text/csv 的响应，包含匹配过滤条件的所有记录

#### Scenario: 列表查询自动过滤已删除记录
- **WHEN** 调用列表接口 `GET /api/technology-stack`（无 status 参数）
- **THEN** 返回结果不包含 status = 'Deleted' 的记录
