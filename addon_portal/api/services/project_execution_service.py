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
        # Create log files for stdout and stderr
        # Clear existing logs for fresh start (each execution gets clean logs)
        stdout_log = output_folder / "execution_stdout.log"
        stderr_log = output_folder / "execution_stderr.log"
        
        # Clear old log files if they exist (start fresh for each execution)
        if stdout_log.exists():
            stdout_log.unlink()
        if stderr_log.exists():
            stderr_log.unlink()
        
        # Open files in write mode (fresh start) and keep them open for subprocess
        stdout_file = open(stdout_log, 'w', encoding='utf-8')
        stderr_file = open(stderr_log, 'w', encoding='utf-8')
        
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
        
        # Track progress to detect stuck processes
        last_log_size = 0
        last_task_count = 0
        no_progress_count = 0
        stuck_threshold = 300  # 5 minutes (60 checks * 5 seconds) with no progress
        
        while waited < max_wait_time:
            # Check for stuck process (no progress for extended period)
            if waited > 60 and waited % 60 == 0:  # Check every minute
                try:
                    # Check log file size (indicates if process is writing)
                    stderr_log = output_folder / "execution_stderr.log"
                    current_log_size = stderr_log.stat().st_size if stderr_log.exists() else 0
                    
                    # Check task count
                    db_check = AsyncSessionLocal()
                    try:
                        from ..services.agent_task_service import calculate_project_progress
                        result = await db_check.execute(
                            select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
                        )
                        project_check = result.scalar_one_or_none()
                        if project_check and project_check.execution_started_at:
                            task_stats = await calculate_project_progress(
                                db_check,
                                project_id,
                                execution_started_at=project_check.execution_started_at
                            )
                            current_task_count = task_stats.get('total_tasks', 0)
                        else:
                            current_task_count = 0
                    finally:
                        await db_check.close()
                    
                    # Check if making progress
                    if current_log_size == last_log_size and current_task_count == last_task_count:
                        no_progress_count += 1
                        if no_progress_count >= stuck_threshold:
                            # Process is stuck - check for error patterns in logs
                            if stderr_log.exists():
                                try:
                                    import aiofiles
                                    async with aiofiles.open(stderr_log, 'r', encoding='utf-8', errors='ignore') as f:
                                        log_content = await f.read()
                                except ImportError:
                                    with open(stderr_log, 'r', encoding='utf-8', errors='ignore') as f:
                                        log_content = f.read()
                                
                                # Check for stuck patterns (repeated LLM failures, event loop errors)
                                stuck_patterns = [
                                    'LLM task breakdown failed',
                                    'Event loop is closed',
                                    'All providers failed',
                                    'Task was destroyed but it is pending'
                                ]
                                
                                if any(pattern in log_content for pattern in stuck_patterns):
                                    # Process is stuck in error loop - terminate it
                                    LOGGER.error(
                                        "project_execution_stuck_detected",
                                        extra={
                                            "project_id": project_id,
                                            "tenant_id": tenant_id,
                                            "process_id": process_id,
                                            "no_progress_minutes": no_progress_count,
                                            "task_count": current_task_count,
                                            "log_size": current_log_size,
                                        }
                                    )
                                    # Try to terminate the process
                                    try:
                                        import platform
                                        if platform.system() == "Windows":
                                            try:
                                                import psutil
                                                proc = psutil.Process(process_id)
                                                proc.terminate()
                                                await asyncio.sleep(2)
                                                if proc.is_running():
                                                    proc.kill()
                                            except (ImportError, psutil.NoSuchProcess):
                                                pass
                                        else:
                                            import signal
                                            os.kill(process_id, signal.SIGTERM)
                                            await asyncio.sleep(2)
                                            try:
                                                os.kill(process_id, signal.SIGKILL)
                                            except ProcessLookupError:
                                                pass
                                    except Exception as term_error:
                                        LOGGER.warning(f"Could not terminate stuck process {process_id}: {term_error}")
                                    
                                    # Mark as failed and exit monitoring
                                    return_code = -1
                                    break
                    else:
                        # Progress detected - reset counter
                        no_progress_count = 0
                        last_log_size = current_log_size
                        last_task_count = current_task_count
                except Exception as progress_check_error:
                    LOGGER.debug(f"Error checking progress: {progress_check_error}")
            
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
        
        # Before updating status, check for errors in logs and verify task creation
        stderr_log = output_folder / "execution_stderr.log"
        stdout_log = output_folder / "execution_stdout.log"
        has_errors = False
        error_message = None
        has_tasks_completed = False
        
        # Check stderr log for fatal errors (syntax errors, import errors, etc.)
        if stderr_log.exists():
            try:
                try:
                    import aiofiles
                    async with aiofiles.open(stderr_log, 'r', encoding='utf-8', errors='ignore') as f:
                        stderr_content = await f.read()
                except ImportError:
                    # Fallback to sync file I/O if aiofiles not available
                    with open(stderr_log, 'r', encoding='utf-8', errors='ignore') as f:
                        stderr_content = f.read()
                
                # Check for common fatal errors
                fatal_errors = [
                    'SyntaxError',
                    'IndentationError',
                    'ImportError',
                    'ModuleNotFoundError',
                    'NameError',
                    'TypeError',
                    'AttributeError',
                    'FileNotFoundError',
                    'PermissionError',
                ]
                for error_type in fatal_errors:
                    if error_type in stderr_content:
                        has_errors = True
                        # Extract error message (first occurrence)
                        lines = stderr_content.split('\n')
                        for i, line in enumerate(lines):
                            if error_type in line:
                                # Get context (current line + next few lines)
                                error_context = '\n'.join(lines[max(0, i-2):min(len(lines), i+5)])
                                error_message = f"{error_type} detected in execution logs:\n{error_context[:500]}"
                                break
                        if error_message:
                            break
            except Exception as log_error:
                LOGGER.warning(
                    "could_not_read_stderr_log",
                    extra={
                        "project_id": project_id,
                        "stderr_log": str(stderr_log),
                        "error": str(log_error),
                    }
                )
        
        # Check stdout log for successful completion message
        if stdout_log.exists() and not has_errors:
            try:
                try:
                    import aiofiles
                    async with aiofiles.open(stdout_log, 'r', encoding='utf-8', errors='ignore') as f:
                        stdout_content = await f.read()
                except ImportError:
                    # Fallback to sync file I/O if aiofiles not available
                    with open(stdout_log, 'r', encoding='utf-8', errors='ignore') as f:
                        stdout_content = f.read()
                
                # Check for successful completion indicators
                if "All tasks completed!" in stdout_content or "completion_percentage': 100.0" in stdout_content:
                    has_tasks_completed = True
            except Exception as log_error:
                LOGGER.warning(
                    "could_not_read_stdout_log",
                    extra={
                        "project_id": project_id,
                        "stdout_log": str(stdout_log),
                        "error": str(log_error),
                    }
                )
        
        # Check if any tasks were created for this run
        db = AsyncSessionLocal()
        try:
            from ..services.agent_task_service import calculate_project_progress
            
            result = await db.execute(
                select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if project:
                # Get task count for current run (filtered by execution_started_at)
                task_stats = await calculate_project_progress(
                    db, 
                    project_id, 
                    execution_started_at=project.execution_started_at
                )
                task_count = task_stats.get('total_tasks', 0)
                
                # Determine final status
                if has_errors:
                    # Fatal errors detected - mark as failed
                    project.execution_status = 'failed'
                    project.execution_error = error_message or f"Fatal error detected in execution logs. Process exited with code {return_code}."
                    project.execution_completed_at = datetime.now(timezone.utc)
                    LOGGER.error(
                        "project_execution_failed_with_errors",
                        extra={
                            "project_id": project_id,
                            "tenant_id": tenant_id,
                            "process_id": process_id,
                            "return_code": return_code,
                            "error_type": "fatal_error_in_logs",
                            "task_count": task_count,
                        }
                    )
                elif return_code != 0:
                    # Non-zero exit code - mark as failed
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
                            "task_count": task_count,
                        }
                    )
                elif task_count == 0 and not has_tasks_completed:
                    # Process exited with code 0 but no tasks created and no completion message
                    # This indicates an immediate crash (e.g., syntax error on import)
                    project.execution_status = 'failed'
                    project.execution_error = (
                        "Process exited successfully but no tasks were created. "
                        "This may indicate an immediate crash (e.g., syntax error, import error). "
                        "Please check execution logs."
                    )
                    project.execution_completed_at = datetime.now(timezone.utc)
                    LOGGER.warning(
                        "project_execution_completed_without_tasks",
                        extra={
                            "project_id": project_id,
                            "tenant_id": tenant_id,
                            "process_id": process_id,
                            "return_code": return_code,
                            "task_count": task_count,
                        }
                    )
                else:
                    # Successful completion
                    project.execution_status = 'completed'
                    project.execution_completed_at = datetime.now(timezone.utc)
                    LOGGER.info(
                        "project_execution_completed",
                        extra={
                            "project_id": project_id,
                            "tenant_id": tenant_id,
                            "process_id": process_id,
                            "return_code": return_code,
                            "task_count": task_count,
                            "has_completion_message": has_tasks_completed,
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


async def check_and_update_project_completion(project_id: str) -> Optional[bool]:
    """
    Check if all tasks for a project are completed and update project status accordingly.
    
    This function should be called:
    - When a task is completed
    - Periodically (e.g., every minute) for running projects
    - When querying project status
    
    Args:
        project_id: Project ID to check
        
    Returns:
        True if project was marked as completed
        False if project was marked as failed
        None if project is still running or no update needed
    """
    db = AsyncSessionLocal()
    try:
        from ..services.agent_task_service import calculate_project_progress
        
        # Get project
        result = await db.execute(
            select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        # Only check projects that are currently running
        if project.execution_status != 'running':
            return None
        
        # Get task statistics for current run
        task_stats = await calculate_project_progress(
            db,
            project_id,
            execution_started_at=project.execution_started_at
        )
        
        total_tasks = task_stats.get('total_tasks', 0)
        completed_tasks = task_stats.get('completed_tasks', 0)
        failed_tasks = task_stats.get('failed_tasks', 0)
        in_progress_tasks = task_stats.get('in_progress_tasks', 0)
        pending_tasks = task_stats.get('pending_tasks', 0)
        
        # If no tasks exist yet, don't update status
        if total_tasks == 0:
            return None
        
        # Check if all tasks are done (no pending or in_progress tasks)
        all_tasks_done = (pending_tasks == 0 and in_progress_tasks == 0)
        
        if all_tasks_done:
            # All tasks are completed or failed
            # Determine final status based on completion rate
            completion_rate = (completed_tasks / total_tasks) * 100.0 if total_tasks > 0 else 0.0
            
            # If more than 50% of tasks completed, mark as completed
            # Otherwise, mark as failed (too many failures)
            if completion_rate >= 50.0:
                project.execution_status = 'completed'
                project.execution_completed_at = datetime.now(timezone.utc)
                project.execution_error = None
                
                LOGGER.info(
                    "project_auto_completed_by_tasks",
                    extra={
                        "project_id": project_id,
                        "tenant_id": project.tenant_id,
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "failed_tasks": failed_tasks,
                        "completion_rate": completion_rate,
                    }
                )
                await db.commit()
                return True
            else:
                # Too many failures - mark as failed
                project.execution_status = 'failed'
                project.execution_completed_at = datetime.now(timezone.utc)
                project.execution_error = (
                    f"Project failed: {failed_tasks} out of {total_tasks} tasks failed "
                    f"(completion rate: {completion_rate:.1f}%). "
                    f"Too many task failures to consider project successful."
                )
                
                LOGGER.warning(
                    "project_auto_failed_by_tasks",
                    extra={
                        "project_id": project_id,
                        "tenant_id": project.tenant_id,
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "failed_tasks": failed_tasks,
                        "completion_rate": completion_rate,
                    }
                )
                await db.commit()
                return False
        
        return None  # Still running
        
    except Exception as e:
        LOGGER.error(
            "check_project_completion_failed",
            extra={
                "project_id": project_id,
                "error": str(e),
            },
            exc_info=True
        )
        await db.rollback()
        return None
    finally:
        await db.close()


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

