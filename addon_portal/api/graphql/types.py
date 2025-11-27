"""
GraphQL Types for Q2O Multi-Agent Dashboard

Strongly-typed schema definitions for all entities exposed via GraphQL.
"""
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import strawberry
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


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
            return 0.0  # No tasks = 0% success rate, not 100%
        rate = (self.tasks_completed / total) * 100.0
        return min(100.0, max(0.0, rate))  # Cap between 0% and 100%


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
        """
        Get project tasks (filtered, batched).
        
        For COMPLETED status: Only returns tasks with completed_at set, sorted chronologically (oldest first).
        This ensures the Task Timeline shows tasks in the order they were completed.
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        if not db:
            logger.warning("No database session available for project.tasks query")
            return []
        
        from ..models.agent_tasks import AgentTask
        from sqlalchemy import select, and_
        
        # Build query for this project
        stmt = select(AgentTask).where(AgentTask.project_id == self.id)
        
        # Apply status filter
        if status:
            if status == TaskStatus.COMPLETED:
                # For completed tasks: only return tasks with completed_at set
                stmt = stmt.where(
                    and_(
                        AgentTask.status == 'completed',
                        AgentTask.completed_at.isnot(None)
                    )
                )
                # Sort by completed_at ascending (oldest first for timeline)
                stmt = stmt.order_by(AgentTask.completed_at.asc())
            elif status == TaskStatus.IN_PROGRESS:
                stmt = stmt.where(AgentTask.status.in_(['started', 'running']))
                stmt = stmt.order_by(AgentTask.created_at.desc())
            elif status == TaskStatus.FAILED:
                stmt = stmt.where(AgentTask.status == 'failed')
                stmt = stmt.order_by(AgentTask.created_at.desc())
            elif status == TaskStatus.PENDING:
                stmt = stmt.where(AgentTask.status == 'pending')
                stmt = stmt.order_by(AgentTask.created_at.desc())
        else:
            # No status filter: return all tasks, sorted by created_at
            stmt = stmt.order_by(AgentTask.created_at.desc())
        
        stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        db_tasks = result.scalars().all()
        
        # Convert to GraphQL Task objects
        tasks = []
        for db_task in db_tasks:
            # Map agent_type to AgentType enum
            try:
                agent_type_str = db_task.agent_type.upper()
                agent_type = AgentType[agent_type_str] if agent_type_str in [e.name for e in AgentType] else AgentType.CODER
            except (KeyError, AttributeError):
                agent_type = AgentType.CODER
            
            # Map status
            status_map = {
                'pending': TaskStatus.PENDING,
                'started': TaskStatus.IN_PROGRESS,
                'running': TaskStatus.IN_PROGRESS,
                'completed': TaskStatus.COMPLETED,
                'failed': TaskStatus.FAILED,
                'cancelled': TaskStatus.CANCELLED,
            }
            task_status = status_map.get(db_task.status, TaskStatus.PENDING)
            
            # Ensure timezone-aware datetimes
            created_at = db_task.created_at
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            started_at = db_task.started_at
            if started_at and started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            
            completed_at = db_task.completed_at
            if completed_at and completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            
            tasks.append(Task(
                id=db_task.task_id,
                project_id=db_task.project_id,
                agent_type=agent_type,
                title=db_task.task_name,
                description=db_task.task_description or "",
                status=task_status,
                priority=db_task.priority,
                created_at=created_at,
                started_at=started_at,
                completed_at=completed_at,
                error_message=db_task.error_message
            ))
        
        return tasks
    
    @strawberry.field
    def success_rate(self) -> float:
        """
        Calculate project success rate based on finished tasks only.
        
        Success Rate = (Completed Tasks) / (Completed + Failed Tasks) * 100%
        
        This shows the percentage of finished tasks that succeeded.
        Only counts tasks that have finished (completed or failed), not pending/in_progress.
        
        Examples:
        - 50 completed, 3 failed, 28 active, 19 pending
          Success Rate = 50 / (50 + 3) = 94.3%
        - 100 completed, 0 failed
          Success Rate = 100 / (100 + 0) = 100%
        - 0 completed, 10 failed
          Success Rate = 0 / (0 + 10) = 0%
        """
        finished_tasks = self.completed_tasks + self.failed_tasks
        if finished_tasks == 0:
            return 0.0  # No finished tasks = 0% success rate
        rate = (self.completed_tasks / finished_tasks) * 100.0
        return max(0.0, min(100.0, rate))  # Cap between 0% and 100%


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

