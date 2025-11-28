-- Migration: Add show_completion_modal field to llm_project_config
-- Date: November 28, 2025
-- Purpose: Store user preference for showing completion modal per project

-- Add show_completion_modal column (default TRUE/1 = show modal)
ALTER TABLE llm_project_config
ADD COLUMN IF NOT EXISTS show_completion_modal BOOLEAN DEFAULT TRUE;

-- Add comment for documentation
COMMENT ON COLUMN llm_project_config.show_completion_modal IS 'User preference for showing completion modal: TRUE (1) = show modal, FALSE (0) = hide modal. Default is TRUE.';

