# Project Execution Issues and Fixes

## Critical Issues Identified

### 1. ❌ **Workspace Path Issue - Code Files Not Saved to Output Folder**

**Problem:**
- `main.py` sets `workspace_path=args.workspace or (args.output_folder if args.output_folder else ".")`
- If `--workspace` is not provided, it defaults to "." (current directory)
- Agents write files to `self.workspace_path`, which might be "." instead of the output folder
- Code files end up in the wrong location or not saved at all

**Evidence:**
- Only log files found in `Tenant_Projects/migrate-zoho-to-odoo/`
- No code files visible in the output folder
- Logs show tasks completing but no "Created file" messages

**Fix Required:**
- Ensure `workspace_path` is set to `output_folder` when `--output-folder` is provided
- Update `main.py` to prioritize `--output-folder` over `--workspace`

### 2. ❌ **Project Execution Status Never Updated to "Completed"**

**Problem:**
- `project_execution_service.py` uses `subprocess.Popen()` which is fire-and-forget
- No mechanism to monitor when the subprocess completes
- `execution_status` stays "running" forever
- Dashboard shows project as still running even after completion

**Evidence:**
- Logs show "All tasks completed!" but project status never updates
- Dashboard metrics show zero because project status query filters by `execution_status != 'completed'`

**Fix Required:**
- Add background task to monitor subprocess completion
- Update `execution_status` to "completed" when process exits successfully
- Update `execution_status` to "failed" if process exits with error code

### 3. ❌ **Event Loop Errors Preventing Task Tracking**

**Problem:**
- `agents/task_tracking.py` uses `run_async()` which creates a new event loop
- Database connection pool is bound to a different event loop
- Causes "is bound to a different event loop" errors
- Task status updates fail silently

**Evidence from logs:**
```
RuntimeError: <Queue at 0x19f52685fd0 maxsize=5 tasks=47> is bound to a different event loop
Failed to update task status in database: <Queue...> is bound to a different event loop
```

**Fix Required:**
- Use the existing event loop instead of creating a new one
- Or use thread-safe database operations
- Ensure database connections use the correct event loop

### 4. ❌ **Metrics Showing Zero Values**

**Problem:**
- GraphQL queries filter by `execution_status == 'completed'`
- Since projects never get marked as completed, queries return empty results
- Dashboard shows zero for all metrics

**Fix Required:**
- Fix issue #2 (project completion status)
- Update GraphQL queries to also check for `execution_status == 'running'` with recent activity
- Show metrics for running projects too

### 5. ❌ **No Agent Activity Visible**

**Problem:**
- Agent activity subscription might not be working
- Or tasks aren't being properly tracked due to event loop issues
- Dashboard shows no real-time agent activity

**Fix Required:**
- Fix event loop issues (#3)
- Verify agent activity subscriptions are working
- Ensure task updates are properly broadcast

## Implementation Plan

### Priority 1: Fix Workspace Path (CRITICAL)
```python
# In main.py line 703
# BEFORE:
workspace_path=args.workspace or (args.output_folder if args.output_folder else ".")

# AFTER:
workspace_path = args.output_folder if args.output_folder else (args.workspace or ".")
```

### Priority 2: Add Subprocess Monitoring (CRITICAL)
```python
# In project_execution_service.py
# Add background task to monitor process completion
import asyncio
from asyncio import create_task

async def _monitor_process(process_id: int, project_id: str, session: AsyncSession):
    """Monitor subprocess and update status when complete."""
    # Poll process status
    # Update execution_status when done
```

### Priority 3: Fix Event Loop Issues (HIGH)
```python
# In agents/task_tracking.py
# Use existing event loop or thread-safe approach
def run_async(coro):
    """Run async function synchronously using existing event loop."""
    try:
        loop = asyncio.get_running_loop()
        # Use run_coroutine_threadsafe or similar
    except RuntimeError:
        # No running loop, create one
        ...
```

### Priority 4: Update GraphQL Queries (MEDIUM)
- Allow metrics for running projects
- Show real-time progress even if not completed

## Testing Checklist

- [ ] Code files are created in `Tenant_Projects/{project_id}/code/`
- [ ] Project execution_status updates to "completed" when done
- [ ] Dashboard shows correct metrics (not all zeros)
- [ ] Agent activity is visible in real-time
- [ ] Task tracking works without event loop errors
- [ ] Project can be downloaded as ZIP file when completed

