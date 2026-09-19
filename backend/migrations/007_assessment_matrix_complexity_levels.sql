-- Assessment-matrix questions (RCP/SCP/PRS, stable ids 55-69) previously used
-- placeholder Yes/No options (Yes=3, No=0). They are complexity drivers used to
-- derive project complexity, so they get four graded levels instead. Their
-- concern mappings are removed separately by the canonical AVDM config.

DO $$
DECLARE
    target UUID;
BEGIN
    FOR target IN
        SELECT DISTINCT option_set_id
        FROM pamp.avdm_question
        WHERE stable_question_id BETWEEN 55 AND 69
          AND option_set_id IS NOT NULL
    LOOP
        DELETE FROM pamp.avdm_question_option_item WHERE option_set_id = target;
        INSERT INTO pamp.avdm_question_option_item
            (option_set_id, option_value, option_label, option_score,
             sort_order, is_active, create_by, update_by, create_at, update_at)
        VALUES
            (target, 'None',   'None',   0, 10, TRUE, 'avdm_seed_v3', 'avdm_seed_v3', now(), now()),
            (target, 'Low',    'Low',    2, 20, TRUE, 'avdm_seed_v3', 'avdm_seed_v3', now(), now()),
            (target, 'Medium', 'Medium', 4, 30, TRUE, 'avdm_seed_v3', 'avdm_seed_v3', now(), now()),
            (target, 'High',   'High',   6, 40, TRUE, 'avdm_seed_v3', 'avdm_seed_v3', now(), now());
    END LOOP;
END
$$;
