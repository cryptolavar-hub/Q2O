"""API routes for administering LLM configuration and prompts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..deps import get_db
from ..models.agent_tasks import AgentTask
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
from sqlalchemy import select, func

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
async def get_llm_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """Return usage statistics for the LLM stack.
    
    Aggregates data from:
    1. Database (agent_tasks table) - persistent historical data
    2. In-memory LLM service - current session data
    """

    # Aggregate LLM usage from database (agent_tasks table)
    result = await db.execute(
        select(
            func.sum(AgentTask.llm_calls_count).label('total_calls'),
            func.sum(AgentTask.llm_tokens_used).label('total_tokens'),
            func.sum(AgentTask.llm_cost_usd).label('total_cost'),
            func.avg(AgentTask.actual_duration_seconds).label('avg_duration'),
            func.count(AgentTask.id).filter(AgentTask.status == 'completed').label('completed_tasks'),
            func.count(AgentTask.id).filter(AgentTask.status == 'failed').label('failed_tasks'),
        )
    )
    db_stats = result.first()
    
    db_total_calls = int(db_stats.total_calls or 0)
    db_total_tokens = int(db_stats.total_tokens or 0)
    db_total_cost = float(db_stats.total_cost or 0.0)
    db_avg_duration = float(db_stats.avg_duration or 0.0)
    db_completed = int(db_stats.completed_tasks or 0)
    db_failed = int(db_stats.failed_tasks or 0)
    db_total_tasks = db_completed + db_failed
    db_success_rate = (db_completed / db_total_tasks * 100) if db_total_tasks > 0 else 0.0

    # Get in-memory stats (current session only)
    in_memory_stats = {}
    monthly_budget = 1000.0
    monthly_spent = db_total_cost  # Use database cost as monthly spent
    
    if LLM_AVAILABLE:
        try:
            llm_service = get_llm_service()
            template_engine = get_template_learning_engine()
            
            in_memory_stats = llm_service.get_usage_stats()
            template_stats = template_engine.get_learning_stats()
            
            monthly_budget = llm_service.cost_monitor.monthly_budget
            # Combine in-memory and database costs
            monthly_spent = db_total_cost + llm_service.cost_monitor.monthly_spent
        except Exception as e:
            LOGGER.warning(f"Failed to get in-memory LLM stats: {e}")
            template_stats = {'total_templates': 0, 'total_uses': 0, 'cost_saved': 0.0}
    else:
        template_stats = {'total_templates': 0, 'total_uses': 0, 'cost_saved': 0.0}

    # Combine database and in-memory stats
    total_calls = db_total_calls + in_memory_stats.get('total_calls', 0)
    total_cost = db_total_cost + in_memory_stats.get('total_cost', 0.0)
    
    # Calculate success rate from database
    success_rate = db_success_rate if db_total_tasks > 0 else (in_memory_stats.get('success_rate', 0.0) * 100)
    
    # Average response time (prefer database, fallback to in-memory)
    avg_response_time = db_avg_duration if db_avg_duration > 0 else in_memory_stats.get('avg_duration', 0.0)

    # Provider breakdown (from in-memory stats, as database doesn't track provider)
    provider_breakdown = in_memory_stats.get('by_provider', {})
    # If no in-memory data, create empty breakdown
    if not provider_breakdown:
        provider_breakdown = {
            'gemini': {'calls': 0, 'total_cost': 0.0, 'avg_cost': 0.0},
            'openai': {'calls': 0, 'total_cost': 0.0, 'avg_cost': 0.0},
            'anthropic': {'calls': 0, 'total_cost': 0.0, 'avg_cost': 0.0},
        }

    alerts = []
    if monthly_spent >= monthly_budget:
        alerts.append({
            'id': 'budget_100',
            'level': 'critical',
            'message': 'Budget limit reached',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    elif monthly_spent >= monthly_budget * 0.95:
        alerts.append({
            'id': 'budget_95',
            'level': 'critical',
            'message': '95% of budget used',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    elif monthly_spent >= monthly_budget * 0.80:
        alerts.append({
            'id': 'budget_80',
            'level': 'warning',
            'message': '80% of budget used',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    # Calculate daily costs from database (last 30 days)
    daily_costs = []
    now = datetime.now(timezone.utc)
    for offset in range(30):
        day = now - timedelta(days=29 - offset)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Query tasks completed on this day
        day_result = await db.execute(
            select(func.sum(AgentTask.llm_cost_usd)).where(
                AgentTask.completed_at >= day_start,
                AgentTask.completed_at <= day_end
            )
        )
        day_cost = float(day_result.scalar() or 0.0)
        daily_costs.append({'date': day.strftime('%Y-%m-%d'), 'cost': day_cost})

    return {
        'totalCalls': total_calls,
        'totalCost': round(total_cost, 2),
        'monthlyBudget': monthly_budget,
        'budgetUsed': round(monthly_spent, 2),
        'avgResponseTime': round(avg_response_time, 2),
        'successRate': round(success_rate, 1),
        'providerBreakdown': provider_breakdown,
        'dailyCosts': daily_costs,
        'templateStats': {
            'total': template_stats.get('total_templates', 0),
            'uses': template_stats.get('total_uses', 0),
            'saved': round(template_stats.get('cost_saved', 0.0), 2),
        },
        'alerts': alerts,
    }

