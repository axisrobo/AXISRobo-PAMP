# AxisArch Mobile Adaptation Guidelines

> Last updated: 2026-06-22

## Supported Breakpoints

| Breakpoint | Min Width | Target |
|------------|-----------|--------|
| Mobile | 375px | Phone (primary) |
| Tablet | 768px | iPad portrait |
| Desktop | 1024px | Laptop |
| Wide | 1280px+ | Desktop monitor |

## Strategy

### Tables → Card List
On screens < 768px, complex data tables should offer a card-based list view as an alternative to horizontal scrolling.

```tsx
<DataTable
  columns={columns}
  data={data}
  mobileView="cards"  // renders cards below md breakpoint
/>
```

Implementation in `DataTable`:
- Below `md` breakpoint with `mobileView="cards"`: render a stacked card for each row
- Each card shows key-value pairs from visible columns
- Card title: first column or rowKey value
- Card body: remaining visible columns as `label: value` rows

### Dialogs → Fullscreen
On screens < 768px:
- AntD `Drawer`: use `size="100%"` or force full width
- AntD `Modal`: apply `width: '100%'` style, remove max-width constraint
- Custom fixed overlays: ensure `inset-0` (already fullscreen)

### Forms → Single Column
- Multi-column search forms → stack vertically below `md` breakpoint
- `SearchForm` with `inline` mode: ensure wrap on small screens

### Navigation
- Desktop: fixed sidebar (240px)
- Tablet/Mobile: hamburger menu → AntD `Drawer` from left
- Header: sticky, logo + hamburger, reduced text on small screens

### Mindmap / Visualization
- Desktop: interactive SVG mindmap with pan/zoom
- Mobile: fallback to a simplified list/tree view of the same data

## Anti-patterns
- Do NOT use `overflow-x-auto` on tables without a card fallback
- Do NOT use `calc(100vh - 280px)` for fixed views on mobile
- Do NOT rely on hover interactions (use click/tap instead)
