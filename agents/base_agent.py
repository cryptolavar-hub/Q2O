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
from utils.event_loop_utils import create_compatible_event_loop

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
        tenant_id: Optional[int] = None,
        orchestrator: Optional[Any] = None,
        workspace_path: Optional[str] = None
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
        self.pending_backup_tasks: Dict[str, str] = {}  # QA_Engineer: logical_task_id -> db_task_id (for backup agents)
        self.orchestrator = orchestrator  # Reference to orchestrator for dependency access
        
        # CRITICAL: Validate and set workspace_path with hard security guarantees
        # workspace_path is REQUIRED when project_id is set (tenant portal execution)
        if project_id and not workspace_path:
            raise ValueError(
                f"CRITICAL: Agent {agent_id} requires workspace_path when project_id is set. "
                f"workspace_path must be set to Tenant_Projects/{{project_id}}/ to ensure all generated files "
                f"are placed in the correct location for client download. "
                f"NO FILES SHOULD BE GENERATED OUTSIDE Tenant_Projects/{{project_id}}/"
            )
        
        if workspace_path:
            from utils.safe_file_writer import validate_workspace_path
            try:
                self.workspace_path = str(validate_workspace_path(workspace_path, self.project_id))
            except Exception as e:
                self.logger.error(f"CRITICAL: Invalid workspace_path '{workspace_path}': {e}")
                raise
        else:
            # Default to current directory (only allowed when project_id is None - local/testing mode)
            self.workspace_path = "."
            if project_id is None:
                self.logger.debug(
                    f"Agent {agent_id} initialized without workspace_path (project_id=None, local/testing mode)"
                )
            else:
                # This should never happen due to the check above, but keep as safety net
                raise ValueError(
                    f"CRITICAL: Agent {agent_id} initialized without workspace_path but project_id is set. "
                    f"This is a programming error. workspace_path must be provided."
                )
        
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
            
            # QA_Engineer: Subscribe to project-specific channel for peer coordination
            if self.project_id:
                self.message_broker.subscribe(f"agents.{self.project_id}", message_handler)
                self.logger.info(f"Subscribed to project channel: agents.{self.project_id}")
            
            # QA_Engineer: Setup task coordination handlers
            self._setup_task_coordination_handlers()
            
            # Announce presence
            self.announce_presence()
        except Exception as e:
            self.logger.warning(f"Messaging setup failed: {e}")
    
    def announce_presence(self):
        """Announce agent presence (can be overridden)."""
        pass
    
    def _setup_task_coordination_handlers(self):
        """Setup handlers for task coordination messages."""
        try:
            from utils.message_protocol import MessageType
            
            if not hasattr(self, 'message_handlers'):
                self.message_handlers = {}
            
            self.message_handlers[MessageType.TASK_COMPLETED_BY_PEER] = self._handle_task_completed_by_peer
        except Exception as e:
            self.logger.warning(f"Failed to setup task coordination handlers: {e}")
    
    def _handle_task_completed_by_peer(self, message_dict: Dict[str, Any]):
        """
        Handle message when peer agent completes a task we're also working on.
        
        QA_Engineer: This prevents duplicate database entries by marking our backup task
        as completed using the peer's result.
        """
        try:
            from utils.message_protocol import AgentMessage
            
            # Extract the actual message data
            msg_data = message_dict.get("data", message_dict)
            agent_msg = AgentMessage.from_dict(msg_data)
            
            # Don't process our own messages
            if agent_msg.sender_agent_id == self.agent_id:
                return
            
            logical_task_id = agent_msg.payload.get("logical_task_id")
            peer_db_task_id = agent_msg.payload.get("peer_db_task_id")  # QA_Engineer: Fixed field name
            peer_result = agent_msg.payload.get("peer_result")  # QA_Engineer: Fixed field name
            project_id = agent_msg.payload.get("project_id")  # QA_Engineer: Get project_id from payload
            peer_agent_id = agent_msg.sender_agent_id
            
            # QA_Engineer: Filter by project_id to avoid processing messages from other projects
            if project_id and project_id != self.project_id:
                self.logger.debug(f"Received peer completion message for different project {project_id}, ignoring")
                return
            
            # QA_Engineer: BIDIRECTIONAL COORDINATION
            # Handle peer completion for both main and backup agents
            # Check if we have this task (either as backup or main)
            our_db_task_id = None
            is_our_backup_task = logical_task_id in self.pending_backup_tasks
            
            if is_our_backup_task:
                # We're a backup agent and this was our tracked backup task
                our_db_task_id = self.pending_backup_tasks[logical_task_id]
            elif logical_task_id in self.db_task_ids:
                # We're a main agent and we have this task
                our_db_task_id = self.db_task_ids.get(logical_task_id)
            
            if our_db_task_id:
                agent_role = "backup" if is_our_backup_task else "main"
                self.logger.info(
                    f"Peer agent {peer_agent_id} completed task {logical_task_id} first. "
                    f"Marking our {agent_role} task {our_db_task_id} as completed."
                )
                
                # Mark our task as completed in database
                try:
                    from agents.task_tracking import update_task_status_in_db, run_async
                    run_async(update_task_status_in_db(
                        task_id=our_db_task_id,
                        status="completed",
                        progress_percentage=100.0,
                        execution_metadata={
                            "completed_by_peer": peer_agent_id,
                            "peer_db_task_id": peer_db_task_id,
                            "backup_task": is_our_backup_task,
                            "logical_task_id": logical_task_id,
                            "agent_role": agent_role
                        }
                    ))
                    
                    # Remove from pending backup tasks if it was tracked
                    if is_our_backup_task:
                        del self.pending_backup_tasks[logical_task_id]
                    
                    # Remove from active_tasks if present and mark as completed
                    if logical_task_id in self.active_tasks:
                        task = self.active_tasks.pop(logical_task_id)
                        task.complete(peer_result)
                        task.status = TaskStatus.COMPLETED
                        self.completed_tasks.append(task)
                        self.logger.info(f"Marked {agent_role} task {logical_task_id} as completed locally")
                    
                except Exception as e:
                    self.logger.error(f"Error marking {agent_role} task as completed: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error handling peer completion message: {e}", exc_info=True)
    
    def _handle_incoming_message(self, message_dict: Dict[str, Any]):
        """
        Handle incoming message (ENHANCED with task coordination).
        """
        try:
            from utils.message_protocol import AgentMessage, MessageType
            
            # Extract the actual message data
            msg_data = message_dict.get("data", message_dict)
            agent_msg = AgentMessage.from_dict(msg_data)
            
            # Check if message is for this agent
            if agent_msg.target_agent_id and agent_msg.target_agent_id != self.agent_id:
                return  # Not for us
            
            if agent_msg.target_agent_type and agent_msg.target_agent_type != self.agent_type.value:
                return  # Not for our agent type
            
            # Don't process our own messages
            if agent_msg.sender_agent_id == self.agent_id:
                return
            
            # Route to appropriate handler
            if hasattr(self, 'message_handlers'):
                handler = self.message_handlers.get(agent_msg.message_type)
                if handler:
                    handler(message_dict)
                else:
                    self.logger.debug(f"No handler for message type {agent_msg.message_type.value}")
        except Exception as e:
            self.logger.debug(f"Error handling incoming message: {e}")

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
        """Emit dashboard event for task started.
        
        Uses background thread with its own event loop to avoid blocking
        and prevent event loop conflicts. Fire-and-forget pattern.
        """
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            import threading
            
            event_manager = get_event_manager()
            
            def emit_in_background():
                """Emit events in background thread with its own event loop."""
                try:
                    # Create new event loop for this thread
                    # Windows compatibility: Use SelectorEventLoop for psycopg async
                    loop = create_compatible_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        loop.run_until_complete(event_manager.emit_task_update(
                            task_id=task_id,
                            status="in_progress",
                            title=task.title,
                            agent_id=self.agent_id,
                            agent_type=self.agent_type.value,
                            started_at=task.started_at.isoformat() if task.started_at else None,
                            dependencies=task.dependencies,
                            progress=0
                        ))
                    finally:
                        loop.close()
                        # Clean up event loop reference
                        try:
                            asyncio.set_event_loop(None)
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.debug(f"Failed to emit task started event: {e}")
            
            # Run in background thread (fire-and-forget)
            # Daemon thread ensures it doesn't block process shutdown
            thread = threading.Thread(target=emit_in_background, daemon=True)
            thread.start()
        except Exception:
            # Fail silently if dashboard not available
            pass
    
    def _emit_task_complete(self, task_id: str, task: Task):
        """Emit dashboard event for task completed.
        
        Uses background thread with its own event loop to avoid blocking
        and prevent event loop conflicts. Fire-and-forget pattern.
        """
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            import threading
            
            event_manager = get_event_manager()
            
            # Calculate duration
            duration = None
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
            
            def emit_in_background():
                """Emit events in background thread with its own event loop."""
                try:
                    # Create new event loop for this thread
                    # Windows compatibility: Use SelectorEventLoop for psycopg async
                    loop = create_compatible_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Emit task update
                        loop.run_until_complete(event_manager.emit_task_update(
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
                        loop.run_until_complete(event_manager.emit_agent_activity(
                            agent_id=self.agent_id,
                            agent_type=self.agent_type.value,
                            activity="task_completed",
                            task_id=task_id,
                            status="idle" if len(self.active_tasks) == 0 else "active"
                        ))
                    finally:
                        loop.close()
                        # Clean up event loop reference
                        try:
                            asyncio.set_event_loop(None)
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.debug(f"Failed to emit task complete event: {e}")
            
            # Run in background thread (fire-and-forget)
            # Daemon thread ensures it doesn't block process shutdown
            thread = threading.Thread(target=emit_in_background, daemon=True)
            thread.start()
        except Exception:
            # Fail silently if dashboard not available
            pass
    
    def safe_write_file(self, file_path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> str:
        """
        Safely write a file with hard guarantees that it won't corrupt platform code.
        
        This is the ONLY method agents should use to write files.
        All file writes MUST go through this method.
        
        Args:
            file_path: Relative path to the file (relative to workspace_path)
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_dirs: Whether to create parent directories (default: True)
            
        Returns:
            Absolute path to the written file
            
        Raises:
            WorkspaceSecurityError: If any security rule is violated
            OSError: If file cannot be written
        """
        from utils.safe_file_writer import safe_write_file, WorkspaceSecurityError
        
        workspace_path = getattr(self, 'workspace_path', '.')
        
        try:
            written_path = safe_write_file(
                file_path=file_path,
                content=content,
                workspace_path=workspace_path,
                project_id=self.project_id,
                encoding=encoding,
                create_dirs=create_dirs
            )
            return str(written_path)
        except WorkspaceSecurityError as e:
            self.logger.error(f"SECURITY VIOLATION: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to write file '{file_path}': {e}")
            raise
    
    def _auto_commit_task(self, task: Task):
        """
        Automatically commit files created by completed task.
        
        QA_Engineer: Solution 2 - Batch Commits - Uses batch commit queue instead of immediate commits.
        """
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
                # QA_Engineer: Solution 2 - Batch Commits - Queue commit instead of committing immediately
                git_manager.auto_commit_task_completion(
                    task_id=task.id,
                    task_title=task.title,
                    files_created=files_created
                )
        except Exception as e:
            # Fail silently - VCS integration is optional
            self.logger.debug(f"Auto-commit failed (optional feature): {e}")
    
    def _emit_task_failed(self, task_id: str, task: Task, error: str):
        """Emit dashboard event for task failed.
        
        Uses background thread with its own event loop to avoid blocking
        and prevent event loop conflicts. Fire-and-forget pattern.
        """
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            import threading
            
            event_manager = get_event_manager()
            def emit_in_background():
                """Emit events in background thread with its own event loop."""
                try:
                    # Create new event loop for this thread
                    # Windows compatibility: Use SelectorEventLoop for psycopg async
                    loop = create_compatible_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Emit task update
                        loop.run_until_complete(event_manager.emit_task_update(
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
                        loop.run_until_complete(event_manager.emit_agent_activity(
                            agent_id=self.agent_id,
                            agent_type=self.agent_type.value,
                            activity="task_failed",
                            task_id=task_id,
                            error=error,
                            status="idle" if len(self.active_tasks) == 0 else "active"
                        ))
                    finally:
                        loop.close()
                        # Clean up event loop reference
                        try:
                            asyncio.set_event_loop(None)
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.debug(f"Failed to emit task failed event: {e}")
            
            # Run in background thread (fire-and-forget)
            # Daemon thread ensures it doesn't block process shutdown
            thread = threading.Thread(target=emit_in_background, daemon=True)
            thread.start()
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
                    
                    # QA_Engineer: Track backup tasks for peer coordination
                    if "_backup" in self.agent_id:
                        # This is a backup agent - track the task for potential peer completion
                        self.pending_backup_tasks[task.id] = db_task_id
                        self.logger.debug(f"Tracked backup task {task.id} -> {db_task_id}")
                else:
                    self.logger.warning(f"Failed to create database task for {task.id} (returned None)")
            except Exception as e:
                self.logger.error(f"Failed to create task in database: {e}", exc_info=True)
        else:
            self.logger.warning(f"project_id is None, skipping database task creation for {task.id}")
        
        # Emit dashboard event
        self._emit_task_started(task.id, task)
    
    def track_llm_usage(self, task: Task, llm_response):
        """
        Track LLM usage for a task.
        
        CRITICAL FIX: Agents must call this after each LLM call to track usage for dashboard.
        
        QA_Engineer: Solution 2 - Async Tracking - Move LLM usage tracking to background task
        to prevent blocking task completion on tracking failures.
        
        Args:
            task: The task that used LLM
            llm_response: LLMResponse object with usage information
        """
        if not llm_response or not llm_response.usage:
            return  # No usage data to track
        
        db_task_id = self.db_task_ids.get(task.id)
        if not db_task_id:
            self.logger.debug(f"No database task ID found for {task.id}, skipping LLM usage tracking")
            return
        
        # QA_Engineer: Solution 2 - Async Tracking - Queue tracking request in background thread
        # This prevents tracking failures from blocking task completion
        def track_in_background():
            """Background function to track LLM usage without blocking."""
            try:
                from agents.task_tracking import update_task_llm_usage_in_db, run_async
                
                usage = llm_response.usage
                
                # Track LLM usage: 1 call, tokens used, cost
                run_async(update_task_llm_usage_in_db(
                    task_id=db_task_id,
                    llm_calls_count=1,
                    llm_tokens_used=usage.total_tokens,
                    llm_cost_usd=usage.total_cost,
                ))
                
                self.logger.debug(
                    f"Tracked LLM usage for {task.id}: "
                    f"{usage.total_tokens} tokens, ${usage.total_cost:.4f}, "
                    f"{llm_response.provider}/{llm_response.model}"
                )
            except Exception as e:
                # Log full exception details for debugging
                import traceback
                self.logger.warning(
                    f"Failed to track LLM usage for {task.id}: {e}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
        
        # Run tracking in background thread (fire-and-forget)
        # Daemon thread ensures it doesn't block process shutdown
        import threading
        thread = threading.Thread(target=track_in_background, daemon=True)
        thread.start()
        
        return True

    def complete_task(self, task_id: str, result: Any = None, task: Optional[Task] = None):
        """
        Mark a task as completed.
        
        Args:
            task_id: The ID of the task to complete
            result: Optional result from task execution
            task: Optional task object to update (QA_Engineer: ensures status synchronization)
        
        Returns:
            The completed task object
        """
        task_obj = None
        
        # Get task from active_tasks if not provided
        if task_id in self.active_tasks:
            task_obj = self.active_tasks.pop(task_id)
        elif task:
            # Task provided but not in active_tasks (may have been removed already)
            task_obj = task
            self.logger.debug(f"Task {task_id} not in active_tasks, using provided task object")
        else:
            self.logger.warning(f"Task {task_id} not found in active tasks")
            return None

        # Update task status
        task_obj.complete(result)
        # QA_Engineer: Explicitly ensure status is set (redundant but ensures consistency)
        task_obj.status = TaskStatus.COMPLETED
        
        # If task parameter provided and different from task_obj, update it too
        if task and task.id == task_id and task is not task_obj:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = task_obj.completed_at
        
        self.completed_tasks.append(task_obj)
        self.logger.info(f"Completed task {task_id}: {task_obj.title}")
        
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
                
                # QA_Engineer: Notify peer agents (main or backup) that we completed this task first
                # BIDIRECTIONAL: Both main and backup agents can notify each other
                # Only notify if we completed first (not already notified by peer)
                is_backup_agent = "_backup" in self.agent_id
                is_tracked_backup = task_id in self.pending_backup_tasks
                
                # Notify peers if:
                # 1. We're a backup agent AND this was our tracked backup task (we completed first)
                # 2. We're a main agent AND this is NOT a tracked backup task (we completed first)
                should_notify = (is_backup_agent and is_tracked_backup) or (not is_backup_agent and not is_tracked_backup)
                
                if should_notify and self.enable_messaging:
                    try:
                        from utils.message_protocol import create_task_completed_by_peer_message
                        from utils.message_broker import get_default_broker
                        
                        message = create_task_completed_by_peer_message(
                            sender_agent_id=self.agent_id,
                            sender_agent_type=self.agent_type.value,
                            logical_task_id=task_id,
                            peer_db_task_id=db_task_id,
                            peer_result=result,
                            project_id=self.project_id  # QA_Engineer: Include project_id for filtering
                        )
                        
                        broker = get_default_broker()
                        broker.publish(message.channel, message.to_dict())
                        
                        self.logger.debug(
                            f"Notified peer agents of task completion: {task_id} "
                            f"(agent_type: {'backup' if is_backup_agent else 'main'})"
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to notify peer agents: {e}")
            except Exception as e:
                self.logger.warning(f"Failed to update task in database: {e}")
        
        # Auto-commit if VCS integration enabled
        self._auto_commit_task(task_obj)
        
        # Emit dashboard event
        self._emit_task_complete(task_id, task_obj)
        
        # QA_Engineer: Return task object for status synchronization (Solution 3)
        return task_obj

    def fail_task(self, task_id: str, error: str, task: Optional[Task] = None):
        """
        Mark a task as failed.
        
        Args:
            task_id: The ID of the task to fail
            error: Error message describing the failure
            task: Optional task object to update (QA_Engineer: ensures status synchronization)
        
        Returns:
            The failed task object
        """
        task_obj = None
        
        # Get task from active_tasks if not provided
        if task_id in self.active_tasks:
            task_obj = self.active_tasks.pop(task_id)
        elif task:
            # Task provided but not in active_tasks (may have been removed already)
            task_obj = task
            self.logger.debug(f"Task {task_id} not in active_tasks, using provided task object")
        else:
            self.logger.warning(f"Task {task_id} not found in active tasks")
            return None

        # Update task status
        task_obj.fail(error)
        # QA_Engineer: Explicitly ensure status is set (redundant but ensures consistency)
        task_obj.status = TaskStatus.FAILED
        
        # If task parameter provided and different from task_obj, update it too
        if task and task.id == task_id and task is not task_obj:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = task_obj.completed_at
        
        self.failed_tasks.append(task_obj)
        self.logger.error(f"Failed task {task_id}: {task_obj.title} - {error}")
        
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
        self._emit_task_failed(task_id, task_obj, error)
        
        # QA_Engineer: Return task object for status synchronization (Solution 3)
        return task_obj

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

