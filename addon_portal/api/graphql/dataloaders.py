"""
DataLoaders for GraphQL Performance Optimization

Implements batch loading and caching to solve the N+1 query problem.

Example: If you query 100 tasks and each task loads its project,
without DataLoader = 101 queries (1 for tasks + 100 for projects)
with DataLoader = 2 queries (1 for tasks + 1 batched for all projects)
"""
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
        
        # In production:
        # result = await self.db.execute(
        #     select(Task).where(Task.project_id.in_(project_ids))
        # )
        # tasks = result.scalars().all()
        # 
        # # Group by project_id
        # tasks_by_project = defaultdict(list)
        # for task in tasks:
        #     tasks_by_project[task.project_id].append(task)
        
        from .types import Task, TaskStatus, AgentType
        from datetime import datetime, timedelta
        
        # Mock: Create tasks for each project
        tasks_by_project = {}
        for pid in project_ids:
            tasks_by_project[pid] = [
                Task(
                    id=f"task-{pid}-{i}",
                    project_id=pid,
                    agent_type=AgentType.CODER if i % 2 == 0 else AgentType.FRONTEND,
                    title=f"Task {i} for {pid}",
                    description=f"Description for task {i}",
                    status=TaskStatus.COMPLETED if i < 3 else TaskStatus.IN_PROGRESS,
                    priority=1,
                    created_at=datetime.utcnow() - timedelta(hours=i),
                    started_at=datetime.utcnow() - timedelta(hours=i-1),
                    completed_at=datetime.utcnow() if i < 3 else None,
                    error_message=None
                )
                for i in range(1, 6)  # 5 tasks per project
            ]
        
        # Return in same order as input
        return [tasks_by_project.get(pid, []) for pid in project_ids]


def create_dataloaders(db: AsyncSession) -> Dict[str, DataLoader]:
    """
    Create all DataLoaders for a GraphQL request context
    
    These are created per-request to ensure proper caching scope.
    """
    return {
        "project_loader": ProjectLoader(db),
        "agent_loader": AgentLoader(db),
        "tasks_by_project_loader": TasksByProjectLoader(db),
    }

