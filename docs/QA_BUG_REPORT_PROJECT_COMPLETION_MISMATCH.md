# Bug Report: Project Completion Status Mismatch

**Date**: November 27, 2025  
**Role**: QA_Engineer - Bug Hunter  
**Severity**: 🔴 **CRITICAL**  
**Status**: 🔍 **IDENTIFIED**

---

## 🐛 Bug Summary

Projects are being incorrectly marked as **"Completed"** when they still have unfinished tasks. The dashboard shows **48 active tasks** remaining, but the completion check logic incorrectly determines that all tasks are done.

**Example Project**: THE WORKPRESS INC (simple-wordpress-like-cms)
- **Dashboard Shows**: 
  - Status: "Completed" ❌
  - Progress: 68% (102/150 tasks)
  - Active Tasks: **48** ⚠️
  - Completed: 102
  - Failed: 0
  - Total: 150

**Database Reality**: 48 tasks are still unfinished (likely `cancelled` or other status)

---

## 🔍 Root Cause Analysis

### **The Problem**

There's a **mismatch** between how the dashboard calculates "active tasks" and how the completion check determines if all tasks are done.

#### **1. Dashboard Calculation** (`status.tsx` line 364-365)

```typescript
activeTasks: currentProject?.totalTasks 
  ? Math.max(0, (currentProject.totalTasks - (currentProject.completedTasks || 0) - (currentProject.failedTasks || 0)))
  : 0,
```

**Logic**: `activeTasks = totalTasks - completedTasks - failedTasks`

This counts **ALL** tasks that are NOT `completed` or `failed` as "active", including:
- ✅ `pending`
- ✅ `started`
- ✅ `running`
- ✅ `cancelled` ⚠️ **PROBLEM HERE**

#### **2. Completion Check Logic** (`project_execution_service.py` line 682)

```python
all_tasks_done = (pending_tasks == 0 and in_progress_tasks == 0)
```

Where `in_progress_tasks` counts tasks with status `'started'` or `'running'` (line 328):

```python
func.sum(case((AgentTask.status.in_(['started', 'running']), 1), else_=0)).label('in_progress'),
```

**The Bug**: Tasks with status `'cancelled'` are:
- ✅ Counted in `totalTasks`
- ✅ NOT counted as `completedTasks`
- ✅ NOT counted as `failedTasks`
- ✅ NOT counted as `pending_tasks`
- ✅ NOT counted as `in_progress_tasks`

**Result**: If there are 48 `cancelled` tasks:
- Dashboard shows: `activeTasks = 150 - 102 - 0 = 48` ✅ (correct)
- Completion check sees: `pending_tasks = 0, in_progress_tasks = 0` → **Marks as completed!** ❌ (WRONG!)

---

## 📋 Task Status Values

From `agent_tasks.py` line 74:
```python
status IN ('pending', 'started', 'running', 'completed', 'failed', 'cancelled')
```

**Possible Statuses**:
- `pending` - Task not started
- `started` - Task started but not running yet
- `running` - Task currently executing
- `completed` - Task finished successfully
- `failed` - Task failed
- `cancelled` - Task was cancelled ⚠️ **NOT HANDLED IN COMPLETION CHECK**

---

## 🎯 Impact Analysis

### **Severity**: 🔴 **CRITICAL**

**Impact**:
1. **User Confusion**: Projects show as "Completed" when they're not finished
2. **Data Integrity**: Incorrect project status in database
3. **Billing Issues**: Users may be charged for "completed" projects that aren't done
4. **Trust Issues**: Platform appears unreliable/untrustworthy
5. **Workflow Disruption**: Users can't distinguish between truly completed and partially completed projects

**Affected Areas**:
- Project status display
- Project completion detection
- Dashboard metrics
- Project filtering/search
- Billing/usage calculations (if based on completion)

---

## 💡 Proposed Solutions

### **Solution 1: Include `cancelled` in Completion Check** ⭐ **RECOMMENDED**

**File**: `addon_portal/api/services/project_execution_service.py`

**Change**: Modify the completion check to include `cancelled` tasks:

```python
# Current (line 682)
all_tasks_done = (pending_tasks == 0 and in_progress_tasks == 0)

# Fixed
all_tasks_done = (
    pending_tasks == 0 
    and in_progress_tasks == 0 
    and cancelled_tasks == 0  # NEW: Check for cancelled tasks
)
```

**Also update** `calculate_project_progress()` to count cancelled tasks:

```python
# Add to line 329
func.sum(case((AgentTask.status == 'cancelled', 1), else_=0)).label('cancelled'),
```

**Pros**:
- ✅ Handles `cancelled` tasks correctly
- ✅ Prevents false completion
- ✅ Clear logic: all tasks must be in final state

**Cons**:
- ⚠️ Need to decide: should `cancelled` tasks prevent completion, or should they be treated as "done"?
- ⚠️ May need to update other logic that counts cancelled tasks

---

### **Solution 2: Exclude `cancelled` from `totalTasks`**

**File**: `addon_portal/api/services/agent_task_service.py`

**Change**: Modify `calculate_project_progress()` to exclude `cancelled` tasks from `totalTasks`:

```python
# Current (line 330)
).where(AgentTask.project_id == project_id)

# Fixed
).where(
    AgentTask.project_id == project_id,
    AgentTask.status != 'cancelled'  # Exclude cancelled from total
)
```

**Pros**:
- ✅ Simple fix
- ✅ Cancelled tasks don't affect completion percentage
- ✅ Matches user expectation (cancelled = not part of project)

**Cons**:
- ⚠️ Cancelled tasks still exist in database but aren't counted
- ⚠️ May hide issues if many tasks are cancelled

---

### **Solution 3: Treat `cancelled` as "Done" State**

**File**: `addon_portal/api/services/project_execution_service.py`

**Change**: Count `cancelled` tasks as "finished" (like `completed` or `failed`):

```python
# Current (line 682)
all_tasks_done = (pending_tasks == 0 and in_progress_tasks == 0)

# Fixed
# A task is "done" if it's completed, failed, OR cancelled
finished_tasks = completed_tasks + failed_tasks + cancelled_tasks
all_tasks_done = (finished_tasks == total_tasks)
```

**Pros**:
- ✅ Cancelled tasks are treated as final state
- ✅ Project can complete even if some tasks were cancelled
- ✅ Matches business logic: cancelled = not going to run

**Cons**:
- ⚠️ May mark projects as completed with many cancelled tasks
- ⚠️ Need to decide threshold: how many cancelled tasks is acceptable?

---

## 🔧 Recommended Fix

**Recommended**: **Solution 1** - Include `cancelled` in completion check **WITH QUALITY THRESHOLD**

**Reasoning**:
1. Most explicit and clear
2. Prevents false completion
3. Maintains data integrity
4. **NEW**: Quality threshold ensures project quality standards

**Quality Requirements**:
- **Quality Calculation**: `quality_percentage = (completed_tasks / total_tasks) * 100`
- **Quality Threshold**: Projects must achieve **≥98% quality** to be marked as completed
- **Cancelled Tasks Impact**: Cancelled tasks reduce quality (they're not completed)
- **Download Prevention**: Projects with quality < 98% cannot be downloaded (must restart/edit)
- **Cancellation Tracking**: Log cancellation reasons to understand why tasks are cancelled

**Implementation Steps**:
1. Update `calculate_project_progress()` to count `cancelled` tasks
2. Update `check_and_update_project_completion()` to:
   - Check `cancelled_tasks == 0` (all tasks must be in final state)
   - Calculate quality: `quality = (completed_tasks / total_tasks) * 100`
   - If quality < 98%, mark as `failed` (not completed)
   - If quality ≥ 98% and all tasks done, mark as `completed`
3. Add cancellation reason tracking (use `error_message` field for cancelled tasks)
4. Update download endpoint to check quality ≥ 98%
5. Add logging to track cancelled tasks and reasons
6. Update dashboard to show cancelled tasks and quality percentage

---

## 🧪 Testing Plan

### **Test Case 1: Cancelled Tasks Prevent Completion**
- **Setup**: Create project with 10 tasks
- **Action**: Complete 6, cancel 4
- **Expected**: Project should NOT be marked as completed
- **Verify**: Dashboard shows 4 active tasks, status = "running"

### **Test Case 2: All Tasks Completed**
- **Setup**: Create project with 10 tasks
- **Action**: Complete all 10
- **Expected**: Project marked as completed
- **Verify**: Dashboard shows 0 active tasks, status = "completed"

### **Test Case 3: Mixed States**
- **Setup**: Create project with 10 tasks
- **Action**: Complete 5, fail 2, cancel 3
- **Expected**: Project should NOT be marked as completed (3 cancelled remain)
- **Verify**: Dashboard shows 3 active tasks, status = "running"

### **Test Case 4: Cancelled Tasks Counted Correctly**
- **Setup**: Create project with 10 tasks
- **Action**: Cancel all 10
- **Expected**: Project should NOT be marked as completed
- **Verify**: Dashboard shows 10 active tasks, status = "running"

---

## 📝 Additional Notes

1. **Why are tasks being cancelled?** Need to investigate root cause:
   - Are agents cancelling tasks incorrectly?
   - Are tasks timing out and being cancelled?
   - Is there a bug in task state management?

2. **Should cancelled tasks be retried?** May need to add logic to:
   - Auto-retry cancelled tasks
   - Allow manual retry
   - Mark project as failed if too many cancelled

3. **Dashboard Display**: Consider showing cancelled tasks separately:
   - "Active: 48 (including 48 cancelled)"
   - Or separate metric: "Cancelled: 48"

---

## ✅ Verification Checklist

After fix is applied:
- [ ] `calculate_project_progress()` counts `cancelled` tasks
- [ ] `check_and_update_project_completion()` checks `cancelled_tasks == 0`
- [ ] Dashboard shows correct active task count
- [ ] Projects with cancelled tasks are NOT marked as completed
- [ ] Projects with all tasks completed ARE marked as completed
- [ ] Logs show cancelled task counts
- [ ] Database queries include cancelled status filter

---

---

## ✅ Implementation Complete

**Status**: ✅ **FIXED**  
**Date Fixed**: November 27, 2025  
**Role**: QA_Engineer + Backend Developer

### **Changes Made**:

1. **`calculate_project_progress()`** (`agent_task_service.py`):
   - ✅ Added `cancelled_tasks` count to query
   - ✅ Added `quality_percentage` calculation: `(completed_tasks / total_tasks) * 100`
   - ✅ Returns `cancelled_tasks` and `quality_percentage` in response

2. **`check_and_update_project_completion()`** (`project_execution_service.py`):
   - ✅ Updated to check `cancelled_tasks == 0` (prevents completion if cancelled tasks exist)
   - ✅ Added quality threshold check: projects must have `quality_percentage >= 98.0` to be marked as completed
   - ✅ Projects with quality < 98% are marked as `failed` with clear error message
   - ✅ Added logging for cancelled tasks with reasons (samples first 10 cancelled tasks)

3. **`download_project()`** (`tenant_api.py`):
   - ✅ Added quality check before allowing download
   - ✅ Projects with quality < 98% cannot be downloaded
   - ✅ Returns clear error message explaining why download is blocked

4. **`cancel_task()`** (`agent_task_service.py`):
   - ✅ New helper function for cancelling tasks with reason tracking
   - ✅ Stores cancellation reason in `error_message` field for investigation

### **Quality Threshold Logic**:

- **Quality Calculation**: `quality = (completed_tasks / total_tasks) * 100`
- **Threshold**: Projects must achieve **≥98% quality** to be completed/downloadable
- **Cancelled Tasks**: Reduce quality (they're not completed)
- **Failed Tasks**: Also reduce quality (they're not completed)
- **Download Prevention**: Projects with quality < 98% cannot be downloaded (must restart/edit)

### **Cancellation Tracking**:

- Cancelled tasks store reason in `error_message` field
- Logs include sample of cancelled tasks with reasons for investigation
- Helps identify patterns: why are tasks being cancelled?

### **Testing Recommendations**:

1. **Test Quality Threshold**: Create project with 100 tasks, complete 97, cancel 3 → Should fail (97% < 98%)
2. **Test Cancellation Prevention**: Create project with cancelled tasks → Should NOT be marked as completed
3. **Test Download Block**: Try to download project with quality < 98% → Should be blocked
4. **Test Cancellation Logging**: Cancel tasks with reasons → Check logs for cancellation reasons

---

**Reported By**: QA_Engineer  
**Date**: November 27, 2025  
**Priority**: P0 - Critical  
**Status**: ✅ **FIXED**

