-- AVDM master-data upsert uniqueness
--
-- Several repository methods upsert with ON CONFLICT (natural key) but the
-- schema snapshot did not create the required unique indexes, so every save of
-- questionnaire config, concern mapping config, or the concern catalog failed
-- with "no unique or exclusion constraint matching the ON CONFLICT
-- specification" (for example avdm_master_data_revision.domain_key).
--
-- This migration creates the missing indexes idempotently. The same indexes are
-- declared in docs/SQL/pamp_schema_ddl.sql for fresh installs. It only acts on
-- tables that already exist, so it is harmless when it runs before the DDL.

DO $$
DECLARE
    target RECORD;
BEGIN
    FOR target IN
        SELECT * FROM (VALUES
            ('avdm_master_data_revision', 'domain_key'),
            ('avdm_question_group', 'group_key'),
            ('avdm_question_answer_type', 'answer_type_key'),
            ('avdm_question_option_set', 'option_set_key'),
            ('avdm_question_option_item', 'option_set_id, option_value'),
            ('avdm_question_category', 'category_key'),
            ('avdm_question', 'stable_question_id'),
            ('avdm_project_type_profile', 'project_type_key'),
            ('avdm_project_type_artifact_mapping', 'project_type_profile_id, artifact_id'),
            ('avdm_artifact_category', 'category_key'),
            ('avdm_artifact', 'artifact_key'),
            ('avdm_viewpoint', 'viewpoint_number'),
            ('avdm_viewpoint_concern_mapping', 'viewpoint_id, concern_id'),
            ('avdm_viewpoint_artifact_mapping', 'viewpoint_id, artifact_id, recommendation_status')
        ) AS t(table_name, columns)
    LOOP
        IF to_regclass('pamp.' || target.table_name) IS NOT NULL THEN
            EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS uq_' || target.table_name || '_'
                || replace(target.columns, ', ', '_')
                || ' ON pamp.' || target.table_name || ' (' || target.columns || ')';
        END IF;
    END LOOP;
END
$$;
