"""
GraphQL Resolvers for Q2O Multi-Agent Dashboard

Handles queries, mutations, and subscriptions.
Integrates with existing database and WebSocket system.
"""
from typing import List, Optional, AsyncGenerator
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import strawberry
import asyncio

from .types import (
    Agent, Task, Project, AgentActivity, SystemMetrics, DashboardStats,
    TaskStatus, AgentType, ProjectStatus,
    CreateProjectInput, UpdateTaskInput, TaskFilterInput, ProjectFilterInput
)
from ..core.logging import get_logger

logger = get_logger(__name__)

# Event queue for real-time subscriptions
subscription_queue: asyncio.Queue = asyncio.Queue()


# ============================================================================
# QUERY RESOLVERS
# ============================================================================

@strawberry.type
class Query:
    """Root Query - All read operations"""
    
    @strawberry.field
    async def agents(
        self,
        info,
        agent_type: Optional[AgentType] = None,
        min_health: float = 0.0
    ) -> List[Agent]:
        """
        Get all agents with optional filtering from REAL database
        
        Example:
        query {
          agents(agentType: CODER, minHealth: 0.8) {
            id
            type
            name
            successRate
            currentTaskId
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        if not db:
            logger.warning("No database session available for agents query")
            return []
        
        # Query REAL agents from database (aggregate from tasks and agent configs)
        from ..models.agent_tasks import AgentTask
        from ..models.llm_config import LLMAgentConfig
        from sqlalchemy import func, and_, case
        
        # Get distinct agent types from tasks
        stmt = select(
            AgentTask.agent_type,
            func.count(AgentTask.id).label('total_tasks'),
            func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
            func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed'),
            func.max(AgentTask.updated_at).label('last_activity')
        ).group_by(AgentTask.agent_type)
        
        # Filter by agent_type if provided
        if agent_type:
            agent_type_str = agent_type.name.lower()
            stmt = stmt.where(AgentTask.agent_type == agent_type_str)
        
        result = await db.execute(stmt)
        agent_stats = result.all()
        
        # Build Agent objects from statistics
        agents = []
        for stats in agent_stats:
            try:
                agent_type_str = stats.agent_type.upper()
                agent_type_enum = AgentType[agent_type_str] if agent_type_str in [e.name for e in AgentType] else AgentType.CODER
            except (KeyError, AttributeError):
                agent_type_enum = AgentType.CODER
            
            total_tasks = stats.total_tasks or 0
            completed = stats.completed or 0
            failed = stats.failed or 0
            
            # Calculate health score (success rate)
            if total_tasks > 0:
                health_score = (completed / total_tasks) * 100.0
            else:
                health_score = 0.0
            
            # Apply min_health filter
            if min_health > 0 and health_score < min_health:
                continue
            
            # Get current task (most recent running task)
            current_task_result = await db.execute(
                select(AgentTask.task_id)
                .where(
                    and_(
                        AgentTask.agent_type == stats.agent_type,
                        AgentTask.status.in_(['started', 'running'])
                    )
                )
                .order_by(AgentTask.started_at.desc())
                .limit(1)
            )
            current_task = current_task_result.scalar_one_or_none()
            
            # Determine status
            status = "active" if current_task else "idle"
            
            last_activity = stats.last_activity or datetime.now(timezone.utc)
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            
            agents.append(Agent(
                id=f"agent-{stats.agent_type}",
                type=agent_type_enum,
                name=f"{stats.agent_type.title()} Agent",
                status=status,
                health_score=health_score,
                tasks_completed=completed,
                tasks_failed=failed,
                current_task_id=current_task,
                last_activity=last_activity
            ))
        
        return agents
    
    @strawberry.field
    async def tasks(
        self,
        info,
        filter: Optional[TaskFilterInput] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Task]:
        """
        Get tasks with flexible filtering from REAL database
        
        Example:
        query {
          tasks(
            filter: { status: IN_PROGRESS, agentType: CODER }
            limit: 10
          ) {
            id
            title
            status
            project { name }
            agent { name successRate }
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        if not db:
            logger.warning("No database session available for tasks query")
            return []
        
        # Query REAL tasks from database
        from ..models.agent_tasks import AgentTask
        
        stmt = select(AgentTask)
        
        # Apply filters
        if filter:
            if filter.status:
                # Map GraphQL TaskStatus to database status
                status_map = {
                    TaskStatus.PENDING: 'pending',
                    TaskStatus.IN_PROGRESS: ['started', 'running'],
                    TaskStatus.COMPLETED: 'completed',
                    TaskStatus.FAILED: 'failed',
                    TaskStatus.CANCELLED: 'cancelled',
                }
                db_status = status_map.get(filter.status)
                if isinstance(db_status, list):
                    stmt = stmt.where(AgentTask.status.in_(db_status))
                else:
                    stmt = stmt.where(AgentTask.status == db_status)
            
            if filter.agent_type:
                # Map GraphQL AgentType to database agent_type
                agent_type_str = filter.agent_type.name.lower()
                stmt = stmt.where(AgentTask.agent_type == agent_type_str)
            
            if filter.project_id:
                stmt = stmt.where(AgentTask.project_id == filter.project_id)
            
            if filter.created_after:
                stmt = stmt.where(AgentTask.created_at >= filter.created_after)
        
        stmt = stmt.order_by(AgentTask.created_at.desc()).limit(limit).offset(offset)
        
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
    async def projects(
        self,
        info,
        filter: Optional[ProjectFilterInput] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Project]:
        """
        Get projects with filtering
        
        Example:
        query {
          projects(filter: { status: IN_PROGRESS }) {
            id
            name
            objective
            completionPercentage
            successRate
            tasks(status: IN_PROGRESS) {
              title
              status
            }
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        # In production, query from projects table
        projects = [
            Project(
                id=f"project-{i}",
                name=f"QuickBooks Migration {i}",
                objective=f"Migrate QuickBooks data to Odoo for client {i}",
                status=ProjectStatus.IN_PROGRESS if i <= 2 else ProjectStatus.COMPLETED,
                created_at=datetime.utcnow() - timedelta(days=i*2),
                updated_at=datetime.utcnow() - timedelta(hours=i),
                completion_percentage=75.0 if i <= 2 else 100.0,
                total_tasks=20,
                completed_tasks=15 if i <= 2 else 20,
                failed_tasks=0
            )
            for i in range(1, 11)
        ]
        
        # Apply filters
        if filter:
            if filter.status:
                projects = [p for p in projects if p.status == filter.status]
            if filter.name_contains:
                projects = [p for p in projects if filter.name_contains.lower() in p.name.lower()]
            if filter.created_after:
                projects = [p for p in projects if p.created_at >= filter.created_after]
        
        return projects[offset:offset + limit]
    
    @strawberry.field
    async def project(self, info, id: str) -> Optional[Project]:
        """
        Get single project by ID
        
        Example:
        query {
          project(id: "project-1") {
            name
            tasks {
              title
              status
              durationSeconds
            }
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        if not db:
            logger.warning("No database session available for project query")
            return None
        
        # Query real project from database
        from ..models.llm_config import LLMProjectConfig
        from sqlalchemy.orm import selectinload
        
        logger.info(f"Querying project with id: {id}")
        result = await db.execute(
            select(LLMProjectConfig)
            .options(selectinload(LLMProjectConfig.agent_configs))
            .where(LLMProjectConfig.project_id == id)
        )
        db_project = result.scalar_one_or_none()
        
        if not db_project:
            logger.warning(f"Project not found with id: {id}")
            return None
        
        logger.info(f"Found project: {db_project.project_id}, execution_status: {db_project.execution_status}")
        
        # Map execution_status to ProjectStatus
        status_map = {
            'pending': ProjectStatus.PLANNING,
            'running': ProjectStatus.IN_PROGRESS,
            'completed': ProjectStatus.COMPLETED,
            'failed': ProjectStatus.FAILED,
            'paused': ProjectStatus.ON_HOLD,
        }
        project_status = status_map.get(db_project.execution_status, ProjectStatus.PLANNING)
        
        # Calculate REAL completion percentage from actual tasks
        from ..services.agent_task_service import calculate_project_progress, get_project_tasks
        from ..models.agent_tasks import AgentTask
        
        # CRITICAL FIX: Pass execution_started_at to only count tasks from current run
        # This prevents showing stale data from previous runs when project is restarted
        execution_started_at = db_project.execution_started_at
        
        # Get real task statistics (filtered by execution_started_at if available)
        task_stats = await calculate_project_progress(db, id, execution_started_at=execution_started_at)
        total_tasks = task_stats["total_tasks"]
        completed_tasks = task_stats["completed_tasks"]
        failed_tasks = task_stats["failed_tasks"]
        completion_percentage = task_stats["completion_percentage"]
        
        logger.info(
            f"Project {id} task stats: total={total_tasks}, completed={completed_tasks}, "
            f"failed={failed_tasks}, completion={completion_percentage}%"
        )
        
        # If no tasks exist yet, use status-based fallback
        if total_tasks == 0:
            if db_project.execution_status == 'completed':
                completion_percentage = 100.0
            elif db_project.execution_status == 'running':
                completion_percentage = 5.0  # Just started, minimal progress
            elif db_project.execution_status == 'failed':
                completion_percentage = 0.0
            else:
                completion_percentage = 0.0
        
        # Map agent_configs to Agent objects with REAL task statistics
        agents = []
        if db_project.agent_configs:
            # Get task counts per agent type
            agent_task_counts = {}
            if total_tasks > 0:
                agent_tasks = await get_project_tasks(db, id)
                for task in agent_tasks:
                    agent_type = task.agent_type
                    if agent_type not in agent_task_counts:
                        agent_task_counts[agent_type] = {"completed": 0, "failed": 0, "running": None}
                    if task.status == 'completed':
                        agent_task_counts[agent_type]["completed"] += 1
                    elif task.status == 'failed':
                        agent_task_counts[agent_type]["failed"] += 1
                    elif task.status in ('started', 'running') and not agent_task_counts[agent_type]["running"]:
                        agent_task_counts[agent_type]["running"] = task.task_id
            
            for agent_config in db_project.agent_configs:
                try:
                    # Map agent_type string to AgentType enum
                    agent_type_str = agent_config.agent_type.upper()
                    agent_type = AgentType[agent_type_str] if agent_type_str in [e.name for e in AgentType] else AgentType.CODER
                except (KeyError, AttributeError):
                    agent_type = AgentType.CODER
                
                # Get real task statistics for this agent
                agent_stats = agent_task_counts.get(agent_config.agent_type, {"completed": 0, "failed": 0, "running": None})
                tasks_completed = agent_stats["completed"]
                tasks_failed = agent_stats["failed"]
                current_task_id = agent_stats["running"]
                
                # Agent is "active" if project is running AND agent is enabled AND has active tasks
                agent_status = "active" if (
                    db_project.execution_status == 'running' 
                    and agent_config.enabled 
                    and current_task_id is not None
                ) else "idle"
                
                # Health score based on success rate
                total_agent_tasks = tasks_completed + tasks_failed
                if total_agent_tasks > 0:
                    health_score = (tasks_completed / total_agent_tasks) * 100.0
                elif agent_status == "active":
                    health_score = 100.0  # Active but no completed tasks yet
                else:
                    health_score = 0.0
                
                agents.append(Agent(
                    id=f"{db_project.project_id}-{agent_config.agent_type}",
                    type=agent_type,
                    name=f"{agent_config.agent_type.title()} Agent",
                    status=agent_status,
                    health_score=health_score,
                    tasks_completed=tasks_completed,
                    tasks_failed=tasks_failed,
                    current_task_id=current_task_id,
                    last_activity=agent_config.updated_at or agent_config.created_at or datetime.now(timezone.utc)
                ))
        
        # Calculate estimated time remaining based on REAL task data
        estimated_time_remaining = None
        if db_project.execution_status == 'running' and total_tasks > 0:
            # Get average task duration from completed tasks
            result = await db.execute(
                select(func.avg(AgentTask.actual_duration_seconds))
                .where(
                    and_(
                        AgentTask.project_id == id,
                        AgentTask.status == 'completed',
                        AgentTask.actual_duration_seconds.isnot(None)
                    )
                )
            )
            avg_duration = result.scalar()
            
            if avg_duration:
                # Estimate: remaining tasks * average duration
                remaining_tasks = total_tasks - completed_tasks - failed_tasks
                estimated_time_remaining = int(remaining_tasks * avg_duration)
            elif db_project.execution_started_at:
                # Fallback: estimate based on elapsed time and progress
                started_at = db_project.execution_started_at
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                elapsed_seconds = (now - started_at).total_seconds()
                if completion_percentage > 0:
                    # Cap completion_percentage to prevent division by very small numbers
                    capped_completion = max(0.1, min(100.0, completion_percentage))
                    estimated_total_seconds = (elapsed_seconds / capped_completion) * 100.0
                    remaining = max(0, estimated_total_seconds - elapsed_seconds)
                    estimated_time_remaining = int(remaining)
        
        # Create Project object with REAL data
        # Note: tasks field is loaded via resolver method, not passed directly
        project = Project(
            id=db_project.project_id,
            name=db_project.client_name or "Unnamed Project",
            objective=db_project.custom_instructions or db_project.description or "",
            status=project_status,
            created_at=db_project.created_at or datetime.now(timezone.utc),
            updated_at=db_project.updated_at or db_project.created_at or datetime.now(timezone.utc),
            completion_percentage=completion_percentage,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            agents=agents,
            estimated_time_remaining_seconds=estimated_time_remaining
        )
        
        return project
    
    @strawberry.field
    async def dashboard_stats(self, info) -> DashboardStats:
        """
        Get high-level dashboard statistics from REAL database data
        
        Example:
        query {
          dashboardStats {
            totalProjects
            activeTasks
            completedTasksToday
            averageSuccessRate
            mostActiveAgent
            recentActivities {
              agentType
              message
              timestamp
            }
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        if not db:
            logger.warning("No database session available for dashboard_stats")
            return DashboardStats(
                total_projects=0,
                active_projects=0,
                total_tasks=0,
                active_tasks=0,
                completed_tasks_today=0,
                average_success_rate=0.0,
                most_active_agent=None,
                recent_activities=[]
            )
        
        # Get REAL statistics from database
        from ..models.llm_config import LLMProjectConfig
        from ..models.agent_tasks import AgentTask
        from datetime import datetime, timezone, timedelta
        
        # Count projects
        result = await db.execute(select(func.count(LLMProjectConfig.id)))
        total_projects = result.scalar() or 0
        
        result = await db.execute(
            select(func.count(LLMProjectConfig.id))
            .where(LLMProjectConfig.execution_status == 'running')
        )
        active_projects = result.scalar() or 0
        
        # Count tasks
        result = await db.execute(select(func.count(AgentTask.id)))
        total_tasks = result.scalar() or 0
        
        result = await db.execute(
            select(func.count(AgentTask.id))
            .where(AgentTask.status.in_(['started', 'running']))
        )
        active_tasks = result.scalar() or 0
        
        # Tasks completed today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(AgentTask.id))
            .where(
                and_(
                    AgentTask.status == 'completed',
                    AgentTask.completed_at >= today_start
                )
            )
        )
        completed_tasks_today = result.scalar() or 0
        
        # Calculate average success rate
        from sqlalchemy import case
        result = await db.execute(
            select(
                func.count(AgentTask.id).label('total'),
                func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed')
            )
        )
        stats = result.first()
        total_completed = stats.total or 0
        completed = stats.completed or 0
        average_success_rate = (completed / total_completed * 100.0) if total_completed > 0 else 0.0
        
        # Find most active agent type
        result = await db.execute(
            select(AgentTask.agent_type, func.count(AgentTask.id).label('count'))
            .where(AgentTask.status == 'completed')
            .group_by(AgentTask.agent_type)
            .order_by(func.count(AgentTask.id).desc())
            .limit(1)
        )
        most_active = result.first()
        most_active_agent = None
        if most_active:
            try:
                agent_type_str = most_active.agent_type.upper()
                most_active_agent = AgentType[agent_type_str] if agent_type_str in [e.name for e in AgentType] else None
            except (KeyError, AttributeError):
                pass
        
        # Get recent activities (last 5 completed tasks)
        result = await db.execute(
            select(AgentTask)
            .where(AgentTask.status == 'completed')
            .order_by(AgentTask.completed_at.desc())
            .limit(5)
        )
        recent_tasks = result.scalars().all()
        
        recent_activities = []
        for task in recent_tasks:
            try:
                agent_type_str = task.agent_type.upper()
                agent_type = AgentType[agent_type_str] if agent_type_str in [e.name for e in AgentType] else AgentType.CODER
            except (KeyError, AttributeError):
                agent_type = AgentType.CODER
            
            completed_at = task.completed_at or datetime.now(timezone.utc)
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            
            recent_activities.append(AgentActivity(
                id=task.task_id,
                agent_type=agent_type,
                agent_id=task.agent_id or f"{task.project_id}-{task.agent_type}",
                event_type="task_completed",
                message=f"Completed task: {task.task_name}",
                timestamp=completed_at,
                task_id=task.task_id,
                metadata=None
            ))
        
        return DashboardStats(
            total_projects=total_projects,
            active_projects=active_projects,
            total_tasks=total_tasks,
            active_tasks=active_tasks,
            completed_tasks_today=completed_tasks_today,
            average_success_rate=average_success_rate,
            most_active_agent=most_active_agent,
            recent_activities=recent_activities
        )
    
    @strawberry.field
    async def system_metrics(self, info) -> SystemMetrics:
        """
        Get real-time system metrics from REAL database data
        
        Example:
        query {
          systemMetrics {
            activeAgents
            activeTasks
            tasksCompletedToday
            averageTaskDurationSeconds
            systemHealthScore
            cpuUsagePercent
            memoryUsagePercent
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        if not db:
            logger.warning("No database session available for system_metrics")
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                active_agents=0,
                active_tasks=0,
                tasks_completed_today=0,
                tasks_failed_today=0,
                average_task_duration_seconds=0.0,
                system_health_score=0.0,
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0
            )
        
        # Get REAL metrics from database
        from ..models.agent_tasks import AgentTask
        from ..models.llm_config import LLMProjectConfig, LLMAgentConfig
        from datetime import datetime, timezone, timedelta
        try:
            import psutil
        except ImportError:
            psutil = None
        
        # Count active agents (agents with running tasks)
        result = await db.execute(
            select(func.count(func.distinct(AgentTask.agent_type)))
            .where(AgentTask.status.in_(['started', 'running']))
        )
        active_agents = result.scalar() or 0
        
        # Count active tasks
        result = await db.execute(
            select(func.count(AgentTask.id))
            .where(AgentTask.status.in_(['started', 'running']))
        )
        active_tasks = result.scalar() or 0
        
        # Tasks completed today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(AgentTask.id))
            .where(
                and_(
                    AgentTask.status == 'completed',
                    AgentTask.completed_at >= today_start
                )
            )
        )
        tasks_completed_today = result.scalar() or 0
        
        # Tasks failed today
        result = await db.execute(
            select(func.count(AgentTask.id))
            .where(
                and_(
                    AgentTask.status == 'failed',
                    AgentTask.failed_at >= today_start
                )
            )
        )
        tasks_failed_today = result.scalar() or 0
        
        # Average task duration (from completed tasks)
        result = await db.execute(
            select(func.avg(AgentTask.actual_duration_seconds))
            .where(
                and_(
                    AgentTask.status == 'completed',
                    AgentTask.actual_duration_seconds.isnot(None)
                )
            )
        )
        avg_duration = result.scalar() or 0.0
        
        # System health score (based on success rate)
        from sqlalchemy import case
        result = await db.execute(
            select(
                func.count(AgentTask.id).label('total'),
                func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed')
            )
        )
        stats = result.first()
        total = stats.total or 0
        completed = stats.completed or 0
        failed = stats.failed or 0
        
        if total > 0:
            system_health_score = ((completed - failed * 0.5) / total) * 100.0
            system_health_score = max(0.0, min(100.0, system_health_score))
        else:
            system_health_score = 100.0  # No tasks = healthy
        
        # System resource usage (from psutil)
        try:
            if psutil:
                cpu_usage_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                memory_usage_percent = memory.percent
            else:
                cpu_usage_percent = 0.0
                memory_usage_percent = 0.0
        except Exception:
            # Fallback if psutil not available
            cpu_usage_percent = 0.0
            memory_usage_percent = 0.0
        
        return SystemMetrics(
            timestamp=datetime.now(timezone.utc),
            active_agents=active_agents,
            active_tasks=active_tasks,
            tasks_completed_today=tasks_completed_today,
            tasks_failed_today=tasks_failed_today,
            average_task_duration_seconds=float(avg_duration),
            system_health_score=system_health_score,
            cpu_usage_percent=cpu_usage_percent,
            memory_usage_percent=memory_usage_percent
        )


# ============================================================================
# MUTATION RESOLVERS
# ============================================================================

@strawberry.type
class Mutation:
    """Root Mutation - All write operations"""
    
    @strawberry.mutation
    async def create_project(
        self,
        info,
        input: CreateProjectInput
    ) -> Project:
        """
        Create a new Q2O project
        
        Example:
        mutation {
          createProject(input: {
            name: "Stripe Integration"
            objective: "Integrate Stripe payments into Odoo"
          }) {
            id
            name
            status
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        # In production, insert into database
        new_project = Project(
            id=f"project-{datetime.utcnow().timestamp()}",
            name=input.name,
            objective=input.objective,
            status=ProjectStatus.PLANNING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completion_percentage=0.0,
            total_tasks=0,
            completed_tasks=0,
            failed_tasks=0
        )
        
        logger.info(f"Created project: {new_project.name} (ID: {new_project.id})")
        
        # Broadcast event to subscribers
        await subscription_queue.put({
            "type": "project_created",
            "project": new_project
        })
        
        return new_project
    
    @strawberry.mutation
    async def update_task(
        self,
        info,
        input: UpdateTaskInput
    ) -> Task:
        """
        Update task status
        
        Example:
        mutation {
          updateTask(input: {
            taskId: "task-1"
            status: COMPLETED
          }) {
            id
            status
            completedAt
            durationSeconds
          }
        }
        """
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        
        # In production, update in database
        # For now, return mock updated task
        updated_task = Task(
            id=input.task_id,
            project_id="project-1",
            agent_type=AgentType.CODER,
            title="Updated Task",
            description="Task was updated",
            status=input.status or TaskStatus.IN_PROGRESS,
            priority=1,
            created_at=datetime.utcnow() - timedelta(hours=1),
            started_at=datetime.utcnow() - timedelta(minutes=30),
            completed_at=datetime.utcnow() if input.status == TaskStatus.COMPLETED else None,
            error_message=input.error_message
        )
        
        logger.info(f"Updated task: {updated_task.id} -> {updated_task.status}")
        
        # Broadcast event to subscribers
        await subscription_queue.put({
            "type": "task_updated",
            "task": updated_task
        })
        
        return updated_task


# ============================================================================
# SUBSCRIPTION RESOLVERS (Real-Time)
# ============================================================================

@strawberry.type
class Subscription:
    """Real-time subscriptions for live widgets"""
    
    @strawberry.subscription
    async def agent_activity(
        self,
        info,
        agent_type: Optional[AgentType] = None
    ) -> AsyncGenerator[AgentActivity, None]:
        """
        Subscribe to real-time agent activity
        
        Example (JavaScript/TypeScript client):
        subscription {
          agentActivity(agentType: CODER) {
            agentType
            message
            timestamp
            taskId
          }
        }
        """
        logger.info(f"New subscription: agent_activity (filter: {agent_type})")
        
        while True:
            # Wait for events from the queue
            event = await subscription_queue.get()
            
            if event["type"] == "agent_activity":
                activity = event["activity"]
                
                # Filter by agent_type if specified
                if agent_type is None or activity.agent_type == agent_type:
                    yield activity
            
            # Small delay to prevent overwhelming clients
            await asyncio.sleep(0.1)
    
    @strawberry.subscription
    async def task_updates(
        self,
        info,
        project_id: Optional[str] = None
    ) -> AsyncGenerator[Task, None]:
        """
        Subscribe to task status changes
        
        Example:
        subscription {
          taskUpdates(projectId: "project-1") {
            id
            status
            completedAt
          }
        }
        """
        logger.info(f"New subscription: task_updates (project: {project_id})")
        
        while True:
            event = await subscription_queue.get()
            
            if event["type"] == "task_updated":
                task = event["task"]
                
                # Filter by project_id if specified
                if project_id is None or task.project_id == project_id:
                    yield task
    
    @strawberry.subscription
    async def system_metrics_stream(
        self,
        info,
        interval_seconds: int = 5,
        project_id: Optional[str] = None
    ) -> AsyncGenerator[SystemMetrics, None]:
        """
        Subscribe to system metrics updates (tenant/project-specific)
        
        Example:
        subscription {
          systemMetricsStream(intervalSeconds: 10, projectId: "project-123") {
            timestamp
            activeAgents
            activeTasks
            systemHealthScore
            cpuUsagePercent
            memoryUsagePercent
          }
        }
        """
        logger.info(f"New subscription: system_metrics_stream (interval: {interval_seconds}s, project_id: {project_id})")
        
        db: AsyncSession = getattr(info.context, 'db', None) if info.context else None
        tenant_id = getattr(info.context, 'tenant_id', None) if info.context else None
        
        if not db:
            logger.warning("No database session available for system_metrics_stream")
            while True:
                yield SystemMetrics(
                    timestamp=datetime.now(timezone.utc),
                    active_agents=0,
                    active_tasks=0,
                    tasks_completed_today=0,
                    tasks_failed_today=0,
                    average_task_duration_seconds=0.0,
                    system_health_score=0.0,
                    cpu_usage_percent=0.0,
                    memory_usage_percent=0.0
                )
                await asyncio.sleep(interval_seconds)
        
        while True:
            try:
                # Get REAL metrics filtered by tenant and optionally project
                from ..models.agent_tasks import AgentTask
                from datetime import datetime, timezone, timedelta
                from sqlalchemy import case
                try:
                    import psutil
                except ImportError:
                    psutil = None
                
                # Build query filters
                query_filters = []
                if tenant_id:
                    query_filters.append(AgentTask.tenant_id == tenant_id)
                if project_id:
                    query_filters.append(AgentTask.project_id == project_id)
                
                # Count active agents (agents with running tasks)
                active_agents_query = select(func.count(func.distinct(AgentTask.agent_type)))
                if query_filters:
                    active_agents_query = active_agents_query.where(and_(*query_filters, AgentTask.status.in_(['started', 'running'])))
                else:
                    active_agents_query = active_agents_query.where(AgentTask.status.in_(['started', 'running']))
                result = await db.execute(active_agents_query)
                active_agents = result.scalar() or 0
                
                # Count active tasks
                active_tasks_query = select(func.count(AgentTask.id))
                if query_filters:
                    active_tasks_query = active_tasks_query.where(and_(*query_filters, AgentTask.status.in_(['started', 'running'])))
                else:
                    active_tasks_query = active_tasks_query.where(AgentTask.status.in_(['started', 'running']))
                result = await db.execute(active_tasks_query)
                active_tasks = result.scalar() or 0
                
                # Tasks completed today (all tasks for project, not just today)
                # For project-specific metrics, we want all completed tasks, not just today
                completed_query = select(func.count(AgentTask.id)).where(
                    AgentTask.status == 'completed'
                )
                if query_filters:
                    # Apply tenant/project filters
                    base_filters = [f for f in query_filters]
                    completed_query = completed_query.where(and_(*base_filters))
                result = await db.execute(completed_query)
                tasks_completed_today = result.scalar() or 0
                
                # Tasks failed (all failed tasks for project)
                failed_query = select(func.count(AgentTask.id)).where(
                    AgentTask.status == 'failed'
                )
                if query_filters:
                    base_filters = [f for f in query_filters]
                    failed_query = failed_query.where(and_(*base_filters))
                result = await db.execute(failed_query)
                tasks_failed_today = result.scalar() or 0
                
                # Average task duration
                duration_query = select(func.avg(AgentTask.actual_duration_seconds)).where(
                    and_(
                        AgentTask.status == 'completed',
                        AgentTask.actual_duration_seconds.isnot(None)
                    )
                )
                if query_filters:
                    base_filters = [f for f in query_filters]
                    duration_query = duration_query.where(and_(*base_filters))
                result = await db.execute(duration_query)
                avg_duration = result.scalar() or 0.0
                
                # System health score (success rate, capped at 100%)
                stats_query = select(
                    func.count(AgentTask.id).label('total'),
                    func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
                    func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed')
                )
                if query_filters:
                    stats_query = stats_query.where(and_(*query_filters))
                result = await db.execute(stats_query)
                stats = result.first()
                total = stats.total or 0
                completed = stats.completed or 0
                failed = stats.failed or 0
                
                if total > 0:
                    system_health_score = ((completed - failed * 0.5) / total) * 100.0
                    system_health_score = max(0.0, min(100.0, system_health_score))  # Cap at 100%
                else:
                    system_health_score = 100.0
                
                # System resource usage (from psutil)
                try:
                    if psutil:
                        cpu_usage_percent = psutil.cpu_percent(interval=0.1)
                        memory = psutil.virtual_memory()
                        memory_usage_percent = memory.percent
                    else:
                        cpu_usage_percent = 0.0
                        memory_usage_percent = 0.0
                except Exception:
                    cpu_usage_percent = 0.0
                    memory_usage_percent = 0.0
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(timezone.utc),
                    active_agents=active_agents,
                    active_tasks=active_tasks,
                    tasks_completed_today=tasks_completed_today,
                    tasks_failed_today=tasks_failed_today,
                    average_task_duration_seconds=float(avg_duration),
                    system_health_score=system_health_score,
                    cpu_usage_percent=cpu_usage_percent,
                    memory_usage_percent=memory_usage_percent
                )
                
                yield metrics
            except Exception as e:
                logger.error(f"Error in system_metrics_stream: {e}", exc_info=True)
                # Yield default metrics on error
                yield SystemMetrics(
                    timestamp=datetime.now(timezone.utc),
                    active_agents=0,
                    active_tasks=0,
                    tasks_completed_today=0,
                    tasks_failed_today=0,
                    average_task_duration_seconds=0.0,
                    system_health_score=0.0,
                    cpu_usage_percent=0.0,
                    memory_usage_percent=0.0
                )
            
            await asyncio.sleep(interval_seconds)
    
    @strawberry.subscription
    async def project_updates(
        self,
        info,
        project_id: str
    ) -> AsyncGenerator[Project, None]:
        """
        Subscribe to real-time project status updates
        
        Example:
        subscription {
          projectUpdates(projectId: "project-1") {
            id
            name
            status
            completionPercentage
            totalTasks
            completedTasks
            updatedAt
          }
        }
        """
        logger.info(f"New subscription: project_updates (project: {project_id})")
        
        while True:
            event = await subscription_queue.get()
            
            if event["type"] == "project_updated" and event.get("project", {}).get("id") == project_id:
                yield event["project"]
            
            # Small delay to prevent overwhelming clients
            await asyncio.sleep(0.1)

