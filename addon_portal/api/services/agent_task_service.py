"""
Agent Task Service - Functions for agents to create and update tasks

This service provides functions that agents can call to:
- Create new tasks when they receive work
- Update task status (started, running, completed, failed)
- Update progress percentage
- Track LLM usage per task
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ..models.agent_tasks import AgentTask
from ..core.logging import get_logger

LOGGER = get_logger(__name__)


async def create_task(
    db: AsyncSession,
    project_id: str,
    agent_type: str,
    task_name: str,
    task_description: Optional[str] = None,
    task_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    priority: int = 1,
    tenant_id: Optional[int] = None,
    estimated_duration_seconds: Optional[int] = None,
) -> AgentTask:
    """
    Create a new task for an agent.
    
    Agents should call this when they receive a new task to work on.
    
    Args:
        db: Database session
        project_id: Project ID this task belongs to
        agent_type: Type of agent (coder, researcher, frontend, etc.)
        task_name: Human-readable task name
        task_description: Detailed task description
        task_type: Type of task (code_generation, research, testing, etc.)
        agent_id: Specific agent instance ID (optional)
        priority: Task priority (1=high, 2=medium, 3=low)
        tenant_id: Tenant ID for scoping (optional)
        estimated_duration_seconds: Estimated duration in seconds
    
    Returns:
        Created AgentTask object
    """
    # Generate unique task_id
    # Format: task-{project_id}-{agent_type}-{timestamp}-{sequence}
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    # Check for existing tasks with same project/agent to generate sequence
    result = await db.execute(
        select(func.count(AgentTask.id)).where(
            and_(
                AgentTask.project_id == project_id,
                AgentTask.agent_type == agent_type
            )
        )
    )
    sequence = result.scalar() + 1
    
    task_id = f"task-{project_id}-{agent_type}-{timestamp}-{sequence}"
    
    # Create task
    task = AgentTask(
        task_id=task_id,
        project_id=project_id,
        agent_type=agent_type,
        agent_id=agent_id,
        task_name=task_name,
        task_description=task_description,
        task_type=task_type,
        status='pending',
        priority=priority,
        tenant_id=tenant_id,
        estimated_duration_seconds=estimated_duration_seconds,
        progress_percentage=0.0,
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    LOGGER.info(
        "agent_task_created",
        extra={
            "task_id": task_id,
            "project_id": project_id,
            "agent_type": agent_type,
            "task_name": task_name,
        }
    )
    
    return task


async def update_task_status(
    db: AsyncSession,
    task_id: str,
    status: str,
    progress_percentage: Optional[float] = None,
    error_message: Optional[str] = None,
    error_stack_trace: Optional[str] = None,
    execution_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[AgentTask]:
    """
    Update task status and related fields.
    
    Agents should call this when:
    - Starting a task: status='started' or 'running'
    - Completing a task: status='completed'
    - Failing a task: status='failed'
    
    Args:
        db: Database session
        task_id: Task ID to update
        status: New status (pending, started, running, completed, failed, cancelled)
        progress_percentage: Progress percentage (0.0 to 100.0)
        error_message: Error message if task failed
        error_stack_trace: Stack trace if available
        execution_metadata: Additional execution details (JSON)
    
    Returns:
        Updated AgentTask object, or None if task not found
    """
    result = await db.execute(
        select(AgentTask).where(AgentTask.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        LOGGER.warning(
            "agent_task_not_found",
            extra={"task_id": task_id}
        )
        return None
    
    # Update status
    old_status = task.status
    task.status = status
    
    # Update timestamps based on status
    now = datetime.now(timezone.utc)
    if status in ('started', 'running') and not task.started_at:
        task.started_at = now
    elif status == 'completed' and not task.completed_at:
        task.completed_at = now
        # Calculate actual duration
        if task.started_at:
            duration = (now - task.started_at).total_seconds()
            task.actual_duration_seconds = int(duration)
        task.progress_percentage = 100.0
    elif status == 'failed' and not task.failed_at:
        task.failed_at = now
    
    # Update progress percentage if provided
    if progress_percentage is not None:
        task.progress_percentage = max(0.0, min(100.0, progress_percentage))
    
    # Update error information if provided
    if error_message:
        task.error_message = error_message
    if error_stack_trace:
        task.error_stack_trace = error_stack_trace
    
    # Update execution metadata if provided
    if execution_metadata:
        if task.execution_metadata:
            # Merge with existing metadata
            task.execution_metadata = {**task.execution_metadata, **execution_metadata}
        else:
            task.execution_metadata = execution_metadata
    
    await db.commit()
    await db.refresh(task)
    
    LOGGER.info(
        "agent_task_status_updated",
        extra={
            "task_id": task_id,
            "old_status": old_status,
            "new_status": status,
            "progress_percentage": task.progress_percentage,
        }
    )
    
    return task


async def update_task_llm_usage(
    db: AsyncSession,
    task_id: str,
    llm_calls_count: Optional[int] = None,
    llm_tokens_used: Optional[int] = None,
    llm_cost_usd: Optional[float] = None,
) -> Optional[AgentTask]:
    """
    Update LLM usage statistics for a task.
    
    Agents should call this to track LLM API calls, tokens, and costs.
    
    Args:
        db: Database session
        task_id: Task ID to update
        llm_calls_count: Number of LLM API calls (will be added to existing count)
        llm_tokens_used: Number of tokens used (will be added to existing count)
        llm_cost_usd: Cost in USD (will be added to existing cost)
    
    Returns:
        Updated AgentTask object, or None if task not found
    """
    result = await db.execute(
        select(AgentTask).where(AgentTask.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        LOGGER.warning(
            "agent_task_not_found_for_llm_update",
            extra={"task_id": task_id}
        )
        return None
    
    # Add to existing values (accumulate usage)
    if llm_calls_count is not None:
        task.llm_calls_count += llm_calls_count
    if llm_tokens_used is not None:
        task.llm_tokens_used += llm_tokens_used
    if llm_cost_usd is not None:
        task.llm_cost_usd += llm_cost_usd
    
    await db.commit()
    await db.refresh(task)
    
    LOGGER.info(
        "agent_task_llm_usage_updated",
        extra={
            "task_id": task_id,
            "llm_calls_count": task.llm_calls_count,
            "llm_tokens_used": task.llm_tokens_used,
            "llm_cost_usd": task.llm_cost_usd,
        }
    )
    
    return task


async def get_project_tasks(
    db: AsyncSession,
    project_id: str,
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    execution_started_at: Optional[datetime] = None,
) -> list[AgentTask]:
    """
    Get all tasks for a project, optionally filtered by status, agent type, and execution_started_at.
    
    Args:
        db: Database session
        project_id: Project ID
        status: Optional status filter
        agent_type: Optional agent type filter
        execution_started_at: Optional datetime - only get tasks created after this time
    
    Returns:
        List of AgentTask objects
    """
    stmt = select(AgentTask).where(AgentTask.project_id == project_id)
    
    if status:
        stmt = stmt.where(AgentTask.status == status)
    if agent_type:
        stmt = stmt.where(AgentTask.agent_type == agent_type)
    
    # CRITICAL: Filter by execution_started_at to only get tasks from current run
    if execution_started_at:
        # Ensure timezone-aware datetime
        if execution_started_at.tzinfo is None:
            execution_started_at = execution_started_at.replace(tzinfo=timezone.utc)
        stmt = stmt.where(AgentTask.created_at >= execution_started_at)
    
    stmt = stmt.order_by(AgentTask.created_at.desc())
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def calculate_project_progress(
    db: AsyncSession,
    project_id: str,
    execution_started_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Calculate real project progress based on completed tasks.
    
    CRITICAL FIX: Filters tasks by execution_started_at to only count tasks from current run.
    This prevents showing stale data from previous runs when a project is restarted.
    
    Args:
        db: Database session
        project_id: Project ID
        execution_started_at: Optional datetime - only count tasks created after this time
    
    Returns:
        Dictionary with:
        - total_tasks: Total number of tasks (from current run only)
        - completed_tasks: Number of completed tasks (from current run only)
        - failed_tasks: Number of failed tasks (from current run only)
        - in_progress_tasks: Number of tasks in progress (started/running)
        - pending_tasks: Number of pending tasks
        - completion_percentage: Real completion percentage (0.0 to 100.0)
    """
    from sqlalchemy import case
    
    # Build query with optional filter for execution_started_at
    query = select(
        func.count(AgentTask.id).label('total'),
        func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed'),
        func.sum(case((AgentTask.status.in_(['started', 'running']), 1), else_=0)).label('in_progress'),
        func.sum(case((AgentTask.status == 'pending', 1), else_=0)).label('pending'),
    ).where(AgentTask.project_id == project_id)
    
    # CRITICAL FIX: Only count tasks from current run (created after execution_started_at)
    if execution_started_at:
        # Ensure timezone-aware datetime
        if execution_started_at.tzinfo is None:
            execution_started_at = execution_started_at.replace(tzinfo=timezone.utc)
        query = query.where(AgentTask.created_at >= execution_started_at)
    
    result = await db.execute(query)
    
    stats = result.first()
    
    total_tasks = stats.total or 0
    completed_tasks = stats.completed or 0
    failed_tasks = stats.failed or 0
    in_progress_tasks = stats.in_progress or 0
    pending_tasks = stats.pending or 0
    
    # Calculate completion percentage (percentage of tasks that have finished)
    # Completion Rate = (Completed + Failed) / Total * 100%
    # This shows how many tasks have finished (regardless of success/failure)
    if total_tasks > 0:
        finished_tasks = completed_tasks + failed_tasks
        completion_percentage = (finished_tasks / total_tasks) * 100.0
        completion_percentage = max(0.0, min(100.0, completion_percentage))  # Cap at 100%
        completion_percentage = round(completion_percentage)  # Round to whole number for clean display
    else:
        completion_percentage = 0.0
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "pending_tasks": pending_tasks,
        "completion_percentage": completion_percentage,
    }

