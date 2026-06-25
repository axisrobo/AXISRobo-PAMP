# Antd Drawer Custom Width

## Problem

在 antd v5 中，`<Drawer width={...}>` 的 `width` prop 已被废弃，运行时会出现：

```
Warning: [antd: Drawer] `width` is deprecated. Please use `size` instead.
```

`size` 只支持 `'default'`（378px）和 `'large'`（736px）两种预设，无法满足自定义宽度需求。

## Rule

设置 antd Drawer 自定义宽度时，**必须使用 `styles.wrapper`**，而非 `width` prop。

## Fix Pattern

```tsx
// ✅ 正确
<Drawer
  placement="right"
  styles={{ wrapper: { width: 1100 } }}
  open={open}
  onClose={onClose}
>
  ...
</Drawer>
```

## Anti-pattern

```tsx
// ❌ 废弃写法，runtime 会出现 deprecation warning
<Drawer width={1100} ...>
  ...
</Drawer>

// ❌ 无法设置任意宽度
<Drawer size="large" ...>
  ...
</Drawer>
```
