"""
Base Agent class that all specialized agents inherit from.
Provides common functionality for task management, communication, and logging.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

if TYPE_CHECKING:
    from utils.project_layout import ProjectLayout
else:
    from utils.project_layout import ProjectLayout, get_default_layout


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentType(Enum):
    """Type of agent."""
    ORCHESTRATOR = "orchestrator"
    CODER = "coder"
    NODEJS = "nodejs"  # Node.js specialized agent
    TESTING = "testing"
    QA = "qa"
    INFRASTRUCTURE = "infrastructure"
    INTEGRATION = "integration"
    FRONTEND = "frontend"
    WORKFLOW = "workflow"
    SECURITY = "security"


@dataclass
class Task:
    """Represents a task in the project."""
    id: str
    title: str
    description: str
    agent_type: AgentType
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    # Additional fields for domain-aware task management
    tech_stack: List[str] = field(default_factory=list)  # e.g., ["python", "nextjs", "terraform"]
    file_paths: List[str] = field(default_factory=list)  # Expected file locations
    config_needs: Dict[str, Any] = field(default_factory=dict)  # Required env vars/secrets

    def start(self):
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, result: Any = None):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, agent_id: str, agent_type: AgentType, project_layout: Optional[ProjectLayout] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"{agent_type.value}.{agent_id}")
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        self.project_layout: ProjectLayout = project_layout or get_default_layout()

    @abstractmethod
    def process_task(self, task: Task) -> Task:
        """
        Process a task. Must be implemented by subclasses.
        
        Args:
            task: The task to process
            
        Returns:
            The updated task
        """
        pass

    def can_handle_task(self, task: Task) -> bool:
        """
        Check if this agent can handle a given task.
        
        Args:
            task: The task to check
            
        Returns:
            True if the agent can handle the task
        """
        return task.agent_type == self.agent_type

    def _emit_task_started(self, task_id: str, task: Task):
        """Emit dashboard event for task started."""
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            asyncio.create_task(event_manager.emit_task_update(
                task_id=task_id,
                status="in_progress",
                title=task.title,
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                started_at=task.started_at.isoformat() if task.started_at else None,
                dependencies=task.dependencies,
                progress=0
            ))
        except Exception:
            # Fail silently if dashboard not available
            pass
    
    def _emit_task_complete(self, task_id: str, task: Task):
        """Emit dashboard event for task completed."""
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            
            # Calculate duration
            duration = None
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
            
            asyncio.create_task(event_manager.emit_task_update(
                task_id=task_id,
                status="completed",
                title=task.title,
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                started_at=task.started_at.isoformat() if task.started_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                duration=duration,
                progress=100
            ))
            
            # Emit agent activity
            asyncio.create_task(event_manager.emit_agent_activity(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                activity="task_completed",
                task_id=task_id,
                status="idle" if len(self.active_tasks) == 0 else "active"
            ))
        except Exception:
            # Fail silently if dashboard not available
            pass
    
    def _emit_task_failed(self, task_id: str, task: Task, error: str):
        """Emit dashboard event for task failed."""
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            asyncio.create_task(event_manager.emit_task_update(
                task_id=task_id,
                status="failed",
                title=task.title,
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                started_at=task.started_at.isoformat() if task.started_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                error=error,
                progress=0
            ))
            
            # Emit agent activity
            asyncio.create_task(event_manager.emit_agent_activity(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                activity="task_failed",
                task_id=task_id,
                error=error,
                status="idle" if len(self.active_tasks) == 0 else "active"
            ))
        except Exception:
            # Fail silently if dashboard not available
            pass

    def assign_task(self, task: Task) -> bool:
        """
        Assign a task to this agent.
        
        Args:
            task: The task to assign
            
        Returns:
            True if assignment was successful
        """
        if not self.can_handle_task(task):
            self.logger.warning(f"Cannot handle task {task.id}: wrong agent type")
            return False

        task.assigned_agent = self.agent_id
        self.active_tasks[task.id] = task
        task.start()
        self.logger.info(f"Assigned task {task.id}: {task.title}")
        
        # Emit dashboard event
        self._emit_task_started(task.id, task)
        
        # Emit agent activity
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            asyncio.create_task(event_manager.emit_agent_activity(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                activity="task_started",
                task_id=task.id,
                status="active"
            ))
        except Exception:
            pass
        
        return True

    def complete_task(self, task_id: str, result: Any = None):
        """
        Mark a task as completed.
        
        Args:
            task_id: The ID of the task to complete
            result: Optional result from task execution
        """
        if task_id not in self.active_tasks:
            self.logger.warning(f"Task {task_id} not found in active tasks")
            return

        task = self.active_tasks.pop(task_id)
        task.complete(result)
        self.completed_tasks.append(task)
        self.logger.info(f"Completed task {task_id}: {task.title}")
        
        # Emit dashboard event
        self._emit_task_complete(task_id, task)

    def fail_task(self, task_id: str, error: str):
        """
        Mark a task as failed.
        
        Args:
            task_id: The ID of the task to fail
            error: Error message describing the failure
        """
        if task_id not in self.active_tasks:
            self.logger.warning(f"Task {task_id} not found in active tasks")
            return

        task = self.active_tasks.pop(task_id)
        task.fail(error)
        self.failed_tasks.append(task)
        self.logger.error(f"Failed task {task_id}: {task.title} - {error}")
        
        # Emit dashboard event
        self._emit_task_failed(task_id, task, error)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the agent.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
        }

    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(message)

    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)

