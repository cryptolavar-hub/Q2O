"""
Agent Tasks Model - Real-time task tracking for agents

This model tracks all tasks assigned to agents, enabling:
- Real progress calculation based on completed tasks
- Agent activity monitoring
- Task performance analytics
- LLM usage tracking per task
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .licensing import Base


class AgentTask(Base):
    """
    Tracks individual tasks assigned to agents.
    
    Agents update this table when they:
    - Receive a task (status: pending)
    - Start working on a task (status: started/running)
    - Complete a task (status: completed)
    - Fail a task (status: failed)
    """
    __tablename__ = "agent_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Task identification
    task_id = Column(String(100), unique=True, nullable=False, index=True)  # Unique task identifier
    project_id = Column(String(100), nullable=False, index=True)  # References llm_project_config.project_id
    agent_type = Column(String(50), nullable=False, index=True)  # coder, researcher, frontend, mobile, etc.
    agent_id = Column(String(100), nullable=True)  # Specific agent instance ID (optional)
    
    # Task details
    task_name = Column(String(255), nullable=False)  # Human-readable task name
    task_description = Column(Text, nullable=True)  # Detailed task description
    task_type = Column(String(50), nullable=True)  # code_generation, research, testing, etc.
    
    # Task status
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, started, running, completed, failed, cancelled
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)  # When agent started working on task
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When task was completed
    failed_at = Column(DateTime(timezone=True), nullable=True)  # When task failed (if applicable)
    
    # Task execution details
    error_message = Column(Text, nullable=True)  # Error message if task failed
    error_stack_trace = Column(Text, nullable=True)  # Stack trace if available
    execution_metadata = Column(JSON, nullable=True)  # Additional execution details (outputs, logs, etc.)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    estimated_duration_seconds = Column(Integer, nullable=True)  # Estimated duration in seconds
    actual_duration_seconds = Column(Integer, nullable=True)  # Actual duration (calculated from timestamps)
    
    # Resource usage (for cost tracking)
    llm_calls_count = Column(Integer, default=0)  # Number of LLM API calls made for this task
    llm_tokens_used = Column(Integer, default=0)  # Total tokens used
    llm_cost_usd = Column(Float, default=0.0)  # Cost in USD for LLM usage
    
    # Relationships
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    # Indexes for performance (composite indexes for common queries)
    __table_args__ = (
        Index('idx_agent_tasks_project_status', 'project_id', 'status'),
        CheckConstraint("status IN ('pending', 'started', 'running', 'completed', 'failed', 'cancelled')", name='agent_tasks_status_check'),
    )

