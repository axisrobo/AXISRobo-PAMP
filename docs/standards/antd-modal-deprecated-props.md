# Antd Deprecated Props & API Migration

## Problem
Ant Design 5.x 废弃了部分组件 props 和静态 API，使用旧方式会在 console 出现警告，影响动态主题和上下文消费。

---

## Modal: `destroyOnClose` → `destroyOnHidden`

| 废弃 prop | 替换 prop |
|---|---|
| `destroyOnClose` | `destroyOnHidden` |

### Rule
使用 `<Modal>` 时，一律使用 `destroyOnHidden` 而非 `destroyOnClose`。

### Fix Pattern
```tsx
// ✅ 正确
<Modal destroyOnHidden ...>

// ❌ 废弃
<Modal destroyOnClose ...>
```

---

## Table: `rowKey` 函数的 `index` 第二参数

### Problem
`rowKey={(record, index) => ...}` 中的第二参数 `index` 在 Antd 5.x 已废弃，不保证正常工作。

### Rule
`rowKey` 函数只使用第一参数 `record`，通过 record 的字段组合唯一 key，不依赖 index。

### Fix Pattern
```tsx
// ✅ 正确 — 用 record 字段组合 key
<Table rowKey={(r) => `${r.rowNo}-${r.errorResult}`} ...>

// ✅ 正确 — 直接使用唯一 id 字段
<Table rowKey="id" ...>

// ❌ 废弃 — 使用 index 参数
<Table rowKey={(r, i) => `${r.rowNo}-${i}`} ...>
```

### Anti-pattern
```tsx
rowKey={(record, index) => index}  // 'index' parameter is deprecated
```

---

## message / notification / modal — 静态 API

### Problem
`message.error(...)` 等静态调用无法消费动态主题和 React context，Antd 5.x 会发出警告：
`Static function can not consume context like dynamic theme. Please use 'App' component instead.`

### Rule
在组件内一律通过 `App.useApp()` hook 获取 `message`、`notification`、`modal` 实例，不使用从 antd 直接导入的静态函数。

### Fix Pattern
```tsx
// ✅ 正确 — 使用 App.useApp() hook
import { App } from 'antd';

export default function MyPage() {
  const { message, modal, notification } = App.useApp();

  const handleAction = async () => {
    message.success('Done');
    message.error('Failed');
  };
}
```

### Anti-pattern
```tsx
// ❌ 静态调用 — 无法消费动态主题
import { message } from 'antd';

message.error('Data Version is required');   // Warning!
message.success('Import success');           // Warning!
```
