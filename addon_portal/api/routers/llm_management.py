"""API routes for administering LLM configuration and prompts."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..core.logging import get_logger
from ..deps import get_db
from ..schemas.llm import (
    AgentPromptResponse,
    AgentPromptUpdate,
    ProjectCollectionResponse,
    ProjectCreatePayload,
    ProjectResponse,
    ProjectUpdatePayload,
    SystemConfigResponse,
    SystemConfigUpdate,
)
from ..services.llm_config_service import (
    create_project,
    delete_project,
    get_project,
    get_system_config,
    list_projects,
    update_agent_prompt,
    update_project,
    update_system_config,
)

LOGGER = get_logger(__name__)

try:  # pragma: no cover - optional dependency
    import sys
    from pathlib import Path
    # Add project root to path to import utils
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from utils.llm_service import get_llm_service
    from utils.template_learning_engine import get_template_learning_engine
    from utils.configuration_manager import get_configuration_manager
    LLM_AVAILABLE = True
except ImportError as e:
    LOGGER.warning('llm_components_unavailable', extra={"error": str(e)})
    LLM_AVAILABLE = False


router = APIRouter(prefix="/api/llm", tags=["llm_management"])


@router.get("/system", response_model=SystemConfigResponse)
async def read_system_configuration(db: AsyncSession = Depends(get_db)) -> SystemConfigResponse:
    """Return the persisted system-level LLM configuration."""

    return await get_system_config(db)


@router.put("/system", response_model=SystemConfigResponse)
async def write_system_configuration(
    payload: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> SystemConfigResponse:
    """Update the system-level LLM configuration and persist the system prompt to .env."""

    LOGGER.info('system_config_update_request', extra={"provider": payload.primary_provider.value})
    return await update_system_config(db, payload)


@router.get("/projects", response_model=ProjectCollectionResponse)
async def list_llm_projects(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
) -> ProjectCollectionResponse:
    """Return paginated LLM project configurations."""

    LOGGER.info('list_llm_projects', extra={"page": page, "pageSize": page_size, "search": search})
    return await list_projects(db, page=page, page_size=page_size, search=search)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    payload: ProjectCreatePayload,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new LLM project configuration."""

    LOGGER.info('create_project_request', extra={'projectId': payload.project_id, 'clientName': payload.client_name})
    return await create_project(db, payload)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def retrieve_project(project_id: str, db: AsyncSession = Depends(get_db)) -> ProjectResponse:
    """Return a single LLM project configuration."""

    return await get_project(db, project_id)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project_configuration(
    project_id: str,
    payload: ProjectUpdatePayload,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update project-level metadata and prompt overrides."""

    return await update_project(db, project_id, payload)


@router.put("/projects/{project_id}/agents/{agent_type}", response_model=AgentPromptResponse)
async def update_agent_configuration(
    project_id: str,
    agent_type: str,
    payload: AgentPromptUpdate,
    db: AsyncSession = Depends(get_db),
) -> AgentPromptResponse:
    """Create or update agent-level prompt overrides for a project."""

    LOGGER.info('agent_prompt_update', extra={"projectId": project_id, "agentType": agent_type})
    sanitized_agent_type = agent_type.strip().lower()
    if not sanitized_agent_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent type is required.")

    return await update_agent_prompt(db, project_id, sanitized_agent_type, payload)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an LLM project configuration (admin only - no tenant scoping)."""

    LOGGER.info('delete_project_request', extra={"projectId": project_id})
    try:
        await delete_project(db, project_id, tenant_id=None)  # Admin can delete any project
    except Exception as e:
        LOGGER.error('delete_project_error', extra={"error": str(e), "projectId": project_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or could not be deleted",
        )


@router.get("/stats")
async def get_llm_stats() -> dict:
    """Return usage statistics for the LLM stack."""

    if not LLM_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM integration not available")

    llm_service = get_llm_service()
    template_engine = get_template_learning_engine()

    cost_stats = llm_service.get_usage_stats()
    template_stats = template_engine.get_learning_stats()
    
    monthly_budget = llm_service.cost_monitor.monthly_budget
    monthly_spent = llm_service.cost_monitor.monthly_spent
    
    # Get provider breakdown with actual model names from usage stats
    provider_breakdown = cost_stats.get('by_provider', {})
    
    # Ensure all providers have model names (even if no usage yet)
    # Also normalize structure to match frontend expectations
    for provider_key in ['gemini', 'openai', 'anthropic']:
        if provider_key not in provider_breakdown:
            if provider_key == 'gemini':
                model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            elif provider_key == 'openai':
                model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
            else:  # anthropic
                model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            
            provider_breakdown[provider_key] = {
                'calls': 0,
                'total_cost': 0.0,
                'cost': 0.0,  # Alias for frontend compatibility
                'avg_cost': 0.0,
                'model': model_name,
                'models': {model_name: {'calls': 0, 'total_cost': 0.0}}
            }
        else:
            # Normalize structure - ensure 'cost' alias exists and 'model' is set
            provider_data = provider_breakdown[provider_key]
            if 'cost' not in provider_data:
                provider_data['cost'] = provider_data.get('total_cost', 0.0)
            if 'model' not in provider_data and provider_data.get('models'):
                # Get first model from models dict
                models_dict = provider_data['models']
                if isinstance(models_dict, dict) and models_dict:
                    provider_data['model'] = list(models_dict.keys())[0]
                elif isinstance(models_dict, list) and models_dict:
                    provider_data['model'] = models_dict[0] if isinstance(models_dict[0], str) else models_dict[0].get('model', 'unknown')

    alerts = []
    if monthly_spent >= monthly_budget:
        alerts.append({
            'id': 'budget_100',
            'level': 'critical',
            'message': 'Budget limit reached',
            'timestamp': datetime.utcnow().isoformat(),
        })
    elif monthly_spent >= monthly_budget * 0.95:
        alerts.append({
            'id': 'budget_95',
            'level': 'critical',
            'message': '95% of budget used',
            'timestamp': datetime.utcnow().isoformat(),
        })
    elif monthly_spent >= monthly_budget * 0.80:
        alerts.append({
            'id': 'budget_80',
            'level': 'warning',
            'message': '80% of budget used',
            'timestamp': datetime.utcnow().isoformat(),
        })

    daily_costs = []
    for offset in range(30):
        day = datetime.utcnow() - timedelta(days=29 - offset)
        cost_estimate = cost_stats.get('daily_costs', {}).get(day.strftime('%Y-%m-%d'))
        if cost_estimate is None:
            cost_estimate = cost_stats.get('total_cost', 0) / 30
        daily_costs.append({'date': day.strftime('%Y-%m-%d'), 'cost': cost_estimate})

    return {
        'totalCalls': cost_stats.get('total_calls', 0),
        'totalCost': cost_stats.get('total_cost', 0.0),
        'monthlyBudget': monthly_budget,
        'budgetUsed': monthly_spent,
        'avgResponseTime': cost_stats.get('avg_duration', 0.0),
        'successRate': cost_stats.get('success_rate', 0.0) * 100,
        'providerBreakdown': cost_stats.get('provider_breakdown', {}),
        'dailyCosts': daily_costs,
        'templateStats': {
            'total': template_stats.get('total_templates', 0),
            'uses': template_stats.get('total_uses', 0),
            'saved': template_stats.get('cost_saved', 0.0),
        },
        'alerts': alerts,
    }


@router.get("/logs")
async def get_llm_logs(
    db: AsyncSession = Depends(get_db),
    range: str = Query("7days", description="Time range: 1day, 7days, 30days, all"),
    agent: Optional[str] = Query(None, description="Filter by agent type"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    status: Optional[str] = Query(None, description="Filter by status: success, error, cached"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    """Return paginated LLM usage logs with filtering."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM integration not available")
    
    from addon_portal.api.models.llm_usage import LLMUsageLog
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    if range == "1day":
        start_date = now - timedelta(days=1)
    elif range == "7days":
        start_date = now - timedelta(days=7)
    elif range == "30days":
        start_date = now - timedelta(days=30)
    else:  # all
        start_date = None
    
    # Build query
    query = select(LLMUsageLog)
    conditions = []
    
    if start_date:
        conditions.append(LLMUsageLog.created_at >= start_date)
    if agent:
        conditions.append(LLMUsageLog.agent_type == agent)
    if provider:
        conditions.append(LLMUsageLog.provider == provider)
    if status == "success":
        conditions.append(LLMUsageLog.success == True)
    elif status == "error":
        conditions.append(LLMUsageLog.success == False)
    elif status == "cached":
        conditions.append(LLMUsageLog.cache_hit == True)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Order by most recent first
    query = query.order_by(LLMUsageLog.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(LLMUsageLog)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Format logs for response
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": str(log.id),
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "agent_type": log.agent_type,
            "provider": log.provider,
            "model": log.model,
            "input_tokens": log.input_tokens,
            "output_tokens": log.output_tokens,
            "cost": round(log.total_cost, 4),
            "duration_seconds": round(log.duration_seconds, 2),
            "success": log.success,
            "error_message": log.error_message,
            "task_description": log.log_metadata.get("task_description", "") if log.log_metadata else "",
            "cached": log.cache_hit,
        })
    
    return {
        "logs": logs_data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }

