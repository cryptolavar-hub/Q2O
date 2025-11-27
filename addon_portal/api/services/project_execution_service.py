"""Service for executing projects via main.py."""

import subprocess
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.llm_config import LLMProjectConfig
from ..models.licensing import Tenant, Subscription, SubscriptionState
from ..core.exceptions import InvalidOperationError
from ..core.logging import get_logger
from ..core.db import AsyncSessionLocal

LOGGER = get_logger(__name__)

# Root folder for all tenant projects
TENANT_PROJECTS_ROOT = Path(__file__).resolve().parents[3] / "Tenant_Projects"

# Configuration for stuck project detection
PROJECT_EXECUTION_TIMEOUT_HOURS = int(os.getenv("PROJECT_EXECUTION_TIMEOUT_HOURS", "24"))


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
    
    if not main_py_path.exists():
        raise InvalidOperationError(f"main.py not found at {main_py_path}")
    
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
    
    LOGGER.info(
        "project_execution_command",
        extra={
            "project_id": project.project_id,
            "tenant_id": tenant_id,
            "command": " ".join(cmd),
            "output_folder": str(output_folder),
        }
    )
    
    # Execute in background (non-blocking)
    try:
        # Create log files for stdout and stderr (open in append mode to allow subprocess to write)
        stdout_log = output_folder / "execution_stdout.log"
        stderr_log = output_folder / "execution_stderr.log"
        
        # Open files in append mode and keep them open for subprocess
        stdout_file = open(stdout_log, 'a', encoding='utf-8')
        stderr_file = open(stderr_log, 'a', encoding='utf-8')
        
        try:
            # Ensure .env file is found - set working directory to project root
            project_root = Path(__file__).resolve().parents[3]
            env = os.environ.copy()
            # Ensure PYTHONPATH includes project root for imports
            pythonpath = env.get("PYTHONPATH", "")
            if pythonpath:
                env["PYTHONPATH"] = f"{project_root}{os.pathsep}{pythonpath}"
            else:
                env["PYTHONPATH"] = str(project_root)
            
            process = subprocess.Popen(
                cmd,
                stdout=stdout_file,
                stderr=stderr_file,
                cwd=str(project_root),  # Run from project root so .env is found
                env=env,  # Pass environment variables (including DB connection)
            )
            
            # Don't close files - subprocess needs them open
            # They'll be closed when subprocess terminates
            
            LOGGER.info(
                "project_execution_started",
                extra={
                    "project_id": project.project_id,
                    "tenant_id": tenant_id,
                    "process_id": process.pid,
                    "output_folder": str(output_folder),
                    "subscription_state": subscription.state.value,
                    "command": " ".join(cmd),
                    "stdout_log": str(stdout_log),
                    "stderr_log": str(stderr_log),
                }
            )
            
            # Process ID is logged above and can be found in logs
            # execution_started_at is already set above (line 89)
            await session.commit()
            
            # Start background task to monitor process completion
            asyncio.create_task(_monitor_process_completion(
                process.pid,
                project.project_id,
                tenant_id,
                output_folder
            ))
            
            return {
                "execution_id": process.pid,
                "status": "running",
                "output_folder_path": str(output_folder),
            }
        except Exception as subprocess_error:
            # Close files if subprocess creation failed
            stdout_file.close()
            stderr_file.close()
            raise subprocess_error
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


async def _monitor_process_completion(
    process_id: int,
    project_id: str,
    tenant_id: int,
    output_folder: Path
):
    """
    Background task to monitor subprocess completion and update project status.
    
    Args:
        process_id: Process ID to monitor
        project_id: Project ID
        tenant_id: Tenant ID
        output_folder: Output folder path
    """
    try:
        # Wait for process to complete (check every 5 seconds)
        max_wait_time = 3600 * 24  # 24 hours max
        check_interval = 5  # Check every 5 seconds
        waited = 0
        
        while waited < max_wait_time:
            # Check if process is still running
            try:
                # Use os.waitpid with WNOHANG to check without blocking
                # On Windows, use psutil or check process handle
                import platform
                if platform.system() == "Windows":
                    # Windows: Check if process exists
                    try:
                        import psutil
                        proc = psutil.Process(process_id)
                        if proc.is_running():
                            await asyncio.sleep(check_interval)
                            waited += check_interval
                            continue
                        else:
                            # Process finished
                            return_code = proc.returncode
                            break
                    except ImportError:
                        # psutil not available, use alternative method
                        # On Windows, try to use subprocess.Popen.poll() approach
                        # Since we don't have the process object, we'll use a simpler check
                        try:
                            # Try to open process handle to check if it exists
                            import ctypes
                            from ctypes import wintypes
                            kernel32 = ctypes.windll.kernel32
                            
                            # Try to open process with PROCESS_QUERY_INFORMATION
                            PROCESS_QUERY_INFORMATION = 0x0400
                            handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, process_id)
                            
                            if handle:
                                # Process exists - check if it's still running
                                exit_code = wintypes.DWORD()
                                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                                    if exit_code.value == 259:  # STILL_ACTIVE
                                        # Process still running
                                        kernel32.CloseHandle(handle)
                                        await asyncio.sleep(check_interval)
                                        waited += check_interval
                                        continue
                                    else:
                                        # Process finished
                                        return_code = exit_code.value
                                        kernel32.CloseHandle(handle)
                                        break
                                else:
                                    # Can't get exit code - assume still running
                                    kernel32.CloseHandle(handle)
                                    await asyncio.sleep(check_interval)
                                    waited += check_interval
                                    continue
                            else:
                                # Process doesn't exist (handle open failed)
                                # This usually means process finished
                                return_code = 0
                                break
                        except Exception as win_error:
                            # Fallback: Assume process finished if we can't check
                            LOGGER.warning(f"Could not check Windows process {process_id}: {win_error}")
                            return_code = 0
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process doesn't exist or we can't access it
                        return_code = -1
                        break
                else:
                    # Unix: Use waitpid with WNOHANG
                    pid, status = os.waitpid(process_id, os.WNOHANG)
                    if pid == 0:
                        # Process still running
                        await asyncio.sleep(check_interval)
                        waited += check_interval
                        continue
                    else:
                        # Process finished
                        return_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                        break
            except (ChildProcessError, ProcessLookupError):
                # Process already finished
                return_code = 0
                break
            except Exception as e:
                LOGGER.warning(f"Error checking process {process_id}: {e}")
                await asyncio.sleep(check_interval)
                waited += check_interval
                continue
        
        # Update project status in database
        db = AsyncSessionLocal()
        try:
            result = await db.execute(
                select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if project:
                if return_code == 0:
                    project.execution_status = 'completed'
                    project.execution_completed_at = datetime.now(timezone.utc)
                    LOGGER.info(
                        "project_execution_completed",
                        extra={
                            "project_id": project_id,
                            "tenant_id": tenant_id,
                            "process_id": process_id,
                        }
                    )
                else:
                    project.execution_status = 'failed'
                    project.execution_error = f"Process exited with code {return_code}"
                    project.execution_completed_at = datetime.now(timezone.utc)
                    LOGGER.error(
                        "project_execution_failed",
                        extra={
                            "project_id": project_id,
                            "tenant_id": tenant_id,
                            "process_id": process_id,
                            "return_code": return_code,
                        }
                    )
                
                await db.commit()
        except Exception as e:
            LOGGER.error(
                "project_execution_status_update_failed",
                extra={
                    "project_id": project_id,
                    "tenant_id": tenant_id,
                    "process_id": process_id,
                    "error": str(e),
                },
                exc_info=True
            )
            await db.rollback()
        finally:
            await db.close()
            
    except Exception as e:
        LOGGER.error(
            "project_execution_monitoring_failed",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_id,
                "process_id": process_id,
                "error": str(e),
            },
            exc_info=True
        )


async def cleanup_stuck_projects():
    """
    Cleanup function to detect and mark stuck projects as failed.
    
    A project is considered "stuck" if:
    - execution_status = 'running'
    - execution_started_at is older than PROJECT_EXECUTION_TIMEOUT_HOURS
    - Process is no longer running (or can't be verified)
    
    This should be called periodically (e.g., every hour) to catch cases where
    process monitoring failed or process crashed without being detected.
    """
    db = AsyncSessionLocal()
    try:
        from datetime import timedelta
        
        # Calculate cutoff time (projects started before this are considered stuck)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=PROJECT_EXECUTION_TIMEOUT_HOURS)
        
        # Find stuck projects (must have execution_started_at set)
        result = await db.execute(
            select(LLMProjectConfig).where(
                LLMProjectConfig.execution_status == 'running',
                LLMProjectConfig.execution_started_at.isnot(None),
                LLMProjectConfig.execution_started_at < cutoff_time
            )
        )
        stuck_projects = result.scalars().all()
        
        if not stuck_projects:
            LOGGER.debug("No stuck projects found during cleanup")
            return
        
        LOGGER.info(
            "cleanup_stuck_projects_started",
            extra={
                "stuck_count": len(stuck_projects),
                "timeout_hours": PROJECT_EXECUTION_TIMEOUT_HOURS,
            }
        )
        
        import platform
        marked_failed = 0
        
        for project in stuck_projects:
            try:
                # Try to verify if process is actually dead
                # Extract process ID from execution_started_at or output folder logs
                # For now, we'll mark as failed if it's been running too long
                # In the future, we could parse execution logs to get actual process ID
                
                # Check if we can verify process is dead (optional enhancement)
                process_dead = True  # Assume dead if we can't verify
                
                # Try to check process if we have a way to identify it
                # This is a simplified check - in production you might want to store process_id
                if process_dead:
                    project.execution_status = 'failed'
                    project.execution_error = (
                        f"Project execution timed out after {PROJECT_EXECUTION_TIMEOUT_HOURS} hours. "
                        "Process may have crashed or been terminated."
                    )
                    project.execution_completed_at = datetime.now(timezone.utc)
                    marked_failed += 1
                    
                    LOGGER.warning(
                        "stuck_project_marked_failed",
                        extra={
                            "project_id": project.project_id,
                            "tenant_id": project.tenant_id,
                            "started_at": project.execution_started_at.isoformat() if project.execution_started_at else None,
                            "hours_running": (datetime.now(timezone.utc) - project.execution_started_at).total_seconds() / 3600 if project.execution_started_at else None,
                        }
                    )
            except Exception as e:
                LOGGER.error(
                    "cleanup_project_failed",
                    extra={
                        "project_id": project.project_id,
                        "error": str(e),
                    },
                    exc_info=True
                )
                continue
        
        if marked_failed > 0:
            await db.commit()
            LOGGER.info(
                "cleanup_stuck_projects_completed",
                extra={
                    "marked_failed": marked_failed,
                    "total_checked": len(stuck_projects),
                }
            )
        else:
            await db.rollback()
            
    except Exception as e:
        LOGGER.error(
            "cleanup_stuck_projects_failed",
            extra={"error": str(e)},
            exc_info=True
        )
        await db.rollback()
    finally:
        await db.close()


async def restart_project(
    session: AsyncSession,
    project: LLMProjectConfig,
    tenant_id: int,
) -> Dict[str, any]:
    """Restart a failed project execution.
    
    Args:
        session: Database session (async)
        project: Project configuration (must have execution_status='failed')
        tenant_id: Tenant ID
    
    Returns:
        dict with execution_id, status, output_folder_path
    
    Requirements:
    - Project must have execution_status='failed' (completed projects cannot be restarted)
    - Project must have activation code assigned
    - Tenant must have active or trialing subscription
    - For trialing subscriptions: only one project can be running at a time
    """
    # Validate project can be restarted (only failed projects)
    if project.execution_status != 'failed':
        raise InvalidOperationError(
            f"Only failed projects can be restarted. Current status: {project.execution_status}"
        )
    
    # Reset execution fields
    project.execution_status = 'pending'
    project.execution_error = None
    project.execution_started_at = None
    project.execution_completed_at = None
    await session.flush()
    
    # Now execute the project (reuse existing execute_project logic)
    return await execute_project(session, project, tenant_id)

