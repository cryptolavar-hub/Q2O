"""Service utilities for managing LLM configuration and prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.exceptions import ConfigurationError, InvalidOperationError
from ..core.logging import get_logger
from ..models.llm_config import LLMAgentConfig, LLMProjectConfig, LLMSystemConfig
from ..schemas.llm import (
    AgentPromptResponse,
    AgentPromptUpdate,
    LLMProvider,
    ProjectCollectionResponse,
    ProjectCreatePayload,
    ProjectResponse,
    ProjectUpdatePayload,
    SystemConfigResponse,
    SystemConfigUpdate,
)
from ..utils.env_manager import read_env_value, write_env_value

LOGGER = get_logger(__name__)
# Path to .env file in project root: C:\Q2O_Combined\.env
# Using explicit path to ensure it's always found
ENV_PATH = Path(r'C:\Q2O_Combined\.env')
SYSTEM_PROMPT_KEY = 'LLM_SYSTEM_PROMPT'


async def _ensure_system_config(session: AsyncSession) -> LLMSystemConfig:
    result = await session.execute(select(LLMSystemConfig))
    config = result.scalar_one_or_none()
    if config is None:
        config = LLMSystemConfig()
        session.add(config)
        await session.commit()
        await session.refresh(config)
    return config


def _serialize_system_config(config: LLMSystemConfig, system_prompt: str) -> SystemConfigResponse:
    return SystemConfigResponse(
        primary_provider=LLMProvider(config.primary_provider),
        secondary_provider=LLMProvider(config.secondary_provider),
        tertiary_provider=LLMProvider(config.tertiary_provider),
        gemini_model=config.gemini_model,
        openai_model=config.openai_model,
        anthropic_model=config.anthropic_model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        retries_per_provider=config.retries_per_provider,
        monthly_budget=config.monthly_budget,
        daily_budget=config.daily_budget,
        template_learning_enabled=config.template_learning_enabled,
        cross_validation_enabled=config.cross_validation_enabled,
        cache_enabled=config.cache_enabled,
        min_quality_score=config.min_quality_score,
        template_min_quality=config.template_min_quality,
        system_prompt=system_prompt,
    )


async def get_system_config(session: AsyncSession, env_path: Path = ENV_PATH) -> SystemConfigResponse:
    """Return the current system-level LLM configuration."""

    config = await _ensure_system_config(session)
    system_prompt = read_env_value(SYSTEM_PROMPT_KEY, env_path) or config.system_prompt or ''
    return _serialize_system_config(config, system_prompt)


async def update_system_config(
    session: AsyncSession,
    payload: SystemConfigUpdate,
    *,
    updated_by: str = 'admin-ui',
    env_path: Path = ENV_PATH,
) -> SystemConfigResponse:
    """Persist system configuration changes and update the .env system prompt."""

    config = await _ensure_system_config(session)

    config.primary_provider = payload.primary_provider.value
    config.secondary_provider = payload.secondary_provider.value
    config.tertiary_provider = payload.tertiary_provider.value
    config.gemini_model = payload.gemini_model
    config.openai_model = payload.openai_model
    config.anthropic_model = payload.anthropic_model
    config.temperature = payload.temperature
    config.max_tokens = payload.max_tokens
    config.retries_per_provider = payload.retries_per_provider
    config.monthly_budget = payload.monthly_budget
    config.daily_budget = payload.daily_budget
    config.template_learning_enabled = payload.template_learning_enabled
    config.cross_validation_enabled = payload.cross_validation_enabled
    config.cache_enabled = payload.cache_enabled
    config.min_quality_score = payload.min_quality_score
    config.template_min_quality = payload.template_min_quality
    config.updated_by = updated_by

    try:
        write_env_value(SYSTEM_PROMPT_KEY, payload.system_prompt, env_path)
        config.system_prompt = payload.system_prompt
        await session.commit()
    except OSError as exc:
        await session.rollback()
        LOGGER.error('system_prompt_write_failed', extra={'error': str(exc)})
        raise ConfigurationError('Failed to persist system prompt to environment file.') from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        LOGGER.error('system_config_update_failed', extra={'error': str(exc)})
        raise InvalidOperationError('Failed to update system configuration.') from exc

    await session.refresh(config)
    return _serialize_system_config(config, payload.system_prompt)


def _serialize_agent(agent: LLMAgentConfig) -> AgentPromptResponse:
    return AgentPromptResponse(
        agent_type=agent.agent_type,
        provider_override=LLMProvider(agent.provider_override) if agent.provider_override else None,
        model_override=agent.model_override,
        temperature_override=agent.temperature_override,
        max_tokens_override=agent.max_tokens_override,
        custom_prompt=agent.custom_prompt,
        custom_instructions=agent.custom_instructions,
        enabled=agent.enabled,
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
    )


def _serialize_project(project: LLMProjectConfig) -> ProjectResponse:
    return ProjectResponse(
        project_id=project.project_id,
        client_name=project.client_name,
        description=project.description,
        provider_override=LLMProvider(project.provider_override) if project.provider_override else None,
        model_override=project.model_override,
        temperature_override=project.temperature_override,
        max_tokens_override=project.max_tokens_override,
        monthly_budget_override=project.monthly_budget_override,
        custom_instructions=project.custom_instructions,
        is_active=project.is_active,
        priority=project.priority,
        created_at=project.created_at.isoformat() if project.created_at else '',
        updated_at=project.updated_at.isoformat() if project.updated_at else None,
        agent_prompts=[_serialize_agent(agent) for agent in project.agent_configs],
        activation_code_id=project.activation_code_id,  # Include activation code ID
        execution_status=project.execution_status,  # Include execution status
    )


async def list_projects(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    tenant_id: Optional[int] = None,  # Filter by tenant (None = all tenants, for admin)
) -> ProjectCollectionResponse:
    """Return paginated project configurations with optional search filter and tenant scoping."""

    stmt = select(LLMProjectConfig).options(selectinload(LLMProjectConfig.agent_configs))
    
    # Tenant scoping: filter by tenant_id if provided
    if tenant_id is not None:
        stmt = stmt.where(LLMProjectConfig.tenant_id == tenant_id)
    
    if search:
        pattern = f"%{search.strip().lower()}%"
        # Search by client_name (which is the project name)
        stmt = stmt.where(func.lower(LLMProjectConfig.client_name).like(pattern))

    result = await session.execute(
        stmt.with_only_columns(func.count(LLMProjectConfig.id)).order_by(None)
    )
    total = result.scalar_one()

    result = await session.execute(
        stmt.order_by(LLMProjectConfig.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    projects = result.scalars().all()

    return ProjectCollectionResponse(
        items=[_serialize_project(project) for project in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_project(
    session: AsyncSession,
    project_id: str,
    tenant_id: Optional[int] = None,  # Verify tenant ownership (None = admin can access any)
) -> ProjectResponse:
    stmt = (
        select(LLMProjectConfig)
        .options(selectinload(LLMProjectConfig.agent_configs))
        .where(LLMProjectConfig.project_id == project_id)
    )
    
    # Tenant scoping: verify ownership if tenant_id provided
    if tenant_id is not None:
        stmt = stmt.where(LLMProjectConfig.tenant_id == tenant_id)
    
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise ConfigurationError('Project not found.', detail={'projectId': project_id})

    return _serialize_project(project)


async def create_project(
    session: AsyncSession,
    payload: ProjectCreatePayload,
    *,
    tenant_id: Optional[int] = None,  # Set tenant_id for tenant-scoped projects
    created_by: str = 'admin-ui',
) -> ProjectResponse:
    """Create a new project-level configuration."""

    # Check if project already exists
    result = await session.execute(
        select(LLMProjectConfig).where(LLMProjectConfig.project_id == payload.project_id)
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        raise InvalidOperationError(
            f'Project with ID "{payload.project_id}" already exists.',
            detail={'projectId': payload.project_id},
        )

    project = LLMProjectConfig(
        project_id=payload.project_id,
        client_name=payload.client_name,
        description=payload.description,
        custom_instructions=payload.custom_instructions,
        is_active=payload.is_active,
        priority=payload.priority,
        tenant_id=tenant_id,  # Set tenant scoping
        created_by=created_by,
    )

    try:
        session.add(project)
        await session.commit()
        await session.refresh(project)
    except SQLAlchemyError as exc:
        await session.rollback()
        LOGGER.error('project_creation_failed', extra={'projectId': payload.project_id, 'error': str(exc)})
        raise InvalidOperationError('Failed to create project configuration.') from exc

    # Reload with agent configs relationship
    result = await session.execute(
        select(LLMProjectConfig)
        .options(selectinload(LLMProjectConfig.agent_configs))
        .where(LLMProjectConfig.project_id == payload.project_id)
    )
    project = result.scalar_one()

    return _serialize_project(project)


async def update_project(
    session: AsyncSession,
    project_id: str,
    payload: ProjectUpdatePayload,
    tenant_id: Optional[int] = None,  # Verify tenant ownership (None = admin can update any)
) -> ProjectResponse:
    """Update project-level configuration values."""

    stmt = (
        select(LLMProjectConfig)
        .options(selectinload(LLMProjectConfig.agent_configs))
        .where(LLMProjectConfig.project_id == project_id)
    )
    
    # Tenant scoping: verify ownership if tenant_id provided
    if tenant_id is not None:
        stmt = stmt.where(LLMProjectConfig.tenant_id == tenant_id)
    
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise ConfigurationError('Project not found.', detail={'projectId': project_id})

    if payload.client_name is not None:
        project.client_name = payload.client_name
    if payload.description is not None:
        project.description = payload.description
    if payload.provider_override is not None:
        project.provider_override = payload.provider_override.value
    if payload.model_override is not None:
        project.model_override = payload.model_override
    if payload.temperature_override is not None:
        project.temperature_override = payload.temperature_override
    if payload.max_tokens_override is not None:
        project.max_tokens_override = payload.max_tokens_override
    if payload.monthly_budget_override is not None:
        project.monthly_budget_override = payload.monthly_budget_override
    if payload.custom_instructions is not None:
        project.custom_instructions = payload.custom_instructions
    if payload.is_active is not None:
        project.is_active = payload.is_active
    if payload.priority is not None:
        project.priority = payload.priority

    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        LOGGER.error('project_update_failed', extra={'projectId': project_id, 'error': str(exc)})
        raise InvalidOperationError('Failed to update project configuration.') from exc

    await session.refresh(project)
    return _serialize_project(project)


async def delete_project(
    session: AsyncSession,
    project_id: str,
    tenant_id: Optional[int] = None,  # Verify tenant ownership (None = admin can delete any)
) -> None:
    """Delete a project configuration."""

    stmt = select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
    
    # Tenant scoping: verify ownership if tenant_id provided
    if tenant_id is not None:
        stmt = stmt.where(LLMProjectConfig.tenant_id == tenant_id)
    
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise ConfigurationError('Project not found.', detail={'projectId': project_id})

    try:
        await session.delete(project)
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        LOGGER.error('project_deletion_failed', extra={'projectId': project_id, 'error': str(exc)})
        raise InvalidOperationError('Failed to delete project configuration.') from exc


async def update_agent_prompt(
    session: AsyncSession,
    project_id: str,
    agent_type: str,
    payload: AgentPromptUpdate,
) -> AgentPromptResponse:
    """Create or update agent-level prompt configuration."""

    result = await session.execute(
        select(LLMProjectConfig)
        .options(selectinload(LLMProjectConfig.agent_configs))
        .where(LLMProjectConfig.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise ConfigurationError('Project not found.', detail={'projectId': project_id})

    agent = next((cfg for cfg in project.agent_configs if cfg.agent_type == agent_type), None)
    if agent is None:
        agent = LLMAgentConfig(project_id=project.project_id, agent_type=agent_type)
        session.add(agent)
        project.agent_configs.append(agent)

    if payload.provider_override is not None:
        agent.provider_override = payload.provider_override.value
    if payload.model_override is not None:
        agent.model_override = payload.model_override
    if payload.temperature_override is not None:
        agent.temperature_override = payload.temperature_override
    if payload.max_tokens_override is not None:
        agent.max_tokens_override = payload.max_tokens_override
    if payload.custom_prompt is not None:
        agent.custom_prompt = payload.custom_prompt
    if payload.custom_instructions is not None:
        agent.custom_instructions = payload.custom_instructions
    if payload.enabled is not None:
        agent.enabled = payload.enabled

    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        LOGGER.error('agent_prompt_update_failed', extra={'projectId': project_id, 'agentType': agent_type, 'error': str(exc)})
        raise InvalidOperationError('Failed to update agent prompt configuration.') from exc

    await session.refresh(agent)
    return _serialize_agent(agent)
