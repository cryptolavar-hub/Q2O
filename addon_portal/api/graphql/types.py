"""
GraphQL Types for Q2O Multi-Agent Dashboard

Strongly-typed schema definitions for all entities exposed via GraphQL.
"""
from typing import Optional, List
from datetime import datetime
from enum import Enum
import strawberry


# ============================================================================
# ENUMS
# ============================================================================

@strawberry.enum
class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@strawberry.enum
class AgentType(Enum):
    """12 Specialized Agent Types"""
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    CODER = "coder"
    INTEGRATION = "integration"
    FRONTEND = "frontend"
    WORKFLOW = "workflow"
    TESTING = "testing"
    QA = "qa"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    NODE = "node"
    MOBILE = "mobile"


@strawberry.enum
class ProjectStatus(Enum):
    """Q2O Project status"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ON_HOLD = "on_hold"


# ============================================================================
# TYPES
# ============================================================================

@strawberry.type
class Agent:
    """AI Agent instance"""
    id: str
    type: AgentType
    name: str
    status: str
    health_score: float
    tasks_completed: int
    tasks_failed: int
    current_task_id: Optional[str]
    last_activity: datetime
    
    # Alias field for frontend compatibility (agentType -> type)
    @strawberry.field
    def agent_type(self) -> AgentType:
        """Alias for type field (for frontend compatibility)"""
        return self.type
    
    # Computed fields (resolved dynamically)
    @strawberry.field
    def success_rate(self) -> float:
        """Calculate agent success rate"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 100.0
        return (self.tasks_completed / total) * 100


@strawberry.type
class Task:
    """Agent task"""
    id: str
    project_id: str
    agent_type: AgentType
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    # Relationships (loaded via DataLoader for performance)
    @strawberry.field
    async def project(self, info) -> "Project":
        """Get parent project (batched)"""
        loader = info.context["project_loader"]
        return await loader.load(self.project_id)
    
    @strawberry.field
    async def agent(self, info) -> Optional[Agent]:
        """Get assigned agent (batched)"""
        loader = info.context["agent_loader"]
        return await loader.load(self.agent_type)
    
    @strawberry.field
    def duration_seconds(self) -> Optional[int]:
        """Calculate task duration"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


@strawberry.type
class Project:
    """Q2O AI-generated project"""
    id: str
    name: str
    objective: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    completion_percentage: float
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    agents: List[Agent] = strawberry.field(default_factory=list)
    estimated_time_remaining_seconds: Optional[int] = None
    
    # Relationships
    @strawberry.field
    async def tasks(
        self,
        info,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Task]:
        """Get project tasks (filtered, batched)"""
        loader = info.context.get("tasks_by_project_loader") if info.context else None
        if loader:
            all_tasks = await loader.load(self.id)
            # Filter by status if provided
            if status:
                all_tasks = [t for t in all_tasks if t.status == status]
            return all_tasks[:limit]
        return []
    
    @strawberry.field
    def success_rate(self) -> float:
        """Calculate project success rate"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100


@strawberry.type
class AgentActivity:
    """Real-time agent activity event"""
    id: str
    agent_type: AgentType
    agent_id: str
    event_type: str
    message: str
    timestamp: datetime
    task_id: Optional[str]
    metadata: Optional[str]  # JSON string


@strawberry.type
class SystemMetrics:
    """System-wide performance metrics"""
    timestamp: datetime
    active_agents: int
    active_tasks: int
    tasks_completed_today: int
    tasks_failed_today: int
    average_task_duration_seconds: float
    system_health_score: float
    cpu_usage_percent: float
    memory_usage_percent: float


@strawberry.type
class DashboardStats:
    """High-level dashboard statistics"""
    total_projects: int
    active_projects: int
    total_tasks: int
    active_tasks: int
    completed_tasks_today: int
    average_success_rate: float
    most_active_agent: Optional[AgentType]
    recent_activities: List[AgentActivity]


# ============================================================================
# INPUT TYPES (for mutations)
# ============================================================================

@strawberry.input
class CreateProjectInput:
    """Input for creating a new Q2O project"""
    name: str
    objective: str
    config: Optional[str] = None  # JSON config


@strawberry.input
class UpdateTaskInput:
    """Input for updating a task"""
    task_id: str
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None


@strawberry.input
class TaskFilterInput:
    """Flexible task filtering"""
    status: Optional[TaskStatus] = None
    agent_type: Optional[AgentType] = None
    project_id: Optional[str] = None
    created_after: Optional[datetime] = None


@strawberry.input
class ProjectFilterInput:
    """Flexible project filtering"""
    status: Optional[ProjectStatus] = None
    name_contains: Optional[str] = None
    created_after: Optional[datetime] = None

