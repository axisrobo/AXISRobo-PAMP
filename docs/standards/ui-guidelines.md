# AxisArch UI Design Guidelines

> Last updated: 2026-06-22

## Component Hierarchy

| Category | Use | Notes |
|----------|-----|-------|
| **Ant Design** | Form, Table, Drawer, Modal, Select, DatePicker, Button, Input | Primary UI kit |
| **Tailwind CSS** | Layout (flex/grid), spacing, colors, responsive breakpoints | Utility-only, not component styles |
| **Custom shared/ui** | StatusBadge, SearchForm, DataTable, FieldLabel | Thin wrappers over AntD |

## Rules

### 1. Prefer AntD for interactive components
- Forms: `Form.Item` with `name`, `rules`, `validateTrigger="onBlur"`
- Tables: `DataTable<T>` (wraps AntD `Table`)
- Dialogs: AntD `Drawer` or `Modal`, not custom fixed overlays
- Select/DatePicker/Input: AntD built-in components

### 2. Tailwind for layout only
- `flex`, `grid`, `gap`, `p-`, `m-`, `w-`, `h-`
- `min-h-screen`, `sticky`, `overflow`
- Color classes from `tailwind.config.ts` theme tokens (`text-brand-primary`, `bg-gray`, etc.)
- Do NOT use Tailwind for: form controls, list rendering, complex stateful components

### 3. Color tokens
- Brand primary: `#E2231A` (red) → `text-brand-primary`, `bg-red-50`
- Primary blue: `#4096FF` → `bg-primary-blue`, `text-primary-blue`
- Status colors: `status-completed` (green), `status-in-progress` (orange), `status-draft` (gray)
- Text: `text-primary` (#262626), `text-secondary` (#8C8C8C)
- Border: `border-light` (#F0F0F0)

### 4. Button conventions
- Primary action: `<Button type="primary">` (AntD)
- Secondary action: `<Button>` (AntD default)
- Destructive: `<Button danger>`
- Icon-only buttons MUST have `aria-label`
- Link-style: `<Button type="link">`

### 5. Form conventions
- Field-level validation: `Form.Item rules={[{ required: true, message: '...' }]}`
- Validation trigger: `validateTrigger="onBlur"` (not onChange)
- Disabled fields: add `tooltip` prop explaining WHY
- Full-page forms: max width `max-w-3xl`, centered

### 6. Table conventions
- Use `DataTable<T>` with typed `Column<T>[]`
- Default column width: 150px (desktop)
- Responsive: provide `mobileView="cards"` on `DataTable` for mobile
- Export: use `exportConfig` prop

### 7. Page organization
- Each page: thin wrapper + imported feature components
- Feature component max ~400 lines (split if larger)
- Shared hooks in `features/xxx/hooks/`
- Shared components in `features/xxx/components/`

### 8. State management
- Server state: `@tanstack/react-query` (useQuery/useMutation)
- Component-local state: `useState`
- Multi-step flows: prefer `useReducer` over multiple useState
- Cross-component shared state: React Context (not Zustand yet)
