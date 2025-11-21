-- Migration 009: Create Agent Tasks Tracking Table
-- Purpose: Dedicated table for tracking agent tasks and calculating real project progress
-- Date: November 20, 2025
--
-- This table stores all tasks assigned to agents, their status, and completion details.
-- Agents will update this table when they receive, start, and complete tasks.
-- This enables real progress calculation based on actual task completion.

-- Create agent_tasks table
CREATE TABLE IF NOT EXISTS agent_tasks (
    id SERIAL PRIMARY KEY,
    
    -- Task identification
    task_id VARCHAR(100) UNIQUE NOT NULL,  -- Unique task identifier (e.g., "task-{project_id}-{agent_type}-{sequence}")
    project_id VARCHAR(100) NOT NULL,  -- References llm_project_config.project_id
    agent_type VARCHAR(50) NOT NULL,  -- coder, researcher, frontend, mobile, etc.
    agent_id VARCHAR(100),  -- Specific agent instance ID (optional)
    
    -- Task details
    task_name VARCHAR(255) NOT NULL,  -- Human-readable task name
    task_description TEXT,  -- Detailed task description
    task_type VARCHAR(50),  -- task_type: code_generation, research, testing, etc.
    
    -- Task status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, started, running, completed, failed, cancelled
    priority INTEGER DEFAULT 1,  -- 1=high, 2=medium, 3=low
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,  -- When agent started working on task
    completed_at TIMESTAMP WITH TIME ZONE,  -- When task was completed
    failed_at TIMESTAMP WITH TIME ZONE,  -- When task failed (if applicable)
    
    -- Task execution details
    error_message TEXT,  -- Error message if task failed
    error_stack_trace TEXT,  -- Stack trace if available
    execution_metadata JSONB,  -- Additional execution details (outputs, logs, etc.)
    
    -- Progress tracking
    progress_percentage FLOAT DEFAULT 0.0,  -- 0.0 to 100.0
    estimated_duration_seconds INTEGER,  -- Estimated duration in seconds
    actual_duration_seconds INTEGER,  -- Actual duration in seconds (calculated from timestamps)
    
    -- Resource usage (for cost tracking)
    llm_calls_count INTEGER DEFAULT 0,  -- Number of LLM API calls made for this task
    llm_tokens_used INTEGER DEFAULT 0,  -- Total tokens used
    llm_cost_usd FLOAT DEFAULT 0.0,  -- Cost in USD for LLM usage
    
    -- Relationships
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL,  -- For tenant scoping (nullable)
    
    -- Indexes for performance
    CONSTRAINT agent_tasks_status_check CHECK (status IN ('pending', 'started', 'running', 'completed', 'failed', 'cancelled'))
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agent_tasks_project_id ON agent_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_type ON agent_tasks(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at ON agent_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_tenant_id ON agent_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_project_status ON agent_tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_task_id ON agent_tasks(task_id);

-- Add comment to table
COMMENT ON TABLE agent_tasks IS 'Tracks all tasks assigned to agents for real-time progress monitoring and analytics';
COMMENT ON COLUMN agent_tasks.task_id IS 'Unique task identifier (e.g., task-{project_id}-{agent_type}-{sequence})';
COMMENT ON COLUMN agent_tasks.project_id IS 'References llm_project_config.project_id';
COMMENT ON COLUMN agent_tasks.status IS 'Task status: pending, started, running, completed, failed, cancelled';
COMMENT ON COLUMN agent_tasks.progress_percentage IS 'Task completion percentage (0.0 to 100.0)';
COMMENT ON COLUMN agent_tasks.execution_metadata IS 'JSON metadata: outputs, logs, intermediate results, etc.';

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON TABLE agent_tasks TO q2o_user;
-- GRANT USAGE, SELECT ON SEQUENCE agent_tasks_id_seq TO q2o_user;

