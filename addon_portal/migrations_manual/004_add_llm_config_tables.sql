-- Migration: Add LLM configuration tables
-- Date: November 11, 2025
-- Purpose: Store system, project, and agent-level LLM prompts and configuration

-- System-level LLM configuration (singleton)
CREATE TABLE IF NOT EXISTS llm_system_config (
    id SERIAL PRIMARY KEY,
    primary_provider VARCHAR(50) DEFAULT 'gemini',
    secondary_provider VARCHAR(50) DEFAULT 'openai',
    tertiary_provider VARCHAR(50) DEFAULT 'anthropic',
    gemini_model VARCHAR(100) DEFAULT 'gemini-1.5-pro',
    openai_model VARCHAR(100) DEFAULT 'gpt-4-turbo-preview',
    anthropic_model VARCHAR(100) DEFAULT 'claude-3-5-sonnet-20241022',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    retries_per_provider INTEGER DEFAULT 3,
    monthly_budget FLOAT DEFAULT 1000.0,
    daily_budget FLOAT DEFAULT 50.0,
    system_prompt TEXT,
    use_llm BOOLEAN DEFAULT TRUE,
    template_learning_enabled BOOLEAN DEFAULT TRUE,
    cross_validation_enabled BOOLEAN DEFAULT TRUE,
    cache_enabled BOOLEAN DEFAULT TRUE,
    min_quality_score INTEGER DEFAULT 95,
    template_min_quality INTEGER DEFAULT 90,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    version INTEGER DEFAULT 1
);

-- Project-level configuration
CREATE TABLE IF NOT EXISTS llm_project_config (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    description TEXT,
    provider_override VARCHAR(50),
    model_override VARCHAR(100),
    temperature_override FLOAT,
    max_tokens_override INTEGER,
    monthly_budget_override FLOAT,
    custom_instructions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    priority VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_project_client ON llm_project_config(client_name);
CREATE INDEX IF NOT EXISTS idx_project_active ON llm_project_config(is_active);

-- Agent-level configuration per project
CREATE TABLE IF NOT EXISTS llm_agent_config (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) REFERENCES llm_project_config(project_id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    provider_override VARCHAR(50),
    model_override VARCHAR(100),
    temperature_override FLOAT,
    max_tokens_override INTEGER,
    custom_prompt TEXT,
    custom_instructions TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_agent_project ON llm_agent_config(project_id, agent_type);

-- Configuration history/audit trail
CREATE TABLE IF NOT EXISTS llm_config_history (
    id SERIAL PRIMARY KEY,
    config_type VARCHAR(50),
    config_id VARCHAR(100),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_history_config ON llm_config_history(config_type, config_id);
CREATE INDEX IF NOT EXISTS idx_history_time ON llm_config_history(changed_at);

-- Insert default system configuration
INSERT INTO llm_system_config (id) VALUES (1) ON CONFLICT DO NOTHING;

COMMENT ON TABLE llm_system_config IS 'Singleton system-level LLM configuration';
COMMENT ON TABLE llm_project_config IS 'Per-project LLM configuration and prompts';
COMMENT ON TABLE llm_agent_config IS 'Per-agent configuration within projects';
COMMENT ON TABLE llm_config_history IS 'Audit trail for configuration changes';

