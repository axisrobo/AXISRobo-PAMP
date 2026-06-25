## ADDED Requirements

> Merged from: `home-dashboard-interaction`, `architecture-ai-check`

---

## Part 1: Dashboard Interaction

### Requirement: Stats cards default to collapsed
The homepage stats cards (My Projects, My Requests, My Actions, Request Queue) SHALL default to collapsed with no data table visible on page load.

#### Scenario: Mobile stats card grid
- **WHEN** viewport width < 768px (md breakpoint)
- **THEN** the stats cards SHALL display in a 2-column grid with reduced padding

#### Scenario: Desktop stats card grid
- **WHEN** viewport width >= 768px
- **THEN** the stats cards SHALL display in a 4-column grid as currently implemented

### Requirement: Card click toggles data table
Clicking a stats card SHALL toggle the corresponding data table. Only one panel active at a time, with ring highlight on active card.

### Requirement: Lazy data loading
List data SHALL NOT be fetched until the corresponding panel is activated. On page load only `/dashboard/home-stats` is called.

### Requirement: Home stats shows user-specific counts
`/dashboard/home-stats` SHALL return counts filtered to the authenticated user:
- `myProjects`: projects where user is PM, DT Lead, or IT Lead
- `myRequests`: requests created by user (excluding Deleted)
- `myActions`: actions assigned to user
- `requestQueue`: all Submitted requests (global)

### Requirement: My Projects endpoint
`/dashboard/my-projects` SHALL return projects where user is PM, DT Lead, or IT Lead. Supports pagination.

### Requirement: My Requests endpoint
`/dashboard/my-requests` SHALL return EA requests created by user, excluding deleted.

### Requirement: My Requests table Request ID link
Clicking a Request ID in the My Requests table SHALL navigate to `/ea-review/request/create?id={uuid}` (the wizard page with the request loaded), not to a standalone detail page.

### Requirement: My Actions endpoint
`/dashboard/my-actions` SHALL return actions assigned to user, with status breakdown stats.

### Requirement: Request Queue is global
`/dashboard/request-queue` SHALL return all "Submitted" requests regardless of user.

### Requirement: Keycloak init timeout protection
Keycloak init SHALL have a 10-second timeout. On timeout: reject, `authenticated = false`, reset `initPromise`.

### Requirement: Auth dev mode bypass
When `NEXT_PUBLIC_AUTH_DISABLED=true`, skip Keycloak and fetch user info from `/api/auth/me`.

---

## Part 2: AI Architecture Check

### Requirement: AI architecture check endpoint
`POST /api/ea-requests/ai-check` SHALL accept `{ requestId, bizType, language, attachmentName, attachmentUuid }` and forward to `AI_CHECK_URL`.

Result stored in `eam_arch_ai_check` with `attachment_uuid`, `result` (JSON), `request` (JSON).

Returns `{ score, result, attachmentUuid }`.

### Requirement: AI check configuration
`AI_CHECK_URL` from environment (default: empty). Returns 503 when not configured.

---

## Part 3: Responsive Layout

> Merged from: `responsive-layout`

### Requirement: Homepage Hero banner responsive sizing
The homepage Hero banner section SHALL scale its padding and typography for mobile viewports.

#### Scenario: Mobile Hero banner
- **WHEN** viewport width < 640px (sm breakpoint)
- **THEN** the Hero section SHALL use `py-8` vertical padding (instead of `py-16`), `text-2xl` heading (instead of `text-4xl`), and `text-base` subtitle (instead of `text-lg`)

#### Scenario: Desktop Hero banner
- **WHEN** viewport width >= 640px
- **THEN** the Hero section SHALL render with current sizing (py-16, text-4xl, text-lg)

### Requirement: Homepage content responsive padding
The homepage content sections (stats cards, data tables, recommend links) SHALL use responsive horizontal padding.

#### Scenario: Mobile content padding
- **WHEN** viewport width < 640px
- **THEN** content sections SHALL use `px-4` horizontal padding

#### Scenario: Desktop content padding
- **WHEN** viewport width >= 640px
- **THEN** content sections SHALL use `px-6` horizontal padding as currently implemented
