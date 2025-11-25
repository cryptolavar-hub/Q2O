"""
Pydantic models for Dashboard API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class TaskStatusModel(BaseModel):
    """Task status model for dashboard."""
    id: str
    title: str
    status: str = Field(..., description="pending, in_progress, completed, failed, blocked")
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    progress: int = Field(0, ge=0, le=100, description="Progress percentage 0-100")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentActivityModel(BaseModel):
    """Agent activity model for dashboard."""
    agent_id: str
    agent_type: str
    status: str = Field(..., description="idle, active, error")
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=100.0)
    last_activity: Optional[str] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class SystemMetricsModel(BaseModel):
    """System metrics model for dashboard."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    in_progress_tasks: int = 0
    pending_tasks: int = 0
    completion_percentage: float = Field(0.0, ge=0.0, le=100.0)
    active_agents: int = 0
    idle_agents: int = 0
    average_task_time: float = 0.0
    success_rate: float = Field(0.0, ge=0.0, le=100.0)


class ProjectInfoModel(BaseModel):
    """Project information model."""
    project_description: str
    objectives: List[str]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class DashboardStateModel(BaseModel):
    """Complete dashboard state model."""
    tasks: Dict[str, TaskStatusModel] = Field(default_factory=dict)
    agents: Dict[str, AgentActivityModel] = Field(default_factory=dict)
    metrics: SystemMetricsModel
    project: Optional[ProjectInfoModel] = None

