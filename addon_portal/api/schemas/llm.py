"""Pydantic models for LLM configuration endpoints."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(component.capitalize() for component in components[1:])


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    GEMINI = 'gemini'
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'


class SortDirection(str, Enum):
    """Paging sort direction."""

    ASC = 'asc'
    DESC = 'desc'


class SystemConfigResponse(BaseModel):
    """Serialized system configuration."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    primary_provider: LLMProvider
    secondary_provider: LLMProvider
    tertiary_provider: LLMProvider
    gemini_model: str
    openai_model: str
    anthropic_model: str
    temperature: float
    max_tokens: int
    retries_per_provider: int
    monthly_budget: float
    daily_budget: float
    template_learning_enabled: bool
    cross_validation_enabled: bool
    cache_enabled: bool
    min_quality_score: int
    template_min_quality: int
    system_prompt: str


class SystemConfigUpdate(BaseModel):
    """Payload for updating system configuration."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra='forbid')

    primary_provider: LLMProvider
    secondary_provider: LLMProvider
    tertiary_provider: LLMProvider
    gemini_model: str
    openai_model: str
    anthropic_model: str
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(ge=64, le=8192)
    retries_per_provider: int = Field(ge=0, le=5)
    monthly_budget: float = Field(ge=0.0)
    daily_budget: float = Field(ge=0.0)
    template_learning_enabled: bool
    cross_validation_enabled: bool
    cache_enabled: bool
    min_quality_score: int = Field(ge=0, le=100)
    template_min_quality: int = Field(ge=0, le=100)
    system_prompt: str


class AgentPromptResponse(BaseModel):
    """Agent-specific LLM configuration."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    agent_type: str
    provider_override: Optional[LLMProvider] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None
    custom_prompt: Optional[str] = None
    custom_instructions: Optional[str] = None
    enabled: bool
    updated_at: Optional[str] = None


class AgentPromptUpdate(BaseModel):
    """Payload for updating agent prompts."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra='forbid')

    provider_override: Optional[LLMProvider] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens_override: Optional[int] = Field(default=None, ge=64, le=8192)
    custom_prompt: Optional[str] = None
    custom_instructions: Optional[str] = None
    enabled: Optional[bool] = None


class ProjectResponse(BaseModel):
    """Serialized project configuration with agent prompts."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    project_id: str
    client_name: str
    description: Optional[str] = None
    provider_override: Optional[LLMProvider] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None
    monthly_budget_override: Optional[float] = None
    custom_instructions: Optional[str] = None
    is_active: bool
    priority: str
    created_at: str
    updated_at: Optional[str] = None
    agent_prompts: List[AgentPromptResponse]
    activation_code_id: Optional[int] = None  # ID of assigned activation code
    execution_status: Optional[str] = None  # pending, running, completed, failed, paused
    tenant_name: Optional[str] = None  # Tenant name for display
    tenant_slug: Optional[str] = None  # Tenant slug for display
    show_completion_modal: Optional[bool] = True  # Whether to show completion modal (default: True/On)


class ProjectCollectionResponse(BaseModel):
    """Paginated collection of project configurations."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int


class ProjectCreatePayload(BaseModel):
    """Payload for creating a new project-level prompt configuration."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra='forbid')

    project_id: str = Field(..., min_length=1, max_length=100)
    client_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    custom_instructions: Optional[str] = None
    is_active: bool = True
    priority: str = Field(default='normal', pattern=r'^(low|normal|high|critical)$')


class ProjectUpdatePayload(BaseModel):
    """Payload for updating project-level prompt configuration."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra='forbid')

    client_name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    provider_override: Optional[LLMProvider] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens_override: Optional[int] = Field(default=None, ge=64, le=8192)
    monthly_budget_override: Optional[float] = Field(default=None, ge=0.0)
    custom_instructions: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[str] = Field(default=None, pattern=r'^(low|normal|high|critical)$')
