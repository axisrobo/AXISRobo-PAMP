-- Align persisted AVDM data with the published 0-5 contribution contract and
-- the 0.90/0.50 reference classification policy.
--
-- NOTE: this file is executed through SQLAlchemy text(), so it must not contain
-- a bare ":<name>" sequence inside string literals. The policy object is built
-- with jsonb_build_object() instead of a JSON literal for that reason.
DO $$
BEGIN
    IF to_regclass('pamp.avdm_question_answer_concern_mapping') IS NOT NULL THEN
        UPDATE pamp.avdm_question_answer_concern_mapping
        SET mapping_score = LEAST(5, GREATEST(0, mapping_score));
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_avdm_question_mapping_score_0_5'
        ) THEN
            ALTER TABLE pamp.avdm_question_answer_concern_mapping
                ADD CONSTRAINT ck_avdm_question_mapping_score_0_5
                CHECK (mapping_score >= 0 AND mapping_score <= 5);
        END IF;
    END IF;

    IF to_regclass('pamp.avdm_concern_activation_rule_score') IS NOT NULL THEN
        UPDATE pamp.avdm_concern_activation_rule_score
        SET mapping_score = LEAST(5, GREATEST(0, mapping_score));
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_avdm_rule_score_0_5'
        ) THEN
            ALTER TABLE pamp.avdm_concern_activation_rule_score
                ADD CONSTRAINT ck_avdm_rule_score_0_5
                CHECK (mapping_score >= 0 AND mapping_score <= 5);
        END IF;
    END IF;

    IF to_regclass('pamp.avdm_static_document') IS NOT NULL THEN
        INSERT INTO pamp.avdm_static_document
            (document_key, document_json, create_by, update_by, create_at, update_at)
        VALUES (
            'classification_policy',
            jsonb_build_object(
                'mandatoryThreshold', 0.90,
                'recommendedThreshold', 0.50,
                'complexityCoefficient', 0.15,
                'maxMandatoryCount', NULL,
                'maxMandatoryRatio', NULL,
                'topNPriorityBudget', NULL,
                'tieBreakStrategy', 'score_then_key'
            ),
            'migration_008', 'migration_008', now(), now()
        )
        ON CONFLICT (document_key) DO UPDATE
        SET document_json = jsonb_set(
                jsonb_set(
                    pamp.avdm_static_document.document_json,
                    '{mandatoryThreshold}',
                    CASE
                        WHEN COALESCE(
                                 jsonb_typeof(pamp.avdm_static_document.document_json -> 'mandatoryThreshold'),
                                 'missing'
                             ) <> 'number'
                          OR (pamp.avdm_static_document.document_json ->> 'mandatoryThreshold')::numeric = 0.66
                        THEN '0.9'::jsonb
                        ELSE pamp.avdm_static_document.document_json -> 'mandatoryThreshold'
                    END
                ),
                '{recommendedThreshold}',
                CASE
                    WHEN COALESCE(
                             jsonb_typeof(pamp.avdm_static_document.document_json -> 'recommendedThreshold'),
                             'missing'
                         ) <> 'number'
                      OR (pamp.avdm_static_document.document_json ->> 'recommendedThreshold')::numeric = 0.38
                    THEN '0.5'::jsonb
                    ELSE pamp.avdm_static_document.document_json -> 'recommendedThreshold'
                END
            ),
            update_by = 'migration_008',
            update_at = now();
    END IF;
END
$$;
