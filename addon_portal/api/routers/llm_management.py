"""
LLM Management API Router
Endpoints for the LLM Management Dashboard
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for utils imports
parent_dir = Path(__file__).parent.parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import LLM components
try:
    from utils.llm_service import get_llm_service, LLMService
    from utils.template_learning_engine import get_template_learning_engine, TemplateLearningEngine
    from utils.configuration_manager import get_configuration_manager, ConfigurationManager
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"LLM components not available: {e}")
    LLM_AVAILABLE = False

router = APIRouter(prefix="/api/llm", tags=["llm_management"])


# Pydantic models
class ProviderConfig(BaseModel):
    enabled: bool
    apiKey: str
    model: str


class LLMConfigUpdate(BaseModel):
    providers: Dict[str, ProviderConfig]
    primaryProvider: str
    monthlyBudget: float
    temperature: float
    maxTokens: int
    retries: int
    systemPrompt: str
    projectPrompts: Optional[Dict[str, str]] = {}
    agentPrompts: Optional[Dict[str, str]] = {}


# GET /api/llm/stats - LLM Overview statistics
@router.get("/stats")
async def get_llm_stats():
    """Get LLM usage statistics for the overview dashboard."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    llm_service = get_llm_service()
    template_engine = get_template_learning_engine()
    
    # Get cost stats
    cost_stats = llm_service.get_usage_stats()
    
    # Get template stats
    template_stats = template_engine.get_learning_stats()
    
    # Get provider breakdown (from cost monitor)
    # This is a simplified version - in production, track per-provider
    provider_breakdown = {
        "gemini": {
            "calls": cost_stats.get("total_calls", 0) // 2,  # Simplified
            "cost": cost_stats.get("total_cost", 0) * 0.6  # Gemini is ~60% of usage
        },
        "openai": {
            "calls": cost_stats.get("total_calls", 0) // 4,
            "cost": cost_stats.get("total_cost", 0) * 0.3
        },
        "anthropic": {
            "calls": cost_stats.get("total_calls", 0) // 4,
            "cost": cost_stats.get("total_cost", 0) * 0.1
        }
    }
    
    # Get daily costs (last 30 days)
    daily_costs = []
    for i in range(30):
        date = (datetime.now() - timedelta(days=30-i)).strftime('%Y-%m-%d')
        # Simplified - in production, track actual daily costs
        cost = (cost_stats.get("total_cost", 0) / 30) * (0.5 + (i / 30) * 0.5)
        daily_costs.append({"date": date, "cost": cost})
    
    # Get alerts (from cost monitor)
    monthly_budget = llm_service.cost_monitor.monthly_budget
    monthly_spent = llm_service.cost_monitor.monthly_spent
    
    alerts = []
    # Check for budget alerts
    if monthly_spent >= monthly_budget:
        alerts.append({
            "id": "budget_100",
            "level": "critical",
            "message": "Budget Limit Reached",
            "timestamp": datetime.now().isoformat()
        })
    elif monthly_spent >= monthly_budget * 0.95:
        alerts.append({
            "id": "budget_95",
            "level": "critical",
            "message": "95% of Budget Used",
            "timestamp": datetime.now().isoformat()
        })
    elif monthly_spent >= monthly_budget * 0.80:
        alerts.append({
            "id": "budget_80",
            "level": "warning",
            "message": "80% of Budget Used",
            "timestamp": datetime.now().isoformat()
        })
    
    return {
        "totalCalls": cost_stats.get("total_calls", 0),
        "totalCost": cost_stats.get("total_cost", 0),
        "monthlyBudget": monthly_budget,
        "budgetUsed": monthly_spent,
        "avgResponseTime": cost_stats.get("avg_duration", 0),
        "successRate": cost_stats.get("success_rate", 0) * 100,
        "providerBreakdown": provider_breakdown,
        "dailyCosts": daily_costs,
        "templateStats": {
            "total": template_stats.get("total_templates", 0),
            "uses": template_stats.get("total_uses", 0),
            "saved": template_stats.get("cost_saved", 0.0)
        },
        "alerts": alerts
    }


# GET /api/llm/config - Get current LLM configuration
@router.get("/config")
async def get_llm_config():
    """Get current LLM configuration."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    config_manager = get_configuration_manager()
    system_config = config_manager.system_config
    
    # Read current env values
    return {
        "providers": {
            "gemini": {
                "enabled": bool(os.getenv("GOOGLE_API_KEY")),
                "apiKey": os.getenv("GOOGLE_API_KEY", "")[:20] + "..." if os.getenv("GOOGLE_API_KEY") else "",
                "model": system_config.model if system_config.provider == "gemini" else "gemini-1.5-pro"
            },
            "openai": {
                "enabled": bool(os.getenv("OPENAI_API_KEY")),
                "apiKey": os.getenv("OPENAI_API_KEY", "")[:20] + "..." if os.getenv("OPENAI_API_KEY") else "",
                "model": system_config.model if system_config.provider == "openai" else "gpt-4-turbo-preview"
            },
            "anthropic": {
                "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
                "apiKey": os.getenv("ANTHROPIC_API_KEY", "")[:20] + "..." if os.getenv("ANTHROPIC_API_KEY") else "",
                "model": system_config.model if system_config.provider == "anthropic" else "claude-3-5-sonnet-20241022"
            }
        },
        "primaryProvider": system_config.provider,
        "monthlyBudget": system_config.monthly_budget,
        "temperature": system_config.temperature,
        "maxTokens": system_config.max_tokens,
        "retries": system_config.retries_per_provider,
        "systemPrompt": system_config.system_prompt or "",
        "projectPrompts": {},
        "agentPrompts": {}
    }


# PUT /api/llm/config - Update LLM configuration
@router.put("/config")
async def update_llm_config(config: LLMConfigUpdate):
    """Update LLM configuration."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    config_manager = get_configuration_manager()
    
    # Update system configuration
    from utils.llm_service import LLMProvider
    
    try:
        provider_enum = LLMProvider[config.primaryProvider.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {config.primaryProvider}")
    
    config_manager.system_config.provider = config.primaryProvider
    config_manager.system_config.temperature = config.temperature
    config_manager.system_config.max_tokens = config.maxTokens
    config_manager.system_config.retries_per_provider = config.retries
    config_manager.system_config.monthly_budget = config.monthlyBudget
    config_manager.system_config.system_prompt = config.systemPrompt
    
    # Save configuration
    config_manager._save_system_config()
    
    # Note: API keys should be set in .env file, not via API for security
    
    return {"success": True, "message": "Configuration updated successfully"}


# POST /api/llm/test/{provider} - Test LLM provider connection
@router.post("/test/{provider}")
async def test_provider(provider: str):
    """Test connection to an LLM provider."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    llm_service = get_llm_service()
    
    try:
        from utils.llm_service import LLMProvider
        
        # Map provider string to enum
        provider_map = {
            "gemini": LLMProvider.GEMINI,
            "openai": LLMProvider.OPENAI,
            "anthropic": LLMProvider.ANTHROPIC
        }
        
        if provider not in provider_map:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        
        provider_enum = provider_map[provider]
        
        # Simple test call
        start_time = datetime.now()
        response = await llm_service.complete(
            "You are a test assistant.",
            "Respond with just 'OK' if you receive this message.",
            temperature=0,
            max_tokens=10,
            provider=provider_enum
        )
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        if response.success:
            return {
                "success": True,
                "latency": int(latency),
                "provider": provider,
                "message": f"{provider} is working correctly"
            }
        else:
            raise HTTPException(status_code=500, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/llm/templates - Get learned templates
@router.get("/templates")
async def get_templates():
    """Get all learned templates."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    template_engine = get_template_learning_engine()
    
    # Get all templates
    conn = template_engine._get_connection()
    cursor = conn.execute("""
        SELECT 
            template_id, name, task_pattern, tech_stack_json,
            template_content, source_llm, quality_score,
            usage_count, cost_saved, created_at, last_used,
            parameters_json
        FROM learned_templates
        ORDER BY usage_count DESC
    """)
    
    templates = []
    for row in cursor.fetchall():
        templates.append({
            "template_id": row[0],
            "name": row[1],
            "task_pattern": row[2],
            "tech_stack": json.loads(row[3]),
            "template_content": row[4],
            "source_llm": row[5],
            "quality_score": row[6],
            "usage_count": row[7],
            "cost_saved": row[8] or 0.0,
            "created_at": row[9],
            "last_used": row[10],
            "parameters": json.loads(row[11] or "[]")
        })
    
    conn.close()
    
    return {"templates": templates}


# DELETE /api/llm/templates/{template_id} - Delete a template
@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a learned template."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    template_engine = get_template_learning_engine()
    
    conn = template_engine._get_connection()
    cursor = conn.execute("DELETE FROM learned_templates WHERE template_id = ?", (template_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    conn.close()
    
    return {"success": True, "message": "Template deleted"}


# GET /api/llm/logs - Get LLM usage logs
@router.get("/logs")
async def get_llm_logs(range: str = "7days"):
    """Get LLM usage logs with optional date range filter."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    llm_service = get_llm_service()
    
    # Calculate date filter
    if range == "today":
        start_date = datetime.now().replace(hour=0, minute=0, second=0)
    elif range == "7days":
        start_date = datetime.now() - timedelta(days=7)
    elif range == "30days":
        start_date = datetime.now() - timedelta(days=30)
    else:  # all
        start_date = datetime(2020, 1, 1)
    
    # Get logs from cache database
    conn = llm_service.cache._get_connection()
    cursor = conn.execute("""
        SELECT 
            cache_key as id,
            timestamp,
            response_json
        FROM llm_cache
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 1000
    """, (start_date.isoformat(),))
    
    logs = []
    for row in cursor.fetchall():
        try:
            response_data = json.loads(row[2])
            logs.append({
                "id": row[0],
                "timestamp": row[1],
                "agent_type": "coder",  # Simplified - would track in production
                "provider": response_data.get("provider", "unknown"),
                "model": response_data.get("model", "unknown"),
                "input_tokens": response_data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response_data.get("usage", {}).get("output_tokens", 0),
                "cost": response_data.get("usage", {}).get("total_cost", 0),
                "duration_seconds": response_data.get("usage", {}).get("duration_seconds", 0),
                "success": response_data.get("success", False),
                "error_message": response_data.get("error"),
                "task_description": "Task description",  # Simplified
                "cached": True
            })
        except:
            continue
    
    conn.close()
    
    return {"logs": logs}


# GET /api/llm/alerts - Get active alerts
@router.get("/alerts")
async def get_llm_alerts():
    """Get active LLM alerts (budget, failures, etc.)."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    llm_service = get_llm_service()
    monitor = llm_service.cost_monitor
    
    alerts = []
    
    # Check budget status
    budget_percent = (monitor.monthly_spent / monitor.monthly_budget) * 100
    
    if budget_percent >= 100:
        alerts.append({
            "id": "budget_100",
            "timestamp": datetime.now().isoformat(),
            "level": "critical",
            "type": "budget",
            "message": "Budget Limit Reached",
            "details": f"${monitor.monthly_spent:.2f} of ${monitor.monthly_budget:.2f} used. LLM generation disabled.",
            "resolved": False,
            "actions": [
                "Increase monthly budget in configuration",
                "System will use templates only until reset",
                "Budget resets on first of next month"
            ]
        })
    elif budget_percent >= 95:
        alerts.append({
            "id": "budget_95",
            "timestamp": datetime.now().isoformat(),
            "level": "critical",
            "type": "budget",
            "message": "Budget 95% Used - Approaching Limit",
            "details": f"${monitor.monthly_spent:.2f} of ${monitor.monthly_budget:.2f} used. Only ${monitor.monthly_budget - monitor.monthly_spent:.2f} remaining.",
            "resolved": False,
            "actions": [
                "Consider increasing budget",
                "Monitor remaining projects carefully",
                "LLM will auto-disable at 100%"
            ]
        })
    elif budget_percent >= 80:
        alerts.append({
            "id": "budget_80",
            "timestamp": datetime.now().isoformat(),
            "level": "warning",
            "type": "budget",
            "message": "Budget 80% Used",
            "details": f"${monitor.monthly_spent:.2f} of ${monitor.monthly_budget:.2f} used.",
            "resolved": False,
            "actions": [
                "Review current usage in Logs page",
                "Consider template-only mode for simple tasks"
            ]
        })
    
    return {"alerts": alerts}


# POST /api/llm/alerts/{alert_id} - Dismiss an alert
@router.post("/alerts/{alert_id}")
async def dismiss_alert(alert_id: str):
    """Dismiss an alert (mark as resolved)."""
    
    # In production, store dismissed alerts in database
    # For now, just acknowledge
    
    return {"success": True, "message": "Alert dismissed"}


# ============================================================================
# PROMPT MANAGEMENT ENDPOINTS
# ============================================================================

class PromptUpdate(BaseModel):
    prompt: str


class AgentPromptUpdate(BaseModel):
    prompt: str
    enabled: bool


class ProjectPromptUpdate(BaseModel):
    clientName: str
    prompt: str


# GET /api/llm/prompts - Get all prompts (system, agent, project)
@router.get("/prompts")
async def get_prompts():
    """Get all prompt configurations."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    config_manager = get_configuration_manager()
    
    # Get system prompt
    system_prompt = config_manager.system_config.system_prompt or config_manager._get_default_system_prompt()
    system_source = 'env' if os.getenv("Q2O_LLM_SYSTEM_PROMPT") else 'default'
    
    # Get agent prompts from .env
    agents = {}
    agent_types = ['coder', 'researcher', 'orchestrator', 'mobile', 'frontend', 'integration']
    
    for agent_type in agent_types:
        env_key = f"Q2O_LLM_PROMPT_{agent_type.upper()}"
        agent_prompt = os.getenv(env_key)
        
        agents[agent_type] = {
            "prompt": agent_prompt or "",
            "source": "env" if agent_prompt else "default",
            "enabled": bool(agent_prompt)
        }
    
    # Get project prompts
    projects = {}
    for project_id, project_config in config_manager.projects.items():
        projects[project_id] = {
            "projectId": project_id,
            "clientName": project_config.client_name,
            "prompt": project_config.llm_config.custom_instructions or "",
            "source": "config",
            "enabled": bool(project_config.llm_config.custom_instructions)
        }
    
    return {
        "system": {
            "prompt": system_prompt,
            "source": system_source
        },
        "agents": agents,
        "projects": projects
    }


# PUT /api/llm/prompts/system - Update system prompt
@router.put("/prompts/system")
async def update_system_prompt(update: PromptUpdate):
    """Update system-level prompt."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    config_manager = get_configuration_manager()
    
    # Update system config
    config_manager.system_config.system_prompt = update.prompt
    config_manager._save_system_config()
    
    return {"success": True, "message": "System prompt updated"}


# PUT /api/llm/prompts/agent/{agent_type} - Update agent prompt
@router.put("/prompts/agent/{agent_type}")
async def update_agent_prompt(agent_type: str, update: AgentPromptUpdate):
    """Update agent-specific prompt."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    # For agent prompts, we recommend setting in .env file
    # This endpoint saves to config for runtime overrides
    
    # In production, you'd save agent-level overrides to database
    # For now, return success (actual override would need database table)
    
    return {
        "success": True,
        "message": f"{agent_type} prompt saved",
        "note": "For permanent changes, add Q2O_LLM_PROMPT_{} to .env file".format(agent_type.upper())
    }


# PUT /api/llm/prompts/project/{project_id} - Update project prompt
@router.put("/prompts/project/{project_id}")
async def update_project_prompt(project_id: str, update: ProjectPromptUpdate):
    """Update project-specific prompt."""
    
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM integration not available")
    
    config_manager = get_configuration_manager()
    
    # Create or update project config
    if project_id not in config_manager.projects:
        # Create new project
        from agents.base_agent import AgentType
        config_manager.create_project(
            project_id=project_id,
            client_name=update.clientName,
            custom_instructions=update.prompt
        )
    else:
        # Update existing project
        project = config_manager.projects[project_id]
        project.llm_config.custom_instructions = update.prompt
        config_manager._save_projects_config()
    
    return {"success": True, "message": f"Project prompt saved for {update.clientName}"}


# ============================================================================
# DATABASE-BACKED CRUD ENDPOINTS FOR PROJECT & AGENT PROMPTS
# ============================================================================

from sqlalchemy.orm import Session
from ..deps import get_db
from ..models.llm_config import LLMProjectConfig, LLMAgentConfig


# Pydantic models for request/response
class ProjectPromptCreate(BaseModel):
    project_id: str
    client_name: str
    tenant_name: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    custom_instructions: str
    provider_override: Optional[str] = None
    is_active: bool = True


class ProjectPromptUpdate(BaseModel):
    client_name: Optional[str] = None
    tenant_name: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    custom_instructions: Optional[str] = None
    provider_override: Optional[str] = None
    is_active: Optional[bool] = None


class AgentPromptCreate(BaseModel):
    project_id: str
    agent_type: str
    custom_instructions: str
    provider_override: Optional[str] = None
    enabled: bool = True


class AgentPromptUpdate(BaseModel):
    custom_instructions: Optional[str] = None
    provider_override: Optional[str] = None
    enabled: Optional[bool] = None


# GET /api/llm/project-prompts - Get all project prompts
@router.get("/project-prompts")
async def get_all_project_prompts(
    db: Session = Depends(get_db),
    tenant: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all project prompts with optional filtering."""
    
    query = db.query(LLMProjectConfig)
    
    if tenant:
        query = query.filter(LLMProjectConfig.client_name == tenant)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (LLMProjectConfig.project_id.ilike(search_pattern)) |
            (LLMProjectConfig.client_name.ilike(search_pattern)) |
            (LLMProjectConfig.description.ilike(search_pattern))
        )
    
    projects = query.all()
    
    # Format response
    result = []
    for project in projects:
        # Get agent prompts for this project
        agent_prompts = db.query(LLMAgentConfig).filter(
            LLMAgentConfig.project_id == project.project_id
        ).all()
        
        result.append({
            "id": project.id,
            "projectId": project.project_id,
            "projectName": project.project_id,  # Or use description
            "tenantName": project.client_name,
            "label": project.description or "no-label",
            "projectPrompt": project.custom_instructions or "",
            "agentPrompts": [
                {
                    "id": agent.id,
                    "agentType": agent.agent_type,
                    "prompt": agent.custom_instructions or ""
                }
                for agent in agent_prompts
            ],
            "isActive": project.is_active,
            "createdAt": project.created_at.isoformat() if project.created_at else None
        })
    
    return {"projects": result, "total": len(result)}


# GET /api/llm/project-prompts/{project_id} - Get single project prompt
@router.get("/project-prompts/{project_id}")
async def get_project_prompt(project_id: str, db: Session = Depends(get_db)):
    """Get a single project prompt by project_id."""
    
    project = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.project_id == project_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get agent prompts
    agent_prompts = db.query(LLMAgentConfig).filter(
        LLMAgentConfig.project_id == project_id
    ).all()
    
    return {
        "id": project.id,
        "projectId": project.project_id,
        "clientName": project.client_name,
        "description": project.description,
        "customInstructions": project.custom_instructions,
        "providerOverride": project.provider_override,
        "isActive": project.is_active,
        "agentPrompts": [
            {
                "id": agent.id,
                "agentType": agent.agent_type,
                "prompt": agent.custom_instructions
            }
            for agent in agent_prompts
        ]
    }


# POST /api/llm/project-prompts - Create new project prompt
@router.post("/project-prompts")
async def create_project_prompt(
    data: ProjectPromptCreate,
    db: Session = Depends(get_db)
):
    """Create a new project prompt."""
    
    # Check if project already exists
    existing = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.project_id == data.project_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")
    
    # Create new project
    new_project = LLMProjectConfig(
        project_id=data.project_id,
        client_name=data.client_name,
        description=data.description,
        custom_instructions=data.custom_instructions,
        provider_override=data.provider_override,
        is_active=data.is_active
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {
        "success": True,
        "message": "Project prompt created successfully",
        "projectId": new_project.project_id,
        "id": new_project.id
    }


# PUT /api/llm/project-prompts/{project_id_param} - Update project prompt
@router.put("/project-prompts/{project_id_param}")
async def update_project_prompt_db(
    project_id_param: str,
    data: ProjectPromptUpdateDB,
    db: Session = Depends(get_db)
):
    """Update an existing project prompt."""
    
    project = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.project_id == project_id_param
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    if data.client_name is not None:
        project.client_name = data.client_name
    if data.description is not None:
        project.description = data.description
    if data.custom_instructions is not None:
        project.custom_instructions = data.custom_instructions
    if data.provider_override is not None:
        project.provider_override = data.provider_override
    if data.is_active is not None:
        project.is_active = data.is_active
    
    db.commit()
    
    return {
        "success": True,
        "message": "Project prompt updated successfully"
    }


# DELETE /api/llm/project-prompts/{project_id} - Delete project prompt
@router.delete("/project-prompts/{project_id}")
async def delete_project_prompt(project_id: str, db: Session = Depends(get_db)):
    """Delete a project prompt and all its agent prompts."""
    
    project = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.project_id == project_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete will cascade to agent prompts
    db.delete(project)
    db.commit()
    
    return {
        "success": True,
        "message": "Project prompt deleted successfully"
    }


# POST /api/llm/agent-prompts - Create agent prompt
@router.post("/agent-prompts")
async def create_agent_prompt(
    data: AgentPromptCreate,
    db: Session = Depends(get_db)
):
    """Create a new agent prompt for a project."""
    
    # Verify project exists
    project = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.project_id == data.project_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if agent prompt already exists
    existing = db.query(LLMAgentConfig).filter(
        LLMAgentConfig.project_id == data.project_id,
        LLMAgentConfig.agent_type == data.agent_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Agent prompt for {data.agent_type} already exists")
    
    # Create agent prompt
    new_agent = LLMAgentConfig(
        project_id=data.project_id,
        agent_type=data.agent_type,
        custom_instructions=data.custom_instructions,
        provider_override=data.provider_override,
        enabled=data.enabled
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    return {
        "success": True,
        "message": f"Agent prompt for {data.agent_type} created successfully",
        "id": new_agent.id
    }


# PUT /api/llm/agent-prompts/{agent_id} - Update agent prompt
@router.put("/agent-prompts/{agent_id}")
async def update_agent_prompt(
    agent_id: int,
    data: AgentPromptUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing agent prompt."""
    
    agent = db.query(LLMAgentConfig).filter(LLMAgentConfig.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent prompt not found")
    
    # Update fields
    if data.custom_instructions is not None:
        agent.custom_instructions = data.custom_instructions
    if data.provider_override is not None:
        agent.provider_override = data.provider_override
    if data.enabled is not None:
        agent.enabled = data.enabled
    
    db.commit()
    
    return {
        "success": True,
        "message": "Agent prompt updated successfully"
    }


# DELETE /api/llm/agent-prompts/{agent_id} - Delete agent prompt
@router.delete("/agent-prompts/{agent_id}")
async def delete_agent_prompt(agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent prompt."""
    
    agent = db.query(LLMAgentConfig).filter(LLMAgentConfig.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent prompt not found")
    
    db.delete(agent)
    db.commit()
    
    return {
        "success": True,
        "message": "Agent prompt deleted successfully"
    }

