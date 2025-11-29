# Bug Report: Project Restart Not Clearing Old Tasks

**Date**: November 29, 2025  
**Role**: QA_Engineer - Bug Investigation  
**Status**: 🔴 **CRITICAL** - Restarted projects failing immediately

---

## 📊 **Issue Summary**

When a failed project is restarted, old tasks from the previous execution remain in the database, causing the new execution to fail immediately or behave incorrectly.

**Impact**:
- Restarted projects fail immediately after restart
- Old task data interferes with new execution
- Project progress calculations include stale data
- Users cannot successfully restart failed projects

---

## 🔍 **Root Cause Analysis**

### **Problem: Old Tasks Not Deleted on Restart**

**Location**: `addon_portal/api/services/project_execution_service.py`, `restart_project()` function

**Current Behavior**:
```python
async def restart_project(...):
    # Reset execution fields
    project.execution_status = 'pending'
    project.execution_error = None
    project.execution_started_at = None
    project.execution_completed_at = None
    await session.flush()
    
    # Now execute the project (reuse existing execute_project logic)
    return await execute_project(session, project, tenant_id)
```

**Issue**: The function only resets project execution fields but **does not delete old tasks** from the database. This causes:
1. Old tasks remain in database with `project_id` matching the restarted project
2. New execution creates new tasks, but old tasks interfere
3. Progress calculations may include old tasks (even though `execution_started_at` filtering helps)
4. Task conflicts or duplicate task IDs may occur

---

## ✅ **Solution**

### **Fix: Delete Old Tasks Before Restart**

**Updated Code**:
```python
async def restart_project(...):
    # Validate project can be restarted (only failed projects)
    if project.execution_status != 'failed':
        raise InvalidOperationError(...)
    
    # QA_Engineer: Clear old tasks from previous execution to prevent interference
    from ..models.agent_tasks import AgentTask
    from sqlalchemy import delete
    
    # Delete all tasks associated with this project from previous runs
    # This ensures a clean slate for the restart
    delete_stmt = delete(AgentTask).where(AgentTask.project_id == project.project_id)
    await session.execute(delete_stmt)
    
    LOGGER.info(
        "project_restart_cleared_old_tasks",
        extra={
            "project_id": project.project_id,
            "tenant_id": tenant_id,
        }
    )
    
    # Reset execution fields
    project.execution_status = 'pending'
    project.execution_error = None
    project.execution_started_at = None
    project.execution_completed_at = None
    await session.flush()
    
    # Now execute the project (reuse existing execute_project logic)
    return await execute_project(session, project, tenant_id)
```

**Why This Works**:
- Deletes all old tasks before restart
- Ensures clean slate for new execution
- Prevents task conflicts and stale data
- Logs the cleanup action for debugging

---

## 🧪 **Testing**

**Test Cases**:
1. ✅ Restart failed project → Old tasks deleted
2. ✅ Restart failed project → New execution starts clean
3. ✅ Restart failed project → Progress calculations accurate
4. ✅ Restart failed project → No task conflicts

---

**QA Engineer**: Identified critical bug where restart doesn't clear old tasks, causing immediate failures. Fixed by deleting old tasks before restart.

