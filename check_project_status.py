"""
Diagnostic script to check project execution status and task tracking.

Run this to investigate why a project shows as "completed" but has 0 tasks.
"""
import asyncio
import sys
from pathlib import Path

# Add addon_portal to path
addon_portal_path = Path(__file__).parent / "addon_portal"
sys.path.insert(0, str(addon_portal_path))
sys.path.insert(0, str(Path(__file__).parent))

from datetime import timezone
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.db import AsyncSessionLocal
from api.models.llm_config import LLMProjectConfig
from api.models.agent_tasks import AgentTask


async def check_project(project_id: str):
    """Check project status and tasks."""
    async with AsyncSessionLocal() as db:
        # Get project
        result = await db.execute(
            select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            print(f"ERROR: Project '{project_id}' not found!")
            return
        
        print(f"\n{'='*80}")
        print(f"PROJECT: {project.project_id}")
        print(f"{'='*80}")
        print(f"Client Name: {project.client_name}")
        print(f"Execution Status: {project.execution_status}")
        print(f"Execution Started At: {project.execution_started_at}")
        print(f"Execution Completed At: {project.execution_completed_at}")
        print(f"Output Folder: {project.output_folder_path}")
        print(f"Execution Error: {project.execution_error}")
        
        # Count ALL tasks for this project (no filter)
        result = await db.execute(
            select(
                func.count(AgentTask.id).label('total'),
                func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed'),
                func.sum(case((AgentTask.status.in_(['started', 'running']), 1), else_=0)).label('in_progress'),
                func.sum(case((AgentTask.status == 'pending', 1), else_=0)).label('pending'),
            ).where(AgentTask.project_id == project_id)
        )
        all_stats = result.first()
        
        print(f"\n--- ALL TASKS (No Filter) ---")
        print(f"Total Tasks: {all_stats.total or 0}")
        print(f"Completed: {all_stats.completed or 0}")
        print(f"Failed: {all_stats.failed or 0}")
        print(f"In Progress: {all_stats.in_progress or 0}")
        print(f"Pending: {all_stats.pending or 0}")
        
        # Count tasks filtered by execution_started_at
        if project.execution_started_at:
            result = await db.execute(
                select(
                    func.count(AgentTask.id).label('total'),
                    func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
                    func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed'),
                    func.sum(case((AgentTask.status.in_(['started', 'running']), 1), else_=0)).label('in_progress'),
                    func.sum(case((AgentTask.status == 'pending', 1), else_=0)).label('pending'),
                ).where(
                    AgentTask.project_id == project_id,
                    AgentTask.created_at >= project.execution_started_at
                )
            )
            filtered_stats = result.first()
            
            print(f"\n--- TASKS FROM CURRENT RUN (Filtered by execution_started_at) ---")
            print(f"Execution Started At: {project.execution_started_at}")
            print(f"Total Tasks: {filtered_stats.total or 0}")
            print(f"Completed: {filtered_stats.completed or 0}")
            print(f"Failed: {filtered_stats.failed or 0}")
            print(f"In Progress: {filtered_stats.in_progress or 0}")
            print(f"Pending: {filtered_stats.pending or 0}")
        else:
            print(f"\n--- TASKS FROM CURRENT RUN ---")
            print(f"WARNING: execution_started_at is NULL - cannot filter tasks!")
            print(f"This means the project was never properly started, or was restarted incorrectly.")
        
        # Get sample tasks
        result = await db.execute(
            select(AgentTask)
            .where(AgentTask.project_id == project_id)
            .order_by(AgentTask.created_at.desc())
            .limit(10)
        )
        tasks = result.scalars().all()
        
        print(f"\n--- RECENT TASKS (Last 10) ---")
        if tasks:
            for task in tasks:
                print(f"  - {task.task_id}: {task.task_name}")
                print(f"    Status: {task.status}, Created: {task.created_at}")
                if project.execution_started_at:
                    # Make timezone-aware for comparison
                    task_created = task.created_at
                    exec_started = project.execution_started_at
                    if task_created.tzinfo is None:
                        task_created = task_created.replace(tzinfo=timezone.utc)
                    if exec_started.tzinfo is None:
                        exec_started = exec_started.replace(tzinfo=timezone.utc)
                    
                    if task_created >= exec_started:
                        print(f"    [INCLUDED in current run]")
                    else:
                        print(f"    [EXCLUDED - created before execution_started_at]")
        else:
            print("  No tasks found!")
        
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_project_status.py <project_id>")
        print("Example: python check_project_status.py nextjs-saas-platform-for-managing-sports-teams")
        sys.exit(1)
    
    # Fix event loop for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    project_id = sys.argv[1]
    asyncio.run(check_project(project_id))

