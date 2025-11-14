"""
GraphQL Resolvers for Q2O Multi-Agent Dashboard

Handles queries, mutations, and subscriptions.
Integrates with existing database and WebSocket system.
"""
from typing import List, Optional, AsyncGenerator
from datetime import datetime, timedelta
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
        Get all agents with optional filtering
        
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
        db: AsyncSession = info.context["db"]
        
        # Mock data for now - replace with actual DB queries
        # In production, query from agent_activity table
        agents = [
            Agent(
                id=f"agent-{i}",
                type=AgentType.CODER if i % 2 == 0 else AgentType.RESEARCHER,
                name=f"Agent-{i}",
                status="active",
                health_score=0.95,
                tasks_completed=100,
                tasks_failed=5,
                current_task_id=f"task-{i}" if i < 3 else None,
                last_activity=datetime.utcnow()
            )
            for i in range(1, 13)  # 12 agents
        ]
        
        # Apply filters
        if agent_type:
            agents = [a for a in agents if a.type == agent_type]
        if min_health > 0:
            agents = [a for a in agents if a.health_score >= min_health]
        
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
        Get tasks with flexible filtering
        
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
        db: AsyncSession = info.context["db"]
        
        # Build query based on filters
        # In production, query from tasks table
        tasks = [
            Task(
                id=f"task-{i}",
                project_id=f"project-{i % 5}",
                agent_type=AgentType.CODER if i % 2 == 0 else AgentType.FRONTEND,
                title=f"Task {i}: Generate API endpoint",
                description=f"Create FastAPI endpoint for entity {i}",
                status=TaskStatus.IN_PROGRESS if i < 3 else TaskStatus.COMPLETED,
                priority=1 if i < 3 else 2,
                created_at=datetime.utcnow() - timedelta(hours=i),
                started_at=datetime.utcnow() - timedelta(hours=i-1) if i < 10 else None,
                completed_at=datetime.utcnow() - timedelta(minutes=30) if i >= 3 else None,
                error_message=None
            )
            for i in range(1, 51)
        ]
        
        # Apply filters
        if filter:
            if filter.status:
                tasks = [t for t in tasks if t.status == filter.status]
            if filter.agent_type:
                tasks = [t for t in tasks if t.agent_type == filter.agent_type]
            if filter.project_id:
                tasks = [t for t in tasks if t.project_id == filter.project_id]
            if filter.created_after:
                tasks = [t for t in tasks if t.created_at >= filter.created_after]
        
        return tasks[offset:offset + limit]
    
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
        db: AsyncSession = info.context["db"]
        
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
        projects = await self.projects(info)
        return next((p for p in projects if p.id == id), None)
    
    @strawberry.field
    async def dashboard_stats(self, info) -> DashboardStats:
        """
        Get high-level dashboard statistics
        
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
        db: AsyncSession = info.context["db"]
        
        # In production, aggregate from database
        return DashboardStats(
            total_projects=10,
            active_projects=3,
            total_tasks=200,
            active_tasks=5,
            completed_tasks_today=45,
            average_success_rate=95.5,
            most_active_agent=AgentType.CODER,
            recent_activities=[
                AgentActivity(
                    id=f"activity-{i}",
                    agent_type=AgentType.CODER if i % 2 == 0 else AgentType.RESEARCHER,
                    agent_id=f"agent-{i}",
                    event_type="task_completed",
                    message=f"Completed task: Generate API endpoint #{i}",
                    timestamp=datetime.utcnow() - timedelta(minutes=i*5),
                    task_id=f"task-{i}",
                    metadata=None
                )
                for i in range(1, 6)
            ]
        )
    
    @strawberry.field
    async def system_metrics(self, info) -> SystemMetrics:
        """
        Get real-time system metrics
        
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
        # In production, collect from monitoring system
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            active_agents=12,
            active_tasks=5,
            tasks_completed_today=45,
            tasks_failed_today=2,
            average_task_duration_seconds=120.5,
            system_health_score=98.5,
            cpu_usage_percent=35.2,
            memory_usage_percent=62.8
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
        db: AsyncSession = info.context["db"]
        
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
        db: AsyncSession = info.context["db"]
        
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
        interval_seconds: int = 5
    ) -> AsyncGenerator[SystemMetrics, None]:
        """
        Subscribe to system metrics updates
        
        Example:
        subscription {
          systemMetricsStream(intervalSeconds: 10) {
            timestamp
            activeAgents
            activeTasks
            systemHealthScore
            cpuUsagePercent
            memoryUsagePercent
          }
        }
        """
        logger.info(f"New subscription: system_metrics_stream (interval: {interval_seconds}s)")
        
        while True:
            # In production, collect real metrics
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                active_agents=12,
                active_tasks=5,
                tasks_completed_today=45,
                tasks_failed_today=2,
                average_task_duration_seconds=120.5,
                system_health_score=98.5,
                cpu_usage_percent=35.2,
                memory_usage_percent=62.8
            )
            
            yield metrics
            await asyncio.sleep(interval_seconds)

