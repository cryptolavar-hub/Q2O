"""
Database model for LLM usage logs.
Stores individual LLM API calls for analytics and debugging.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from ..core.db import Base


class LLMUsageLog(Base):
    """
    Logs individual LLM API calls for analytics and debugging.
    
    Each row represents a single LLM API call with full details:
    - Provider, model, tokens, cost, duration
    - Success/failure status
    - Agent and task context
    - Request/response metadata
    """
    __tablename__ = "llm_usage_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Request identification
    request_id = Column(String(255), unique=True, nullable=False, index=True)  # UUID or hash
    project_id = Column(String(255), nullable=True, index=True)  # Which project made the call
    task_id = Column(String(255), nullable=True, index=True)  # Which task triggered the call
    agent_type = Column(String(100), nullable=False, index=True)  # orchestrator, researcher, coder, etc.
    agent_id = Column(String(255), nullable=True)  # Specific agent instance
    
    # LLM provider details
    provider = Column(String(50), nullable=False, index=True)  # gemini, openai, anthropic
    model = Column(String(100), nullable=False, index=True)  # Actual model name (e.g., "gemini-2.5-flash")
    
    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Cost tracking
    input_cost = Column(Float, default=0.0)
    output_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Performance metrics
    duration_seconds = Column(Float, default=0.0)  # Response time
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Cache status
    cache_hit = Column(Boolean, default=False, index=True)
    
    # Request/response metadata (optional, for debugging)
    system_prompt_hash = Column(String(64), nullable=True)  # MD5 hash of system prompt
    user_prompt_hash = Column(String(64), nullable=True)  # MD5 hash of user prompt
    response_preview = Column(Text, nullable=True)  # First 500 chars of response
    log_metadata = Column(JSON, nullable=True)  # Additional metadata (retry attempts, etc.) - renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_llm_logs_provider_model', 'provider', 'model'),
        Index('idx_llm_logs_project_agent', 'project_id', 'agent_type'),
        Index('idx_llm_logs_created_at', 'created_at'),
        Index('idx_llm_logs_success_cache', 'success', 'cache_hit'),
    )

