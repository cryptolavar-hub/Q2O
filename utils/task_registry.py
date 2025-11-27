"""
Global Task Registry for Cross-Agent Task Access.

Provides a singleton registry that allows agents to access tasks from other agents
and the orchestrator, enabling dependency resolution and research result sharing.
"""

from typing import Dict, Optional
from agents.base_agent import Task
import threading
import logging

logger = logging.getLogger(__name__)


class TaskRegistry:
    """Global task registry for cross-agent task access."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._lock = threading.RLock()
        return cls._instance
    
    def register_task(self, task: Task):
        """Register a task in the registry.
        
        Args:
            task: Task to register
        """
        with self._lock:
            self._tasks[task.id] = task
            logger.debug(f"Registered task {task.id} in global registry")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task from the registry.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task if found, None otherwise
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Task]:
        """Get all registered tasks.
        
        Returns:
            Dictionary of all registered tasks
        """
        with self._lock:
            return self._tasks.copy()
    
    def clear(self):
        """Clear all tasks (for testing)."""
        with self._lock:
            self._tasks.clear()
            logger.debug("Cleared global task registry")
    
    def unregister_task(self, task_id: str):
        """Unregister a task from the registry.
        
        Args:
            task_id: ID of the task to unregister
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.debug(f"Unregistered task {task_id} from global registry")


def get_task_registry() -> TaskRegistry:
    """Get the global task registry instance.
    
    Returns:
        Global TaskRegistry singleton
    """
    return TaskRegistry()


def register_task(task: Task):
    """Register a task in the global registry.
    
    Convenience function for registering tasks.
    
    Args:
        task: Task to register
    """
    get_task_registry().register_task(task)


def get_task(task_id: str) -> Optional[Task]:
    """Get a task from the global registry.
    
    Convenience function for retrieving tasks.
    
    Args:
        task_id: ID of the task to retrieve
        
    Returns:
        Task if found, None otherwise
    """
    return get_task_registry().get_task(task_id)


def unregister_task(task_id: str):
    """Unregister a task from the global registry.
    
    Convenience function for unregistering tasks.
    
    Args:
        task_id: ID of the task to unregister
    """
    get_task_registry().unregister_task(task_id)

