## Authorization Requirements

### Requirement: The system SHALL use a hybrid authorization model with baseline roles and scoped business roles
The system SHALL authorize users by combining:
- baseline roles that define platform-wide access
- scoped business roles that grant additional permissions only for explicitly assigned or owned records

The system SHALL support the following roles:
- `EA_Admin`
- `Normal_User`
- `EA_Reviewer`
- `App_Owner`
- `Project_Owner`

The system SHALL classify these roles as follows:
- baseline roles: `EA_Admin`, `Normal_User`
- scoped business roles: `EA_Reviewer`, `App_Owner`, `Project_Owner`

The system SHALL additionally recognize `Request_Owner` as a per-record ownership concept that is evaluated at the record level rather than resolved as a session-wide role. `Request_Owner` is the user whose identifier matches the `requester` field on a given EA Review Request.

The system SHALL evaluate role precedence in the following order:
1. `EA_Admin`
2. scoped business roles
3. `Normal_User`

The system MUST treat scoped business roles as additive permissions on top of `Normal_User`.

#### Scenario: User has only baseline access
- **WHEN** an authenticated user is not resolved as `EA_Admin`, `EA_Reviewer`, `App_Owner`, or `Project_Owner`
- **THEN** the system SHALL treat the user as `Normal_User`

#### Scenario: User has both baseline and scoped roles
- **WHEN** an authenticated user matches one or more scoped business roles
- **THEN** the system SHALL apply `Normal_User` baseline access plus the scoped permissions of those roles

#### Scenario: EA admin overrides scoped restrictions
- **WHEN** an authenticated user is resolved as `EA_Admin`
- **THEN** the system SHALL grant unrestricted access regardless of scoped business role evaluation


### Requirement: The system SHALL define baseline role sources explicitly
The system SHALL derive baseline roles from the following sources:
- `EA_Admin`: sourced from table `eam_bigea_team_members` field `ea_admin_status`
- `Normal_User`: automatically granted to every authenticated user

The system MUST treat every successfully authenticated user as `Normal_User` even if no additional application-specific role is resolved.

The system SHALL allow `EA_Admin` to access and operate on all functions and all data without scope restriction.

The system SHALL restrict `Normal_User` access to only the modules and operations defined in the per-module permission matrix.

The system SHALL allow `Normal_User` to create EA Review Requests.

The system SHALL allow `Normal_User` who is the Request_Owner to update the EA Review Request only when the request is in draft status.

The system SHALL allow `Normal_User` who is the Request_Owner to submit the EA Review Request only when the request is in draft status.

The system SHALL allow `Normal_User` who is the Request_Owner to delete the EA Review Request only when the request is in draft status.

The system SHALL allow `Normal_User` who is the Request_Owner to upload diagrams only when the request is not in completed status.

The system SHALL allow `Normal_User` who is the Request_Owner to upload attachments only when the request is not in completed status.

The system SHALL allow `Normal_User` to add comments on Actions (Action Update Comment).

The system MUST NOT allow `Normal_User` to access Certification, Resources, Reports, or Settings modules unless another role explicitly grants such access.

The system SHALL allow `Normal_User` read-only access to the Meetings module.

The system MUST NOT allow `Normal_User` to approve, assign, close, review, or otherwise modify business data outside the user's own EA Review Requests unless another role explicitly grants such access.

#### Scenario: Authenticated user without elevated role
- **WHEN** a user logs in successfully and is not mapped to `EA_Admin`, `EA_Reviewer`, `App_Owner`, or `Project_Owner`
- **THEN** the system SHALL grant `Normal_User` access limited to the modules and operations defined in the per-module permission matrix

#### Scenario: Normal user updates own request
- **WHEN** a logged-in user updates an EA Review Request where the `requester` field matches the current user and the request is in draft status
- **THEN** the system SHALL allow the operation

#### Scenario: Normal user submits own draft request
- **WHEN** a logged-in user submits an EA Review Request where the `requester` field matches the current user and the request is in draft status
- **THEN** the system SHALL allow the submit operation

#### Scenario: Normal user submits non-draft request
- **WHEN** a logged-in user attempts to submit an EA Review Request that is not in draft status
- **THEN** the system SHALL reject the request with `403 Forbidden` or a business validation error defined by the API contract

#### Scenario: Normal user deletes own draft request
- **WHEN** a logged-in user deletes an EA Review Request where the `requester` field matches the current user and the request is in draft status
- **THEN** the system SHALL allow the delete operation

#### Scenario: Normal user deletes non-draft request
- **WHEN** a logged-in user attempts to delete an EA Review Request where the `requester` field matches the current user but the request is not in draft status
- **THEN** the system SHALL reject the request with `403 Forbidden` or a business validation error defined by the API contract

#### Scenario: Normal user modifies another user's request
- **WHEN** a logged-in user attempts to update, submit, or delete an EA Review Request where the `requester` field does not match the current user
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Normal user uploads diagram on non-completed request
- **WHEN** a logged-in user who is the Request_Owner uploads a diagram and the request is not in completed status
- **THEN** the system SHALL allow the upload operation

#### Scenario: Normal user uploads diagram on completed request
- **WHEN** a logged-in user who is the Request_Owner attempts to upload a diagram on a request in completed status
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Normal user adds action update comment
- **WHEN** a logged-in user adds a comment on an Action
- **THEN** the system SHALL allow the operation

#### Scenario: Normal user attempts to access restricted module
- **WHEN** a `Normal_User` attempts to access Certification, Resources, Reports, or Settings
- **THEN** the system SHALL reject the request with `403 Forbidden`


### Requirement: The system SHALL define scoped business role sources explicitly
The system SHALL derive scoped business roles from application data.

The system SHALL resolve `EA_Reviewer` from table `eam_bigea_team_members`.

The system SHALL resolve `App_Owner` from:
- table `cmdb_application` field `app_dt_owner`
- table `cmdb_application` field `app_operation_owner`
- table `cmdb_application` field `app_it_owner`
- table `application_member` field `itcode`

The system SHALL resolve `Project_Owner` from:
- table `project` field `pm_itcode`
- table `project` field `dt_lead_itcode`
- table `project` field `it_lead_itcode`

The system SHALL resolve `Request_Owner` per-record from:
- table `eam_request` field `requester`

The system SHALL interpret `application_member.itcode` as the email prefix of the current user.

The system MUST compare `application_member.itcode` with the authenticated user's email prefix or an equivalent normalized login identifier.

The system MUST NOT grant unrestricted access merely because a scoped business role is present.

The system SHALL apply scoped business roles only to records explicitly assigned to or owned by the current user.

#### Scenario: Scoped reviewer role is resolved
- **WHEN** the authenticated user exists in `eam_bigea_team_members`
- **THEN** the system SHALL add `EA_Reviewer` to the user's authorization context

#### Scenario: Scoped app owner role is resolved by application member
- **WHEN** the authenticated user's email prefix matches `application_member.itcode`
- **THEN** the system SHALL add `App_Owner` to the user's authorization context for the corresponding owned application scope

#### Scenario: Scoped app owner role is resolved by application ownership fields
- **WHEN** the authenticated user matches `app_dt_owner`, `app_operation_owner`, or `app_it_owner`
- **THEN** the system SHALL add `App_Owner` to the user's authorization context for the corresponding owned application scope

#### Scenario: Scoped project owner role is resolved
- **WHEN** the authenticated user's identifier matches `pm_itcode`, `dt_lead_itcode`, or `it_lead_itcode` on any project record
- **THEN** the system SHALL add `Project_Owner` to the user's authorization context

#### Scenario: Request owner is evaluated per record
- **WHEN** the authenticated user's identifier matches the `requester` field on a specific EA Review Request
- **THEN** the system SHALL treat the user as the Request_Owner for that specific record only

#### Scenario: Scoped role does not match target data
- **WHEN** the authenticated user has a scoped business role but the target record is not assigned to or owned by that user
- **THEN** the system SHALL not grant additional mutation capability for that record


### Requirement: The system SHALL enforce the per-module permission matrix

The system SHALL enforce the following per-module permission matrix. Each cell defines the allowed operations for the given role on the given module. Empty cells mean the role has no access to that module. Scoped conditions in parentheses indicate record-level ownership or assignment checks that MUST be enforced in addition to the feature-level permission.

#### Projects

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| Create | yes | yes | yes |
| Read | yes | yes | yes |
| Change | yes | yes | yes, Project_Owner only |
| Delete | yes | no | no |
| Add applications | yes | yes | yes, Project_Owner only |

For `Normal_User`, Change and Add applications operations on projects SHALL be restricted to records where the user is the Project_Owner (i.e., the user's identifier matches `pm_itcode`, `dt_lead_itcode`, or `it_lead_itcode` on the target project).

#### Scenario: Project owner updates owned project
- **WHEN** a `Normal_User` who is the Project_Owner attempts to update a project record
- **THEN** the system SHALL allow the update

#### Scenario: Non-owner normal user updates project
- **WHEN** a `Normal_User` who is not the Project_Owner attempts to update a project record
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: EA Reviewer creates project
- **WHEN** an `EA_Reviewer` creates a new project
- **THEN** the system SHALL allow the operation

#### Scenario: EA Reviewer deletes project
- **WHEN** an `EA_Reviewer` attempts to delete a project
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### EA Review — EA Review Request Details

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| Read | yes | yes | yes |
| Return/Accept EA Review Request | yes | no | no |
| Assign reviewer | yes | no | no |
| Add Meeting | yes | yes | no |
| Add Action | yes | yes | no |
| Upload Attachment | yes | yes | yes, Request_Owner only when not in terminal status |
| Delete Attachment | yes | yes | yes, Request_Owner only when not in terminal status |

The EA Review Request Details view is the managed/reviewer view of a specific request.

`EA_Reviewer` SHALL be allowed to upload and delete attachments on any request at any time, regardless of assignment or request status.

`Normal_User` who is the Request_Owner MAY upload and delete attachments on this view only when the request is NOT in a terminal status (Completed, Approved, Approved with Actions, Rejected).

#### Scenario: EA Reviewer adds meeting from request details
- **WHEN** an `EA_Reviewer` adds a meeting from the EA Review Request Details view
- **THEN** the system SHALL allow the operation

#### Scenario: Normal user uploads attachment on own request detail
- **WHEN** a `Normal_User` who is the Request_Owner uploads an attachment from the request details view
- **THEN** the system SHALL allow the operation

#### Scenario: Normal user adds meeting from request details
- **WHEN** a `Normal_User` attempts to add a meeting from the EA Review Request Details view
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### EA Review — I'm Requester

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| Create EA Review Request | yes | yes | yes |
| Read | yes | yes | yes |
| Change EA Review Request | yes | yes | yes, Request_Owner in Draft only |
| Add/Create Meeting | yes | yes | no |
| Add/Create Action | yes | yes | no |
| Upload Diagram | yes | yes | yes, Request_Owner when not in Completed |
| Upload Attachment | yes | yes | yes, Request_Owner when not in Completed |
| Complete EA Review | yes | yes, Assigned_Reviewer only | no |

For `Normal_User`:
- Change is restricted to requests where the user is the Request_Owner AND the request is in Draft status.
- Upload Diagram and Upload Attachment are restricted to requests where the user is the Request_Owner AND the request is NOT in Completed status.

For `EA_Reviewer`:
- Complete EA Review is restricted to requests where the reviewer is the Assigned_Reviewer (i.e., the user's identifier appears in the `assign_reviewer` field).

#### Scenario: Request owner edits draft request
- **WHEN** a `Normal_User` who is the Request_Owner edits a request in Draft status
- **THEN** the system SHALL allow the operation

#### Scenario: Request owner edits non-draft request
- **WHEN** a `Normal_User` who is the Request_Owner attempts to edit a request not in Draft status
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Request owner uploads diagram on in-progress request
- **WHEN** a `Normal_User` who is the Request_Owner uploads a diagram on a request in In Progress status
- **THEN** the system SHALL allow the operation

#### Scenario: Request owner uploads diagram on completed request
- **WHEN** a `Normal_User` who is the Request_Owner attempts to upload a diagram on a request in Completed status
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Assigned reviewer completes review
- **WHEN** an `EA_Reviewer` who is the Assigned_Reviewer completes the EA review
- **THEN** the system SHALL allow the operation

#### Scenario: Unassigned reviewer attempts to complete review
- **WHEN** an `EA_Reviewer` who is NOT the Assigned_Reviewer attempts to complete the EA review
- **THEN** the system SHALL reject the request with `403 Forbidden`

The system SHALL NOT update existing project records when creating or saving an EA Review Request that references an existing project. Only when the user explicitly creates a new project (via the "Create New" option) SHALL a `POST /projects` call be made. Selecting an existing project SHALL only associate the request with that project without modifying the project record.

#### EA Review Process Page — Button Behavior for Non-Draft Requests

When the EA Review Request is NOT in Draft status (e.g., Submitted, In Progress), the frontend SHOULD adjust the request creation/edit page as follows:

- **Step 01**: The "Save & Next Step" button SHALL be replaced with a "Next Step" button that navigates to Step 02 without saving. The "Reset" button SHALL be hidden.
- **Step 02**: The "Confirm to Submit & Next Step" button SHALL be replaced with a "Next Step" button that navigates to Step 03 without submitting. The "Save as Draft" button SHALL be hidden.

#### EA Review — Meetings

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Create | yes | yes | no |
| Read | yes | yes | yes |
| Change | yes | yes | no |
| Delete | yes | no | no |

`Normal_User` SHALL have read-only access to the Meetings module. `Normal_User` SHALL NOT be allowed to create, change, or delete meetings.

`EA_Reviewer` SHALL NOT be allowed to delete meetings.

#### EA Review — Action

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Create | yes | yes | no |
| Read | yes | yes | yes |
| Change | yes | yes | no |
| Delete | yes | no | no |
| Add Action Update Comment | yes | yes | yes |

`Normal_User` SHALL have read access and the ability to add Action Update Comments. `Normal_User` SHALL NOT be allowed to create, change, or delete Actions.

`EA_Reviewer` SHALL NOT be allowed to delete Actions.

#### Scenario: Normal user adds action comment
- **WHEN** a `Normal_User` adds a comment on an Action
- **THEN** the system SHALL allow the operation

#### Scenario: Normal user attempts to create action
- **WHEN** a `Normal_User` attempts to create a new Action
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### EA Review — EA Calendar

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Create | yes | no | no |
| Read | yes | yes | yes |
| Change | yes | no | no |
| Delete | yes | no | no |

The EA Calendar module SHALL be readable by all authenticated roles. Only `EA_Admin` can create, change, or delete calendar entries.

#### Certification

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Create | yes | no access | no access |
| Read | yes | no access | no access |
| Change | yes | no access | no access |
| Delete | yes | no access | no access |

The Certification module SHALL be accessible only to `EA_Admin`.

#### Application Management — Business Capability Mapping

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| Create | yes | yes | yes, App_Owner only |
| Read | yes | yes | yes |
| Change | yes | yes | yes, App_Owner only |
| Delete | yes | no | yes, App_Owner only |

For `Normal_User`, Create, Change, and Delete operations SHALL be restricted to records belonging to applications owned by the user (App_Owner).

`EA_Reviewer` SHALL NOT be allowed to delete BCM records.

#### Scenario: App owner creates BCM mapping for owned application
- **WHEN** a `Normal_User` who is the App_Owner creates a BCM mapping for an application they own
- **THEN** the system SHALL allow the operation

#### Scenario: Non-owner normal user creates BCM mapping
- **WHEN** a `Normal_User` who is not the App_Owner attempts to create a BCM mapping
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: EA Reviewer deletes BCM mapping
- **WHEN** an `EA_Reviewer` attempts to delete a BCM mapping
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Application Management — Business Capability Analysis

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Read | yes | yes | yes |

Business Capability Analysis is read-only for all roles.

#### Application Management — Business Capability Master Data

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Import | yes | no | no |
| Read | yes | yes | yes |

Only `EA_Admin` SHALL be allowed to import Business Capability Master Data. All other roles have read-only access.

#### Application Management — Application Master Data

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Read | yes | yes | yes |

Application Master Data (CMDB) is read-only for all roles.

#### Application Management — Application BC Mapping

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| Create | yes | yes | yes, App_Owner only |
| Read | yes | yes | yes |
| Change | yes | yes | yes, App_Owner only |
| Delete | yes | no | yes, App_Owner only |

Application BC Mapping follows the same permission rules as Business Capability Mapping.

#### Technology Stack — Technology Stack Lifecycle Management

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| Read | yes | yes | yes |
| Change | yes | no | yes, App_Owner only |

`EA_Admin` and `App_Owner` (for owned applications) MAY update lifecycle status. All other roles have read-only access.

#### Scenario: App owner updates lifecycle for owned application
- **WHEN** a `Normal_User` who is the App_Owner updates the lifecycle status of an application they own
- **THEN** the system SHALL allow the operation

#### Scenario: EA Reviewer updates lifecycle
- **WHEN** an `EA_Reviewer` attempts to update lifecycle status
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Technology Stack — Technology Stack Version Master Data

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` + scoped roles |
|-----------|------------|---------------|------------------------------|
| New (Create) | yes | no | yes, App_Owner only |
| Import | yes | no | no |
| Read | yes | yes | yes |
| Change | yes | no | yes, App_Owner only |
| Delete | yes | no | yes, App_Owner only |
| Add Team Member | yes | no | yes, App_Owner only |

For `Normal_User`, Create, Change, Delete, and Add Team Member operations SHALL be restricted to records belonging to applications owned by the user (App_Owner).

Import SHALL be restricted to `EA_Admin` only.

#### Scenario: App owner adds tech stack entry for owned application
- **WHEN** a `Normal_User` who is the App_Owner creates a tech stack entry for an application they own
- **THEN** the system SHALL allow the operation

#### Scenario: EA Reviewer creates tech stack entry
- **WHEN** an `EA_Reviewer` attempts to create a tech stack entry
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Resources

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Read (Resource Pool list page) | yes | no access | no access |

The Resource Pool management list page SHALL be accessible only to `EA_Admin`.

The resource search autocomplete endpoint (`/api/resources/search`) SHALL be accessible to all authenticated users regardless of role, as it is used across the application by shared components (e.g., project creation forms, resource selectors).

#### Reports

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Read | yes | no access | no access |

The Reports module SHALL be accessible only to `EA_Admin`.

#### Dashboard — Home Statistics

The dashboard home statistics endpoint (`/api/dashboard/home-stats`) SHALL be accessible to all authenticated users regardless of role. This endpoint returns personalized data (e.g., the user's project count, request count) for the home page dashboard widget and is NOT part of the admin Reports module.

#### Data Export

The CSV data export endpoint (`/api/export/{entity}`) SHALL be accessible to all authenticated users regardless of role. All roles (`EA_Admin`, `EA_Reviewer`, `Normal_User`, `App_Owner`, `Project_Owner`) SHALL have `export:execute` permission, allowing them to export data for any entity type they can view (ea-requests, projects, meetings, actions, bcm, lead-time, technology-stack).

#### Settings

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Create | yes | no access | no access |
| Read | yes | no access | no access |
| Change | yes | no access | no access |
| Delete | yes | no access | no access |

The Settings module (including Team Members, Dictionary Options, Audit Logs, Email Logs for actions) SHALL be accessible only to `EA_Admin`.

The meeting-specific email logs endpoint (`/api/email-logs/meetings`) SHALL be gated by `meeting:read` permission rather than `settings:read`, since it is accessed from the meeting detail page. Any role with meeting read access (including `Normal_User`) MAY view email logs for a specific meeting.

#### Help

| Operation | `EA_Admin` | `EA_Reviewer` | `Normal_User` |
|-----------|------------|---------------|---------------|
| Create | yes | no | no |
| Read | yes | yes | yes |
| Change | yes | no | no |
| Delete | yes | no | no |

Help content is readable by all roles. Only `EA_Admin` can manage (create, change, delete) help content.


### Requirement: The system SHALL enforce the following baseline feature capability matrix
The system SHALL support the following baseline feature capabilities.

| Role | EA Review (own requests) | EA Review (managed) | Projects | BCM / App BC Mapping | Tech Stack Version Master Data | Tech Stack Lifecycle | Action comments |
|---|---|---|---|---|---|---|---|
| `EA_Admin` | full access | full access | full CRUD | full CRUD | full CRUD + Import | full access | full access |
| `Normal_User` | C/R/U*/D* own requests | R + upload/delete attachment* | C/R/U* | R | R | R | R + add comment |
| `EA_Reviewer` | C/R + review assigned | R + add meeting/action + upload/delete attachment (any request, any time) | C/R/U | C/R/U | R | R | R + add comment |
| `App_Owner` | same as Normal_User | same as Normal_User | C/R/U* | C/R/U*/D* owned | C/R/U*/D* owned + add team member* | R/U* owned | same as Normal_User |
| `Project_Owner` | same as Normal_User | same as Normal_User | C/R/U* owned | same as Normal_User | same as Normal_User | same as Normal_User | same as Normal_User |

`*` indicates record-level scoping applies (ownership, assignment, or status-based restriction). For `Normal_User` attachment management on the managed view, the user must be the Request_Owner and the request must NOT be in a terminal status (Completed, Approved, Approved with Actions, Rejected).

The system MUST return `403 Forbidden` for authenticated requests that exceed the user's effective capability.

#### Scenario: Normal user attempts unrelated mutation
- **WHEN** a `Normal_User` attempts to modify data outside the user's permitted scope
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Scoped role attempts unrelated mutation
- **WHEN** a scoped role user attempts to modify data outside the role's scoped records
- **THEN** the system SHALL reject the request with `403 Forbidden`


### Requirement: The system SHALL grant EA_Reviewer only record-scoped review authority
The system SHALL treat `EA_Reviewer` as a scoped business role for the Review Flow.

The system SHALL allow `EA_Reviewer` to operate only in the `Complete EA Review` step of Review Flow.

The system SHALL determine whether a request is reviewable by the current `EA_Reviewer` using table `eam_request` and field `assign_reviewer`.

The system SHALL allow an `EA_Reviewer` to perform the following actions on an assigned request:
- complete the review
- set the review result
- fill in review comments or review opinion

The system SHALL additionally allow `EA_Reviewer` the following operations:
- Create, Read, and Change projects (no Delete)
- Create, Read, and Change meetings (no Delete)
- Create, Read, and Change actions (no Delete)
- Read and write meeting decks
- Read and write scope data
- Create, Read, and Change BCM / Application BC Mapping records (no Delete)
- Upload and delete attachments on any EA Review Request at any time
- Export data

The system MUST NOT allow an `EA_Reviewer` to review requests not assigned to that user.

The system MUST NOT allow an `EA_Reviewer` to delete projects, meetings, actions, or BCM records.

The system MUST NOT allow an `EA_Reviewer` to access Certification, Resources, Reports, or Settings modules.

The system MUST NOT allow an `EA_Reviewer` to create, change, or delete Technology Stack data.

#### Scenario: Assigned reviewer completes EA review
- **WHEN** the current user is an `EA_Reviewer`, the target `eam_request.assign_reviewer` includes that user, and the request is in `Complete EA Review`
- **THEN** the system SHALL allow the user to set the review result and submit review comments

#### Scenario: Reviewer accesses unassigned request
- **WHEN** the current user is an `EA_Reviewer` but the target request is not assigned through `eam_request.assign_reviewer`
- **THEN** the system SHALL reject the review operation with `403 Forbidden`

#### Scenario: Reviewer attempts unrelated update
- **WHEN** the current user is an `EA_Reviewer` and attempts to update a field outside the permitted review result and review opinion scope
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Reviewer attempts to delete a meeting
- **WHEN** an `EA_Reviewer` attempts to delete a meeting
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Reviewer attempts to access certification
- **WHEN** an `EA_Reviewer` attempts to access the Certification module
- **THEN** the system SHALL reject the request with `403 Forbidden`


### Requirement: The system SHALL grant App_Owner only record-scoped maintenance authority
The system SHALL treat `App_Owner` as a scoped business role for Business Capability Mapping, Application BC Mapping, Technology Stack Version Master Data, and Technology Stack Lifecycle Management.

The system SHALL determine whether a record is maintainable by the current `App_Owner` by resolving ownership through:
- `cmdb_application.app_dt_owner`
- `cmdb_application.app_operation_owner`
- `cmdb_application.app_it_owner`
- `application_member.itcode`

The system SHALL interpret `application_member.itcode` as the email prefix of the authenticated user.

The system SHALL allow `App_Owner` to perform the following operations on owned application data:
- Create, Read, Change, and Delete BCM / Application BC Mapping records for owned applications
- Create, Read, Change, and Delete Technology Stack Version Master Data entries for owned applications
- Add Team Members for owned applications in Technology Stack
- Read and Change Technology Stack Lifecycle status for owned applications

The system MUST NOT allow `App_Owner` to modify records for applications that are not owned by that user.

The system MUST NOT allow `App_Owner` to import Business Capability Master Data or Technology Stack data.

The system MUST NOT allow `App_Owner` to access Certification, Resources, Reports, or Settings modules.

If a target record does not directly contain owner fields, the system SHALL resolve ownership through its associated application record.

#### Scenario: App owner updates owned BCM data
- **WHEN** the current user matches one of the owner fields on the associated application record
- **THEN** the system SHALL allow create, update, or delete operations for the corresponding Business Capability Mapping data

#### Scenario: App owner updates owned data through application member mapping
- **WHEN** the authenticated user's email prefix matches `application_member.itcode` for the associated application
- **THEN** the system SHALL allow create, update, or delete operations for the corresponding owned data

#### Scenario: App owner updates unowned lifecycle data
- **WHEN** the current user does not match any owner field or related membership on the associated application record
- **THEN** the system SHALL reject the mutation with `403 Forbidden`

#### Scenario: App owner reads owned data
- **WHEN** the current user is an `App_Owner`
- **THEN** the system SHALL allow read access as part of the user's scoped owner capability

#### Scenario: App owner attempts to access restricted module
- **WHEN** an `App_Owner` attempts to access Certification, Resources, Reports, or Settings
- **THEN** the system SHALL reject the request with `403 Forbidden`


### Requirement: The system SHALL grant Project_Owner only record-scoped project maintenance authority
The system SHALL treat `Project_Owner` as a scoped business role for the Projects module.

The system SHALL resolve `Project_Owner` from:
- `project.pm_itcode` (Project Manager)
- `project.dt_lead_itcode` (DT Lead)
- `project.it_lead_itcode` (IT Lead)

The system SHALL allow `Project_Owner` to:
- Create projects (same as `Normal_User` baseline)
- Read projects (same as `Normal_User` baseline)
- Change projects that the user owns (where the user's identifier matches `pm_itcode`, `dt_lead_itcode`, or `it_lead_itcode`)
- Add applications to projects that the user owns

The system MUST NOT allow `Project_Owner` to delete projects.

The system MUST NOT allow `Project_Owner` to change projects that the user does not own.

#### Scenario: Project owner updates owned project
- **WHEN** the current user is a `Project_Owner` and the target project's `pm_itcode`, `dt_lead_itcode`, or `it_lead_itcode` matches the user's identifier
- **THEN** the system SHALL allow the update operation

#### Scenario: Project owner updates unowned project
- **WHEN** the current user is a `Project_Owner` but the target project does not list the user in any owner field
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Project owner attempts to delete project
- **WHEN** a `Project_Owner` attempts to delete a project
- **THEN** the system SHALL reject the request with `403 Forbidden`

#### Scenario: Project owner adds application to owned project
- **WHEN** a `Project_Owner` adds an application to a project they own
- **THEN** the system SHALL allow the operation


### Requirement: The system SHALL recognize Request_Owner as a per-record ownership concept
The system SHALL determine Request_Owner status by comparing the authenticated user's identifier with the `requester` field on table `eam_request`.

The system SHALL NOT resolve Request_Owner as a session-wide role. Request_Owner status is evaluated per record at the time of each mutation request.

The system SHALL allow the Request_Owner the following operations on the corresponding EA Review Request:
- Change the request when the request is in Draft status
- Submit the request when the request is in Draft status
- Delete the request when the request is in Draft status
- Upload diagrams when the request is NOT in Completed status
- Upload attachments when the request is NOT in Completed status

The system MUST NOT allow the Request_Owner to:
- Change a request that is not in Draft status
- Submit a request that is not in Draft status
- Delete a request that is not in Draft status
- Upload diagrams or attachments on a request in Completed status

#### Scenario: Request owner identified by requester field
- **WHEN** the authenticated user's identifier matches `eam_request.requester` for a given request
- **THEN** the system SHALL treat the user as the Request_Owner for that request

#### Scenario: Request owner uploads attachment on in-progress request
- **WHEN** the Request_Owner uploads an attachment on a request in In Progress status
- **THEN** the system SHALL allow the operation

#### Scenario: Request owner attempts to edit submitted request
- **WHEN** the Request_Owner attempts to edit a request in Submitted status
- **THEN** the system SHALL reject the request with `403 Forbidden`


### Requirement: The system SHALL separate feature visibility from mutation authority
The system SHALL allow the frontend to expose only the functional pages that the current user has access to based on the per-module permission matrix.

The frontend SHOULD hide navigation entries for modules the current user cannot access.

The frontend SHOULD disable or hide mutation actions that are not allowed for the current user.

The backend MUST remain the final enforcement point for all create, update, delete, review, approval, assignment, and status transition operations.

The frontend MUST NOT be treated as a security boundary.

#### Scenario: Read-only page with disabled actions
- **WHEN** a user opens a page containing edit, delete, review, or approve actions that are not allowed
- **THEN** the frontend SHOULD disable or hide those actions

#### Scenario: Direct API call bypass attempt
- **WHEN** a client directly calls a mutation API without sufficient authority
- **THEN** the backend SHALL reject the request with `403 Forbidden`

#### Scenario: User without module access sees hidden navigation
- **WHEN** a `Normal_User` views the sidebar navigation
- **THEN** the frontend SHOULD hide entries for Certification, Resources, Reports, and Settings


### Requirement: The system SHALL build a unified authorization context from Keycloak and database sources
The system SHALL normalize the authenticated user into an authorization context containing at least:
- `user_id`
- `baseline_roles`
- `scoped_roles`
- `permissions`
- identifiers needed to evaluate Request_Owner (the `requester` field match)
- identifiers needed to evaluate assigned review requests
- identifiers needed to evaluate owned application data
- identifiers needed to evaluate owned project data
- normalized email prefix for ownership matching

The system SHALL derive:
- `EA_Admin` from `eam_bigea_team_members` field `ea_admin_status`
- `Normal_User` from successful authentication
- `EA_Reviewer` from `eam_bigea_team_members`
- `App_Owner` from `cmdb_application` and `application_member`
- `Project_Owner` from `project` (fields `pm_itcode`, `dt_lead_itcode`, `it_lead_itcode`)
- `Request_Owner` per-record from `eam_request.requester`

The system SHOULD cache authorization context briefly per request or token lifetime, but MUST ensure that scoped data decisions remain correct for the current request.

#### Scenario: Unified authorization context is created
- **WHEN** a valid token is presented
- **THEN** the system SHALL resolve baseline roles from authentication state and application data (including `EA_Admin` from `eam_bigea_team_members.ea_admin_status`), and scoped roles from application data, before business authorization is evaluated


### Requirement: The system SHALL make scoped authorization decisions auditable
The system SHALL make privileged and denied authorization decisions auditable.

For the following operations, the system SHOULD record an authorization audit event:
- EA Review Request creation
- EA Review Request submit
- EA Review Request update
- EA Review Request delete
- review completion
- review result update
- review opinion update
- Business Capability Mapping mutation
- Application BC Mapping mutation
- Technology Stack mutation
- Lifecycle Management mutation
- Project mutation
- denied mutation attempts
- denied review attempts
- denied access to restricted modules

Each audit event SHOULD include:
- authenticated user identifier
- resolved effective roles
- target resource type
- target record identifier where available
- scope basis used for the decision
- allow or deny result
- timestamp

#### Scenario: Denied scoped operation is audited
- **WHEN** a scoped business role attempts to modify an unassigned or unowned record
- **THEN** the system SHOULD record an audit event describing the deny decision

#### Scenario: Denied module access is audited
- **WHEN** a user attempts to access a restricted module
- **THEN** the system SHOULD record an audit event describing the deny decision

---

## Frontend Auth Error Handling

> Merged from: `auth-error-handling`

### Requirement: Auto-refresh on 401
The system SHALL intercept HTTP 401 responses in `fetchApi()` and attempt a single silent token refresh via Keycloak. If refresh succeeds, the original request SHALL be retried with the new token. If refresh fails, the user SHALL be redirected to Keycloak login.

#### Scenario: Token expired, refresh succeeds
- **WHEN** an API call returns 401 and the Keycloak refresh token is still valid
- **THEN** the system silently refreshes the access token and retries the original request

#### Scenario: Multiple concurrent 401s
- **WHEN** multiple API calls return 401 simultaneously
- **THEN** only one refresh request is made; all pending calls wait for the same refresh result

### Requirement: Redirect on 403
The system SHALL intercept HTTP 403 responses and redirect the user to a `/forbidden` page.

### Requirement: Forbidden page
The system SHALL provide a `/forbidden` route that displays a clear message with a "Back to Home" button.

### Requirement: Unified auth fetch for raw requests
The system SHALL export an `authFetch()` wrapper that includes auth headers and 401/403 handling, for use in places that bypass `api.*` (e.g., file uploads).
