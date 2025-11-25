"""
Pydantic models for dashboard API responses.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TaskStateModel(BaseModel):
    """Model for a single task state."""
    task_id: str
    status: str
    title: Optional[str] = None
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: Optional[float] = None
    progress: Optional[int] = None
    error: Optional[str] = None
    dependencies: Optional[List[str]] = None


class AgentStateModel(BaseModel):
    """Model for a single agent state."""
    agent_id: str
    agent_type: str
    status: str  # idle, active, busy
    activity: Optional[str] = None
    task_id: Optional[str] = None
    last_activity: Optional[str] = None


class SystemMetricsModel(BaseModel):
    """Model for system metrics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    in_progress_tasks: int = 0
    pending_tasks: int = 0
    completion_percentage: float = 0.0
    active_agents: int = 0
    idle_agents: int = 0
    average_task_time: float = 0.0


class ProjectModel(BaseModel):
    """Model for project information."""
    name: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    estimatedTimeRemaining: Optional[float] = None


class DashboardStateModel(BaseModel):
    """Model for complete dashboard state."""
    project: Optional[Dict[str, Any]] = None
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None

