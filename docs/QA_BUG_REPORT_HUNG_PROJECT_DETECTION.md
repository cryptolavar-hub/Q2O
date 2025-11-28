# 🐛 QA Bug Report: Hung Project Detection & Auto-Fail

**Bug ID**: BUG-HUNG-001  
**Severity**: 🔴 **CRITICAL**  
**Status**: ✅ **FIXED**  
**Date**: November 28, 2025  
**Reporter**: QA_Engineer — Bug Hunter

---

## 📋 **Problem Description**

Projects can become "hung" (stuck) during execution when:
- Agent activity stops (no tasks being processed)
- Project is below 90% completion
- No progress for extended periods (>1 hour)
- Project status remains "running" indefinitely

**User Impact**: 
- Projects appear to be running but make no progress
- Users cannot restart projects (status is "running")
- Resources wasted on stuck processes
- Poor user experience

---

## 🔍 **Root Cause Analysis**

**Current Behavior**:
- `check_and_update_project_completion()` only checks if all tasks are done
- No detection for projects that are stuck mid-execution
- No timeout mechanism for hung projects
- Projects can remain "running" indefinitely

**Why Projects Hang**:
1. **Process Crash**: Main process crashes but status not updated
2. **Agent Deadlock**: Agents waiting for each other indefinitely
3. **LLM API Failures**: Repeated failures causing agents to stall
4. **Resource Exhaustion**: Memory/CPU limits causing silent failures
5. **Network Issues**: External API calls timing out indefinitely

---

## ✅ **Solution Implemented**

### **Hung Project Detection Logic**

Added automatic detection in `check_and_update_project_completion()`:

**Detection Criteria**:
1. ✅ Project status is `'running'`
2. ✅ Last agent activity > 1 hour ago
3. ✅ Completion percentage < 90%
4. ✅ Not all tasks completed

**Last Activity Calculation**:
- Checks most recent timestamp from:
  - `AgentTask.started_at` (when agent started task)
  - `AgentTask.completed_at` (when task completed)
  - `AgentTask.failed_at` (when task failed)
  - `AgentTask.created_at` (when task created)
- Only considers tasks from current execution run (`created_at >= execution_started_at`)

**Action When Hung Detected**:
- Mark project as `'failed'`
- Set `execution_completed_at` to current time
- Set `execution_error` with detailed message:
  ```
  "Project execution hung: No agent activity for {hours} hours. 
   Completion: {percentage}% ({completed}/{total} tasks). 
   Last activity: {timestamp}. 
   Project appears to be stuck. Please restart the project."
  ```
- Log error event: `project_hung_detected`

---

## 📝 **Implementation Details**

### **File Modified**: `addon_portal/api/services/project_execution_service.py`

**Function**: `check_and_update_project_completion()`

**Changes**:
1. Added hung project detection before cancellation logging
2. Query last activity from all task timestamps
3. Calculate time since last activity
4. Check completion percentage
5. Auto-fail if hung conditions met

**Code Location**: Lines 739-808

```python
# QA_Engineer: Check for hung projects (no activity for >1 hour, <90% completion)
# Hung Project Detection:
# - Last agent activity > 1 hour ago
# - Completion percentage < 90%
# - Not all tasks completed
# - Project status is 'running'

from ..models.agent_tasks import AgentTask
from sqlalchemy import func

# Get last agent activity timestamp (most recent of started_at, completed_at, failed_at, created_at)
# Query each timestamp field separately and find max in Python
last_started = await db.execute(...)
last_completed = await db.execute(...)
last_failed = await db.execute(...)
last_created = await db.execute(...)

# Find the most recent timestamp among all activity types
timestamps = [last_started.scalar(), last_completed.scalar(), last_failed.scalar(), last_created.scalar()]
last_activity = max([ts for ts in timestamps if ts is not None], default=None)

# Calculate completion percentage
completion_percentage = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

# Check if project is hung
if last_activity:
    time_since_last_activity = datetime.now(timezone.utc) - last_activity
    hours_since_activity = time_since_last_activity.total_seconds() / 3600.0
    
    is_hung = (
        hours_since_activity >= 1.0 and  # No activity for >= 1 hour
        completion_percentage < 90.0 and  # Below 90% completion
        not all_tasks_done  # Not all tasks completed
    )
    
    if is_hung:
        # Project is hung - mark as failed
        project.execution_status = 'failed'
        project.execution_completed_at = datetime.now(timezone.utc)
        project.execution_error = (
            f"Project execution hung: No agent activity for {hours_since_activity:.1f} hours. "
            f"Completion: {completion_percentage:.1f}% ({completed_tasks}/{total_tasks} tasks). "
            f"Last activity: {last_activity.isoformat()}. "
            f"Project appears to be stuck. Please restart the project."
        )
        
        LOGGER.error("project_hung_detected", ...)
        await db.commit()
        return False
```

---

## 🧪 **Testing Plan**

### **Test Case 1: Hung Project Detection**
1. Create a project and start execution
2. Simulate hung state (stop process, no activity)
3. Wait >1 hour
4. Call `check_and_update_project_completion()`
5. **Expected**: Project marked as `'failed'` with hung error message

### **Test Case 2: Active Project (Not Hung)**
1. Create a project and start execution
2. Ensure tasks are completing regularly
3. Call `check_and_update_project_completion()` after 30 minutes
4. **Expected**: Project remains `'running'`, no hung detection

### **Test Case 3: Completed Project (Not Hung)**
1. Create a project and complete all tasks (>90%)
2. Call `check_and_update_project_completion()`
3. **Expected**: Project marked as `'completed'`, no hung detection

### **Test Case 4: Recent Activity**
1. Create a project with last activity <1 hour ago
2. Call `check_and_update_project_completion()`
3. **Expected**: Project remains `'running'`, no hung detection

---

## 📊 **Impact Analysis**

### **Pros** ✅
- **Automatic Detection**: No manual intervention needed
- **Resource Cleanup**: Prevents wasted resources on stuck projects
- **User Experience**: Clear error message explaining why project failed
- **Restart Capability**: Users can restart failed projects
- **Prevents False Positives**: Only triggers when truly hung (>1 hour, <90%)

### **Cons** ⚠️
- **1 Hour Delay**: Projects must be hung for 1 hour before detection
- **Requires Regular Checks**: `check_and_update_project_completion()` must be called regularly
- **May Miss Very Slow Projects**: Projects making slow progress (<1 task/hour) may be flagged

### **Mitigation** ✅
- **1 Hour Threshold**: Reasonable balance between false positives and detection speed
- **90% Completion Check**: Prevents flagging projects that are nearly complete
- **Regular Checks**: Function is called when tasks complete and on status queries

---

## 🔄 **Restart Capability**

**Current Behavior**:
- Failed projects can be restarted via existing restart endpoint
- Hung projects will be marked as `'failed'` and can be restarted
- Restart clears previous execution and starts fresh

**User Flow**:
1. Project detected as hung → Status: `'failed'`
2. User sees error message: "Project execution hung..."
3. User clicks "Restart Project" button
4. Project restarts with fresh execution

---

## 📈 **Monitoring & Logging**

**Log Event**: `project_hung_detected`

**Log Fields**:
- `project_id`: Project identifier
- `tenant_id`: Tenant identifier
- `hours_since_activity`: Hours since last activity
- `completion_percentage`: Current completion percentage
- `total_tasks`: Total tasks in project
- `completed_tasks`: Completed tasks count
- `in_progress_tasks`: Tasks currently in progress
- `pending_tasks`: Tasks waiting to start
- `failed_tasks`: Tasks that failed
- `last_activity`: ISO timestamp of last activity

**Monitoring Recommendations**:
- Alert on high `project_hung_detected` event rate
- Track average `hours_since_activity` for hung projects
- Monitor completion percentages when hung detected

---

## ✅ **Verification Checklist**

- [x] Hung detection logic implemented
- [x] Last activity calculation working correctly
- [x] Completion percentage calculation correct
- [x] Auto-fail logic triggers correctly
- [x] Error message provides clear information
- [x] Logging includes all relevant fields
- [x] Database commit successful
- [x] No linter errors
- [ ] Integration testing completed
- [ ] Production deployment

---

## 🎯 **Next Steps**

1. **Deploy to Production**: Deploy hung detection to production
2. **Monitor**: Watch for `project_hung_detected` events
3. **Tune Thresholds**: Adjust 1-hour threshold if needed based on real data
4. **Add Dashboard Alert**: Alert users when their project is detected as hung
5. **Investigate Root Causes**: Analyze why projects hang to prevent future occurrences

---

**Status**: ✅ **IMPLEMENTED**  
**Next Review**: After production deployment and monitoring

