"""
LLM Configuration Models - PostgreSQL storage for scalable multi-host deployments.

Stores:
- System-level LLM configuration
- Project-level LLM configuration
- Agent-level configuration per project
- Configuration history and versioning
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .licensing import Base


class LLMSystemConfig(Base):
    """
    System-level LLM configuration (singleton record).
    Shared across ALL hosts in multi-host deployment.
    """
    __tablename__ = "llm_system_config"
    
    id = Column(Integer, primary_key=True)  # Should only have 1 record
    
    # Provider configuration
    primary_provider = Column(String(50), default="gemini")  # gemini, openai, anthropic
    secondary_provider = Column(String(50), default="openai")
    tertiary_provider = Column(String(50), default="anthropic")
    
    # Model selection per provider
    # Updated to current models (Nov 2025):
    # - Gemini: gemini-2.5-flash (fast) or gemini-3-pro (advanced)
    # - OpenAI: gpt-4o (latest) or gpt-4-turbo (fallback)
    # - Anthropic: claude-3-5-sonnet-20250219 (latest) or claude-3-5-sonnet-20241022 (fallback)
    gemini_model = Column(String(100), default="gemini-2.5-flash")
    openai_model = Column(String(100), default="gpt-4o")
    anthropic_model = Column(String(100), default="claude-3-5-sonnet-20250219")
    
    # Generation parameters
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    retries_per_provider = Column(Integer, default=3)
    
    # Budget controls
    monthly_budget = Column(Float, default=1000.0)
    daily_budget = Column(Float, default=50.0)
    
    # Prompts
    system_prompt = Column(Text)
    
    # Feature flags
    use_llm = Column(Boolean, default=True)
    template_learning_enabled = Column(Boolean, default=True)
    cross_validation_enabled = Column(Boolean, default=True)
    cache_enabled = Column(Boolean, default=True)
    
    # Quality thresholds
    min_quality_score = Column(Integer, default=95)
    template_min_quality = Column(Integer, default=90)
    
    # Metadata
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(100))  # User who made the change
    version = Column(Integer, default=1)  # Config version for change tracking


class LLMProjectConfig(Base):
    """
    Project-level LLM configuration.
    One record per client project.
    Scoped to tenant for security and access control.
    """
    __tablename__ = "llm_project_config"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Tenant scoping (NULL = admin-only access, for backward compatibility)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Project information
    client_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # LLM provider override (null = use system default)
    provider_override = Column(String(50))  # gemini, openai, anthropic
    model_override = Column(String(100))
    
    # Generation parameter overrides
    temperature_override = Column(Float)
    max_tokens_override = Column(Integer)
    
    # Budget allocation
    monthly_budget_override = Column(Float)  # null = use system budget
    
    # Custom prompts/instructions
    custom_instructions = Column(Text)  # Appended to system prompt
    
    # Project status
    is_active = Column(Boolean, default=True)
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    project_status = Column(String(20), default="active")  # active, pending, completed, paused
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Activation code used to activate this project (one code = one project activation)
    activation_code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="SET NULL"), nullable=True)
    
    # Project execution tracking
    execution_status = Column(String(20), default='pending')  # pending, running, completed, failed, paused
    execution_started_at = Column(DateTime(timezone=True), nullable=True)
    execution_completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_error = Column(Text, nullable=True)
    output_folder_path = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    activation_code = relationship("ActivationCode", foreign_keys=[activation_code_id])
    agent_configs = relationship("LLMAgentConfig", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_client', 'client_name'),
        Index('idx_project_active', 'is_active'),
    )


class LLMAgentConfig(Base):
    """
    Agent-level LLM configuration per project.
    Allows per-agent customization within a project.
    """
    __tablename__ = "llm_agent_config"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), ForeignKey('llm_project_config.project_id'), nullable=False)
    agent_type = Column(String(50), nullable=False)  # coder, researcher, mobile, etc.
    
    # Agent-specific overrides
    provider_override = Column(String(50))  # Override project/system provider
    model_override = Column(String(100))
    temperature_override = Column(Float)
    max_tokens_override = Column(Integer)
    
    # Agent-specific prompts
    custom_prompt = Column(Text)  # Replaces system prompt for this agent
    custom_instructions = Column(Text)  # Appended to prompts
    
    # Agent settings
    enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("LLMProjectConfig", back_populates="agent_configs")
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_project', 'project_id', 'agent_type'),
    )


class LLMConfigHistory(Base):
    """
    Configuration change history for auditing.
    Tracks who changed what and when.
    """
    __tablename__ = "llm_config_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What was changed
    config_type = Column(String(50))  # system, project, agent
    config_id = Column(String(100))  # system, project_id, or agent_id
    
    # Change details
    field_name = Column(String(100))  # Which field was changed
    old_value = Column(Text)  # Previous value (JSON if complex)
    new_value = Column(Text)  # New value (JSON if complex)
    
    # Who and when
    changed_by = Column(String(100))
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    change_reason = Column(Text)  # Optional note
    
    # Indexes
    __table_args__ = (
        Index('idx_history_config', 'config_type', 'config_id'),
        Index('idx_history_time', 'changed_at'),
    )
