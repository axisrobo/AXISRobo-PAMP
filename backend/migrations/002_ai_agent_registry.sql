-- Agent Registration & Governance (design-time governed-element registry)
-- NOTE: This is governance registration, NOT runtime Agent identity (SPIFFE/SVID/ANS).
-- Maps to roadmap v2.0 "Architecture Element Registry" (AI-agent slice).

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

CREATE INDEX IF NOT EXISTS idx_ai_agent_registry_status ON eam.ai_agent_registry (status);
CREATE INDEX IF NOT EXISTS idx_ai_agent_registry_model_id_ref ON eam.ai_agent_registry (model_id_ref);
