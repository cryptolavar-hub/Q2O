# LLM Dashboard & Project Status Issues
**Date**: November 25, 2025  
**Status**: Issues Identified

---

## 🔴 Issue 1: LLM Dashboard Shows Only Average Response Time

### Problem:
- Dashboard shows **0 calls, $0.00 cost** for all LLM providers
- Only **average response time (1.55s)** is displayed
- All other metrics are zero

### Root Cause:
The dashboard reads LLM metrics from `agent_tasks` table columns:
- `llm_calls_count`
- `llm_tokens_used`
- `llm_cost_usd`
- `actual_duration_seconds` (this one has data, hence 1.55s average)

**However**, agents are **NOT calling `update_task_llm_usage_in_db()`** to track LLM usage after making LLM calls.

### Evidence:
- Execution log shows tasks being created and completed
- No LLM usage tracking calls found in logs
- Tasks have `actual_duration_seconds` (from task completion tracking)
- But `llm_calls_count`, `llm_tokens_used`, `llm_cost_usd` are all NULL/0

### Fix Required:
Agents need to call `update_task_llm_usage_in_db()` after each LLM call:
1. **OrchestratorAgent** - Track LLM calls for task breakdown
2. **ResearcherAgent** - Track LLM calls for research
3. **CoderAgent** - Track LLM calls for code generation
4. **Other agents** - Track any LLM usage

**Location**: `agents/task_tracking.py` - `update_task_llm_usage_in_db()` function exists but is not being called.

---

## 🔴 Issue 2: Project Status Stuck in "Running"

### Problem:
- Project: `saas-platform-for-managing-remote-teams`
- **829 tasks completed, 100% completion**
- But `execution_status` is still **"running"** instead of **"completed"**

### Root Cause:
The subprocess monitoring (`_monitor_process_completion`) may not be detecting completion properly, OR the subprocess hasn't exited yet.

### Evidence from Logs:
```
2025-11-25 05:59:50 [INFO] project_execution_started
2025-11-25 05:59:51 [INFO] Project saas-platform-for-managing-remote-teams task stats: total=829, completed=829, failed=0, completion=100.0%
2025-11-25 05:59:51 [INFO] execution_status: running
```

### Possible Causes:
1. Subprocess is still running (checking for completion)
2. Monitoring function isn't detecting subprocess exit
3. Database update isn't happening when subprocess completes

### Fix Required:
Check `addon_portal/api/services/project_execution_service.py`:
- Verify `_monitor_process_completion` is running
- Verify it detects subprocess exit correctly
- Verify it updates `execution_status` to 'completed' when all tasks are done

---

## 📊 Summary

| Issue | Severity | Status | Fix Required |
|-------|----------|--------|--------------|
| LLM Usage Not Tracked | HIGH | Identified | Agents need to call `update_task_llm_usage_in_db()` |
| Project Status Stuck | MEDIUM | Identified | Verify subprocess monitoring |

---

## 🔧 Next Steps

1. **Fix LLM Usage Tracking**:
   - Update `OrchestratorAgent` to track LLM calls
   - Update `ResearcherAgent` to track LLM calls
   - Update `CoderAgent` to track LLM calls
   - Update other agents as needed

2. **Fix Project Status**:
   - Check subprocess monitoring logic
   - Verify database updates on completion
   - Test with a new project run

3. **Test**:
   - Run a new project
   - Verify LLM metrics appear in dashboard
   - Verify project status updates to "completed"

