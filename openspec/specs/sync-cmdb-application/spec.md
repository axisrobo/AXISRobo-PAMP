# OpenSpec Change Proposal: CMDB Application Synchronization

## 1. Objective
Implement an automated daily synchronization process to fetch application configuration items (CIs) from the external CMDB API and persist them into the `eam.cmdb_application` table. This ensures the AxisArch system has up-to-date information regarding application ownership, status, and classification.

## 2. Target Schema
The data will be synchronized into the following PostgreSQL table:

```sql
-- eam.cmdb_application definition
CREATE TABLE eam.cmdb_application (
    _id varchar NULL,
    short_description varchar NULL,
    u_service_area varchar NULL,
    u_status varchar NULL,
    app_full_name varchar NULL,
    owned_by varchar NULL,
    "name" varchar NULL,
    app_it_owner varchar NULL,
    app_owner_tower varchar NULL,
    app_owner_domain varchar NULL,
    app_id varchar NULL, -- Unique Identifier (e.g., patch_level)
    patch_level varchar NULL,
    portfolio_mgt varchar NULL,
    app_classification varchar NULL,
    update_at timestamp DEFAULT now() NULL,
    app_ownership varchar NULL,
    app_solution_type varchar NULL,
    app_operation_owner varchar NULL,
    app_operation_owner_tower varchar NULL,
    app_operation_owner_domain varchar NULL,
    decommissioned_at timestamp NULL,
    app_dt_owner varchar NULL,
    CONSTRAINT cmdb_application_unique UNIQUE (app_id)
);
```

## 3. Data Mapping

| CMDB API Field | Target DB Column | Logic/Transformation |
| :--- | :--- | :--- |
| `_id` | `_id` | Direct mapping |
| `short_description` | `short_description` | Direct mapping |
| `u_service_area` | `u_service_area` | Direct mapping |
| `u_status` | `u_status` | Direct mapping |
| `app_full_name` | `app_full_name` | Direct mapping |
| `owned_by` | `owned_by` | Direct mapping (IT Owner ID) |
| `name` | `name` | Direct mapping (Short Name) |
| `owned_by` | `app_it_owner` | Mapping `owned_by` to `app_it_owner` |
| `appowner_orgname` | `app_owner_tower` | Mapping tower info |
| `functionOwnerL4OrgName`| `app_owner_domain` | Mapping domain info |
| `patch_level` | `app_id` | **Primary Key** for UPSERT logic |
| `patch_level` | `patch_level` | Redundant storage for convenience |
| `appPortfolioMgt` | `portfolio_mgt` | Direct mapping |
| `appClassification` | `app_classification`| Join array to string (e.g., `,`) |
| `u_budget_owner` | `app_ownership` | Mapping budget owner to ownership |
| `applicationSolutionType`| `app_solution_type` | Direct mapping |
| `app_operation_owner` | `app_operation_owner` | Direct mapping |
| `AppOperationOwnerTower`| `app_operation_owner_tower`| Direct mapping |
| `AppOperationOwnerDomain`| `app_operation_owner_domain`| Direct mapping |
| `appDtOwner` | `app_dt_owner` | Direct mapping |
| N/A | `update_at` | Set to `now()` on every sync |
| N/A | `decommissioned_at` | Set to `now()` if `u_status` becomes 'Decommissioned' and previously wasn't |

## 4. Technical Implementation

### 4.1 Integration Logic
1. **Authentication**: Use the stored CMDB API credentials to obtain an authorization token.
2. **Extraction**: 
   - Call `POST <configured-endpoint>/cmdb/api/v2/ci-query/search/1`.
   - Implement pagination logic (loop through `page` until all `totalElements` are processed).
   - Filter: Fetch all relevant applications (potentially filtering by `u_status` if requested, otherwise full sync).
3. **Transformation**:
   - Clean strings and handle nulls.
   - Convert `appClassification` array to a comma-separated string.
4. **Loading (UPSERT)**:
   - Use `INSERT INTO eam.cmdb_application (...) VALUES (...) ON CONFLICT (app_id) DO UPDATE SET ...`.
   - Update `update_at` timestamp.

### 4.2 Schedule
- **Frequency**: Daily.
- **Timing**: 02:00 AM CST (to minimize impact on production systems).

### 4.3 Error Handling & Monitoring
- Log sync start, end, and record counts.
- Catch and alert on API timeouts or authentication failures.
- Record any rows that fail validation in a separate error log.

## 5. Security
- CMDB API Token must be stored securely in the environment configuration or secret manager.
- Database access limited to the sync service account with `INSERT/UPDATE` permissions on `eam.cmdb_application`.

## 6. Success Criteria
- Daily automated execution without manual intervention.
- `eam.cmdb_application` reflects the current state of CMDB within 24 hours.
- No duplicate records for the same `patch_level`.
