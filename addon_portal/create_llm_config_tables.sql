-- LLM Configuration Tables Migration
-- Enables scalable multi-host deployments with centralized configuration
-- Run this to migrate from file-based to database-backed configuration

-- System Configuration Table (Singleton)
CREATE TABLE IF NOT EXISTS llm_system_config (
    id INTEGER PRIMARY KEY DEFAULT 1,
    
    -- Provider configuration
    primary_provider VARCHAR(50) DEFAULT 'gemini',
    secondary_provider VARCHAR(50) DEFAULT 'openai',
    tertiary_provider VARCHAR(50) DEFAULT 'anthropic',
    
    -- Model selection
    gemini_model VARCHAR(100) DEFAULT 'gemini-1.5-pro',
    openai_model VARCHAR(100) DEFAULT 'gpt-4-turbo-preview',
    anthropic_model VARCHAR(100) DEFAULT 'claude-3-5-sonnet-20241022',
    
    -- Generation parameters
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    retries_per_provider INTEGER DEFAULT 3,
    
    -- Budget controls
    monthly_budget FLOAT DEFAULT 1000.0,
    daily_budget FLOAT DEFAULT 50.0,
    
    -- Prompts
    system_prompt TEXT,
    
    -- Feature flags
    use_llm BOOLEAN DEFAULT TRUE,
    template_learning_enabled BOOLEAN DEFAULT TRUE,
    cross_validation_enabled BOOLEAN DEFAULT TRUE,
    cache_enabled BOOLEAN DEFAULT TRUE,
    
    -- Quality thresholds
    min_quality_score INTEGER DEFAULT 95,
    template_min_quality INTEGER DEFAULT 90,
    
    -- Metadata
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    version INTEGER DEFAULT 1,
    
    -- Ensure only one record
    CONSTRAINT single_system_config CHECK (id = 1)
);

-- Project Configuration Table
CREATE TABLE IF NOT EXISTS llm_project_config (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Project information
    client_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- LLM provider overrides
    provider_override VARCHAR(50),
    model_override VARCHAR(100),
    
    -- Generation parameter overrides
    temperature_override FLOAT,
    max_tokens_override INTEGER,
    
    -- Budget allocation
    monthly_budget_override FLOAT,
    
    -- Custom prompts
    custom_instructions TEXT,
    
    -- Project status
    is_active BOOLEAN DEFAULT TRUE,
    priority VARCHAR(20) DEFAULT 'normal',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Agent Configuration Table (Per Project)
CREATE TABLE IF NOT EXISTS llm_agent_config (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES llm_project_config(project_id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    
    -- Agent-specific overrides
    provider_override VARCHAR(50),
    model_override VARCHAR(100),
    temperature_override FLOAT,
    max_tokens_override INTEGER,
    
    -- Agent-specific prompts
    custom_prompt TEXT,
    custom_instructions TEXT,
    
    -- Agent settings
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(project_id, agent_type)
);

-- Configuration History Table (Audit Trail)
CREATE TABLE IF NOT EXISTS llm_config_history (
    id SERIAL PRIMARY KEY,
    
    -- What was changed
    config_type VARCHAR(50) NOT NULL,
    config_id VARCHAR(100) NOT NULL,
    
    -- Change details
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    
    -- Who and when
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_project_client ON llm_project_config(client_name);
CREATE INDEX IF NOT EXISTS idx_project_active ON llm_project_config(is_active);
CREATE INDEX IF NOT EXISTS idx_agent_project ON llm_agent_config(project_id, agent_type);
CREATE INDEX IF NOT EXISTS idx_history_config ON llm_config_history(config_type, config_id);
CREATE INDEX IF NOT EXISTS idx_history_time ON llm_config_history(changed_at);

-- Insert default system configuration
INSERT INTO llm_system_config (id, system_prompt) 
VALUES (1, 'You are an expert software developer. Generate production-ready code following best practices.')
ON CONFLICT (id) DO NOTHING;

-- Comments
COMMENT ON TABLE llm_system_config IS 'System-level LLM configuration (singleton, shared across all hosts)';
COMMENT ON TABLE llm_project_config IS 'Per-project LLM configuration for client-specific customization';
COMMENT ON TABLE llm_agent_config IS 'Per-agent configuration within each project';
COMMENT ON TABLE llm_config_history IS 'Audit trail for configuration changes';

-- Grant permissions (adjust based on your setup)
-- GRANT ALL ON llm_system_config TO q2o_user;
-- GRANT ALL ON llm_project_config TO q2o_user;
-- GRANT ALL ON llm_agent_config TO q2o_user;
-- GRANT ALL ON llm_config_history TO q2o_user;
-- GRANT USAGE, SELECT ON SEQUENCE llm_project_config_id_seq TO q2o_user;
-- GRANT USAGE, SELECT ON SEQUENCE llm_agent_config_id_seq TO q2o_user;
-- GRANT USAGE, SELECT ON SEQUENCE llm_config_history_id_seq TO q2o_user;
