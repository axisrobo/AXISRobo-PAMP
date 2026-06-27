-- PAMF Complete Schema DDL
-- Generated: 2026-06-24
-- Tables: 101

-- Table: eam.ai_project_assessment
CREATE TABLE IF NOT EXISTS eam.ai_project_assessment (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    project_id_ref VARCHAR(255),
    status VARCHAR(255) NOT NULL DEFAULT 'draft'::character varying,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.ai_review_checklist
CREATE TABLE IF NOT EXISTS eam.ai_review_checklist (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    assessment_id UUID NOT NULL,
    section_key VARCHAR(255) NOT NULL,
    section_label VARCHAR(255) NOT NULL,
    item_key VARCHAR(255) NOT NULL,
    item_label TEXT NOT NULL,
    is_checked BOOLEAN NOT NULL DEFAULT false,
    is_critical BOOLEAN NOT NULL DEFAULT false,
    notes TEXT DEFAULT ''::text,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.ai_self_assessment
CREATE TABLE IF NOT EXISTS eam.ai_self_assessment (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    assessment_id UUID NOT NULL,
    scenario_class VARCHAR(255) NOT NULL DEFAULT 'enterprise'::character varying,
    counterparty_type VARCHAR(255) NOT NULL DEFAULT 'cp1'::character varying,
    adoption_tier INTEGER NOT NULL DEFAULT 0,
    governance_maturity INTEGER NOT NULL DEFAULT 0,
    matrix_position VARCHAR(255) NOT NULL DEFAULT 'unassessed'::character varying,
    description TEXT DEFAULT ''::text,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.ai_model_registry
CREATE TABLE IF NOT EXISTS eam.ai_model_registry (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_key VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(255) DEFAULT ''::character varying,
    model_type VARCHAR(255) DEFAULT 'llm'::character varying,
    description TEXT DEFAULT ''::text,
    owner VARCHAR(255) DEFAULT ''::character varying,
    status VARCHAR(255) NOT NULL DEFAULT 'draft'::character varying,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.ai_model_version
CREATE TABLE IF NOT EXISTS eam.ai_model_version (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_id UUID NOT NULL REFERENCES eam.ai_model_registry(id) ON DELETE CASCADE,
    version VARCHAR(255) NOT NULL,
    source VARCHAR(255) DEFAULT ''::character varying,
    source_uri TEXT DEFAULT ''::text,
    checksum VARCHAR(255) DEFAULT ''::character varying,
    license VARCHAR(255) DEFAULT ''::character varying,
    training_data_provenance TEXT DEFAULT ''::text,
    approval_status VARCHAR(255) NOT NULL DEFAULT 'pending'::character varying,
    is_production BOOLEAN NOT NULL DEFAULT false,
    notes TEXT DEFAULT ''::text,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_id, version)
);

-- Table: eam.ai_agent_registry
CREATE TABLE IF NOT EXISTS eam.ai_agent_registry (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_key VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(255) DEFAULT 'assistant'::character varying,
    description TEXT DEFAULT ''::text,
    owner VARCHAR(255) DEFAULT ''::character varying,
    scenario_class VARCHAR(255) NOT NULL DEFAULT 'enterprise'::character varying,
    counterparty_type VARCHAR(255) NOT NULL DEFAULT 'cp1'::character varying,
    adoption_tier INTEGER NOT NULL DEFAULT 1,
    autonomy_level VARCHAR(255) NOT NULL DEFAULT 'human_approval'::character varying,
    trust_level VARCHAR(255) NOT NULL DEFAULT 'limited'::character varying,
    hitl_required BOOLEAN NOT NULL DEFAULT false,
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_id_ref UUID REFERENCES eam.ai_model_registry(id) ON DELETE SET NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'draft'::character varying,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.application_data
CREATE TABLE IF NOT EXISTS eam.application_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255) NOT NULL,
    data_residency_geo VARCHAR(255),
    data_residency_country VARCHAR(255),
    data_center VARCHAR(255),
    support VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.application_data_comment
CREATE TABLE IF NOT EXISTS eam.application_data_comment (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    object_type VARCHAR(255) NOT NULL,
    object_id UUID NOT NULL,
    content VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP DEFAULT now()
);

-- Table: eam.application_data_entity
CREATE TABLE IF NOT EXISTS eam.application_data_entity (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    simple_id VARCHAR(255) DEFAULT ('DE'::text || to_char(nextval('application_data_entity_simple_id_seq'::regclass), 'FM000000'::text)),
    name VARCHAR(255),
    source VARCHAR(255),
    data_volume VARCHAR(255),
    memo VARCHAR(255),
    attachment VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP DEFAULT now(),
    app_id UUID NOT NULL
);

-- Table: eam.application_data_entity_classification
CREATE TABLE IF NOT EXISTS eam.application_data_entity_classification (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID,
    method VARCHAR(255),
    level1 UUID,
    level2 UUID,
    level3 UUID,
    level4 UUID
);

-- Table: eam.application_data_flow
CREATE TABLE IF NOT EXISTS eam.application_data_flow (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    business_scenarios_l1 VARCHAR(255),
    source_data_entity_id UUID,
    destination_data_entity_id UUID,
    remark VARCHAR(255),
    simple_id VARCHAR(255) DEFAULT ('DF'::text || to_char(nextval('dataflow_simple_id_seq'::regclass), 'FM000000'::text)),
    business_scenarios_l2 VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.application_legal_entity
CREATE TABLE IF NOT EXISTS eam.application_legal_entity (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id UUID NOT NULL,
    company_code VARCHAR(255),
    create_at TIMESTAMP DEFAULT now()
);

-- Table: eam.application_member
CREATE TABLE IF NOT EXISTS eam.application_member (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255),
    itcode VARCHAR(255),
    create_at TIMESTAMP
);

-- Table: eam.avdm_artifact
CREATE TABLE IF NOT EXISTS eam.avdm_artifact (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    artifact_key VARCHAR(255) NOT NULL,
    artifact_category_id UUID NOT NULL,
    artifact_name VARCHAR(255) NOT NULL,
    purpose TEXT NOT NULL,
    stage VARCHAR(255) NOT NULL DEFAULT 'Preparation'::character varying,
    typical_contents JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_artifact_category
CREATE TABLE IF NOT EXISTS eam.avdm_artifact_category (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    category_key VARCHAR(255) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_concern_activation_rule
CREATE TABLE IF NOT EXISTS eam.avdm_concern_activation_rule (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    rule_key VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    all_conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    any_conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_concern_activation_rule_score
CREATE TABLE IF NOT EXISTS eam.avdm_concern_activation_rule_score (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    rule_id UUID NOT NULL,
    concern_id UUID NOT NULL,
    mapping_score NUMERIC NOT NULL DEFAULT 0,
    severity NUMERIC,
    likelihood NUMERIC,
    note_text TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_master_data_revision
CREATE TABLE IF NOT EXISTS eam.avdm_master_data_revision (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    domain_key VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    change_note TEXT,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_pact_concern
CREATE TABLE IF NOT EXISTS eam.avdm_pact_concern (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    concern_key VARCHAR(255) NOT NULL,
    concern_name VARCHAR(255) NOT NULL,
    layer VARCHAR(255) NOT NULL,
    risk_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now(),
    severity VARCHAR(255) NOT NULL DEFAULT 'medium'::character varying,
    likelihood VARCHAR(255) NOT NULL DEFAULT 'medium'::character varying,
    classification VARCHAR(255) NOT NULL DEFAULT 'recommended'::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.avdm_project_assessment
CREATE TABLE IF NOT EXISTS eam.avdm_project_assessment (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    project_type VARCHAR(255),
    project_complexity NUMERIC NOT NULL DEFAULT 0.500,
    questionnaire JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluation JSONB,
    review_result JSONB,
    needs_avdm BOOLEAN,
    judgement_reason TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(255) NOT NULL DEFAULT 'draft'::character varying,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now(),
    artifact_selection JSONB,
    artifact_confirmed_at TIMESTAMP,
    questionnaire_submitted_at TIMESTAMP,
    questionnaire_confirmed_at TIMESTAMP,
    concern_requirement_confirmed_at TIMESTAMP,
    artifact_requirement_confirmed_at TIMESTAMP,
    artifact_submitted_at TIMESTAMP
);

-- Table: eam.avdm_project_type_artifact_mapping
CREATE TABLE IF NOT EXISTS eam.avdm_project_type_artifact_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_type_profile_id UUID NOT NULL,
    artifact_id UUID NOT NULL,
    default_status VARCHAR(255) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_project_type_profile
CREATE TABLE IF NOT EXISTS eam.avdm_project_type_profile (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_type_key VARCHAR(255) NOT NULL,
    project_type_label VARCHAR(255) NOT NULL,
    description TEXT,
    typical_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
    typical_risks JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question
CREATE TABLE IF NOT EXISTS eam.avdm_question (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    stable_question_id INTEGER NOT NULL,
    question_key VARCHAR(255),
    category_id UUID NOT NULL,
    answer_type_id UUID NOT NULL,
    option_set_id UUID,
    question_text TEXT NOT NULL,
    design_intent TEXT,
    placeholder TEXT,
    source_scope VARCHAR(255) NOT NULL DEFAULT 'question_bank'::character varying,
    source_ref VARCHAR(255),
    requires_comment_on_answers JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question_answer_concern_mapping
CREATE TABLE IF NOT EXISTS eam.avdm_question_answer_concern_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question_id UUID NOT NULL,
    option_item_id UUID,
    concern_id UUID NOT NULL,
    match_operator VARCHAR(255) NOT NULL DEFAULT 'equals'::character varying,
    answer_value VARCHAR(255),
    mapping_score NUMERIC NOT NULL DEFAULT 0,
    severity NUMERIC,
    likelihood NUMERIC,
    hint_text TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question_answer_type
CREATE TABLE IF NOT EXISTS eam.avdm_question_answer_type (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    answer_type_key VARCHAR(255) NOT NULL,
    answer_type_name VARCHAR(255) NOT NULL,
    storage_kind VARCHAR(255) NOT NULL,
    widget VARCHAR(255) NOT NULL,
    allows_multiple BOOLEAN NOT NULL DEFAULT false,
    allows_free_text BOOLEAN NOT NULL DEFAULT false,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question_category
CREATE TABLE IF NOT EXISTS eam.avdm_question_category (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_id UUID NOT NULL,
    category_key VARCHAR(255) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question_group
CREATE TABLE IF NOT EXISTS eam.avdm_question_group (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_key VARCHAR(255) NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question_option_item
CREATE TABLE IF NOT EXISTS eam.avdm_question_option_item (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    option_set_id UUID NOT NULL,
    option_value VARCHAR(255) NOT NULL,
    option_label VARCHAR(255) NOT NULL,
    option_score NUMERIC,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_question_option_set
CREATE TABLE IF NOT EXISTS eam.avdm_question_option_set (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    option_set_key VARCHAR(255) NOT NULL,
    option_set_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_shared BOOLEAN NOT NULL DEFAULT true,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_questionnaire_config
CREATE TABLE IF NOT EXISTS eam.avdm_questionnaire_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    version INTEGER NOT NULL DEFAULT 1,
    change_note TEXT,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_static_document
CREATE TABLE IF NOT EXISTS eam.avdm_static_document (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_key VARCHAR(255) NOT NULL,
    document_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_viewpoint
CREATE TABLE IF NOT EXISTS eam.avdm_viewpoint (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    viewpoint_number INTEGER NOT NULL,
    layer_name VARCHAR(255) NOT NULL,
    viewpoint_name VARCHAR(255) NOT NULL,
    logical_physical VARCHAR(255),
    structure_behavior VARCHAR(255),
    purpose TEXT,
    example TEXT,
    primary_source VARCHAR(255),
    audience VARCHAR(255),
    notes TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_viewpoint_artifact_mapping
CREATE TABLE IF NOT EXISTS eam.avdm_viewpoint_artifact_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    viewpoint_id UUID NOT NULL,
    artifact_id UUID NOT NULL,
    recommendation_status VARCHAR(255) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.avdm_viewpoint_concern_mapping
CREATE TABLE IF NOT EXISTS eam.avdm_viewpoint_concern_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    viewpoint_id UUID NOT NULL,
    concern_id UUID NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    update_by VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    create_at TIMESTAMP NOT NULL DEFAULT now(),
    update_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.bcpf_master_data
CREATE TABLE IF NOT EXISTS eam.bcpf_master_data (
    id BIGINT NOT NULL DEFAULT nextval('bcpf_master_data_id_seq'::regclass),
    data_version VARCHAR(255) NOT NULL,
    bc_id VARCHAR(255) NOT NULL,
    parent_bc_id VARCHAR(255) NOT NULL,
    bc_name VARCHAR(255) NOT NULL,
    bc_name_cn VARCHAR(255) DEFAULT ''::character varying,
    level SMALLINT NOT NULL,
    alias VARCHAR(255) DEFAULT ''::character varying,
    bc_description TEXT DEFAULT ''::text,
    biz_group VARCHAR(255) DEFAULT ''::character varying,
    geo VARCHAR(255) DEFAULT ''::character varying,
    biz_owner VARCHAR(255) DEFAULT ''::character varying,
    biz_team VARCHAR(255) DEFAULT ''::character varying,
    dt_owner VARCHAR(255) DEFAULT ''::character varying,
    dt_team VARCHAR(255) DEFAULT ''::character varying,
    remark VARCHAR(255) DEFAULT ''::character varying,
    create_time TIMESTAMP NOT NULL,
    lv1_domain VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    lv2_sub_domain VARCHAR(255) DEFAULT ''::character varying,
    lv3_capability_group VARCHAR(255) DEFAULT ''::character varying
);

-- Table: eam.biz_cap_map
CREATE TABLE IF NOT EXISTS eam.biz_cap_map (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    app_id VARCHAR(255) NOT NULL,
    bcpf_master_id BIGINT NOT NULL,
    create_by VARCHAR(255),
    create_at TIMESTAMP DEFAULT now(),
    update_by VARCHAR(255),
    update_at TIMESTAMP DEFAULT now(),
    data_version VARCHAR(255),
    bc_id VARCHAR(255)
);

-- Table: eam.business_object_sequences
CREATE TABLE IF NOT EXISTS eam.business_object_sequences (
    sequence_name VARCHAR(255) NOT NULL,
    current_value BIGINT NOT NULL
);

-- Table: eam.certification
CREATE TABLE IF NOT EXISTS eam.certification (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    simple_id VARCHAR(255) DEFAULT ('CN'::text || to_char(nextval('certification_simple_id_seq'::regclass), 'FM000000'::text)),
    itcode VARCHAR(255) NOT NULL,
    exam_name VARCHAR(255) NOT NULL,
    certificate_type VARCHAR(255) NOT NULL,
    issue_date TIMESTAMP NOT NULL,
    expiration_date TIMESTAMP,
    comment VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP,
    user_name VARCHAR(255),
    duration NUMERIC NOT NULL
);

-- Table: eam.cmdb_application
CREATE TABLE IF NOT EXISTS eam.cmdb_application (
    _id VARCHAR(255),
    short_description VARCHAR(255),
    u_service_area VARCHAR(255),
    u_status VARCHAR(255),
    app_full_name VARCHAR(255),
    owned_by VARCHAR(255),
    name VARCHAR(255),
    app_it_owner VARCHAR(255),
    app_owner_tower VARCHAR(255),
    app_owner_domain VARCHAR(255),
    app_id VARCHAR(255),
    patch_level VARCHAR(255),
    portfolio_mgt VARCHAR(255),
    app_classification VARCHAR(255),
    update_at TIMESTAMP DEFAULT now(),
    app_ownership VARCHAR(255),
    app_solution_type VARCHAR(255),
    app_operation_owner VARCHAR(255),
    app_operation_owner_tower VARCHAR(255),
    app_operation_owner_domain VARCHAR(255),
    decommissioned_at TIMESTAMP,
    app_dt_owner VARCHAR(255)
);

-- Table: eam.company
CREATE TABLE IF NOT EXISTS eam.company (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    company_code VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    company_remark VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP,
    s4 VARCHAR(255),
    area VARCHAR(255),
    profit_ecc VARCHAR(255),
    profit_s4 VARCHAR(255)
);

-- Table: eam.data_center
CREATE TABLE IF NOT EXISTS eam.data_center (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP
);

-- Table: eam.data_classification
CREATE TABLE IF NOT EXISTS eam.data_classification (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    method VARCHAR(255),
    code VARCHAR(255),
    name_zh VARCHAR(255),
    name_en VARCHAR(255),
    parent UUID,
    sort VARCHAR(255),
    status VARCHAR(255),
    comment VARCHAR(255),
    level NUMERIC
);

-- Table: eam.df_timer_details
CREATE TABLE IF NOT EXISTS eam.df_timer_details (
    id VARCHAR(255) NOT NULL,
    timer_job_id VARCHAR(255) NOT NULL,
    process_id VARCHAR(255) NOT NULL,
    app_id VARCHAR(255) NOT NULL,
    payload VARCHAR(255),
    cron_expression VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    is_running INTEGER NOT NULL DEFAULT 0
);

-- Table: eam.dict_option
CREATE TABLE IF NOT EXISTS eam.dict_option (
    category_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    option VARCHAR(255),
    lang VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    status INTEGER DEFAULT 1,
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT now(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT now()
);

-- Table: eam.eam_actions
CREATE TABLE IF NOT EXISTS eam.eam_actions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    meeting_id UUID,
    action_no BIGINT NOT NULL DEFAULT nextval('eam_actions_action_no_seq'::regclass),
    action_title VARCHAR(255) NOT NULL,
    priority VARCHAR(255) NOT NULL,
    due_date TIMESTAMP,
    assignee TEXT[] NOT NULL,
    assignee_name TEXT[] NOT NULL,
    action_description VARCHAR(255),
    status VARCHAR(255),
    type VARCHAR(255) NOT NULL,
    requested_by VARCHAR(255) NOT NULL,
    requested_by_name VARCHAR(255) NOT NULL,
    action_updates VARCHAR(255),
    applicable_domain VARCHAR(255) NOT NULL,
    start_date TIMESTAMP,
    notification_times SMALLINT,
    open_date TIMESTAMP,
    in_validtion_date TIMESTAMP,
    close_date TIMESTAMP,
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    update_at TIMESTAMP,
    update_by VARCHAR(255),
    request_id VARCHAR(255)
);

-- Table: eam.eam_actions_email_log
CREATE TABLE IF NOT EXISTS eam.eam_actions_email_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    meeting_id UUID,
    action_id UUID NOT NULL,
    log_time TIMESTAMP NOT NULL,
    from VARCHAR(255) NOT NULL,
    recipients TEXT[] NOT NULL,
    subject VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL
);

-- Table: eam.eam_arch_ai_check
CREATE TABLE IF NOT EXISTS eam.eam_arch_ai_check (
    total_cost NUMERIC,
    check_cost NUMERIC,
    request JSONB,
    result JSONB,
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    attachment_uuid UUID
);

-- Table: eam.eam_arch_ai_check_0122
CREATE TABLE IF NOT EXISTS eam.eam_arch_ai_check_0122 (
    request_id VARCHAR(255),
    arch_diagram VARCHAR(255),
    biz_type VARCHAR(255),
    total_cost NUMERIC,
    check_cost NUMERIC,
    request JSONB,
    result JSONB,
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    attachment_uuid UUID
);

-- Table: eam.eam_arch_ai_check_app
CREATE TABLE IF NOT EXISTS eam.eam_arch_ai_check_app (
    ai_check_id VARCHAR(255) NOT NULL,
    app_id VARCHAR(255),
    id_is_standard BOOLEAN,
    standard_id VARCHAR(255),
    app_name VARCHAR(255),
    functions TEXT[],
    check_app_status VARCHAR(255),
    remark VARCHAR(255),
    status VARCHAR(255),
    status_changed_by VARCHAR(255),
    status_changed_at TIMESTAMP,
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    update_at TIMESTAMP,
    update_by VARCHAR(255),
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type VARCHAR(255) DEFAULT 'aicheck'::character varying
);

-- Table: eam.eam_arch_ai_check_interaction
CREATE TABLE IF NOT EXISTS eam.eam_arch_ai_check_interaction (
    ai_check_id VARCHAR(255) NOT NULL,
    source_app_id VARCHAR(255),
    target_app_id VARCHAR(255),
    interaction_type VARCHAR(255),
    direction VARCHAR(255),
    source_function VARCHAR(255),
    target_function VARCHAR(255),
    interface_status VARCHAR(255),
    business_object VARCHAR(255),
    remark VARCHAR(255),
    status VARCHAR(255),
    status_changed_by VARCHAR(255),
    status_changed_at TIMESTAMP,
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    update_at TIMESTAMP,
    update_by VARCHAR(255),
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type VARCHAR(255) DEFAULT 'aicheck'::character varying
);

-- Table: eam.eam_audit_log
CREATE TABLE IF NOT EXISTS eam.eam_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    object_type VARCHAR(255) NOT NULL,
    object_id UUID NOT NULL,
    field VARCHAR(255),
    new_value VARCHAR(255),
    old_value VARCHAR(255),
    create_by VARCHAR(255),
    create_time TIMESTAMP,
    project_id VARCHAR(255),
    user_id VARCHAR(255),
    roles JSONB,
    resource VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    action VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    decision VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    reason TEXT,
    request_id VARCHAR(255),
    client_ip VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.eam_bigea_team_members
CREATE TABLE IF NOT EXISTS eam.eam_bigea_team_members (
    worker VARCHAR(255),
    itcode VARCHAR(255) NOT NULL,
    worker_type VARCHAR(255),
    name VARCHAR(255),
    email VARCHAR(255),
    country VARCHAR(255),
    location VARCHAR(255),
    primary_skill VARCHAR(255),
    skill_level VARCHAR(255),
    job_role VARCHAR(255),
    rate NUMERIC,
    track_focal VARCHAR(255),
    manager_level_1 VARCHAR(255),
    manager_level_2 VARCHAR(255),
    manager_level_3 VARCHAR(255),
    manager_level_4 VARCHAR(255),
    manager_level_5 VARCHAR(255),
    manager_level_6 VARCHAR(255),
    manager_level_7 VARCHAR(255),
    manager_level_8 VARCHAR(255),
    manager_level_9 VARCHAR(255),
    tier_1_org VARCHAR(255),
    tier_2_org VARCHAR(255),
    tier_3_org VARCHAR(255),
    tier_4_org VARCHAR(255),
    tier_5_org VARCHAR(255),
    tier_6_org VARCHAR(255),
    create_time TIMESTAMP,
    create_by VARCHAR(255),
    update_time TIMESTAMP,
    update_by VARCHAR(255),
    manager_itcode VARCHAR(255),
    manager_name VARCHAR(255),
    email_option BOOLEAN DEFAULT true,
    ea_admin_status BOOLEAN DEFAULT false
);

-- Table: eam.eam_ea_calendar
CREATE TABLE IF NOT EXISTS eam.eam_ea_calendar (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255),
    schedule_no BIGINT NOT NULL DEFAULT nextval('eam_ea_calendar_schedule_no_seq'::regclass),
    schedule_title VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration SMALLINT,
    recurrence_pattern VARCHAR(255),
    end_after INTEGER,
    owner TEXT[],
    remark VARCHAR(255),
    status VARCHAR(255),
    for_project VARCHAR(255),
    for_meeting VARCHAR(255)
);

-- Table: eam.eam_email_log
CREATE TABLE IF NOT EXISTS eam.eam_email_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    module_code VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    trigger_event VARCHAR(255) NOT NULL,
    template_code VARCHAR(255) NOT NULL,
    template_tag VARCHAR(255) NOT NULL,
    mail_from VARCHAR(255) NOT NULL,
    mail_to TEXT NOT NULL,
    mail_cc TEXT,
    subject TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    send_status VARCHAR(255) NOT NULL,
    error_message TEXT,
    retry_of_log_id UUID,
    triggered_by VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Table: eam.eam_email_recipient
CREATE TABLE IF NOT EXISTS eam.eam_email_recipient (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    email_action VARCHAR(255),
    cc_pm BOOLEAN,
    cc_dt BOOLEAN,
    cc_it BOOLEAN,
    cc_ea_admin BOOLEAN,
    cc_big_ea BOOLEAN,
    cc_project_member BOOLEAN,
    cc_attendee BOOLEAN,
    cc_presenter BOOLEAN,
    cc_assignee BOOLEAN
);

-- Table: eam.eam_file_storage
CREATE TABLE IF NOT EXISTS eam.eam_file_storage (
    key TEXT NOT NULL,
    data BYTEA NOT NULL,
    content_type VARCHAR(255) DEFAULT 'application/octet-stream'::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.eam_meeting_deck
CREATE TABLE IF NOT EXISTS eam.eam_meeting_deck (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    meeting_id VARCHAR(255),
    deck_name VARCHAR(255),
    deck_url VARCHAR(255)
);

-- Table: eam.eam_meeting_minutes
CREATE TABLE IF NOT EXISTS eam.eam_meeting_minutes (
    id BIGINT NOT NULL DEFAULT nextval('eam_meeting_minutes_id_seq'::regclass),
    project_id VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_leader VARCHAR(255) NOT NULL,
    project_objectives TEXT NOT NULL,
    meeting_title VARCHAR(255) NOT NULL,
    review_date TIMESTAMP NOT NULL,
    presenter TEXT[] NOT NULL,
    attendees TEXT[] NOT NULL,
    meeting_agenda TEXT NOT NULL,
    key_agreement_findings TEXT NOT NULL,
    review_decks TEXT[] NOT NULL,
    review_recording TEXT[] NOT NULL
);

-- Table: eam.eam_meetings
CREATE TABLE IF NOT EXISTS eam.eam_meetings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    meeting_no BIGINT NOT NULL DEFAULT nextval('eam_meetings_meeting_no_seq'::regclass),
    project_id VARCHAR(255) NOT NULL,
    project_objectives TEXT,
    meeting_title VARCHAR(255) NOT NULL,
    available_ea_schedule VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    presenter TEXT[] NOT NULL,
    attendees TEXT[] NOT NULL,
    location VARCHAR(255),
    meeting_agenda TEXT NOT NULL,
    key_agreement_findings TEXT,
    review_decks TEXT[] NOT NULL,
    review_recording TEXT[] NOT NULL,
    status VARCHAR(255) NOT NULL,
    calendar_id VARCHAR(255),
    status_remark VARCHAR(255),
    ea_review_result VARCHAR(255),
    ea_review_remark VARCHAR(255),
    email_cc TEXT[],
    create_by VARCHAR(255),
    update_by VARCHAR(255),
    create_at TIMESTAMP,
    update_at TIMESTAMP,
    request_id VARCHAR(255)
);

-- Table: eam.eam_meetings_email_log
CREATE TABLE IF NOT EXISTS eam.eam_meetings_email_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    meeting_id UUID NOT NULL,
    log_time TIMESTAMP NOT NULL,
    from VARCHAR(255) NOT NULL,
    recipients TEXT[] NOT NULL,
    subject VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL
);

-- Table: eam.eam_project
CREATE TABLE IF NOT EXISTS eam.eam_project (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT ''::text,
    status VARCHAR(255) DEFAULT 'active'::character varying,
    owner_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    project_id VARCHAR(255),
    pm VARCHAR(255) DEFAULT ''::character varying,
    pm_itcode VARCHAR(255) DEFAULT ''::character varying,
    dt_lead VARCHAR(255) DEFAULT ''::character varying,
    dt_lead_itcode VARCHAR(255) DEFAULT ''::character varying,
    it_lead VARCHAR(255) DEFAULT ''::character varying,
    it_lead_itcode VARCHAR(255) DEFAULT ''::character varying,
    type VARCHAR(255) DEFAULT ''::character varying,
    start_date DATE,
    go_live_date DATE,
    duration INTEGER,
    objectives TEXT DEFAULT ''::text,
    ai_related VARCHAR(255) DEFAULT ''::character varying,
    comment TEXT DEFAULT ''::text,
    category VARCHAR(255) DEFAULT 'regular'::character varying
);

-- Table: eam.eam_project_app
CREATE TABLE IF NOT EXISTS eam.eam_project_app (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255) NOT NULL,
    app_name VARCHAR(255) DEFAULT ''::character varying,
    description TEXT DEFAULT ''::text,
    owner VARCHAR(255) DEFAULT ''::character varying,
    status VARCHAR(255) DEFAULT 'active'::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.eam_project_summary
CREATE TABLE IF NOT EXISTS eam.eam_project_summary (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    business_owner1 VARCHAR(255),
    business_owner2 VARCHAR(255),
    cost VARCHAR(255),
    schedule VARCHAR(255),
    function_summary VARCHAR(255),
    benefit VARCHAR(255),
    paint_point VARCHAR(255),
    application_list TEXT[],
    architect_summary VARCHAR(255),
    ea_status VARCHAR(255),
    status_remark VARCHAR(255),
    attachments TEXT[],
    ea_review_submitter VARCHAR(255),
    comments_app VARCHAR(255),
    ea_review_type VARCHAR(255),
    domain_ea_reviewer VARCHAR(255)
);

-- Table: eam.eam_request
CREATE TABLE IF NOT EXISTS eam.eam_request (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    review_scope VARCHAR(255),
    ws_phase_name VARCHAR(255),
    requester VARCHAR(255),
    status VARCHAR(255) NOT NULL,
    status_remark VARCHAR(255),
    status_changed_by VARCHAR(255),
    status_changed_at TIMESTAMP,
    link VARCHAR(255),
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    update_at TIMESTAMP,
    update_by VARCHAR(255),
    assign_reviewer TEXT[],
    review_result VARCHAR(255),
    process_id VARCHAR(255),
    organization VARCHAR(255),
    request_desc VARCHAR(255)
);

-- Table: eam.eam_request_attachment
CREATE TABLE IF NOT EXISTS eam.eam_request_attachment (
    request_id VARCHAR(255) NOT NULL,
    attachment_name VARCHAR(255),
    create_at TIMESTAMP,
    create_by VARCHAR(255),
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    biz_type VARCHAR(255),
    app_arch_type VARCHAR(255),
    original_name VARCHAR(255)
);

-- Table: eam.eam_request_process_log
CREATE TABLE IF NOT EXISTS eam.eam_request_process_log (
    request_id VARCHAR(255),
    action VARCHAR(255),
    comment VARCHAR(255),
    operator VARCHAR(255),
    create_at TIMESTAMP,
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid()
);

-- Table: eam.eam_review_log
CREATE TABLE IF NOT EXISTS eam.eam_review_log (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    comment VARCHAR(255),
    create_at TIMESTAMP DEFAULT now(),
    operator VARCHAR(255),
    operation VARCHAR(255),
    project_id VARCHAR(255)
);

-- Table: eam.eam_scope_check_list
CREATE TABLE IF NOT EXISTS eam.eam_scope_check_list (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    checklist_no SMALLINT NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    questions VARCHAR(255),
    answer VARCHAR(255),
    option VARCHAR(255),
    comment VARCHAR(255),
    link TEXT[],
    sub_category VARCHAR(255)
);

-- Table: eam.eam_scope_check_list_template
CREATE TABLE IF NOT EXISTS eam.eam_scope_check_list_template (
    checklist_no SMALLINT NOT NULL,
    category VARCHAR(255) NOT NULL,
    questions VARCHAR(255),
    answer VARCHAR(255),
    option VARCHAR(255),
    comment VARCHAR(255),
    link TEXT[],
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sub_category VARCHAR(255),
    answer_type VARCHAR(255),
    selection_type VARCHAR(255),
    selection_option TEXT[]
);

-- Table: eam.eam_scope_of_change
CREATE TABLE IF NOT EXISTS eam.eam_scope_of_change (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    scope_no BIGINT NOT NULL DEFAULT nextval('eam_scope_of_change_scope_no_seq'::regclass),
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    create_using_template VARCHAR(255) NOT NULL,
    sample VARCHAR(255) NOT NULL
);

-- Table: eam.eam_scope_of_change_pages
CREATE TABLE IF NOT EXISTS eam.eam_scope_of_change_pages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scope_of_change_id UUID NOT NULL,
    name VARCHAR(255),
    description VARCHAR(255),
    diagram TEXT
);

-- Table: eam.eam_scope_of_change_template
CREATE TABLE IF NOT EXISTS eam.eam_scope_of_change_template (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scope_no BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    create_using_template VARCHAR(255) NOT NULL,
    sample VARCHAR(255) NOT NULL
);

-- Table: eam.eam_team_member
CREATE TABLE IF NOT EXISTS eam.eam_team_member (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id UUID NOT NULL,
    user_itcode VARCHAR(255) NOT NULL,
    role VARCHAR(255) DEFAULT 'member'::character varying
);

-- Table: eam.email_notification_log
CREATE TABLE IF NOT EXISTS eam.email_notification_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    object_type VARCHAR(255) NOT NULL,
    object_id VARCHAR(255),
    object_business_id VARCHAR(255) NOT NULL,
    create_at TIMESTAMP NOT NULL,
    create_by VARCHAR(255) NOT NULL,
    email_from VARCHAR(255) NOT NULL,
    email_to TEXT[] NOT NULL,
    email_cc TEXT[] NOT NULL,
    subject VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    remark VARCHAR(255) NOT NULL
);

-- Table: eam.fiscal_year_sequences
CREATE TABLE IF NOT EXISTS eam.fiscal_year_sequences (
    sequence_name VARCHAR(255) NOT NULL,
    fiscal_year VARCHAR(255),
    current_value BIGINT NOT NULL
);

-- Table: eam.help_file
CREATE TABLE IF NOT EXISTS eam.help_file (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    usage VARCHAR(255) NOT NULL,
    file_name VARCHAR(255),
    file_path VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.local_users
CREATE TABLE IF NOT EXISTS eam.local_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    email VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    role VARCHAR(255) NOT NULL DEFAULT 'requestor'::character varying,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.process_role
CREATE TABLE IF NOT EXISTS eam.process_role (
    node_name VARCHAR(255),
    pre_status VARCHAR(255),
    role VARCHAR(255),
    process_id VARCHAR(255),
    description VARCHAR(255),
    order_no INTEGER,
    reminder_cycle INTEGER,
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY
);

-- Table: eam.project_app
CREATE TABLE IF NOT EXISTS eam.project_app (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    project_id VARCHAR(255),
    app_id VARCHAR(255) NOT NULL,
    app_name VARCHAR(255),
    app_full_name VARCHAR(255),
    app_it_owner VARCHAR(255),
    current_state VARCHAR(255),
    app_tech_id_in_cmdb VARCHAR(255),
    app_description VARCHAR(255),
    business_function VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.project_ea_status_log
CREATE TABLE IF NOT EXISTS eam.project_ea_status_log (
    project_id VARCHAR(255),
    ea_status VARCHAR(255),
    status_change_date DATE,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.project_task
CREATE TABLE IF NOT EXISTS eam.project_task (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    project_id VARCHAR(255) NOT NULL,
    project_name VARCHAR(255),
    task_name VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP,
    assignee VARCHAR(255),
    approval_status VARCHAR(255),
    task_status VARCHAR(255),
    approval_date VARCHAR(255),
    comment VARCHAR(255),
    description VARCHAR(255)
);

-- Table: eam.project_team_members
CREATE TABLE IF NOT EXISTS eam.project_team_members (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    project_id VARCHAR(255),
    itcode VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    worker_type VARCHAR(255),
    manager_itcode VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.project_user_bookmark
CREATE TABLE IF NOT EXISTS eam.project_user_bookmark (
    project_id VARCHAR(255) NOT NULL,
    user_itcode VARCHAR(255),
    favourite VARCHAR(255),
    default VARCHAR(255)
);

-- Table: eam.resource_pool
CREATE TABLE IF NOT EXISTS eam.resource_pool (
    worker VARCHAR(255),
    itcode VARCHAR(255) NOT NULL,
    worker_type VARCHAR(255),
    name VARCHAR(255),
    email VARCHAR(255),
    country VARCHAR(255),
    location VARCHAR(255),
    primary_skill VARCHAR(255),
    skill_level VARCHAR(255),
    job_role VARCHAR(255),
    rate NUMERIC,
    track_focal VARCHAR(255),
    manager_level_1 VARCHAR(255),
    manager_level_2 VARCHAR(255),
    manager_level_3 VARCHAR(255),
    manager_level_4 VARCHAR(255),
    manager_level_5 VARCHAR(255),
    manager_level_6 VARCHAR(255),
    manager_level_7 VARCHAR(255),
    manager_level_8 VARCHAR(255),
    manager_level_9 VARCHAR(255),
    tier_1_org VARCHAR(255),
    tier_2_org VARCHAR(255),
    tier_3_org VARCHAR(255),
    tier_4_org VARCHAR(255),
    tier_5_org VARCHAR(255),
    tier_6_org VARCHAR(255),
    create_time TIMESTAMP DEFAULT now(),
    create_by VARCHAR(255),
    update_time TIMESTAMP DEFAULT now(),
    update_by VARCHAR(255),
    manager_itcode VARCHAR(255),
    manager_name VARCHAR(255),
    email_option BOOLEAN
);

-- Table: eam.resource_pool_extend
CREATE TABLE IF NOT EXISTS eam.resource_pool_extend (
    worker VARCHAR(255),
    itcode VARCHAR(255) NOT NULL,
    worker_type VARCHAR(255),
    name VARCHAR(255),
    email VARCHAR(255),
    country VARCHAR(255),
    location VARCHAR(255),
    primary_skill VARCHAR(255),
    skill_level VARCHAR(255),
    job_role VARCHAR(255),
    rate NUMERIC,
    track_focal VARCHAR(255),
    manager_level_1 VARCHAR(255),
    manager_level_2 VARCHAR(255),
    manager_level_3 VARCHAR(255),
    manager_level_4 VARCHAR(255),
    manager_level_5 VARCHAR(255),
    manager_level_6 VARCHAR(255),
    manager_level_7 VARCHAR(255),
    manager_level_8 VARCHAR(255),
    manager_level_9 VARCHAR(255),
    tier_1_org VARCHAR(255),
    tier_2_org VARCHAR(255),
    tier_3_org VARCHAR(255),
    tier_4_org VARCHAR(255),
    tier_5_org VARCHAR(255),
    tier_6_org VARCHAR(255),
    create_time TIMESTAMP DEFAULT now(),
    create_by VARCHAR(255),
    update_time TIMESTAMP,
    update_by VARCHAR(255),
    manager_itcode VARCHAR(255),
    manager_name VARCHAR(255),
    email_option BOOLEAN
);

-- Table: eam.schema_migrations
CREATE TABLE IF NOT EXISTS eam.schema_migrations (
    id INTEGER NOT NULL DEFAULT nextval('schema_migrations_id_seq'::regclass),
    filename VARCHAR(255) NOT NULL,
    hash VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Table: eam.smart_agent
CREATE TABLE IF NOT EXISTS eam.smart_agent (
    itcode VARCHAR(255)
);

-- Table: eam.sys_log
CREATE TABLE IF NOT EXISTS eam.sys_log (
    id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid(),
    log_content JSON,
    create_at TIMESTAMP,
    user VARCHAR(255),
    action VARCHAR(255),
    object VARCHAR(255)
);

-- Table: eam.tech_key_stack_auto_checking_log
CREATE TABLE IF NOT EXISTS eam.tech_key_stack_auto_checking_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    update_time TIMESTAMP NOT NULL,
    last_update_time TIMESTAMP NOT NULL,
    old_content JSONB,
    new_content JSONB,
    app_id VARCHAR(255),
    create_by VARCHAR(255) NOT NULL
);

-- Table: eam.tech_key_stack_item
CREATE TABLE IF NOT EXISTS eam.tech_key_stack_item (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    stack_id VARCHAR(255) NOT NULL DEFAULT lpad((nextval('tech_key_stack_item_seq'::regclass))::text, 7, '0'::text),
    app_id VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    component VARCHAR(255) NOT NULL,
    use_status VARCHAR(255),
    sub_category VARCHAR(255) NOT NULL,
    major_version INTEGER NOT NULL,
    minor_version VARCHAR(255) NOT NULL,
    patch_version VARCHAR(255),
    eol_date DATE,
    eol_interval_time VARCHAR(255),
    maintainability_risk_level VARCHAR(255),
    maintainability_risk_light VARCHAR(255),
    standard VARCHAR(255),
    status_comments VARCHAR(255),
    remark VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP,
    component_package VARCHAR(255) NOT NULL,
    security_risk_level VARCHAR(255),
    security_risk_light VARCHAR(255),
    master_no INTEGER,
    cvss_v3_score NUMERIC,
    ea_advice VARCHAR(255),
    security_advice VARCHAR(255)
);

-- Table: eam.tech_stack_app
CREATE TABLE IF NOT EXISTS eam.tech_stack_app (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255) NOT NULL,
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.tech_stack_category
CREATE TABLE IF NOT EXISTS eam.tech_stack_category (
    id INTEGER NOT NULL DEFAULT nextval('tech_stack_category_id_seq'::regclass),
    category_code VARCHAR(255) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    parent_category VARCHAR(255) NOT NULL DEFAULT 'root'::character varying,
    level SMALLINT NOT NULL,
    create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying
);

-- Table: eam.tech_stack_component
CREATE TABLE IF NOT EXISTS eam.tech_stack_component (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    stack_id VARCHAR(255) DEFAULT lpad((nextval('tech_stack_component_seq'::regclass))::text, 6, '0'::text),
    dependency_id UUID NOT NULL,
    remark VARCHAR(255),
    category VARCHAR(255),
    group_id VARCHAR(255),
    component_package VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    specifier VARCHAR(255),
    type VARCHAR(255),
    scope VARCHAR(255),
    source VARCHAR(255),
    inherited BOOLEAN,
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.tech_stack_dependency
CREATE TABLE IF NOT EXISTS eam.tech_stack_dependency (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255) NOT NULL,
    devops_link VARCHAR(255) NOT NULL,
    devops_project VARCHAR(255) NOT NULL,
    pipline_name VARCHAR(255) NOT NULL,
    package_type VARCHAR(255) NOT NULL,
    remark VARCHAR(255),
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.tech_stack_dependency_file
CREATE TABLE IF NOT EXISTS eam.tech_stack_dependency_file (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255) NOT NULL,
    dependency_id UUID NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    file_content TEXT NOT NULL,
    mime_type VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP
);

-- Table: eam.tech_stack_item
CREATE TABLE IF NOT EXISTS eam.tech_stack_item (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    stack_id VARCHAR(255) DEFAULT lpad((nextval('tech_stack_item_seq'::regclass))::text, 6, '0'::text),
    app_id VARCHAR(255) NOT NULL,
    devops_link VARCHAR(255) NOT NULL,
    devops_project VARCHAR(255) NOT NULL,
    pipline_name VARCHAR(255) NOT NULL,
    package_type VARCHAR(255) NOT NULL,
    remark VARCHAR(255),
    category VARCHAR(255),
    group_id VARCHAR(255),
    component_package VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    type VARCHAR(255),
    scope VARCHAR(255),
    source VARCHAR(255),
    inherited BOOLEAN,
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP,
    specifier VARCHAR(255)
);

-- Table: eam.tech_stack_lifecyle
CREATE TABLE IF NOT EXISTS eam.tech_stack_lifecyle (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255) NOT NULL,
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.tech_stack_master_data
CREATE TABLE IF NOT EXISTS eam.tech_stack_master_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    master_no INTEGER NOT NULL,
    category VARCHAR(255) NOT NULL,
    component VARCHAR(255) NOT NULL,
    component_package VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    ea_advice VARCHAR(255) NOT NULL,
    remark VARCHAR(255),
    initial_release_date DATE,
    final_release_date DATE,
    security_vulnerability VARCHAR(255),
    security_serverity VARCHAR(255),
    cvss_v3_score NUMERIC,
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP,
    eol_link VARCHAR(255),
    sub_category VARCHAR(255),
    standard VARCHAR(255),
    major_version INTEGER,
    minor_version VARCHAR(255),
    patch_version VARCHAR(255),
    eol_date DATE,
    security_advice VARCHAR(255),
    vulnerability_link VARCHAR(255),
    restricted VARCHAR(255),
    source_type VARCHAR(255),
    source VARCHAR(255)
);

-- Table: eam.tech_stack_operate_log
CREATE TABLE IF NOT EXISTS eam.tech_stack_operate_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    app_id VARCHAR(255),
    stack_id VARCHAR(255),
    field VARCHAR(255),
    old_value TEXT,
    new_value TEXT,
    create_by VARCHAR(255),
    create_at TIMESTAMP DEFAULT now()
);

-- Table: eam.tech_stack_standard
CREATE TABLE IF NOT EXISTS eam.tech_stack_standard (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tech_layer VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    component_group VARCHAR(255),
    component_name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    license VARCHAR(255),
    internal_effective_version VARCHAR(255),
    latest_version VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.tech_stack_template
CREATE TABLE IF NOT EXISTS eam.tech_stack_template (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    template_no INTEGER NOT NULL DEFAULT nextval('tech_stack_template_template_no_seq'::regclass),
    standard_uuid UUID,
    status VARCHAR(255),
    create_by VARCHAR(255),
    create_at TIMESTAMP,
    update_by VARCHAR(255),
    update_at TIMESTAMP
);

-- Table: eam.user_profile
CREATE TABLE IF NOT EXISTS eam.user_profile (
    itcode VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    country VARCHAR(255),
    manager_itcode VARCHAR(255),
    manager_name VARCHAR(255),
    tier_1_org VARCHAR(255),
    tier_2_org VARCHAR(255),
    tier_3_org VARCHAR(255),
    tier_4_org VARCHAR(255),
    tier_5_org VARCHAR(255),
    tier_6_org VARCHAR(255),
    create_time TIMESTAMP DEFAULT now()
);

-- Table: eam.v_user_role_scope
CREATE TABLE IF NOT EXISTS eam.v_user_role_scope (
    itcode TEXT,
    role TEXT
);
