## ADDED Requirements

> Merged from: `create-request-flow`, `request-step-persistence`, `standalone-request-detail`, `diagram-upload-ui`, `request-attachment-upload`

---

## Part 1: Create EA Request Flow

### Overview
3-step vertical wizard for creating an EA Review Request at `/ea-review/request/create`. Uses standalone layout (no sidebar).

- Left side: antd `Steps` with `direction="vertical"`, sticky
- Right side: Step content area (Card-based forms)

### Step 01: Create an EA Review request for a project

#### Section: Select a MSPO project or create project

Two modes controlled by `isCreateNew` state:

**Mode 1: Select from MSPO** — ProjectID dropdown with search, auto-fills Project Name / PM / DT Lead / IT Lead / Requestor (all read-only).

**Mode 2: Create New Project** — Manual input for Project Name, `ResourceAutoComplete` for PM / DT Lead / IT Lead.

`ResourceAutoComplete` component: built on antd `AutoComplete` + `react-query`, calls `GET /api/resources/search?q=xxx` when input ≥ 2 chars.

#### Section: Describe review scope

| Field | Control | Required |
|-------|---------|----------|
| Review Scope | `Radio.Group` ("All" / "Part of Project") | Yes |
| WS Name / Phase Name | `Input` | Yes (if Part of Project) |
| Request Description | `TextArea` | No |

### Step 02: Provide Architecture Design

- Organization radio: "I am from DT/IT" → Confluence page input; "Other org" → file upload
- Application Architecture Diagram: Upload cards + App Arch Type radio + AI Score
- Technical Architecture Diagram: Upload cards + AI Score
- Submit EA review task in MSPO: read-only instructions + "Go to MSPO" link

### Step 03: EA Review (post-submission)
After submission, the wizard page SHALL remain on the same page (no redirect). The page shows the EA Review Process progress section above the step content.

---

## Part 2: Step Persistence

### Requirement: Step 01 creates Draft request on save
The system SHALL call `POST /api/ea-requests` on first "Save & Next Step", or `PUT /api/ea-requests/{id}` on subsequent saves. URL updates to `?id=<requestId>`.

### Requirement: Restore state from URL on page load
If URL contains `?id=<requestId>`, the system SHALL fetch `GET /api/ea-requests/{id}` and restore all form fields and advance to the appropriate step. The GET endpoint SHALL support both UUID and `request_id` lookup (`WHERE r.request_id = :rid OR r.id::text = :rid`).

### Requirement: Step navigation preserves data
Clicking step indicators SHALL navigate between completed steps without losing data.

---

## Part 3: Standalone Request Detail

### Requirement: Standalone request detail route
`/request/[id]` SHALL display the request detail using `HomeLayout` (Header + Footer, no sidebar), using shared `RequestDetailView` component.

### Requirement: Shared RequestDetailView component
The detail UI SHALL be a shared component reused by both `/request/[id]` (standalone) and `/ea-review/request/[id]` (managed).

### Requirement: Header tab highlighting
The "I'm Requester" tab SHALL be highlighted when on `/request/*` paths.

### Requirement: HomeLayout authentication gate
`HomeLayout` SHALL be wrapped with `LoginGate` for authentication.

---

## Part 4: Diagram Upload UI

### Requirement: Diagram upload card component
Each uploaded diagram SHALL show: image thumbnail, file name, App Arch Type radio (for Application section), AI Evaluation Score, delete button.

An empty "+" card SHALL always appear at the end for adding more.

### Requirement: Upload triggers immediate AI check
After upload, the system SHALL automatically call the AI check API. Loading indicator shown during check.

### Requirement: Multiple uploads per section
Each section (Application / Technical Architecture) SHALL support multiple image uploads with flex-wrap layout.

### Requirement: Per-card App Arch Type
For Application section, each card SHALL have its own App Arch Type radio (`New_App` / `E2E_Solution`, default `E2E_Solution`).

### Requirement: Delete uploaded diagram
Clicking delete SHALL call `DELETE /api/ea-requests/attachments/{id}` and remove the card.

---

## Part 5: Attachment Upload API

### Requirement: Upload attachment file
`POST /api/ea-requests/attachments/upload` SHALL accept multipart/form-data with `file`, `requestId`, `bizType` (`App_Arch` | `Tech_Arch` | `Proj_Intro`), optional `appArchType`.

File stored to S3 via `s3_storage.upload_file()` with key `<S3_PREFIX>/<sequence>-<YYYYMMDDHHmmssSSS>.<ext>`. Record inserted into `eam_request_attachment`. Returns `{ attachmentName, attachmentUuid, fileName }`.

File size limit: 10MB.

### Requirement: Delete attachment
`DELETE /api/ea-requests/attachments/{id}` SHALL delete from S3 and DB, including associated `eam_arch_ai_check` records.

### Requirement: Download attachment file
`GET /api/ea-requests/attachments/{id}/file` SHALL serve the file from S3 with appropriate Content-Type.

### Requirement: AI architecture check endpoint
`POST /api/ea-requests/ai-check` SHALL forward to `AI_CHECK_URL` third-party service and store result in `eam_arch_ai_check`. Returns 503 when not configured.

---

## Part 6: EA Review Process Progress

### Requirement: Progress section above step content
When viewing a submitted request (`?id=` with status ≠ Draft), the wizard page SHALL display an "EA Review Process" collapsible section above the step content area.

### Requirement: Steps progress bar
The progress section SHALL show an antd `Steps` component (horizontal) with four steps: **Draft → Submitted → In Progress → Completed**. The current step highlights based on request status.

### Requirement: Status alert message
Below the steps, an antd `Alert` SHALL display a status-specific message (e.g. "已提交 EA Review 审核申请，请等待审核结果" for Submitted). Alert type maps: Draft/Submitted → `info`, In Progress → `warning`, Completed → `success`.

### Requirement: Process log table
Below the alert, a `DataTable` SHALL display process logs from `GET /api/ea-requests/process-logs?requestId={requestId}`. Columns: Step, Operator, Status, Remark, Time.

### Requirement: Created log backfill
When a status-change is made via `PUT /api/ea-requests/{id}`, the handler SHALL check if a "Created" process log exists for the request. If missing, it SHALL insert one using the request's `create_at` and `create_by` fields before recording the new status change.

### Requirement: Banner with request name
When viewing a submitted request, a banner SHALL display `Request Name : {request_id}-{project_id}-{project_name}` with a Home icon linking back to the homepage.

---

## Part 7: Email Notification on Status Change

### Requirement: Send email on request submission
When a request status changes to "Submitted" via `PUT /api/ea-requests/{id}`, the system SHALL send an email notification via BCT Message API.

### Requirement: Email BCT template
- **appId**: `ProjectManagement`
- **templateCode**: `EAReviewRequest`
- **templateTag**: `EAReviewRequestNotify`

### Requirement: Email payload variables
The payload SHALL include the following variables matching the BCT template:

| Variable | Description | Example |
|----------|-------------|---------|
| `requester` | Submitter display name | `"John Doe"` |
| `requestId` | Request ID string | `"EA250019"` |
| `projectId` | Project ID string | `"10011"` |
| `projectName` | Project name | `"My Project"` |
| `reviewScope` | Review scope | `"All"` |
| `wsPhaseName` | WS Phase Name | `""` |
| `statusChangedAt` | ISO timestamp of change | `"2025-01-15T10:00:00"` |
| `status` | New status | `"Submitted"` |
| `assignReviewer` | Assigned reviewer | `""` |
| `reviewResult` | Review result | `""` |
| `statusRemark` | Status change remark | `""` |
| `requestName` | Clickable link text | `"EA250019 - 10011 - ProjectName"` |
| `linkUrl` | Full URL to request | `"<configured-endpoint>/ea-review/request/{uuid}"` |
| `notifyContentVar` | Notification body text | `"Thank you for submitting..."` |

### Requirement: Email link uses UUID
The `linkUrl` SHALL use the request's UUID (not `request_id`) to match the frontend route: `{EAM_SITE_URL}/ea-review/request/{uuid}`.

### Requirement: Email recipients and CC
- **To**: EA team recipients from `eam.dict_option` where `category_id = '2400'`
- **CC**: `<configured-email>` + PM email + DT Lead email (if available)

### Requirement: Email subject
Subject format: `EA Review Request - {request_id} - {project_name}`
