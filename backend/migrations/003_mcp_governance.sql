-- MCP Server & Tool Governance (registration, approval, provenance)
-- Roadmap: AI Management -> "MCP server and tool governance (registration, approval, provenance)"

CREATE TABLE IF NOT EXISTS eam.mcp_server_registry (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    server_key VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT ''::text,
    owner VARCHAR(255) DEFAULT ''::character varying,
    provider VARCHAR(255) DEFAULT ''::character varying,
    transport VARCHAR(255) NOT NULL DEFAULT 'stdio'::character varying,
    endpoint_uri TEXT DEFAULT ''::text,
    auth_method VARCHAR(255) NOT NULL DEFAULT 'none'::character varying,
    provenance_source VARCHAR(255) DEFAULT ''::character varying,
    provenance_uri TEXT DEFAULT ''::text,
    scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(255) NOT NULL DEFAULT 'draft'::character varying,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eam.mcp_tool (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    server_id UUID NOT NULL REFERENCES eam.mcp_server_registry(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT ''::text,
    description_hash VARCHAR(255) DEFAULT ''::character varying,
    signature VARCHAR(255) DEFAULT ''::character varying,
    risk_level VARCHAR(255) NOT NULL DEFAULT 'low'::character varying,
    approval_status VARCHAR(255) NOT NULL DEFAULT 'pending'::character varying,
    lifecycle_stage VARCHAR(255) NOT NULL DEFAULT 'sandbox'::character varying,
    notes TEXT DEFAULT ''::text,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT ''::character varying,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (server_id, tool_name)
);

CREATE INDEX IF NOT EXISTS idx_mcp_tool_server_id ON eam.mcp_tool (server_id);
CREATE INDEX IF NOT EXISTS idx_mcp_server_registry_status ON eam.mcp_server_registry (status);
