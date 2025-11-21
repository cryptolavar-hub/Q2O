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
import os

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
    RESEARCHER = "researcher"  # Web research agent
    MOBILE = "mobile"  # React Native mobile development agent (12th agent!)


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

    def __init__(
        self, 
        agent_id: str, 
        agent_type: AgentType, 
        project_layout: Optional[ProjectLayout] = None, 
        enable_messaging: bool = True,
        project_id: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"{agent_type.value}.{agent_id}")
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        self.project_layout: ProjectLayout = project_layout or get_default_layout()
        self.enable_messaging = enable_messaging
        self.project_id = project_id or os.getenv("Q2O_PROJECT_ID")
        self.tenant_id = tenant_id or (int(os.getenv("Q2O_TENANT_ID")) if os.getenv("Q2O_TENANT_ID") else None)
        self.db_task_ids: Dict[str, str] = {}  # Map task.id -> db_task_id
        
        # Initialize messaging if enabled
        if enable_messaging:
            try:
                from agents.messaging import MessagingMixin
                # Apply messaging mixin dynamically
                for attr_name in dir(MessagingMixin):
                    if not attr_name.startswith('_') and callable(getattr(MessagingMixin, attr_name)):
                        if not hasattr(self, attr_name):
                            setattr(self, attr_name, getattr(MessagingMixin, attr_name).__get__(self, self.__class__))
                
                # Initialize messaging
                self.message_broker = None
                self.message_handlers = {}
                self._init_messaging()
            except Exception as e:
                self.logger.warning(f"Messaging initialization failed (continuing without messaging): {e}")
                self.enable_messaging = False
    
    def _init_messaging(self):
        """Initialize messaging capabilities."""
        try:
            from utils.message_broker import get_default_broker
            from utils.message_protocol import MessageType
            
            self.message_broker = get_default_broker()
            self.message_handlers = {}
            
            # Subscribe to channels
            def message_handler(msg_dict):
                self._handle_incoming_message(msg_dict)
            
            self.message_broker.subscribe("agents", message_handler)
            self.message_broker.subscribe(f"agents.{self.agent_type.value}", message_handler)
            self.message_broker.subscribe(f"agents.{self.agent_id}", message_handler)
            
            # Announce presence
            self.announce_presence()
        except Exception as e:
            self.logger.warning(f"Messaging setup failed: {e}")
    
    def announce_presence(self):
        """Announce agent presence (can be overridden)."""
        pass
    
    def _handle_incoming_message(self, message_dict: Dict[str, Any]):
        """Handle incoming message (can be overridden)."""
        pass

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
    
    def process_task_with_retry(self, task: Task) -> Task:
        """
        Process a task with automatic retry mechanism.
        
        Args:
            task: The task to process
            
        Returns:
            The updated task
        """
        from utils.retry_policy import get_policy_manager
        from utils.load_balancer import get_load_balancer
        import time
        
        policy_manager = get_policy_manager()
        policy = policy_manager.get_policy(self.agent_type.value, task.title)
        
        self.logger.info(f"Processing task {task.id} with retry policy: max_retries={policy.max_retries}, strategy={policy.strategy.value}")
        
        last_exception = None
        
        for attempt in range(policy.max_retries + 1):
            try:
                # Update task status to "running" in database
                db_task_id = self.db_task_ids.get(task.id)
                if db_task_id and self.project_id:
                    try:
                        from agents.task_tracking import update_task_status_in_db, run_async
                        run_async(update_task_status_in_db(
                            task_id=db_task_id,
                            status="running",
                            progress_percentage=5.0,  # Just started
                        ))
                    except Exception as e:
                        self.logger.debug(f"Failed to update task status to running: {e}")
                
                # Process the task
                result = self.process_task(task)
                
                # If successful, record success and return
                if attempt > 0:
                    self.logger.info(f"Task {task.id} succeeded on retry attempt {attempt + 1}")
                    load_balancer = get_load_balancer()
                    load_balancer.record_task_success(self.agent_id)
                
                return result
            
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                if not policy.should_retry(e, attempt):
                    self.logger.warning(f"Task {task.id} failed with non-retryable exception: {type(e).__name__}")
                    break
                
                # Check if we have retries remaining
                if attempt < policy.max_retries:
                    delay = policy.get_delay(attempt)
                    self.logger.warning(
                        f"Task {task.id} failed on attempt {attempt + 1}/{policy.max_retries + 1}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Optionally try with a different agent instance (via load balancer)
                    if attempt > 0:  # After first retry, try different agent
                        try:
                            load_balancer = get_load_balancer()
                            alternative_instance = load_balancer.route_task(
                                task, 
                                routing_algorithm="health_based"
                            )
                            
                            if alternative_instance and alternative_instance.agent_id != self.agent_id:
                                self.logger.info(
                                    f"Attempting task {task.id} on alternative agent {alternative_instance.agent_id}"
                                )
                                # Update task assignment
                                task.assigned_agent = alternative_instance.agent_id
                                continue  # Skip delay, try immediately on alternative agent
                        except Exception as lb_error:
                            self.logger.debug(f"Load balancer routing failed: {lb_error}")
                    
                    # Wait before retry
                    time.sleep(delay)
                else:
                    # No more retries
                    self.logger.error(f"Task {task.id} failed after {policy.max_retries + 1} attempts")
                    load_balancer = get_load_balancer()
                    load_balancer.record_task_failure(self.agent_id)
        
        # All retries exhausted - mark task as failed
        error_msg = f"Task failed after {policy.max_retries + 1} attempts: {str(last_exception)}"
        self.fail_task(task.id, error_msg)
        
        # Re-raise the exception for caller handling
        raise last_exception or Exception(error_msg)

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
    
    def _auto_commit_task(self, task: Task):
        """Automatically commit files created by completed task."""
        try:
            from utils.git_manager import get_git_manager
            
            # Get workspace path (some agents have it, use project layout as fallback)
            workspace_path = getattr(self, 'workspace_path', '.')
            git_manager = get_git_manager(str(workspace_path))
            
            if not git_manager.auto_commit:
                return
            
            # Extract files created from task result
            files_created = []
            if task.result and isinstance(task.result, dict):
                files_created = task.result.get("files_created", [])
                # Also check for agent-specific file lists
                if not files_created:
                    files_created = task.result.get("integration_files", [])
                if not files_created:
                    files_created = task.result.get("frontend_files", [])
                if not files_created:
                    files_created = task.result.get("infrastructure_files", [])
                if not files_created:
                    files_created = task.result.get("workflow_files", [])
                if not files_created:
                    files_created = task.result.get("node_files", [])
            
            if files_created:
                git_manager.auto_commit_task_completion(
                    task_id=task.id,
                    task_title=task.title,
                    files_created=files_created
                )
        except Exception as e:
            # Fail silently - VCS integration is optional
            self.logger.debug(f"Auto-commit failed (optional feature): {e}")
    
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
        
        # Create task in database for tracking
        if self.project_id:
            try:
                from agents.task_tracking import create_task_in_db, run_async
                
                self.logger.info(
                    f"Creating database task for {task.id}: "
                    f"project_id={self.project_id}, tenant_id={self.tenant_id}, "
                    f"agent_type={self.agent_type.value}"
                )
                
                db_task_id = run_async(create_task_in_db(
                    project_id=self.project_id,
                    agent_type=self.agent_type.value,
                    task_name=task.title,
                    task_description=task.description,
                    task_type=getattr(task, 'task_type', None),
                    agent_id=self.agent_id,
                    priority=1,  # Default priority
                    tenant_id=self.tenant_id,
                ))
                
                if db_task_id:
                    self.db_task_ids[task.id] = db_task_id
                    self.logger.info(f"Successfully created database task {db_task_id} for {task.id}")
                else:
                    self.logger.warning(f"Failed to create database task for {task.id} (returned None)")
            except Exception as e:
                self.logger.error(f"Failed to create task in database: {e}", exc_info=True)
        else:
            self.logger.warning(f"project_id is None, skipping database task creation for {task.id}")
        
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
        
        # Update task in database
        db_task_id = self.db_task_ids.get(task_id)
        if db_task_id:
            try:
                from agents.task_tracking import update_task_status_in_db, run_async
                
                # Prepare execution metadata
                execution_metadata = {}
                if result and isinstance(result, dict):
                    execution_metadata = {
                        "files_created": result.get("files_created", []),
                        "files_modified": result.get("files_modified", []),
                        "outputs": result.get("outputs", {}),
                    }
                
                run_async(update_task_status_in_db(
                    task_id=db_task_id,
                    status="completed",
                    progress_percentage=100.0,
                    execution_metadata=execution_metadata if execution_metadata else None,
                ))
                self.logger.info(f"Updated database task {db_task_id} to completed")
            except Exception as e:
                self.logger.warning(f"Failed to update task in database: {e}")
        
        # Auto-commit if VCS integration enabled
        self._auto_commit_task(task)
        
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
        
        # Update task in database
        db_task_id = self.db_task_ids.get(task_id)
        if db_task_id:
            try:
                from agents.task_tracking import update_task_status_in_db, run_async
                import traceback
                
                run_async(update_task_status_in_db(
                    task_id=db_task_id,
                    status="failed",
                    error_message=error,
                    error_stack_trace=traceback.format_exc(),
                ))
                self.logger.info(f"Updated database task {db_task_id} to failed")
            except Exception as e:
                self.logger.warning(f"Failed to update task in database: {e}")
        
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

