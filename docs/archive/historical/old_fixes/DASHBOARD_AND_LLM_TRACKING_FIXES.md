# Dashboard & LLM Tracking Fixes
**Date**: November 25, 2025  
**Status**: FIXED ✅

---

## 🔴 Issue 1: Dashboard Showing Stale Task Data (FIXED)

### Problem:
- Dashboard showed **829 completed tasks** from a **previous failed run**
- Project was restarted after editing objectives
- New run was executing, but dashboard displayed old data

### Root Cause:
`calculate_project_progress()` was counting **ALL tasks** for the project, including tasks from previous runs before `execution_started_at`.

### Fix Applied:
1. **Updated `calculate_project_progress()`** in `addon_portal/api/services/agent_task_service.py`:
   - Added `execution_started_at` parameter
   - Filters tasks by `created_at >= execution_started_at` to only count current run

2. **Updated GraphQL resolver** in `addon_portal/api/graphql/resolvers.py`:
   - Passes `execution_started_at` from project to `calculate_project_progress()`

### Result:
- Dashboard now only shows tasks from the current run
- Previous runs' tasks are excluded from completion percentage
- Accurate progress tracking for restarted projects

---

## 🔴 Issue 2: LLM Usage Not Tracked (FIXED)

### Problem:
- Dashboard showed **0 LLM calls, $0.00 cost** for all providers
- Only average response time (1.55s) was displayed
- LLM usage was happening but not being tracked

### Root Cause:
Agents were making LLM calls but **NOT calling `update_task_llm_usage_in_db()`** to track usage.

### Fix Applied:
1. **Added `track_llm_usage()` helper method** to `BaseAgent`:
   - Takes `task` and `llm_response` as parameters
   - Extracts usage data (tokens, cost) from `LLMResponse.usage`
   - Calls `update_task_llm_usage_in_db()` to persist to database

2. **Updated `ResearcherAgent`**:
   - Calls `self.track_llm_usage(task, response)` after LLM research call
   - Tracks usage for main research calls (synthesis calls skipped as they don't have task context)

3. **Updated `OrchestratorAgent`**:
   - Added logging for LLM usage (orchestrator doesn't have a specific task, so full tracking deferred)

### Result:
- LLM calls are now tracked per task
- Dashboard will show:
  - Total LLM calls
  - Total cost
  - Tokens used
  - Provider breakdown
- Metrics aggregate from `agent_tasks` table

---

## 📊 Files Modified

1. **`addon_portal/api/services/agent_task_service.py`**:
   - `calculate_project_progress()` - Added `execution_started_at` filter

2. **`addon_portal/api/graphql/resolvers.py`**:
   - `project()` resolver - Passes `execution_started_at` to `calculate_project_progress()`

3. **`agents/base_agent.py`**:
   - Added `track_llm_usage()` helper method

4. **`agents/researcher_agent.py`**:
   - Added `self.track_llm_usage(task, response)` call after LLM research

5. **`agents/orchestrator.py`**:
   - Added LLM usage logging (full tracking deferred)

---

## ✅ Testing Required

1. **Dashboard Stale Data**:
   - Restart a project
   - Verify dashboard shows only tasks from current run
   - Verify completion percentage is accurate

2. **LLM Usage Tracking**:
   - Run a project that uses LLM (research, code generation)
   - Check dashboard LLM metrics
   - Verify calls, costs, and tokens are displayed
   - Verify provider breakdown shows correct data

---

## 📝 Notes

- **Synthesis calls**: `_synthesize_findings_with_llm()` doesn't have task context, so tracking is skipped for now
- **Orchestrator tracking**: Full tracking deferred as orchestrator doesn't have a specific task
- **Future enhancement**: Consider project-level LLM tracking for orchestrator and synthesis calls

