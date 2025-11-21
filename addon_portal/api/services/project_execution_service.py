"""Service for executing projects via main.py."""

import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.llm_config import LLMProjectConfig
from ..models.licensing import Tenant, Subscription, SubscriptionState
from ..core.exceptions import InvalidOperationError
from ..core.logging import get_logger

LOGGER = get_logger(__name__)

# Root folder for all tenant projects
TENANT_PROJECTS_ROOT = Path(__file__).resolve().parents[3] / "Tenant_Projects"


async def execute_project(
    session: AsyncSession,
    project: LLMProjectConfig,
    tenant_id: int,
) -> Dict[str, any]:
    """Execute a project by calling main.py with project attributes.
    
    Args:
        session: Database session (async)
        project: Project configuration
        tenant_id: Tenant ID
    
    Returns:
        dict with execution_id, status, output_folder_path
    
    Requirements:
    - Project must have activation code assigned
    - Tenant must have active or trialing subscription
    - For trialing subscriptions: only one project can be running at a time
    """
    # Validate subscription status
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise InvalidOperationError("Tenant not found.")
    
    result = await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise InvalidOperationError("Subscription required to run projects.")
    
    if subscription.state == SubscriptionState.trialing:
        # Check if another project is already running
        from sqlalchemy import func
        result = await session.execute(
            select(func.count(LLMProjectConfig.id)).where(
                LLMProjectConfig.tenant_id == tenant_id,
                LLMProjectConfig.execution_status == 'running'
            )
        )
        running_projects = result.scalar()
        
        if running_projects >= 1:
            raise InvalidOperationError(
                "Trialing subscription allows only one running project at a time. "
                "Please wait for the current project to complete or upgrade your plan."
            )
    elif subscription.state != SubscriptionState.active:
        raise InvalidOperationError(
            f"{subscription.state.value.title()} subscription cannot run projects. Please renew your subscription."
        )
    
    # Validate project has activation code
    if not project.activation_code_id:
        raise InvalidOperationError("Project must be activated with an activation code before running.")
    
    # Validate required fields
    if not all([project.project_id, project.client_name, project.description, project.custom_instructions]):
        raise InvalidOperationError("Project ID, Name, Description, and Objectives are required.")
    
    # Create output folder: Tenant_Projects/{project_id}/
    output_folder = TENANT_PROJECTS_ROOT / project.project_id
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Update project status
    project.execution_status = 'running'
    project.execution_started_at = datetime.now(timezone.utc)
    project.output_folder_path = str(output_folder)
    await session.commit()
    
    # Prepare main.py command
    # Assuming main.py is in the project root
    main_py_path = Path(__file__).resolve().parents[3] / "main.py"
    
    # Build command with project attributes
    cmd = [
        "python",
        str(main_py_path),
        "--project-id", project.project_id,
        "--project-name", project.client_name,
        "--description", project.description or "",
        "--objectives", project.custom_instructions or "",
        "--output-folder", str(output_folder),
        "--tenant-id", str(tenant_id),
    ]
    
    # Execute in background (non-blocking)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(output_folder.parent),
        )
        
        LOGGER.info(
            "project_execution_started",
            extra={
                "project_id": project.project_id,
                "tenant_id": tenant_id,
                "process_id": process.pid,
                "output_folder": str(output_folder),
                "subscription_state": subscription.state.value,
            }
        )
        
        return {
            "execution_id": process.pid,
            "status": "running",
            "output_folder_path": str(output_folder),
        }
    except Exception as e:
        # Update project status to failed
        project.execution_status = 'failed'
        project.execution_error = str(e)
        project.execution_completed_at = datetime.now(timezone.utc)
        await session.commit()
        
        LOGGER.error(
            "project_execution_failed",
            extra={
                "project_id": project.project_id,
                "tenant_id": tenant_id,
                "error": str(e),
            }
        )
        
        raise InvalidOperationError(f"Failed to start project execution: {str(e)}")

