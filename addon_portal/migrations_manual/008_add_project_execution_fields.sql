-- Migration 008: Add project execution tracking fields
-- Date: November 19, 2025
-- Purpose: Track project execution status, timing, errors, and output folder paths

-- Add execution status tracking
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS execution_status VARCHAR(20) DEFAULT 'pending';

-- Add execution timing fields
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS execution_started_at TIMESTAMP NULL;

ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS execution_completed_at TIMESTAMP NULL;

-- Add execution error tracking
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS execution_error TEXT NULL;

-- Add output folder path
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS output_folder_path VARCHAR(500) NULL;

-- Add indexes for faster queries
CREATE INDEX IF NOT EXISTS ix_llm_projects_execution_status 
ON llm_project_config(execution_status);

CREATE INDEX IF NOT EXISTS ix_llm_projects_activation_code 
ON llm_project_config(activation_code_id);

CREATE INDEX IF NOT EXISTS ix_llm_projects_execution_started 
ON llm_project_config(execution_started_at);

-- Add check constraint for execution_status (PostgreSQL doesn't support IF NOT EXISTS for constraints)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_execution_status' 
        AND conrelid = 'llm_project_config'::regclass
    ) THEN
        ALTER TABLE llm_project_config
        ADD CONSTRAINT chk_execution_status 
        CHECK (execution_status IN ('pending', 'running', 'completed', 'failed', 'paused'));
    END IF;
END $$;

-- Update existing projects to have 'pending' status if NULL
UPDATE llm_project_config
SET execution_status = 'pending'
WHERE execution_status IS NULL;

-- Log migration completion
-- Note: alembic_version table may not exist, so we'll use a comment instead
-- INSERT INTO alembic_version (version_num) VALUES ('008_add_project_execution_fields') ON CONFLICT (version_num) DO NOTHING;

