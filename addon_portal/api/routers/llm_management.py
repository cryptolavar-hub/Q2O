"""API routes for administering LLM configuration and prompts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

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
    from utils.llm_service import get_llm_service
    from utils.template_learning_engine import get_template_learning_engine
    from utils.configuration_manager import get_configuration_manager
    LLM_AVAILABLE = True
except ImportError:
    LOGGER.warning('llm_components_unavailable')
    LLM_AVAILABLE = False


router = APIRouter(prefix="/api/llm", tags=["llm_management"])


@router.get("/system", response_model=SystemConfigResponse)
async def read_system_configuration(db: Session = Depends(get_db)) -> SystemConfigResponse:
    """Return the persisted system-level LLM configuration."""

    return get_system_config(db)


@router.put("/system", response_model=SystemConfigResponse)
async def write_system_configuration(
    payload: SystemConfigUpdate,
    db: Session = Depends(get_db),
) -> SystemConfigResponse:
    """Update the system-level LLM configuration and persist the system prompt to .env."""

    LOGGER.info('system_config_update_request', extra={"provider": payload.primary_provider.value})
    return update_system_config(db, payload)


@router.get("/projects", response_model=ProjectCollectionResponse)
async def list_llm_projects(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
) -> ProjectCollectionResponse:
    """Return paginated LLM project configurations."""

    LOGGER.info('list_llm_projects', extra={"page": page, "pageSize": page_size, "search": search})
    return list_projects(db, page=page, page_size=page_size, search=search)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    payload: ProjectCreatePayload,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create a new LLM project configuration."""

    LOGGER.info('create_project_request', extra={'projectId': payload.project_id, 'clientName': payload.client_name})
    return create_project(db, payload)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def retrieve_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    """Return a single LLM project configuration."""

    return get_project(db, project_id)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project_configuration(
    project_id: str,
    payload: ProjectUpdatePayload,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project-level metadata and prompt overrides."""

    return update_project(db, project_id, payload)


@router.put("/projects/{project_id}/agents/{agent_type}", response_model=AgentPromptResponse)
async def update_agent_configuration(
    project_id: str,
    agent_type: str,
    payload: AgentPromptUpdate,
    db: Session = Depends(get_db),
) -> AgentPromptResponse:
    """Create or update agent-level prompt overrides for a project."""

    LOGGER.info('agent_prompt_update', extra={"projectId": project_id, "agentType": agent_type})
    sanitized_agent_type = agent_type.strip().lower()
    if not sanitized_agent_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent type is required.")

    return update_agent_prompt(db, project_id, sanitized_agent_type, payload)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Delete an LLM project configuration (admin only - no tenant scoping)."""

    LOGGER.info('delete_project_request', extra={"projectId": project_id})
    try:
        delete_project(db, project_id, tenant_id=None)  # Admin can delete any project
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

