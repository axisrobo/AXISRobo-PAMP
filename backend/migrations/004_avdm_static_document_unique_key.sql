-- AVDM static document uniqueness
--
-- The repository upserts configuration documents with
--   INSERT ... ON CONFLICT (document_key) DO UPDATE ...
-- which requires a unique index on pamp.avdm_static_document.document_key.
-- The original schema snapshot did not create that index, so configuration
-- saves (questionnaire sections, project-type guide, viewpoint-artifact
-- mapping, and the classification policy) would fail on an existing install.
--
-- The index is also declared in docs/SQL/pamp_schema_ddl.sql for fresh
-- installs. This migration only acts when the table already exists, so it is
-- harmless when migrations run before the DDL is loaded.

DO $$
BEGIN
    IF to_regclass('pamp.avdm_static_document') IS NOT NULL THEN
        EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS '
             || 'avdm_static_document_document_key_key '
             || 'ON pamp.avdm_static_document (document_key)';
    END IF;
END
$$;
