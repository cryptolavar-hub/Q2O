"""
DataLoaders for GraphQL Performance Optimization

Implements batch loading and caching to solve the N+1 query problem.

Example: If you query 100 tasks and each task loads its project,
without DataLoader = 101 queries (1 for tasks + 100 for projects)
with DataLoader = 2 queries (1 for tasks + 1 batched for all projects)
"""
import asyncio
from typing import List, Optional, Dict
from aiodataloader import DataLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..core.logging import get_logger

logger = get_logger(__name__)


class ProjectLoader(DataLoader):
    """
    Batch load projects by ID
    
    Instead of N queries for N tasks, this batches all project IDs
    and loads them in a single query.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
    
    async def batch_load_fn(self, project_ids: List[str]) -> List[Optional[Dict]]:
        """
        Load multiple projects in a single query
        
        Args:
            project_ids: List of project IDs to load
        
        Returns:
            List of projects in the same order as input IDs
        """
        logger.debug(f"DataLoader: Batching {len(project_ids)} project queries into 1")
        
        # In production, query from database:
        # result = await self.db.execute(
        #     select(Project).where(Project.id.in_(project_ids))
        # )
        # projects = result.scalars().all()
        
        # For now, return mock data
        from .types import Project, ProjectStatus
        from datetime import datetime, timedelta
        
        projects_dict = {
            pid: Project(
                id=pid,
                name=f"Project {pid}",
                objective=f"Objective for {pid}",
                status=ProjectStatus.IN_PROGRESS,
                created_at=datetime.utcnow() - timedelta(days=1),
                updated_at=datetime.utcnow(),
                completion_percentage=75.0,
                total_tasks=20,
                completed_tasks=15,
                failed_tasks=0
            )
            for pid in project_ids
        }
        
        # Return in same order as input (DataLoader requirement)
        return [projects_dict.get(pid) for pid in project_ids]


class AgentLoader(DataLoader):
    """
    Batch load agents by type
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
    
    async def batch_load_fn(self, agent_types: List[str]) -> List[Optional[Dict]]:
        """
        Load multiple agents in a single query
        """
        logger.debug(f"DataLoader: Batching {len(agent_types)} agent queries into 1")
        
        # In production, query from agent_activity table
        from .types import Agent, AgentType
        from datetime import datetime
        
        agents_dict = {
            agent_type: Agent(
                id=f"agent-{agent_type}",
                type=AgentType[agent_type],
                name=f"{agent_type} Agent",
                status="active",
                health_score=0.95,
                tasks_completed=100,
                tasks_failed=5,
                current_task_id=None,
                last_activity=datetime.utcnow()
            )
            for agent_type in agent_types
        }
        
        return [agents_dict.get(at) for at in agent_types]


class TasksByProjectLoader(DataLoader):
    """
    Batch load tasks by project ID
    
    Used when querying: project.tasks
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
    
    async def batch_load_fn(self, project_ids: List[str]) -> List[List[Dict]]:
        """
        Load tasks for multiple projects in a single query
        
        Returns:
            List of task lists (one list per project)
        """
        logger.debug(f"DataLoader: Batching tasks for {len(project_ids)} projects into 1 query")
        
        # Query REAL tasks from database
        from ..models.agent_tasks import AgentTask
        from .types import Task, TaskStatus, AgentType
        from collections import defaultdict
        from datetime import timezone
        
        result = await self.db.execute(
            select(AgentTask).where(AgentTask.project_id.in_(project_ids))
            .order_by(AgentTask.created_at.desc())
        )
        db_tasks = result.scalars().all()
        
        # Group by project_id and convert to GraphQL Task objects
        tasks_by_project = defaultdict(list)
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
            
            task = Task(
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
            )
            
            tasks_by_project[db_task.project_id].append(task)
        
        # Return in same order as input (empty list if no tasks)
        return [tasks_by_project.get(pid, []) for pid in project_ids]


def create_dataloaders(db: AsyncSession) -> Dict[str, DataLoader]:
    """
    Create all DataLoaders for a GraphQL request context
    
    These are created per-request to ensure proper caching scope.
    
    Uses async Session for optimal performance in SaaS platform.
    """
    return {
        "project_loader": ProjectLoader(db),
        "agent_loader": AgentLoader(db),
        "tasks_by_project_loader": TasksByProjectLoader(db),
    }

