## ADDED Requirements

### Requirement: Certification data model
The system SHALL store certifications in `eam.certification` with the following fields:

| DB Column | API Field | Type | Description |
|-----------|-----------|------|-------------|
| `id` | `id` | serial PK | Auto-increment ID |
| `simple_id` | `certId` | varchar | Certificate No. (e.g. `CLSA-a1b2c3d4e5f67890`) |
| `exam_name` | `name` | varchar | Exam name |
| `certificate_type` | `type` | varchar | `CLSA (Certified Solution Architect)` or `CLTA (Certified Technical Architect)` |
| `itcode` | `itCode` | varchar | Owner IT code |
| `user_name` | `ownerName` | varchar | Owner full name |
| `issue_date` | `issuedDate` | date | Certificate issue date |
| `expiration_date` | `expiryDate` | date | Certificate expiration date |
| `duration` | `duration` | numeric | Duration in months (12, 24, or 36) |
| `comment` | `comment` | text | Optional comment |
| `create_by` | — | varchar | Creator IT code |
| `create_at` | — | timestamp | Creation timestamp |
| `update_by` | — | varchar | Last updater IT code |
| `update_at` | — | timestamp | Last update timestamp |

### Requirement: Certificate No. auto-generation
When creating a certification (single or import), the system SHALL auto-generate a `simple_id` in the format `{PREFIX}-{16_hex_chars}`.

The prefix SHALL be extracted from the certificate type abbreviation:
- `CLSA (...)` → prefix `CLSA`
- `CLTA (...)` → prefix `CLTA`
- Fallback → prefix `CERT`

The suffix SHALL be 16 random hexadecimal characters generated via `secrets.token_hex(8)`.

#### Scenario: CLSA certificate
- **GIVEN** certificate type is `CLSA (Certified Solution Architect)`
- **THEN** Certificate No. is generated as `CLSA-<16 hex chars>` (e.g. `CLSA-a1b2c3d4e5f67890`)

### Requirement: Computed status field
The API response SHALL include a computed `status` field:
- `"Valid"` — when `expiration_date >= NOW()`
- `"Expired"` — when `expiration_date < NOW()`
- `null` — when `expiration_date` is null

---

## CRUD Endpoints

### Requirement: List certifications
`GET /api/certifications` (requires `certification:read` permission) SHALL return paginated, sortable, filterable certification data.

Supported filters (query params):

| Param | Filter | Match |
|-------|--------|-------|
| `name` | `exam_name` | ILIKE (partial) |
| `type` | `certificate_type` | multi-value exact |
| `itCode` | `itcode` | ILIKE (partial) |
| `certId` | `simple_id` | ILIKE (partial) |
| `status` | computed | `Valid` → `expiration_date >= CURRENT_DATE`; `Expired` → `< CURRENT_DATE` |

Sortable fields: `certId`, `name`, `type`, `itCode`, `ownerName`, `issuedDate`, `expiryDate`, `duration`.

### Requirement: Get single certification
`GET /api/certifications/{cert_id}` (requires `certification:read`) SHALL return a single certification by ID.

Returns 404 if not found.

### Requirement: Create certification
`POST /api/certifications` (requires `certification:write`) SHALL create a new certification.

The Certificate No. SHALL be auto-generated (not provided by the client).

Date fields (`issuedDate`, `expiryDate`) SHALL be parsed via the shared `parse_date()` helper.

An audit log entry SHALL be recorded with action `create`.

### Requirement: Update certification
`PUT /api/certifications/{cert_id}` (requires `certification:write`) SHALL update an existing certification.

Only provided fields SHALL be updated (partial update). The `update_by` and `update_at` fields SHALL be set automatically.

An audit log entry SHALL be recorded with action `update`.

### Requirement: Delete certification
`DELETE /api/certifications/{cert_id}` (requires `certification:write`) SHALL delete a certification.

Returns 404 if not found. An audit log entry SHALL be recorded with action `delete`.

---

## Certificate Rendering

### Requirement: Certificate image preview
`GET /api/certifications/{cert_id}/image` (requires `certification:read`) SHALL render and return the certificate as a PNG image using `cert_image.generate_cert_image()`.

Content-Disposition SHALL be `inline` for browser preview.

### Requirement: Certificate PDF download
`GET /api/certifications/{cert_id}/pdf` (requires `certification:read`) SHALL render and return the certificate as a PDF using `cert_image.generate_cert_pdf()`.

Content-Disposition SHALL be `attachment` for download.

---

## Import Feature

### Requirement: Template download
`GET /api/certifications/template/download` (requires `certification:read`) SHALL return an xlsx template with:
- Header row with column names (blue fill, white bold text)
- Instruction row (italic gray text)
- Data validation: Certificate Type dropdown (`CLSA(...)`, `CLTA(...)`), Duration dropdown (`12`, `24`, `36`)
- Max 5000 data rows supported

Columns: Exam Name*, IT Code*, User Name*, Certificate Type*, Issue Date*, Duration(Months)*, Expiration Date, Comment.

### Requirement: Import validation
`POST /api/certifications/import/validate` (requires `certification:write`) SHALL accept an xlsx file upload and return a preview of parsed rows with validation results.

Validation rules:
- Required fields: Exam Name, IT Code, User Name, Certificate Type, Issue Date, Duration
- Certificate Type must be one of the two allowed values
- Duration must be 12, 24, or 36
- Issue Date must be a valid date
- Duplicate detection: same `itcode + exam_name + certificate_type + issue_date + duration`
- If Expiration Date is empty, auto-calculate from Issue Date + Duration months

Each row SHALL have a `result` field: `"OK"` or `"Warning"` with a `warnings` array.

### Requirement: Import confirmation
`POST /api/certifications/import/confirm` (requires `certification:write`) SHALL insert validated rows into the database.

Each row gets an auto-generated Certificate No. The response SHALL include per-row results (`"Successfully imported"` or `"Failed: <reason>"`), plus summary counts (`total`, `success`, `failed`).

An audit log entry SHALL be recorded with action `import`.

---

## Export Feature

### Requirement: Export certifications
`POST /api/certifications/export` (requires `certification:read`) SHALL export certifications as xlsx.

Request body accepts:
- `{ ids: ["id1", "id2", ...] }` — export selected rows
- `{ filters: { name, type, itCode, certId, status } }` — export filtered results
- `{}` — export all

The xlsx SHALL have styled headers (blue fill, white bold text, borders) with columns: Certificate No., Exam Name, IT Code, User Name, Certificate Type, Issue Date, Duration(Months), Expiration Date, Status.

---

## Email Notification

### Requirement: Certification expiration notification
`POST /api/certifications/send-expiration-notification` (requires `EA_ADMIN` role) SHALL send a digest email listing certifications that are expired or expiring within 30 days.

The endpoint SHALL:
1. Query `eam.certification` where `expiration_date <= CURRENT_DATE + 30 days`
2. Fetch EA team recipients from `eam.dict_option` where `category_id = '2400'`
3. Send email via shared `send_email()` service with:
   - **Subject**: `AxisArch – Certification Expiration Reminder [<YYYY-MM-DD>]`
   - **Template code**: `Certifications`
   - **Template tag**: `CertExpiration`
   - **Payload**: `{ certifications: [{ simple_id, exam_name, certificate_type, itcode, user_name, issue_date, expiration_date, duration, status }] }`

`Decimal` values in the `duration` field SHALL be converted to `int` before JSON serialization.

#### Scenario: Expiring certifications found
- **WHEN** admin triggers notification and 9 certifications are expired or expiring
- **THEN** one email is sent to all EA team members
- **THEN** response returns `{ message: "...", count: 9, emailResult: {...} }`

#### Scenario: No expiring certifications
- **WHEN** no certifications are expired or expiring within 30 days
- **THEN** no email is sent
- **THEN** response returns `{ message: "No expiring or expired certifications found", count: 0 }`

---

## Frontend — Certification Page

### Requirement: Certification list page
The Certification page (`/certification`) SHALL display a DataTable with columns:
Certificate No. (pinned left, clickable link → view mode), Exam Name, IT Code, User Name, Certificate Type, Issue Date, Duration(Months), Expiration Date, Status (color-coded: green=Valid, red=Expired), Operation (pinned right).

### Requirement: Search form
The page SHALL provide a SearchForm with filters: Certificate No., Exam Name, Certificate Type (select), IT Code, Status (Valid/Expired select).

### Requirement: Action buttons
The page SHALL display action buttons: **New**, **Import**, **Export**, **Email**.

- **New** — opens create drawer
- **Import** — opens 3-step import wizard modal
- **Export** — exports selected rows (with count badge) or all filtered rows
- **Email** — sends expiration notification with confirmation modal

### Requirement: View/Edit drawer
Clicking Certificate No. SHALL open the drawer in **view-only mode** (all fields disabled). The drawer footer shows an "Edit" button to switch to edit mode.

The drawer (antd `Drawer` with `size="large"`, `destroyOnHidden`) SHALL contain a form with fields: Certificate No. (disabled, edit only), Exam Name, IT Code (with `ResourceAutoComplete`), User Name (auto-filled), Certificate Type (select), Issue Date + Duration + Expiration Date (grid layout, auto-compute expiry), Status (disabled), Comment.

### Requirement: Auto-compute expiration date
When Issue Date or Duration changes, Expiration Date SHALL be auto-computed as `issueDate + duration months`.

### Requirement: Operation column
Each row SHALL have 4 icon buttons: Preview (eye), Download (arrow-down), Edit (pencil), Delete (trash, with confirmation modal).

### Requirement: Row selection for export
The DataTable SHALL support checkbox row selection. The Export button SHALL show the selected count (e.g. `Export (3)`). When rows are selected, only those rows are exported; otherwise all filtered rows are exported.

### Requirement: Import wizard
The import modal SHALL use antd `Steps` with 3 steps:
1. **Select a file** — template download link, file upload (.xls/.xlsx), validate button
2. **Validate the data** — preview table with result/warning icons, result log export, confirm import button
3. **Import Result** — result table with success/fail counts, result log export

### Requirement: Email button
The Email button SHALL show a confirmation modal: "This will send an email to all EA team members listing certifications that are expired or expiring within 30 days. Continue?"

On confirm, it calls `POST /api/certifications/send-expiration-notification`. The button shows "Sending..." state while loading. Success/error/info messages are shown via antd `message`.

---

## Implementation Files

| File | Role |
|------|------|
| `backend/app/routers/config_data/certifications.py` | All certification endpoints |
| `backend/app/utils/cert_image.py` | Certificate image/PDF rendering |
| `backend/app/utils/date_helpers.py` | Shared date parsing (used for date fields) |
| `backend/app/utils/email_service.py` | Shared email service (used for notifications) |
| `frontend/src/app/certification/page.tsx` | Full certification page UI |
| `frontend/src/components/ui/DataTable.tsx` | Shared table with `rowSelection` support |
| `frontend/src/components/ui/ResourceAutoComplete.tsx` | IT Code autocomplete component |
