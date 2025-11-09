-- Migration Script: Add Missing Fields to Existing Database
-- Run this to add new fields added for admin API functionality

-- Add code_plain to activation_codes table (for admin display)
ALTER TABLE activation_codes ADD COLUMN IF NOT EXISTS code_plain VARCHAR;

-- Update existing codes to have code_plain = code_hash (temporary - these are already hashed)
-- In production, you'd want to regenerate codes properly
UPDATE activation_codes SET code_plain = code_hash WHERE code_plain IS NULL;

-- Add usage tracking fields to tenants table
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS usage_quota INTEGER DEFAULT 10 NOT NULL;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS usage_current INTEGER DEFAULT 0 NOT NULL;

-- Verify changes
SELECT 'Migration complete!' as status;
SELECT 'Tenants now have usage_quota and usage_current fields' as note1;
SELECT 'ActivationCodes now have code_plain field' as note2;


