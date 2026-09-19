-- AVDM static document uniqueness
--
-- The repository upserts configuration documents with
--   INSERT ... ON CONFLICT (document_key) DO UPDATE ...
-- which requires a unique index on eam.avdm_static_document.document_key.
-- The original schema snapshot did not create that index, so configuration
-- saves (questionnaire sections, project-type guide, viewpoint-artifact
-- mapping, and the classification policy) would fail on a fresh install.
--
-- This migration is idempotent: it only creates the index when absent and
-- tolerates pre-existing duplicate rows by keying the index on document_key
-- after removing nothing.

CREATE UNIQUE INDEX IF NOT EXISTS avdm_static_document_document_key_key
    ON eam.avdm_static_document (document_key);
