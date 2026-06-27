# Database Schema Documentation

**Schema**: `eam`
**Total Tables**: 100
**Total Foreign Key Relationships**: 23

> Auto-generated from live database using `information_schema`.

---

## `eam.avdm_pact_concern`

PACT concern master catalog (68 architecture concerns). Defines concern keys, names, layers, risk tags.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `concern_key` | `character varying(128)` | NOT NULL | - |
| `concern_name` | `character varying(256)` | NOT NULL | - |
| `layer` | `character varying(64)` | NOT NULL | - |
| `risk_tags` | `jsonb` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |
| `severity` | `character varying(50)` | NOT NULL | - |
| `likelihood` | `character varying(50)` | NOT NULL | - |
| `classification` | `character varying(50)` | NOT NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |
| `updated_at` | `timestamp with time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_concern_activation_rule_score.concern_id` <- `eam.avdm_pact_concern`
- `eam.avdm_question_answer_concern_mapping.concern_id` <- `eam.avdm_pact_concern`
- `eam.avdm_viewpoint_concern_mapping.concern_id` <- `eam.avdm_pact_concern`

---

## `eam.avdm_question_group`

Question groups (e.g., Scale Overall, Complexity Overall, Change Trigger, Architecture Type).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `group_key` | `character varying(64)` | NOT NULL | - |
| `group_name` | `character varying(128)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question_category.group_id` <- `eam.avdm_question_group`

---

## `eam.avdm_question_category`

Question categories within groups (e.g., Project Scale, Technical Complexity, Business Change).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `group_id` | `uuid` | NOT NULL | FK -> `avdm_question_group.id` |
| `category_key` | `character varying(64)` | NOT NULL | - |
| `category_name` | `character varying(128)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question_category.group_id` -> `eam.avdm_question_group.id`
- `eam.avdm_question.category_id` <- `eam.avdm_question_category`

---

## `eam.avdm_question_answer_type`

Answer type definitions (radio, select, multiselect, text, textarea) with widget and storage kinds.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `answer_type_key` | `character varying(32)` | NOT NULL | - |
| `answer_type_name` | `character varying(128)` | NOT NULL | - |
| `storage_kind` | `character varying(32)` | NOT NULL | - |
| `widget` | `character varying(32)` | NOT NULL | - |
| `allows_multiple` | `boolean` | NOT NULL | - |
| `allows_free_text` | `boolean` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question.answer_type_id` <- `eam.avdm_question_answer_type`

---

## `eam.avdm_question_option_set`

Shared option sets (e.g., Yes/No, Application Count Ranges, Project Types).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `option_set_key` | `character varying(64)` | NOT NULL | - |
| `option_set_name` | `character varying(128)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `is_shared` | `boolean` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question.option_set_id` <- `eam.avdm_question_option_set`
- `eam.avdm_question_option_item.option_set_id` <- `eam.avdm_question_option_set`

---

## `eam.avdm_question_option_item`

Individual option items within option sets (e.g., 'Yes', '5 or fewer', 'Web App').

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `option_set_id` | `uuid` | NOT NULL | FK -> `avdm_question_option_set.id` |
| `option_value` | `character varying(128)` | NOT NULL | - |
| `option_label` | `character varying(256)` | NOT NULL | - |
| `option_score` | `numeric(8,3)` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `metadata` | `jsonb` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question_option_item.option_set_id` -> `eam.avdm_question_option_set.id`
- `eam.avdm_question_answer_concern_mapping.option_item_id` <- `eam.avdm_question_option_item`

---

## `eam.avdm_question`

Question bank items with stable IDs, text, design intent, and answer type references.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `stable_question_id` | `integer(32)` | NOT NULL | - |
| `question_key` | `character varying(128)` | NULL | - |
| `category_id` | `uuid` | NOT NULL | FK -> `avdm_question_category.id` |
| `answer_type_id` | `uuid` | NOT NULL | FK -> `avdm_question_answer_type.id` |
| `option_set_id` | `uuid` | NULL | FK -> `avdm_question_option_set.id` |
| `question_text` | `text` | NOT NULL | - |
| `design_intent` | `text` | NULL | - |
| `placeholder` | `text` | NULL | - |
| `source_scope` | `character varying(32)` | NOT NULL | - |
| `source_ref` | `character varying(128)` | NULL | - |
| `requires_comment_on_answers` | `jsonb` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question.category_id` -> `eam.avdm_question_category.id`
- `eam.avdm_question.answer_type_id` -> `eam.avdm_question_answer_type.id`
- `eam.avdm_question.option_set_id` -> `eam.avdm_question_option_set.id`
- `eam.avdm_question_answer_concern_mapping.question_id` <- `eam.avdm_question`

---

## `eam.avdm_question_answer_concern_mapping`

Maps question answers (or option selections) to PACT concerns with scores, severity, likelihood.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `question_id` | `uuid` | NOT NULL | FK -> `avdm_question.id` |
| `option_item_id` | `uuid` | NULL | FK -> `avdm_question_option_item.id` |
| `concern_id` | `uuid` | NOT NULL | FK -> `avdm_pact_concern.id` |
| `match_operator` | `character varying(32)` | NOT NULL | - |
| `answer_value` | `character varying(256)` | NULL | - |
| `mapping_score` | `numeric(8,3)` | NOT NULL | - |
| `severity` | `numeric(8,3)` | NULL | - |
| `likelihood` | `numeric(8,3)` | NULL | - |
| `hint_text` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_question_answer_concern_mapping.question_id` -> `eam.avdm_question.id`
- `eam.avdm_question_answer_concern_mapping.option_item_id` -> `eam.avdm_question_option_item.id`
- `eam.avdm_question_answer_concern_mapping.concern_id` -> `eam.avdm_pact_concern.id`

---

## `eam.avdm_artifact_category`

Artifact categories (Architecture Diagram, Business Architecture, Data Architecture, etc.).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `category_key` | `character varying(64)` | NOT NULL | - |
| `category_name` | `character varying(128)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_artifact.artifact_category_id` <- `eam.avdm_artifact_category`

---

## `eam.avdm_artifact`

Named artifacts (tech diagram, app collaboration, biz diagram, data model, etc.) with purpose and typical contents.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `artifact_key` | `character varying(64)` | NOT NULL | - |
| `artifact_category_id` | `uuid` | NOT NULL | FK -> `avdm_artifact_category.id` |
| `artifact_name` | `character varying(128)` | NOT NULL | - |
| `purpose` | `text` | NOT NULL | - |
| `stage` | `character varying(64)` | NOT NULL | - |
| `typical_contents` | `jsonb` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_artifact.artifact_category_id` -> `eam.avdm_artifact_category.id`
- `eam.avdm_project_type_artifact_mapping.artifact_id` <- `eam.avdm_artifact`
- `eam.avdm_viewpoint_artifact_mapping.artifact_id` <- `eam.avdm_artifact`

---

## `eam.avdm_viewpoint`

Architecture viewpoint definitions with L/P classification, S/B classification, purpose, examples, audience.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `viewpoint_number` | `integer(32)` | NOT NULL | - |
| `layer_name` | `character varying(128)` | NOT NULL | - |
| `viewpoint_name` | `character varying(256)` | NOT NULL | - |
| `logical_physical` | `character varying(16)` | NULL | - |
| `structure_behavior` | `character varying(16)` | NULL | - |
| `purpose` | `text` | NULL | - |
| `example` | `text` | NULL | - |
| `primary_source` | `character varying(256)` | NULL | - |
| `audience` | `character varying(256)` | NULL | - |
| `notes` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_viewpoint_artifact_mapping.viewpoint_id` <- `eam.avdm_viewpoint` (ON DELETE CASCADE)
- `eam.avdm_viewpoint_concern_mapping.viewpoint_id` <- `eam.avdm_viewpoint` (ON DELETE CASCADE)

---

## `eam.avdm_viewpoint_concern_mapping`

Maps viewpoints to their associated PACT concerns.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `viewpoint_id` | `uuid` | NOT NULL | FK -> `avdm_viewpoint.id`, ON DELETE CASCADE |
| `concern_id` | `uuid` | NOT NULL | FK -> `avdm_pact_concern.id` |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_viewpoint_concern_mapping.viewpoint_id` -> `eam.avdm_viewpoint.id` (ON DELETE CASCADE)
- `eam.avdm_viewpoint_concern_mapping.concern_id` -> `eam.avdm_pact_concern.id`

---

## `eam.avdm_viewpoint_artifact_mapping`

Maps viewpoints to recommended artifacts with Mandatory/Optional status.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `viewpoint_id` | `uuid` | NOT NULL | FK -> `avdm_viewpoint.id`, ON DELETE CASCADE |
| `artifact_id` | `uuid` | NOT NULL | FK -> `avdm_artifact.id` |
| `recommendation_status` | `character varying(32)` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_viewpoint_artifact_mapping.viewpoint_id` -> `eam.avdm_viewpoint.id` (ON DELETE CASCADE)
- `eam.avdm_viewpoint_artifact_mapping.artifact_id` -> `eam.avdm_artifact.id`

---

## `eam.avdm_project_type_profile`

Project type profiles (e.g., Web App, Data Project, AI/ML) with typical patterns and risks.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_type_key` | `character varying(128)` | NOT NULL | - |
| `project_type_label` | `character varying(256)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `typical_patterns` | `jsonb` | NOT NULL | - |
| `typical_risks` | `jsonb` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_project_type_artifact_mapping.project_type_profile_id` <- `eam.avdm_project_type_profile` (ON DELETE CASCADE)

---

## `eam.avdm_project_type_artifact_mapping`

Maps project type profiles to default artifact recommendations.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_type_profile_id` | `uuid` | NOT NULL | FK -> `avdm_project_type_profile.id`, ON DELETE CASCADE |
| `artifact_id` | `uuid` | NOT NULL | FK -> `avdm_artifact.id` |
| `default_status` | `character varying(32)` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_project_type_artifact_mapping.project_type_profile_id` -> `eam.avdm_project_type_profile.id` (ON DELETE CASCADE)
- `eam.avdm_project_type_artifact_mapping.artifact_id` -> `eam.avdm_artifact.id`

---

## `eam.avdm_concern_activation_rule`

Conditional rules for activating concerns based on question answer combinations.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `rule_key` | `character varying(128)` | NOT NULL | - |
| `description` | `text` | NOT NULL | - |
| `all_conditions` | `jsonb` | NOT NULL | - |
| `any_conditions` | `jsonb` | NOT NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_concern_activation_rule_score.rule_id` <- `eam.avdm_concern_activation_rule` (ON DELETE CASCADE)

---

## `eam.avdm_concern_activation_rule_score`

Scoring entries per rule+concern combination.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `rule_id` | `uuid` | NOT NULL | FK -> `avdm_concern_activation_rule.id`, ON DELETE CASCADE |
| `concern_id` | `uuid` | NOT NULL | FK -> `avdm_pact_concern.id` |
| `mapping_score` | `numeric(8,3)` | NOT NULL | - |
| `severity` | `numeric(8,3)` | NULL | - |
| `likelihood` | `numeric(8,3)` | NULL | - |
| `note_text` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.avdm_concern_activation_rule_score.rule_id` -> `eam.avdm_concern_activation_rule.id` (ON DELETE CASCADE)
- `eam.avdm_concern_activation_rule_score.concern_id` -> `eam.avdm_pact_concern.id`

---

## `eam.avdm_questionnaire_config`

JSONB-based questionnaire configuration store (config key, versioned).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `config_key` | `character varying(64)` | NOT NULL | - |
| `config_json` | `jsonb` | NOT NULL | - |
| `version` | `integer(32)` | NOT NULL | - |
| `change_note` | `text` | NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

---

## `eam.avdm_master_data_revision`

Revision tracking for AVDM master data domains (questionnaire, concern_mapping, artifact_catalog, etc.).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `domain_key` | `character varying(64)` | NOT NULL | - |
| `version` | `integer(32)` | NOT NULL | - |
| `change_note` | `text` | NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

---

## `eam.avdm_static_document`

JSONB-based static document store (viewpoint_artifact_mapping, project_type_profiles, questionnaire_sections).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `document_key` | `character varying(64)` | NOT NULL | - |
| `document_json` | `jsonb` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |

---

## `eam.avdm_project_assessment`

Project-level AVDM assessment records with questionnaire, risk items, evaluation, concerns, and artifact selections.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying(64)` | NOT NULL | - |
| `project_type` | `character varying(128)` | NULL | - |
| `project_complexity` | `numeric(4,3)` | NOT NULL | - |
| `questionnaire` | `jsonb` | NOT NULL | - |
| `risk_items` | `jsonb` | NOT NULL | - |
| `evaluation` | `jsonb` | NULL | - |
| `review_result` | `jsonb` | NULL | - |
| `needs_avdm` | `boolean` | NULL | - |
| `judgement_reason` | `text` | NULL | - |
| `version` | `integer(32)` | NOT NULL | - |
| `status` | `character varying(32)` | NOT NULL | - |
| `create_by` | `character varying(64)` | NOT NULL | - |
| `update_by` | `character varying(64)` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `update_at` | `timestamp without time zone` | NOT NULL | - |
| `artifact_selection` | `jsonb` | NULL | - |
| `artifact_confirmed_at` | `timestamp without time zone` | NULL | - |
| `questionnaire_submitted_at` | `timestamp without time zone` | NULL | - |
| `questionnaire_confirmed_at` | `timestamp without time zone` | NULL | - |
| `concern_requirement_confirmed_at` | `timestamp without time zone` | NULL | - |
| `artifact_requirement_confirmed_at` | `timestamp without time zone` | NULL | - |
| `artifact_submitted_at` | `timestamp without time zone` | NULL | - |

---

## `eam.eam_request`

Architecture review requests - the core entity for the EA review workflow.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `request_id` | `character varying` | NOT NULL | - |
| `project_id` | `character varying` | NOT NULL | - |
| `review_scope` | `character varying` | NULL | - |
| `ws_phase_name` | `character varying` | NULL | - |
| `requester` | `character varying` | NULL | - |
| `status` | `character varying` | NOT NULL | - |
| `status_remark` | `character varying` | NULL | - |
| `status_changed_by` | `character varying` | NULL | - |
| `status_changed_at` | `timestamp without time zone` | NULL | - |
| `link` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `assign_reviewer` | `ARRAY` | NULL | - |
| `review_result` | `character varying` | NULL | - |
| `process_id` | `character varying` | NULL | - |
| `organization` | `character varying` | NULL | - |
| `request_desc` | `character varying` | NULL | - |

---

## `eam.eam_request_process_log`

Process log tracking state transitions and workflow steps per request.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `request_id` | `character varying` | NULL | - |
| `action` | `character varying` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `operator` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `id` | `character varying` | NOT NULL | PK |

---

## `eam.eam_request_attachment`

Attachments/documents uploaded for architecture review requests.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `request_id` | `character varying` | NOT NULL | - |
| `attachment_name` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `id` | `uuid` | NOT NULL | PK |
| `biz_type` | `character varying` | NULL | - |
| `app_arch_type` | `character varying` | NULL | - |
| `original_name` | `character varying(512)` | NULL | - |

---

## `eam.eam_meetings`

Review meeting records linked to projects/requests.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `meeting_no` | `bigint(64)` | NOT NULL | SERIAL |
| `project_id` | `character varying` | NOT NULL | - |
| `project_objectives` | `text` | NULL | - |
| `meeting_title` | `character varying` | NOT NULL | - |
| `available_ea_schedule` | `character varying` | NULL | - |
| `start_time` | `timestamp without time zone` | NOT NULL | - |
| `end_time` | `timestamp without time zone` | NOT NULL | - |
| `presenter` | `ARRAY` | NOT NULL | - |
| `attendees` | `ARRAY` | NOT NULL | - |
| `location` | `character varying` | NULL | - |
| `meeting_agenda` | `text` | NOT NULL | - |
| `key_agreement_findings` | `text` | NULL | - |
| `review_decks` | `ARRAY` | NOT NULL | - |
| `review_recording` | `ARRAY` | NOT NULL | - |
| `status` | `character varying` | NOT NULL | - |
| `calendar_id` | `character varying` | NULL | - |
| `status_remark` | `character varying` | NULL | - |
| `ea_review_result` | `character varying` | NULL | - |
| `ea_review_remark` | `character varying` | NULL | - |
| `email_cc` | `ARRAY` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `request_id` | `character varying` | NULL | - |

---

## `eam.eam_actions`

Action items from review meetings linked to requests.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | - |
| `meeting_id` | `uuid` | NULL | - |
| `action_no` | `bigint(64)` | NOT NULL | SERIAL |
| `action_title` | `character varying` | NOT NULL | - |
| `priority` | `character varying` | NOT NULL | - |
| `due_date` | `timestamp without time zone` | NULL | - |
| `assignee` | `ARRAY` | NOT NULL | - |
| `assignee_name` | `ARRAY` | NOT NULL | - |
| `action_description` | `character varying` | NULL | - |
| `status` | `character varying` | NULL | - |
| `type` | `character varying` | NOT NULL | - |
| `requested_by` | `character varying` | NOT NULL | - |
| `requested_by_name` | `character varying` | NOT NULL | - |
| `action_updates` | `character varying` | NULL | - |
| `applicable_domain` | `character varying` | NOT NULL | - |
| `start_date` | `timestamp without time zone` | NULL | - |
| `notification_times` | `smallint(16)` | NULL | - |
| `open_date` | `timestamp without time zone` | NULL | - |
| `in_validtion_date` | `timestamp without time zone` | NULL | - |
| `close_date` | `timestamp without time zone` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `request_id` | `character varying` | NULL | - |

---

## `eam.eam_bigea_team_members`

EA team member directory (itcode, name, org hierarchy).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `worker` | `character varying(255)` | NULL | - |
| `itcode` | `character varying(255)` | NOT NULL | PK |
| `worker_type` | `character varying(255)` | NULL | - |
| `name` | `character varying(255)` | NULL | - |
| `email` | `character varying(255)` | NULL | - |
| `country` | `character varying(255)` | NULL | - |
| `location` | `character varying(255)` | NULL | - |
| `primary_skill` | `character varying(255)` | NULL | - |
| `skill_level` | `character varying(255)` | NULL | - |
| `job_role` | `character varying(255)` | NULL | - |
| `rate` | `numeric(10,3)` | NULL | - |
| `track_focal` | `character varying(255)` | NULL | - |
| `manager_level_1` | `character varying(255)` | NULL | - |
| `manager_level_2` | `character varying(255)` | NULL | - |
| `manager_level_3` | `character varying(255)` | NULL | - |
| `manager_level_4` | `character varying(255)` | NULL | - |
| `manager_level_5` | `character varying(255)` | NULL | - |
| `manager_level_6` | `character varying(255)` | NULL | - |
| `manager_level_7` | `character varying(255)` | NULL | - |
| `manager_level_8` | `character varying(255)` | NULL | - |
| `manager_level_9` | `character varying(255)` | NULL | - |
| `tier_1_org` | `character varying(255)` | NULL | - |
| `tier_2_org` | `character varying(255)` | NULL | - |
| `tier_3_org` | `character varying(255)` | NULL | - |
| `tier_4_org` | `character varying(255)` | NULL | - |
| `tier_5_org` | `character varying(255)` | NULL | - |
| `tier_6_org` | `character varying(255)` | NULL | - |
| `create_time` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying(255)` | NULL | - |
| `update_time` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying(255)` | NULL | - |
| `manager_itcode` | `character varying` | NULL | - |
| `manager_name` | `character varying` | NULL | - |
| `email_option` | `boolean` | NULL | - |
| `ea_admin_status` | `boolean` | NULL | - |

---

## `eam.eam_arch_ai_check`

AI review check results against architecture diagrams.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `total_cost` | `numeric` | NULL | - |
| `check_cost` | `numeric` | NULL | - |
| `request` | `jsonb` | NULL | - |
| `result` | `jsonb` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `id` | `uuid` | NOT NULL | PK |
| `attachment_uuid` | `uuid` | NULL | - |

---

## `eam.eam_arch_ai_check_interaction`

AI analysis of interactions between applications in a check.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `ai_check_id` | `character varying` | NOT NULL | - |
| `source_app_id` | `character varying` | NULL | - |
| `target_app_id` | `character varying` | NULL | - |
| `interaction_type` | `character varying` | NULL | - |
| `direction` | `character varying` | NULL | - |
| `source_function` | `character varying` | NULL | - |
| `target_function` | `character varying` | NULL | - |
| `interface_status` | `character varying` | NULL | - |
| `business_object` | `character varying` | NULL | - |
| `remark` | `character varying` | NULL | - |
| `status` | `character varying` | NULL | - |
| `status_changed_by` | `character varying` | NULL | - |
| `status_changed_at` | `timestamp without time zone` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `id` | `uuid` | NOT NULL | PK |
| `type` | `character varying` | NULL | - |

---

## `eam.eam_arch_ai_check_app`

Applications referenced in AI architecture checks.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `ai_check_id` | `character varying` | NOT NULL | - |
| `app_id` | `character varying` | NULL | - |
| `id_is_standard` | `boolean` | NULL | - |
| `standard_id` | `character varying` | NULL | - |
| `app_name` | `character varying` | NULL | - |
| `functions` | `ARRAY` | NULL | - |
| `check_app_status` | `character varying` | NULL | - |
| `remark` | `character varying` | NULL | - |
| `status` | `character varying` | NULL | - |
| `status_changed_by` | `character varying` | NULL | - |
| `status_changed_at` | `timestamp without time zone` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `id` | `uuid` | NOT NULL | PK |
| `type` | `character varying` | NULL | - |

---

## `eam.tech_key_stack_item`

Technology stack items with version, compliance status, and security advice.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `stack_id` | `character varying` | NOT NULL | SERIAL |
| `app_id` | `character varying` | NOT NULL | - |
| `category` | `character varying` | NOT NULL | - |
| `component` | `character varying` | NOT NULL | - |
| `use_status` | `character varying` | NULL | - |
| `sub_category` | `character varying` | NOT NULL | - |
| `major_version` | `integer(32)` | NOT NULL | - |
| `minor_version` | `character varying(30)` | NOT NULL | - |
| `patch_version` | `character varying` | NULL | - |
| `eol_date` | `date` | NULL | - |
| `eol_interval_time` | `character varying` | NULL | - |
| `maintainability_risk_level` | `character varying` | NULL | - |
| `maintainability_risk_light` | `character varying` | NULL | - |
| `standard` | `character varying` | NULL | - |
| `status_comments` | `character varying` | NULL | - |
| `remark` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `component_package` | `character varying` | NOT NULL | - |
| `security_risk_level` | `character varying` | NULL | - |
| `security_risk_light` | `character varying` | NULL | - |
| `master_no` | `integer(32)` | NULL | - |
| `cvss_v3_score` | `numeric` | NULL | - |
| `ea_advice` | `character varying` | NULL | - |
| `security_advice` | `character varying` | NULL | - |

---

## `eam.tech_stack_master_data`

Master data for technology stack definitions (approved lists, categories).

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `master_no` | `integer(32)` | NOT NULL | - |
| `category` | `character varying` | NOT NULL | - |
| `component` | `character varying` | NOT NULL | - |
| `component_package` | `character varying` | NOT NULL | - |
| `version` | `character varying` | NOT NULL | - |
| `ea_advice` | `character varying` | NOT NULL | - |
| `remark` | `character varying` | NULL | - |
| `initial_release_date` | `date` | NULL | - |
| `final_release_date` | `date` | NULL | - |
| `security_vulnerability` | `character varying` | NULL | - |
| `security_serverity` | `character varying` | NULL | - |
| `cvss_v3_score` | `numeric` | NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `eol_link` | `character varying` | NULL | - |
| `sub_category` | `character varying` | NULL | - |
| `standard` | `character varying` | NULL | - |
| `major_version` | `integer(32)` | NULL | - |
| `minor_version` | `character varying(255)` | NULL | - |
| `patch_version` | `character varying` | NULL | - |
| `eol_date` | `date` | NULL | - |
| `security_advice` | `character varying` | NULL | - |
| `vulnerability_link` | `character varying` | NULL | - |
| `restricted` | `character varying` | NULL | - |
| `source_type` | `character varying` | NULL | - |
| `source` | `character varying` | NULL | - |

---

## `eam.tech_stack_operate_log`

Audit log for field-level changes to tech stack items.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NULL | - |
| `stack_id` | `character varying` | NULL | - |
| `field` | `character varying` | NULL | - |
| `old_value` | `text` | NULL | - |
| `new_value` | `text` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |

---

## `eam.biz_cap_map`

Business capability mapping to applications/data versions.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `app_id` | `character varying` | NOT NULL | - |
| `bcpf_master_id` | `bigint(64)` | NOT NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `data_version` | `character varying` | NULL | - |
| `bc_id` | `character varying` | NULL | - |

---

## `eam.eam_project`

Projects tracked in the project management module.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `name` | `character varying(255)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `status` | `character varying(50)` | NULL | - |
| `owner_id` | `character varying(255)` | NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |
| `updated_at` | `timestamp with time zone` | NOT NULL | - |

### Relationships

- `eam.eam_team_member.project_id` <- `eam.eam_project` (ON DELETE CASCADE)

---

## `eam.eam_team_member`

Team members assigned to projects.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `uuid` | NOT NULL | FK -> `eam_project.id`, ON DELETE CASCADE |
| `user_itcode` | `character varying(255)` | NOT NULL | - |
| `role` | `character varying(50)` | NULL | - |

### Relationships

- `eam.eam_team_member.project_id` -> `eam.eam_project.id` (ON DELETE CASCADE)

---

## `eam.eam_project_app`

Applications associated with projects.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying(255)` | NOT NULL | - |
| `app_name` | `character varying(255)` | NULL | - |
| `description` | `text` | NULL | - |
| `owner` | `character varying(255)` | NULL | - |
| `status` | `character varying(50)` | NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |

---

## `eam.resource_pool`

Resource directory (itcode, name, email, org hierarchy) for autocomplete.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `worker` | `character varying(255)` | NULL | - |
| `itcode` | `character varying(255)` | NOT NULL | PK |
| `worker_type` | `character varying(255)` | NULL | - |
| `name` | `character varying(255)` | NULL | - |
| `email` | `character varying(255)` | NULL | - |
| `country` | `character varying(255)` | NULL | - |
| `location` | `character varying(255)` | NULL | - |
| `primary_skill` | `character varying(255)` | NULL | - |
| `skill_level` | `character varying(255)` | NULL | - |
| `job_role` | `character varying(255)` | NULL | - |
| `rate` | `numeric(10,3)` | NULL | - |
| `track_focal` | `character varying(255)` | NULL | - |
| `manager_level_1` | `character varying(255)` | NULL | - |
| `manager_level_2` | `character varying(255)` | NULL | - |
| `manager_level_3` | `character varying(255)` | NULL | - |
| `manager_level_4` | `character varying(255)` | NULL | - |
| `manager_level_5` | `character varying(255)` | NULL | - |
| `manager_level_6` | `character varying(255)` | NULL | - |
| `manager_level_7` | `character varying(255)` | NULL | - |
| `manager_level_8` | `character varying(255)` | NULL | - |
| `manager_level_9` | `character varying(255)` | NULL | - |
| `tier_1_org` | `character varying(255)` | NULL | - |
| `tier_2_org` | `character varying(255)` | NULL | - |
| `tier_3_org` | `character varying(255)` | NULL | - |
| `tier_4_org` | `character varying(255)` | NULL | - |
| `tier_5_org` | `character varying(255)` | NULL | - |
| `tier_6_org` | `character varying(255)` | NULL | - |
| `create_time` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying(255)` | NULL | - |
| `update_time` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying(255)` | NULL | - |
| `manager_itcode` | `character varying` | NULL | - |
| `manager_name` | `character varying` | NULL | - |
| `email_option` | `boolean` | NULL | - |

---

## `eam.eam_audit_log`

RBAC audit log recording all access decisions (allow/deny) with user, resource, action.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `object_type` | `character varying` | NOT NULL | - |
| `object_id` | `uuid` | NOT NULL | - |
| `field` | `character varying` | NULL | - |
| `new_value` | `character varying` | NULL | - |
| `old_value` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_time` | `timestamp without time zone` | NULL | - |
| `project_id` | `character varying` | NULL | - |
| `user_id` | `character varying(255)` | NULL | - |
| `roles` | `jsonb` | NULL | - |
| `resource` | `character varying(255)` | NOT NULL | - |
| `action` | `character varying(50)` | NOT NULL | - |
| `decision` | `character varying(20)` | NOT NULL | - |
| `reason` | `text` | NULL | - |
| `request_id` | `character varying(64)` | NULL | - |
| `client_ip` | `character varying(45)` | NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |

---

## `eam.eam_file_storage`

Binary file storage (S3 alternative) keyed by path.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `key` | `text` | NOT NULL | PK |
| `data` | `bytea` | NOT NULL | - |
| `content_type` | `character varying(255)` | NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |

---

## `eam.local_users`

Local authentication users (username, password hash, role). Used when AUTH_MODE=local.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `username` | `character varying(100)` | NOT NULL | - |
| `password_hash` | `character varying(255)` | NOT NULL | - |
| `name` | `character varying(255)` | NOT NULL | - |
| `email` | `character varying(255)` | NOT NULL | - |
| `role` | `character varying(50)` | NOT NULL | - |
| `is_active` | `boolean` | NOT NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |
| `updated_at` | `timestamp with time zone` | NOT NULL | - |

---

## `eam.schema_migrations`

Migration tracking table recording applied migration filenames and hashes.

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `integer(32)` | NOT NULL | PK, SERIAL |
| `filename` | `character varying(255)` | NOT NULL | - |
| `hash` | `character varying(64)` | NOT NULL | - |
| `applied_at` | `timestamp with time zone` | NOT NULL | - |

---

## `eam.ai_project_assessment`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_name` | `character varying(255)` | NOT NULL | - |
| `project_id_ref` | `character varying(255)` | NULL | - |
| `status` | `character varying(50)` | NOT NULL | - |
| `created_by` | `character varying(128)` | NOT NULL | - |
| `updated_by` | `character varying(128)` | NOT NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |
| `updated_at` | `timestamp with time zone` | NOT NULL | - |

### Relationships

- `eam.ai_review_checklist.assessment_id` <- `eam.ai_project_assessment` (ON DELETE CASCADE)
- `eam.ai_self_assessment.assessment_id` <- `eam.ai_project_assessment` (ON DELETE CASCADE)

---

## `eam.ai_review_checklist`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `assessment_id` | `uuid` | NOT NULL | FK -> `ai_project_assessment.id`, ON DELETE CASCADE |
| `section_key` | `character varying(64)` | NOT NULL | - |
| `section_label` | `character varying(255)` | NOT NULL | - |
| `item_key` | `character varying(64)` | NOT NULL | - |
| `item_label` | `text` | NOT NULL | - |
| `is_checked` | `boolean` | NOT NULL | - |
| `is_critical` | `boolean` | NOT NULL | - |
| `notes` | `text` | NULL | - |
| `sort_order` | `integer(32)` | NOT NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |
| `updated_at` | `timestamp with time zone` | NOT NULL | - |

### Relationships

- `eam.ai_review_checklist.assessment_id` -> `eam.ai_project_assessment.id` (ON DELETE CASCADE)

---

## `eam.ai_self_assessment`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `assessment_id` | `uuid` | NOT NULL | FK -> `ai_project_assessment.id`, ON DELETE CASCADE |
| `scenario_class` | `character varying(32)` | NOT NULL | - |
| `counterparty_type` | `character varying(32)` | NOT NULL | - |
| `adoption_tier` | `integer(32)` | NOT NULL | - |
| `governance_maturity` | `integer(32)` | NOT NULL | - |
| `matrix_position` | `character varying(32)` | NOT NULL | - |
| `description` | `text` | NULL | - |
| `created_at` | `timestamp with time zone` | NOT NULL | - |
| `updated_at` | `timestamp with time zone` | NOT NULL | - |

### Relationships

- `eam.ai_self_assessment.assessment_id` -> `eam.ai_project_assessment.id` (ON DELETE CASCADE)

---

## `eam.application_data`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NOT NULL | - |
| `data_residency_geo` | `character varying` | NULL | - |
| `data_residency_country` | `character varying` | NULL | - |
| `data_center` | `character varying` | NULL | - |
| `support` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.application_data_comment`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `object_type` | `character varying` | NOT NULL | - |
| `object_id` | `uuid` | NOT NULL | - |
| `content` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |

---

## `eam.application_data_entity`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `simple_id` | `character varying` | NULL | SERIAL |
| `name` | `character varying` | NULL | - |
| `source` | `character varying` | NULL | - |
| `data_volume` | `character varying` | NULL | - |
| `memo` | `character varying` | NULL | - |
| `attachment` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `app_id` | `uuid` | NOT NULL | - |

---

## `eam.application_data_entity_classification`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `entity_id` | `uuid` | NULL | - |
| `method` | `character varying` | NULL | - |
| `level1` | `uuid` | NULL | - |
| `level2` | `uuid` | NULL | - |
| `level3` | `uuid` | NULL | - |
| `level4` | `uuid` | NULL | - |

---

## `eam.application_data_flow`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `business_scenarios_l1` | `character varying` | NULL | - |
| `source_data_entity_id` | `uuid` | NULL | - |
| `destination_data_entity_id` | `uuid` | NULL | - |
| `remark` | `character varying` | NULL | - |
| `simple_id` | `character varying` | NULL | SERIAL |
| `business_scenarios_l2` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.application_legal_entity`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `uuid` | NOT NULL | - |
| `company_code` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |

---

## `eam.application_member`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NULL | - |
| `itcode` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |

---

## `eam.bcpf_master_data`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `bigint(64)` | NOT NULL | PK, SERIAL |
| `data_version` | `character varying(16)` | NOT NULL | - |
| `bc_id` | `character varying(32)` | NOT NULL | - |
| `parent_bc_id` | `character varying(32)` | NOT NULL | - |
| `bc_name` | `character varying(255)` | NOT NULL | - |
| `bc_name_cn` | `character varying(255)` | NULL | - |
| `level` | `smallint(16)` | NOT NULL | - |
| `alias` | `character varying(255)` | NULL | - |
| `bc_description` | `text` | NULL | - |
| `biz_group` | `character varying(32)` | NULL | - |
| `geo` | `character varying(32)` | NULL | - |
| `biz_owner` | `character varying(255)` | NULL | - |
| `biz_team` | `character varying(255)` | NULL | - |
| `dt_owner` | `character varying(255)` | NULL | - |
| `dt_team` | `character varying(128)` | NULL | - |
| `remark` | `character varying(255)` | NULL | - |
| `create_time` | `timestamp without time zone` | NOT NULL | - |
| `lv1_domain` | `character varying(255)` | NOT NULL | - |
| `lv2_sub_domain` | `character varying(255)` | NULL | - |
| `lv3_capability_group` | `character varying(255)` | NULL | - |

---

## `eam.business_object_sequences`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `sequence_name` | `character varying(32)` | NOT NULL | - |
| `current_value` | `bigint(64)` | NOT NULL | - |

---

## `eam.certification`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | - |
| `simple_id` | `character varying` | NULL | SERIAL |
| `itcode` | `character varying` | NOT NULL | PK |
| `exam_name` | `character varying` | NOT NULL | PK |
| `certificate_type` | `character varying` | NOT NULL | PK |
| `issue_date` | `timestamp without time zone` | NOT NULL | PK |
| `expiration_date` | `timestamp without time zone` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `user_name` | `character varying` | NULL | - |
| `duration` | `numeric` | NOT NULL | PK |

---

## `eam.cmdb_application`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `_id` | `character varying` | NULL | - |
| `short_description` | `character varying` | NULL | - |
| `u_service_area` | `character varying` | NULL | - |
| `u_status` | `character varying` | NULL | - |
| `app_full_name` | `character varying` | NULL | - |
| `owned_by` | `character varying` | NULL | - |
| `name` | `character varying` | NULL | - |
| `app_it_owner` | `character varying` | NULL | - |
| `app_owner_tower` | `character varying` | NULL | - |
| `app_owner_domain` | `character varying` | NULL | - |
| `app_id` | `character varying` | NULL | - |
| `patch_level` | `character varying` | NULL | - |
| `portfolio_mgt` | `character varying` | NULL | - |
| `app_classification` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `app_ownership` | `character varying` | NULL | - |
| `app_solution_type` | `character varying` | NULL | - |
| `app_operation_owner` | `character varying` | NULL | - |
| `app_operation_owner_tower` | `character varying` | NULL | - |
| `app_operation_owner_domain` | `character varying` | NULL | - |
| `decommissioned_at` | `timestamp without time zone` | NULL | - |
| `app_dt_owner` | `character varying` | NULL | - |

---

## `eam.company`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `company_code` | `character varying` | NOT NULL | - |
| `company_name` | `character varying` | NULL | - |
| `company_remark` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `s4` | `character varying` | NULL | - |
| `area` | `character varying` | NULL | - |
| `profit_ecc` | `character varying` | NULL | - |
| `profit_s4` | `character varying` | NULL | - |

---

## `eam.data_center`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `name` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |

---

## `eam.data_classification`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `method` | `character varying` | NULL | - |
| `code` | `character varying` | NULL | - |
| `name_zh` | `character varying` | NULL | - |
| `name_en` | `character varying` | NULL | - |
| `parent` | `uuid` | NULL | - |
| `sort` | `character varying` | NULL | - |
| `status` | `character varying` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `level` | `numeric` | NULL | - |

---

## `eam.df_timer_details`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying(50)` | NOT NULL | PK |
| `timer_job_id` | `character varying(50)` | NOT NULL | - |
| `process_id` | `character varying(50)` | NOT NULL | - |
| `app_id` | `character varying(20)` | NOT NULL | - |
| `payload` | `character varying(1024)` | NULL | - |
| `cron_expression` | `character varying(100)` | NOT NULL | - |
| `status` | `character varying(10)` | NOT NULL | - |
| `name` | `character varying(100)` | NULL | - |
| `is_running` | `integer(32)` | NOT NULL | - |

---

## `eam.dict_option`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `category_id` | `integer(32)` | NOT NULL | PK |
| `option_id` | `integer(32)` | NOT NULL | PK |
| `option` | `character varying` | NULL | - |
| `lang` | `character varying` | NOT NULL | PK |
| `description` | `character varying` | NULL | - |
| `status` | `integer(32)` | NULL | - |
| `id` | `uuid` | NULL | - |
| `created_by` | `character varying` | NULL | - |
| `created_at` | `timestamp without time zone` | NULL | - |
| `updated_by` | `character varying` | NULL | - |
| `updated_at` | `timestamp without time zone` | NULL | - |

---

## `eam.eam_actions_email_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | - |
| `meeting_id` | `uuid` | NULL | - |
| `action_id` | `uuid` | NOT NULL | - |
| `log_time` | `timestamp without time zone` | NOT NULL | - |
| `from` | `character varying` | NOT NULL | - |
| `recipients` | `ARRAY` | NOT NULL | - |
| `subject` | `character varying` | NOT NULL | - |
| `status` | `character varying` | NOT NULL | - |

---

## `eam.eam_arch_ai_check_0122`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `request_id` | `character varying` | NULL | - |
| `arch_diagram` | `character varying` | NULL | - |
| `biz_type` | `character varying` | NULL | - |
| `total_cost` | `numeric` | NULL | - |
| `check_cost` | `numeric` | NULL | - |
| `request` | `jsonb` | NULL | - |
| `result` | `jsonb` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `id` | `uuid` | NULL | - |
| `attachment_uuid` | `uuid` | NULL | - |

---

## `eam.eam_ea_calendar`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying` | NULL | - |
| `schedule_no` | `bigint(64)` | NOT NULL | SERIAL |
| `schedule_title` | `character varying` | NULL | - |
| `start_time` | `timestamp without time zone` | NOT NULL | - |
| `end_time` | `timestamp without time zone` | NOT NULL | - |
| `duration` | `smallint(16)` | NULL | - |
| `recurrence_pattern` | `character varying` | NULL | - |
| `end_after` | `integer(32)` | NULL | - |
| `owner` | `ARRAY` | NULL | - |
| `remark` | `character varying` | NULL | - |
| `status` | `character varying` | NULL | - |
| `for_project` | `character varying` | NULL | - |
| `for_meeting` | `character varying` | NULL | - |

---

## `eam.eam_email_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `module_code` | `character varying(50)` | NOT NULL | - |
| `entity_type` | `character varying(50)` | NOT NULL | - |
| `entity_id` | `character varying(100)` | NOT NULL | - |
| `trigger_event` | `character varying(100)` | NOT NULL | - |
| `template_code` | `character varying(100)` | NOT NULL | - |
| `template_tag` | `character varying(100)` | NOT NULL | - |
| `mail_from` | `character varying(320)` | NOT NULL | - |
| `mail_to` | `text` | NOT NULL | - |
| `mail_cc` | `text` | NULL | - |
| `subject` | `text` | NOT NULL | - |
| `payload_json` | `jsonb` | NOT NULL | - |
| `send_status` | `character varying(20)` | NOT NULL | - |
| `error_message` | `text` | NULL | - |
| `retry_of_log_id` | `uuid` | NULL | FK -> `eam_email_log.id` |
| `triggered_by` | `character varying(100)` | NOT NULL | - |
| `sent_at` | `timestamp without time zone` | NULL | - |
| `created_at` | `timestamp without time zone` | NOT NULL | - |
| `updated_at` | `timestamp without time zone` | NOT NULL | - |

### Relationships

- `eam.eam_email_log.retry_of_log_id` -> `eam.eam_email_log.id`
- `eam.eam_email_log.retry_of_log_id` <- `eam.eam_email_log`

---

## `eam.eam_email_recipient`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `email_action` | `character varying` | NULL | - |
| `cc_pm` | `boolean` | NULL | - |
| `cc_dt` | `boolean` | NULL | - |
| `cc_it` | `boolean` | NULL | - |
| `cc_ea_admin` | `boolean` | NULL | - |
| `cc_big_ea` | `boolean` | NULL | - |
| `cc_project_member` | `boolean` | NULL | - |
| `cc_attendee` | `boolean` | NULL | - |
| `cc_presenter` | `boolean` | NULL | - |
| `cc_assignee` | `boolean` | NULL | - |

---

## `eam.eam_meeting_deck`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `meeting_id` | `character varying` | NULL | - |
| `deck_name` | `character varying` | NULL | - |
| `deck_url` | `character varying` | NULL | - |

---

## `eam.eam_meeting_minutes`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `bigint(64)` | NOT NULL | PK, SERIAL |
| `project_id` | `character varying` | NOT NULL | - |
| `project_name` | `character varying` | NOT NULL | - |
| `project_leader` | `character varying` | NOT NULL | - |
| `project_objectives` | `text` | NOT NULL | - |
| `meeting_title` | `character varying` | NOT NULL | - |
| `review_date` | `timestamp without time zone` | NOT NULL | - |
| `presenter` | `ARRAY` | NOT NULL | - |
| `attendees` | `ARRAY` | NOT NULL | - |
| `meeting_agenda` | `text` | NOT NULL | - |
| `key_agreement_findings` | `text` | NOT NULL | - |
| `review_decks` | `ARRAY` | NOT NULL | - |
| `review_recording` | `ARRAY` | NOT NULL | - |

---

## `eam.eam_meetings_email_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | - |
| `meeting_id` | `uuid` | NOT NULL | - |
| `log_time` | `timestamp without time zone` | NOT NULL | - |
| `from` | `character varying` | NOT NULL | - |
| `recipients` | `ARRAY` | NOT NULL | - |
| `subject` | `character varying` | NOT NULL | - |
| `status` | `character varying` | NOT NULL | - |

---

## `eam.eam_project_summary`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | - |
| `business_owner1` | `character varying` | NULL | - |
| `business_owner2` | `character varying` | NULL | - |
| `cost` | `character varying` | NULL | - |
| `schedule` | `character varying` | NULL | - |
| `function_summary` | `character varying` | NULL | - |
| `benefit` | `character varying` | NULL | - |
| `paint_point` | `character varying` | NULL | - |
| `application_list` | `ARRAY` | NULL | - |
| `architect_summary` | `character varying` | NULL | - |
| `ea_status` | `character varying` | NULL | - |
| `status_remark` | `character varying` | NULL | - |
| `attachments` | `ARRAY` | NULL | - |
| `ea_review_submitter` | `character varying` | NULL | - |
| `comments_app` | `character varying` | NULL | - |
| `ea_review_type` | `character varying` | NULL | - |
| `domain_ea_reviewer` | `character varying` | NULL | - |

---

## `eam.eam_review_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `comment` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `operator` | `character varying` | NULL | - |
| `operation` | `character varying` | NULL | - |
| `project_id` | `character varying` | NULL | - |

---

## `eam.eam_scope_check_list`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `checklist_no` | `smallint(16)` | NOT NULL | - |
| `project_id` | `character varying` | NOT NULL | - |
| `category` | `character varying` | NOT NULL | - |
| `questions` | `character varying` | NULL | - |
| `answer` | `character varying` | NULL | - |
| `option` | `character varying` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `link` | `ARRAY` | NULL | - |
| `sub_category` | `character varying` | NULL | - |

---

## `eam.eam_scope_check_list_template`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `checklist_no` | `smallint(16)` | NOT NULL | - |
| `category` | `character varying` | NOT NULL | - |
| `questions` | `character varying` | NULL | - |
| `answer` | `character varying` | NULL | - |
| `option` | `character varying` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `link` | `ARRAY` | NULL | - |
| `id` | `uuid` | NOT NULL | PK |
| `sub_category` | `character varying` | NULL | - |
| `answer_type` | `character varying` | NULL | - |
| `selection_type` | `character varying` | NULL | - |
| `selection_option` | `ARRAY` | NULL | - |

---

## `eam.eam_scope_of_change`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | - |
| `scope_no` | `bigint(64)` | NOT NULL | SERIAL |
| `title` | `character varying` | NOT NULL | - |
| `description` | `character varying` | NOT NULL | - |
| `create_using_template` | `character varying` | NOT NULL | - |
| `sample` | `character varying` | NOT NULL | - |

---

## `eam.eam_scope_of_change_pages`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `scope_of_change_id` | `uuid` | NOT NULL | - |
| `name` | `character varying` | NULL | - |
| `description` | `character varying` | NULL | - |
| `diagram` | `text` | NULL | - |

---

## `eam.eam_scope_of_change_template`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `scope_no` | `bigint(64)` | NOT NULL | - |
| `title` | `character varying` | NOT NULL | - |
| `description` | `character varying` | NOT NULL | - |
| `create_using_template` | `character varying` | NOT NULL | - |
| `sample` | `character varying` | NOT NULL | - |

---

## `eam.email_notification_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `object_type` | `character varying` | NOT NULL | - |
| `object_id` | `character varying` | NULL | - |
| `object_business_id` | `character varying` | NOT NULL | - |
| `create_at` | `timestamp without time zone` | NOT NULL | - |
| `create_by` | `character varying` | NOT NULL | - |
| `email_from` | `character varying` | NOT NULL | - |
| `email_to` | `ARRAY` | NOT NULL | - |
| `email_cc` | `ARRAY` | NOT NULL | - |
| `subject` | `character varying` | NOT NULL | - |
| `status` | `character varying` | NOT NULL | - |
| `remark` | `character varying` | NOT NULL | - |

---

## `eam.fiscal_year_sequences`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `sequence_name` | `character varying(32)` | NOT NULL | - |
| `fiscal_year` | `character varying(16)` | NULL | - |
| `current_value` | `bigint(64)` | NOT NULL | - |

---

## `eam.help_file`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `usage` | `character varying` | NOT NULL | - |
| `file_name` | `character varying` | NULL | - |
| `file_path` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.process_role`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `node_name` | `character varying` | NULL | - |
| `pre_status` | `character varying` | NULL | - |
| `role` | `character varying` | NULL | - |
| `process_id` | `character varying` | NULL | - |
| `description` | `character varying` | NULL | - |
| `order_no` | `integer(32)` | NULL | - |
| `reminder_cycle` | `integer(32)` | NULL | - |
| `id` | `uuid` | NOT NULL | PK |

---

## `eam.project`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | SERIAL |
| `project_name` | `character varying` | NULL | - |
| `type` | `character varying` | NULL | - |
| `start_date` | `character varying` | NULL | - |
| `go_live_date` | `character varying` | NULL | - |
| `pps_exit_date` | `character varying` | NULL | - |
| `end_date` | `character varying` | NULL | - |
| `pm` | `character varying` | NULL | - |
| `pm_itcode` | `character varying` | NULL | - |
| `dt_lead` | `character varying` | NULL | - |
| `dt_lead_itcode` | `character varying` | NULL | - |
| `it_lead` | `character varying` | NULL | - |
| `it_lead_itcode` | `character varying` | NULL | - |
| `duration` | `numeric` | NULL | - |
| `objectives` | `character varying` | NULL | - |
| `investment_cost` | `numeric` | NULL | - |
| `yearly_ma_cost` | `numeric` | NULL | - |
| `currency` | `character varying` | NULL | - |
| `expected_man_days` | `numeric` | NULL | - |
| `status` | `character varying` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `ea_review_type` | `character varying` | NULL | - |
| `domain_ea_reviewer` | `character varying` | NULL | - |
| `favourite` | `character varying` | NULL | - |
| `name` | `character varying(56)` | NULL | - |
| `used_in_ea` | `boolean` | NULL | - |
| `risk_status` | `character varying` | NULL | - |
| `overall_status` | `character varying` | NULL | - |
| `check_date` | `character varying` | NULL | - |
| `engagement_status` | `character varying` | NULL | - |
| `follow_up_action` | `character varying` | NULL | - |
| `check_required` | `character varying` | NULL | - |
| `approved_time` | `character varying` | NULL | - |
| `source` | `character varying` | NULL | - |
| `ea_approval_dt` | `character varying` | NULL | - |
| `ai_related` | `character varying` | NULL | - |

---

## `eam.project_app`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `project_id` | `character varying` | NULL | - |
| `app_id` | `character varying` | NOT NULL | - |
| `app_name` | `character varying` | NULL | - |
| `app_full_name` | `character varying` | NULL | - |
| `app_it_owner` | `character varying` | NULL | - |
| `current_state` | `character varying` | NULL | - |
| `app_tech_id_in_cmdb` | `character varying` | NULL | - |
| `app_description` | `character varying` | NULL | - |
| `business_function` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.project_ea_status_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `project_id` | `character varying` | NULL | - |
| `ea_status` | `character varying` | NULL | - |
| `status_change_date` | `date` | NULL | - |
| `create_at` | `timestamp with time zone` | NOT NULL | - |

---

## `eam.project_task`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `project_id` | `character varying` | NOT NULL | - |
| `project_name` | `character varying` | NULL | - |
| `task_name` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `assignee` | `character varying` | NULL | - |
| `approval_status` | `character varying` | NULL | - |
| `task_status` | `character varying` | NULL | - |
| `approval_date` | `character varying` | NULL | - |
| `comment` | `character varying` | NULL | - |
| `description` | `character varying` | NULL | - |

---

## `eam.project_team_members`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `project_id` | `character varying` | NULL | - |
| `itcode` | `character varying` | NOT NULL | - |
| `name` | `character varying` | NULL | - |
| `worker_type` | `character varying` | NULL | - |
| `manager_itcode` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.project_user_bookmark`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `project_id` | `character varying` | NOT NULL | - |
| `user_itcode` | `character varying` | NULL | - |
| `favourite` | `character varying` | NULL | - |
| `default` | `character varying` | NULL | - |

---

## `eam.resource_pool_extend`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `worker` | `character varying(255)` | NULL | - |
| `itcode` | `character varying(255)` | NOT NULL | PK |
| `worker_type` | `character varying(255)` | NULL | - |
| `name` | `character varying(255)` | NULL | - |
| `email` | `character varying(255)` | NULL | - |
| `country` | `character varying(255)` | NULL | - |
| `location` | `character varying(255)` | NULL | - |
| `primary_skill` | `character varying(255)` | NULL | - |
| `skill_level` | `character varying(255)` | NULL | - |
| `job_role` | `character varying(255)` | NULL | - |
| `rate` | `numeric(10,3)` | NULL | - |
| `track_focal` | `character varying(255)` | NULL | - |
| `manager_level_1` | `character varying(255)` | NULL | - |
| `manager_level_2` | `character varying(255)` | NULL | - |
| `manager_level_3` | `character varying(255)` | NULL | - |
| `manager_level_4` | `character varying(255)` | NULL | - |
| `manager_level_5` | `character varying(255)` | NULL | - |
| `manager_level_6` | `character varying(255)` | NULL | - |
| `manager_level_7` | `character varying(255)` | NULL | - |
| `manager_level_8` | `character varying(255)` | NULL | - |
| `manager_level_9` | `character varying(255)` | NULL | - |
| `tier_1_org` | `character varying(255)` | NULL | - |
| `tier_2_org` | `character varying(255)` | NULL | - |
| `tier_3_org` | `character varying(255)` | NULL | - |
| `tier_4_org` | `character varying(255)` | NULL | - |
| `tier_5_org` | `character varying(255)` | NULL | - |
| `tier_6_org` | `character varying(255)` | NULL | - |
| `create_time` | `timestamp without time zone` | NULL | - |
| `create_by` | `character varying(255)` | NULL | - |
| `update_time` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying(255)` | NULL | - |
| `manager_itcode` | `character varying` | NULL | - |
| `manager_name` | `character varying` | NULL | - |
| `email_option` | `boolean` | NULL | - |

---

## `eam.smart_agent`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `itcode` | `character varying` | NULL | - |

---

## `eam.sys_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `character varying` | NOT NULL | PK |
| `log_content` | `json` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `user` | `character varying` | NULL | - |
| `action` | `character varying` | NULL | - |
| `object` | `character varying` | NULL | - |

---

## `eam.tech_key_stack_auto_checking_log`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `update_time` | `timestamp without time zone` | NOT NULL | - |
| `last_update_time` | `timestamp without time zone` | NOT NULL | - |
| `old_content` | `jsonb` | NULL | - |
| `new_content` | `jsonb` | NULL | - |
| `app_id` | `character varying(255)` | NULL | - |
| `create_by` | `character varying(255)` | NOT NULL | - |

---

## `eam.tech_stack_app`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NOT NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.tech_stack_category`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `integer(32)` | NOT NULL | PK, SERIAL |
| `category_code` | `character varying(128)` | NOT NULL | - |
| `category_name` | `character varying(128)` | NOT NULL | - |
| `parent_category` | `character varying(128)` | NOT NULL | - |
| `level` | `smallint(16)` | NOT NULL | - |
| `create_time` | `timestamp without time zone` | NOT NULL | - |
| `created_by` | `character varying(64)` | NOT NULL | - |
| `update_time` | `timestamp without time zone` | NOT NULL | - |
| `updated_by` | `character varying(64)` | NOT NULL | - |

---

## `eam.tech_stack_component`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `stack_id` | `character varying` | NULL | SERIAL |
| `dependency_id` | `uuid` | NOT NULL | - |
| `remark` | `character varying` | NULL | - |
| `category` | `character varying` | NULL | - |
| `group_id` | `character varying` | NULL | - |
| `component_package` | `character varying` | NOT NULL | - |
| `version` | `character varying` | NOT NULL | - |
| `specifier` | `character varying` | NULL | - |
| `type` | `character varying` | NULL | - |
| `scope` | `character varying` | NULL | - |
| `source` | `character varying` | NULL | - |
| `inherited` | `boolean` | NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.tech_stack_dependency`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NOT NULL | - |
| `devops_link` | `character varying` | NOT NULL | - |
| `devops_project` | `character varying` | NOT NULL | - |
| `pipline_name` | `character varying` | NOT NULL | - |
| `package_type` | `character varying` | NOT NULL | - |
| `remark` | `character varying` | NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.tech_stack_dependency_file`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NOT NULL | - |
| `dependency_id` | `uuid` | NOT NULL | - |
| `file_name` | `character varying` | NOT NULL | - |
| `file_size` | `integer(32)` | NULL | - |
| `file_content` | `text` | NOT NULL | - |
| `mime_type` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |

---

## `eam.tech_stack_item`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `stack_id` | `character varying` | NULL | SERIAL |
| `app_id` | `character varying` | NOT NULL | - |
| `devops_link` | `character varying` | NOT NULL | - |
| `devops_project` | `character varying` | NOT NULL | - |
| `pipline_name` | `character varying` | NOT NULL | - |
| `package_type` | `character varying` | NOT NULL | - |
| `remark` | `character varying` | NULL | - |
| `category` | `character varying` | NULL | - |
| `group_id` | `character varying` | NULL | - |
| `component_package` | `character varying` | NOT NULL | - |
| `version` | `character varying` | NOT NULL | - |
| `type` | `character varying` | NULL | - |
| `scope` | `character varying` | NULL | - |
| `source` | `character varying` | NULL | - |
| `inherited` | `boolean` | NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |
| `specifier` | `character varying` | NULL | - |

---

## `eam.tech_stack_lifecyle`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `app_id` | `character varying` | NOT NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.tech_stack_standard`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `tech_layer` | `character varying` | NOT NULL | - |
| `category` | `character varying` | NOT NULL | - |
| `component_group` | `character varying` | NULL | - |
| `component_name` | `character varying` | NOT NULL | - |
| `description` | `character varying` | NULL | - |
| `license` | `character varying` | NULL | - |
| `internal_effective_version` | `character varying` | NULL | - |
| `latest_version` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.tech_stack_template`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `id` | `uuid` | NOT NULL | PK |
| `template_no` | `integer(32)` | NOT NULL | SERIAL |
| `standard_uuid` | `uuid` | NULL | - |
| `status` | `character varying` | NULL | - |
| `create_by` | `character varying` | NULL | - |
| `create_at` | `timestamp without time zone` | NULL | - |
| `update_by` | `character varying` | NULL | - |
| `update_at` | `timestamp without time zone` | NULL | - |

---

## `eam.user_profile`

| Column | Type | Null | FK / PK |
|--------|------|------|---------|
| `itcode` | `character varying` | NOT NULL | PK |
| `name` | `character varying` | NULL | - |
| `email` | `character varying` | NULL | - |
| `country` | `character varying` | NULL | - |
| `manager_itcode` | `character varying` | NULL | - |
| `manager_name` | `character varying` | NULL | - |
| `tier_1_org` | `character varying(255)` | NULL | - |
| `tier_2_org` | `character varying(255)` | NULL | - |
| `tier_3_org` | `character varying(255)` | NULL | - |
| `tier_4_org` | `character varying(255)` | NULL | - |
| `tier_5_org` | `character varying(255)` | NULL | - |
| `tier_6_org` | `character varying(255)` | NULL | - |
| `create_time` | `timestamp without time zone` | NULL | - |

---
