-- AI Model Registry with version & provenance tracking
-- Roadmap: AI Management -> "AI model registry with version and provenance tracking"

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

CREATE INDEX IF NOT EXISTS idx_ai_model_version_model_id ON eam.ai_model_version (model_id);
CREATE INDEX IF NOT EXISTS idx_ai_model_registry_status ON eam.ai_model_registry (status);
