# Antd Tag: 使用 variant 替代 bordered

## Problem

antd v5 中 `Tag` 组件的 `bordered` prop 已废弃，控制台会出现警告：

```
Warning: [antd: Tag] `bordered={false}` is deprecated. Please use `variant="filled"` instead.
```

## Rule

禁止在 `Tag` 组件上使用 `bordered` prop，改用 `variant`。

## Fix Pattern

```tsx
// ✅ 正确
<Tag color={color} variant="filled">...</Tag>       // 无边框（填充色背景）
<Tag color={color} variant="outlined">...</Tag>     // 有边框（默认，等同原 bordered={true}）
<Tag color={color} variant="borderless">...</Tag>   // 无边框无背景

// ❌ 废弃写法
<Tag color={color} bordered={false}>...</Tag>
<Tag color={color} bordered={true}>...</Tag>
```

## 对照表

| 旧写法 | 新写法 |
|--------|--------|
| `bordered={false}` | `variant="filled"` |
| `bordered={true}` 或省略 | `variant="outlined"`（默认） |

## Anti-pattern

```tsx
// ❌ 不要这样写
<Tag bordered={false}>...</Tag>
```
