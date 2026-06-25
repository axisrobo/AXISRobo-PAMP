## ADDED Requirements

> Merged from: `antd-infrastructure`, `antd-shared-components`, `antd-ea-review-pages`

---

## Part 1: Infrastructure

### Requirement: antd 依赖安装
系统 SHALL 安装 `antd@^6.3.2` 和 `@ant-design/nextjs-registry@^1.3.0` 作为 `frontend/package.json` 的 dependencies。

#### Scenario: 依赖安装成功
- **WHEN** 在 `frontend/` 目录执行 `npm install`
- **THEN** `antd` 和 `@ant-design/nextjs-registry` 安装成功，无 peer dependency 冲突

### Requirement: AntdRegistry SSR 样式注入
根布局文件 SHALL 使用 `@ant-design/nextjs-registry` 的 `AntdRegistry` 组件包裹应用内容，确保 antd 组件在 SSR 时样式正确注入。

#### Scenario: SSR 页面无 FOUC
- **WHEN** 用户首次访问任意页面（服务端渲染）
- **THEN** antd 组件样式随 HTML 一起返回，页面无闪烁

#### Scenario: AntdRegistry 包裹位置
- **WHEN** 查看 `app/layout.tsx` 源代码
- **THEN** `AntdRegistry` 组件包裹在 `{children}` 外层，位于 `<body>` 标签内

### Requirement: ConfigProvider 主题配置
根布局文件 SHALL 配置 antd `ConfigProvider`，设置主题 token 与项目现有颜色体系一致。

#### Scenario: 主题颜色匹配
- **WHEN** antd 组件渲染 primary 色
- **THEN** 使用 `#4096FF`（与 Tailwind `primary-blue` 一致）

### Requirement: Tailwind CSS preflight 禁用
`tailwind.config.ts` SHALL 禁用 `preflight` 核心插件，避免 Tailwind CSS reset 覆盖 antd 组件默认样式。

#### Scenario: 基础样式补充
- **WHEN** preflight 禁用后
- **THEN** `globals.css` 中包含最小化的 base reset 样式

---

## Part 2: Shared Components

### Requirement: DataTable 组件替换为 antd Table
`DataTable` 共享组件 SHALL 在内部替换为 antd `Table`，保持对外 props 接口兼容。

#### Scenario: 列定义兼容
- **WHEN** 页面传入现有格式的 `columns` prop（含 `key`、`label`、`sortable`、`render`）
- **THEN** DataTable 内部转换为 antd `ColumnsType` 格式并正确渲染

#### Scenario: 排序功能
- **WHEN** 用户点击支持排序的列标题
- **THEN** 触发 `onSort` 回调，排序行为与当前实现一致

### Requirement: Pagination 组件替换
`Pagination` 共享组件 SHALL 替换为 antd `Pagination` 或整合到 DataTable 的内置分页中。

### Requirement: StatusBadge 替换为 antd Tag
`StatusBadge` 组件 SHALL 替换为基于 antd `Tag` 的实现，保持状态→颜色映射。

### Requirement: ConfirmDialog 替换为 antd Modal
`ConfirmDialog` 组件 SHALL 替换为 antd `Modal.confirm()` 或 antd `Modal`。

---

## Part 3: EA Review Pages

### Requirement: EA Review 列表页使用 antd Table + Form
EA Review 的 4 个列表页（request-summary、actions、meetings、calendar）SHALL 使用 antd `Table`（含排序和分页）替换现有 DataTable + Pagination 组合，搜索区域使用 antd `Form` + `Select` + `Input` + `DatePicker` 替换现有 SearchForm。

#### Scenario: 请求列表页表格渲染
- **WHEN** 用户访问 EA Review Request Summary 页面
- **THEN** 渲染 antd `Table`，包含 15 列、服务端排序、分页功能

### Requirement: 请求创建向导使用 antd Steps + Form
`request/create/page.tsx` 的 4 步创建向导 SHALL 使用 antd `Steps` 替换手写 StepIndicator，表单字段使用 antd `Form.Item` + `Select` + `Input.TextArea`。

### Requirement: 请求详情页使用 antd 组件套件
`request/[id]/page.tsx` SHALL 使用以下 antd 组件替换：

- 可折叠 Section → antd `Collapse`
- 手写 Modal → antd `Modal`
- 手写 reviewer multi-select → antd `Select mode="multiple" showSearch`
- StatusStepper → antd `Steps`
- DataTable → antd `Table`
- Drawer → antd `Drawer`
- 原生 `<select>` → antd `Select`
- 原生 `<input type="date">` → antd `DatePicker`

### Requirement: Action 详情页编辑使用 antd 表单控件
`actions/[actionId]/page.tsx` SHALL 将编辑模式下的原生控件替换为 antd 组件。

### Requirement: 创建会议页使用 antd 表单
`request/[id]/create-meeting/page.tsx` SHALL 使用 antd `Form` + 控件替换手写表单。

### Requirement: 会议详情页使用 antd 展示组件
`meetings/[meetingNo]/page.tsx` SHALL 使用 antd `Collapse` 和 `Descriptions` 替换手写 Section 和 GDRow。

### Requirement: antd 组件使用约定
- Drawer SHALL 使用 `size="large"` 而非 `width={800}`
- Modal 和 Drawer SHALL 使用 `destroyOnHidden` 而非弃用的 `destroyOnClose`
- 确认对话框 SHALL 通过 `App.useApp()` 获取 `modal`、`message` 实例
