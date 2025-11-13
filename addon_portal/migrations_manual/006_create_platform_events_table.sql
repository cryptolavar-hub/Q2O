-- Migration 006: Create Platform Events Table
-- Purpose: Database-backed event logging for all platform activities
-- Date: November 12, 2025

-- Create platform_events table for event logging
CREATE TABLE IF NOT EXISTS platform_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('major', 'minor')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    actor_type VARCHAR(50),
    actor_id INTEGER,
    actor_name VARCHAR(255),
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL,
    project_id VARCHAR(100),
    code_id INTEGER REFERENCES activation_codes(id) ON DELETE SET NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    event_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_event_type ON platform_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON platform_events(severity);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON platform_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_tenant_id ON platform_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_events_project_id ON platform_events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_tenant_type ON platform_events(tenant_id, event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity_type ON platform_events(severity, event_type);

-- Add comments for documentation
COMMENT ON TABLE platform_events IS 'Platform event log for tracking all activities (Major and Minor events)';
COMMENT ON COLUMN platform_events.event_type IS 'Type of event (tenant_created, code_generated, etc.)';
COMMENT ON COLUMN platform_events.severity IS 'Event severity: major (important changes) or minor (routine activities)';
COMMENT ON COLUMN platform_events.event_metadata IS 'Additional event data in JSON format (renamed from metadata to avoid SQLAlchemy reserved name)';

