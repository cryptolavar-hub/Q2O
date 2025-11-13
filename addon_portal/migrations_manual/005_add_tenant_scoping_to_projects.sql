-- Migration: Add tenant scoping to projects and tenant sessions
-- Date: November 12, 2025
-- Purpose: Link projects to tenants and enable tenant authentication

-- Add tenant_id to llm_project_config (nullable initially for backward compatibility)
ALTER TABLE llm_project_config 
ADD COLUMN IF NOT EXISTS tenant_id INTEGER NULL;

-- Add foreign key constraint (only if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_project_tenant'
    ) THEN
        ALTER TABLE llm_project_config 
        ADD CONSTRAINT fk_project_tenant 
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create index for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_project_tenant ON llm_project_config(tenant_id);

-- Add project status fields
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS project_status VARCHAR(20) DEFAULT 'active';

ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE NULL;

ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE NULL;

-- Add activation_code_id to track which code was used to activate this project
-- One code = one project activation (codes are consumed)
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS activation_code_id INTEGER NULL;

-- Add foreign key constraint for activation_code_id (only if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_project_activation_code'
    ) THEN
        ALTER TABLE llm_project_config
        ADD CONSTRAINT fk_project_activation_code
        FOREIGN KEY (activation_code_id) REFERENCES activation_codes(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_project_activation_code ON llm_project_config(activation_code_id);

-- Create tenant_sessions table for OTP authentication and session management
CREATE TABLE IF NOT EXISTS tenant_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    otp_code VARCHAR(6),
    otp_expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for tenant_sessions
CREATE INDEX IF NOT EXISTS idx_session_token ON tenant_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_tenant_sessions ON tenant_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_session_expires ON tenant_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_session_otp ON tenant_sessions(otp_code, otp_expires_at) WHERE otp_code IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN llm_project_config.tenant_id IS 'Tenant that owns this project. NULL = admin-only access.';
COMMENT ON COLUMN llm_project_config.project_status IS 'Project status: active, pending, completed, paused';
COMMENT ON TABLE tenant_sessions IS 'OTP authentication and session management for tenant dashboard access';

