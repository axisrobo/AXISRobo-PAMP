## ADDED Requirements

### Requirement: useMediaQuery hook for responsive state
The system SHALL provide a `useMediaQuery` hook at `frontend/src/lib/useMediaQuery.ts` that accepts a CSS media query string and returns a boolean indicating whether the query matches.

#### Scenario: Desktop viewport detected
- **WHEN** the viewport width is >= 1024px
- **THEN** `useMediaQuery('(min-width: 1024px)')` SHALL return `true`

#### Scenario: Mobile viewport detected
- **WHEN** the viewport width is < 1024px
- **THEN** `useMediaQuery('(min-width: 1024px)')` SHALL return `false`

#### Scenario: SSR default
- **WHEN** rendering on the server (no `window` available)
- **THEN** `useMediaQuery` SHALL return `true` (desktop default) to avoid hydration mismatch

#### Scenario: Viewport resize
- **WHEN** the user resizes the browser window across the breakpoint boundary
- **THEN** the hook SHALL update its return value without page reload

---

### Requirement: Header mobile hamburger menu
The Header component SHALL display a hamburger menu icon (☰) on viewports < 1024px (lg breakpoint). On lg+ viewports, the navigation tabs, language switcher, and auth button SHALL display inline as currently.

#### Scenario: Mobile header layout
- **WHEN** viewport width < 1024px
- **THEN** the Header SHALL show Logo + title + ☰ icon, hiding the inline navigation tabs, language switcher, and auth button

#### Scenario: Mobile menu open
- **WHEN** user taps the ☰ icon on a HomeLayout page (no sidebar)
- **THEN** a dropdown SHALL appear containing: "I'm Requester" link, "EA Review" link, language switcher, and auth button

#### Scenario: Mobile menu close
- **WHEN** user taps the ☰ icon again or taps outside the dropdown
- **THEN** the dropdown SHALL close

#### Scenario: Desktop header layout unchanged
- **WHEN** viewport width >= 1024px
- **THEN** the Header SHALL render identically to current layout (no ☰ icon, all items inline)

---

### Requirement: Header accepts onMenuClick prop for PageLayout integration
The Header component SHALL accept an optional `onMenuClick` callback prop. When provided and viewport < 1024px, clicking the ☰ icon SHALL call `onMenuClick` instead of opening the built-in dropdown menu.

#### Scenario: PageLayout ☰ triggers sidebar drawer
- **WHEN** Header is rendered inside PageLayout and user taps ☰ on mobile
- **THEN** `onMenuClick` SHALL be invoked (which opens the Sidebar Drawer)

#### Scenario: HomeLayout ☰ triggers dropdown
- **WHEN** Header is rendered inside HomeLayout (no `onMenuClick` prop) and user taps ☰ on mobile
- **THEN** the built-in navigation dropdown SHALL open

---

### Requirement: Sidebar Drawer mode on mobile
PageLayout SHALL render the Sidebar inside an antd `<Drawer>` with `placement="left"` on viewports < 1024px. The Drawer SHALL be controlled by state toggled via the Header ☰ button.

#### Scenario: Mobile sidebar hidden by default
- **WHEN** a PageLayout page loads on a viewport < 1024px
- **THEN** the Sidebar SHALL NOT be visible; main content SHALL occupy full width

#### Scenario: Mobile sidebar opens as Drawer
- **WHEN** user taps the ☰ icon in the Header
- **THEN** an antd Drawer SHALL slide in from the left containing the Sidebar navigation items with a semi-transparent backdrop overlay

#### Scenario: Mobile sidebar closes on navigation
- **WHEN** user clicks a navigation link inside the Drawer
- **THEN** the Drawer SHALL close automatically

#### Scenario: Mobile sidebar closes on backdrop click
- **WHEN** user clicks the backdrop overlay
- **THEN** the Drawer SHALL close

#### Scenario: Desktop sidebar unchanged
- **WHEN** viewport width >= 1024px
- **THEN** the Sidebar SHALL render as a persistent `<aside>` element with collapsible behavior (current implementation preserved)

---

### Requirement: Sidebar component works in both contexts
The Sidebar component SHALL render its navigation content inside either an `<aside>` wrapper (desktop) or as children of an antd Drawer (mobile), without duplicating navigation logic.

#### Scenario: Desktop Sidebar renders as aside
- **WHEN** Sidebar is rendered in desktop mode
- **THEN** it SHALL be wrapped in `<aside>` with sticky positioning, border, and collapse toggle button

#### Scenario: Mobile Sidebar renders without aside wrapper
- **WHEN** Sidebar is rendered inside a Drawer
- **THEN** it SHALL render navigation content without the `<aside>` wrapper, sticky positioning, or collapse toggle (Drawer handles these)

---

### Requirement: Create Request page Steps responsive layout
The Create Request page SHALL switch the Steps panel from vertical sidebar layout to horizontal top layout on viewports < 768px (md breakpoint).

#### Scenario: Mobile Steps layout
- **WHEN** viewport width < 768px
- **THEN** the Steps component SHALL render with `direction="horizontal"` above the content area, with the layout switching from `flex-row` to `flex-col`

#### Scenario: Desktop Steps layout
- **WHEN** viewport width >= 768px
- **THEN** the Steps component SHALL render with `direction="vertical"` in a sticky sidebar panel (`w-56`) to the left of content, as currently implemented

#### Scenario: Mobile padding reduction
- **WHEN** viewport width < 768px
- **THEN** the page outer padding SHALL reduce from `px-8` to `px-4`

---

### Requirement: StandaloneLayout responsive header
The StandaloneLayout header SHALL condense on small viewports.

#### Scenario: Mobile standalone header
- **WHEN** viewport width < 640px (sm breakpoint)
- **THEN** the "Back to Home" text SHALL be hidden, showing only the ArrowLeft icon; the "Enterprise Architecture Management" title SHALL be hidden

#### Scenario: Desktop standalone header
- **WHEN** viewport width >= 640px
- **THEN** all header elements SHALL display as currently implemented
