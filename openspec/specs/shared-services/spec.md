## ADDED Requirements

> Merged from: `api-response-envelope`, `s3-file-storage`, `email-notification-service`, `date-handling`

---

## Part 1: API Response Envelope

### Requirement: Unified JSON response envelope
All JSON API endpoints SHALL return: `{ code, message, data, timestamp }`.

- `code`: integer (200 for success, HTTP status code for errors)
- `message`: string (user-friendly)
- `data`: any JSON value or null
- `timestamp`: integer epoch milliseconds

### Requirement: Standard HTTP status codes
- 400: validation errors
- 401: unauthenticated
- 403: insufficient permission
- 404: resource not found
- 500: unhandled server errors

### Requirement: Business failure signaling
Technically successful but business-rule-failed requests SHALL return HTTP 200 with non-200 `code`.

### Requirement: Non-JSON responses not wrapped
File downloads, CSV exports, etc. SHALL NOT be wrapped in the JSON envelope.

---

## Part 2: S3-Compatible Object Storage

### Requirement: S3 storage service
`backend/app/utils/s3_storage.py` SHALL provide `upload_file()`, `download_file()`, `delete_file()`, `file_exists()`, `make_key()` via `boto3`.

Path-style addressing (`s3.addressing_style = "path"`) and S3 v2 signature (`signature_version = "s3"`) for S3-compatible object storage.

### Requirement: S3 configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `S3_ENDPOINT` | `<configured-endpoint>` | S3-compatible endpoint |
| `S3_REGION` | `us-east-1` | AWS region |
| `S3_ACCESS_KEY` | (configured) | Access key ID |
| `S3_SECRET_KEY` | (configured) | Secret access key |
| `S3_BUCKET` | `<your-bucket>` | Bucket name |
| `S3_PREFIX` | `pm/eam/app` | Object key prefix |

### Requirement: Upload explicitly sets ContentLength
`upload_file()` SHALL set `ContentLength` to avoid `Transfer-Encoding: chunked` (unsupported by target OSS).

### Requirement: Download raises FileNotFoundError
`download_file()` SHALL raise `FileNotFoundError` when key does not exist.

### Requirement: Delete is idempotent
`delete_file()` SHALL NOT raise error if key does not exist.

### Requirement: Key construction
`make_key(relative_path)` SHALL prepend `S3_PREFIX` to produce the full key.

---

## Part 3: Email Notification Service

### Requirement: Shared email sending service
`backend/app/utils/email_service.py` SHALL provide `send_email()` via the BCT Message API, authenticated with BCT OIDC tokens.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | `str` | Yes | Semicolon-separated recipient emails |
| `subject` | `str` | Yes | Email subject |
| `payload` | `dict` | Yes | Template data (serialized as JSON string in request body) |
| `template_code` | `str` | Yes | Template code identifier |
| `template_tag` | `str` | Yes | Template tag |
| `cc` | `str` | No | Semicolon-separated CC emails |
| `app_id` | `str` | No | Application identifier (default: `BCT_APP_CODE`) |

### Requirement: BCT OIDC token acquisition
The email service SHALL obtain a short-lived access token from BCT OIDC before sending:
- **Endpoint**: `POST {BCT_TOKEN_URL}/{BCT_APP_CODE}`
- **Header**: `sdk-private-key: <BCT_SDK_KEY>` (Base64-encoded PKCS8 RSA private key)
- **Response**: `{ "success": true, "data": { "token": "..." } }`

### Requirement: Token caching
The service SHALL cache the BCT access token in-process and reuse it until 60 seconds before its JWT `exp` claim. If no `exp` claim is present, default cache TTL is 1 hour.

### Requirement: BCT Message API call
Emails SHALL be sent via:
- **Endpoint**: `POST {BCT_MS_URL}/bct-message/api/v1.0/email/send`
- **Headers**: `sdk-access-token: <token>`, `sdk-app-code: <app_id>`, `Content-Type: application/json`
- **Body**: `{ to, payload (JSON string), subject, appId, templateCode, templateTag, cc? }`

### Requirement: Email service configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `BCT_MS_URL` | `<configured-endpoint>` | BCT Message microservice base URL |
| `BCT_TOKEN_URL` | `<configured-endpoint>` | BCT OIDC token endpoint (without appCode) |
| `BCT_APP_CODE` | `ProjectManagement` | BCT application code |
| `BCT_SDK_KEY` | `""` (empty) | Base64-encoded PKCS8 RSA private key |
| `EAM_SITE_URL` | `<configured-endpoint>` | Production site URL for email links |
| `EMAIL_FROM` | `noreply@axisarch.local` | Sender email |
| `EMAIL_DOMAIN` | `<configured-domain>` | Itcode → email suffix |

### Requirement: Graceful degradation
When `BCT_SDK_KEY` is empty, return `{ status: "skipped" }` without HTTP call.

### Requirement: Error handling
HTTP errors return `{ status: "error", message: "HTTP <code>: <body>" }`. Network errors return `{ status: "error", message: "<detail>" }`. Timeout: 30 seconds for email send, 15 seconds for token acquisition.

### Requirement: EA team recipients
Email addresses read from `eam.dict_option` where `category_id = '2400'`, `description` field.

### Requirement: Action status notification endpoint
`POST /api/actions/send-status-notification` (EA_ADMIN) — digest email of Action status changes in last 24h. Subject: `AxisArch – Action Status Change Collection[<date>]`, template: `Actions` / `Action`.

### Requirement: Action expiration notification endpoint
`POST /api/actions/send-expiration-notification` (EA_ADMIN) — per-assignee emails for actions nearing due date (`due_date <= NOW()+1 day`, `notification_times < 3`). CC to EA team. Increments `notification_times`, logs to `eam_actions_email_log`.

### Requirement: Certification expiration notification endpoint
`POST /api/certifications/send-expiration-notification` (EA_ADMIN) — digest email of certs expired or expiring within 30 days. Subject: `AxisArch – Certification Expiration Reminder [<date>]`, template: `Certifications` / `CertExpiration`.

### Requirement: Notification buttons
Actions page: two buttons (status + expiration). Certification page: Email button. All with confirmation modal, `App.useApp()` message feedback.

---

## Part 4: Date Handling

### Requirement: Shared date parsing module
`backend/app/utils/date_helpers.py` SHALL provide `parse_date()`, `parse_datetime()`, `coerce_params()` for converting request body values to native Python types required by asyncpg.

### Requirement: parse_date
`None` → `None`, `date` → as-is, `datetime` → `.date()`, `str` → first 10 chars → `date.fromisoformat()`.

### Requirement: parse_datetime
`None` → `None`, `datetime` → naive (strip tz), `date` → midnight datetime, `str` → parse multiple ISO formats then strip tz. Raises `ValueError` on failure.

### Requirement: coerce_params
Auto-convert string values in a params dict for named `date_fields` and `datetime_fields`.

### Requirement: All routers must use date helpers
Integrated routers: `certifications.py`, `projects.py`, `actions.py`, `schedules.py`, `meetings.py`.

---

## Implementation Files

| File | Role |
|------|------|
| `backend/app/utils/email_service.py` | Email sending service |
| `backend/app/utils/s3_storage.py` | S3 storage service |
| `backend/app/utils/date_helpers.py` | Date/datetime parsing |
| `backend/app/config.py` | All service configuration |
| `backend/app/main.py` | Response envelope middleware |
