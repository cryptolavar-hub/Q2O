# Agent Execution Issues - Deep Dive Diagnosis

**Date:** November 22, 2025  
**Status:** CRITICAL - Agents Not Completing Projects

## Executive Summary

After deep analysis of logs, database records, and code, I've identified **5 critical issues** preventing agents from successfully completing projects:

1. **Database Connection Leaks** (CRITICAL)
2. **LLM Service Failures** (CRITICAL)  
3. **Unicode Encoding Errors** (HIGH)
4. **Coder Agents Not Getting Tasks** (CRITICAL)
5. **Async/Await Issues** (MEDIUM)

---

## Issue #1: Database Connection Leaks (CRITICAL)

### Problem
- **Symptom:** Logs show hundreds of `SAWarning: The garbage collector is trying to clean up non-checked-in connection` errors
- **Root Cause:** Database sessions in `agents/task_tracking.py` are never closed after use
- **Impact:** Connection pool exhaustion, agents failing silently, database becoming unresponsive

### Evidence
```
<sys>:0: SAWarning: The garbage collector is trying to clean up non-checked-in connection 
<AdaptedConnection <psycopg.AsyncConnection [INTRANS] ...>
```

### Fix Applied
✅ Modified `create_task_in_db()`, `update_task_status_in_db()`, and `update_task_llm_usage_in_db()` to properly close database sessions using `try/finally` blocks.

---

## Issue #2: LLM Service Failures (CRITICAL)

### Problem
- **Symptom:** Logs show `[ERROR] All providers failed after 9 attempts`
- **Root Cause:** No LLM API keys configured (`GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` all NOT SET)
- **Impact:** 
  - Coder agents can't generate code (falling back to templates)
  - Researcher agents can't synthesize findings
  - Orchestrator can't use LLM for intelligent task breakdown

### Evidence
```
GOOGLE_API_KEY: NOT SET
OPENAI_API_KEY: NOT SET
ANTHROPIC_API_KEY: NOT SET
```

### Required Action
⚠️ **USER MUST CONFIGURE:** Add at least one LLM API key to `.env` file:
- `GOOGLE_API_KEY=your_key_here` (for Gemini)
- `OPENAI_API_KEY=your_key_here` (for GPT-4)
- `ANTHROPIC_API_KEY=your_key_here` (for Claude)

---

## Issue #3: Unicode Encoding Errors (HIGH)

### Problem
- **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4c1'`
- **Root Cause:** Emoji characters (✅, ❌, ⚠️, ℹ️, 📁) in log messages can't be encoded in Windows cp1252
- **Impact:** Logging failures, potential crashes, missing error messages

### Fix Applied
✅ Replaced all emoji characters with ASCII-safe alternatives:
- ✅ → `[OK]`
- ❌ → `[ERROR]`
- ⚠️ → `[WARN]`
- ℹ️ → `[INFO]`
- 📁 → Removed (plain text)

**Files Fixed:**
- `agents/researcher_agent.py`
- `agents/coder_agent.py`
- `agents/orchestrator.py`
- `agents/mobile_agent.py`
- `utils/llm_service.py`

---

## Issue #4: Coder Agents Not Getting Tasks (CRITICAL)

### Problem
- **Symptom:** Logs show `coders: coder_main - Active: 0, Completed: 0, Failed: 0`
- **Root Cause Analysis:**
  1. Orchestrator only creates coder tasks if objective_type is `["api", "backend", "service", "model"]` OR if no other tasks were created
  2. For objectives like "QuickBooks migration" or "Odoo integration", objective_type is detected as "integration", so NO coder task is created
  3. Integration agents create integration code, but coder agents never get backend/service tasks

### Evidence from Logs
```
coders: coder_main
  Active: 0, Completed: 0, Failed: 0
coders: coder_backup
  Active: 0, Completed: 0, Failed: 0
```

But other agents ARE working:
```
integration: integration_main
  Active: 0, Completed: 2, Failed: 0
researcher: researcher_main
  Active: 0, Completed: 3, Failed: 0
```

### Required Fix
⚠️ **NEEDS CODE CHANGE:** Orchestrator logic needs to ensure coder tasks are created for ALL objectives that require code generation, not just "api/backend/service/model" types.

---

## Issue #5: Async/Await Issues (MEDIUM)

### Problem
- **Symptom:** `RuntimeWarning: coroutine 'EventManager.emit_task_update' was never awaited`
- **Root Cause:** `asyncio.create_task()` is being called from sync code without proper event loop handling
- **Impact:** Dashboard events not being emitted, potential memory leaks

### Evidence
```
C:\Q2O_Combined\agents\base_agent.py:334: RuntimeWarning: coroutine 'EventManager.emit_task_update' was never awaited
```

### Required Fix
⚠️ **NEEDS CODE CHANGE:** Fix async event emission in `base_agent.py` to properly handle event loops.

---

## Summary of Fixes Applied

✅ **Fixed:**
1. Database connection leaks in `agents/task_tracking.py`
2. Unicode encoding errors (all emojis replaced with ASCII)

⚠️ **Requires User Action:**
1. Configure LLM API keys in `.env` file

⚠️ **Requires Code Changes:**
1. Fix orchestrator to always create coder tasks when code generation is needed
2. Fix async event emission in base_agent.py

---

## Next Steps

1. **IMMEDIATE:** User must add LLM API keys to `.env`
2. **URGENT:** Fix orchestrator task creation logic for coder agents
3. **HIGH:** Fix async event emission warnings
4. **TEST:** Run a project and verify:
   - Database connections are properly closed
   - Coder agents receive and process tasks
   - Code files are actually created in output folders
   - No Unicode encoding errors in logs

---

## Files Modified

1. `agents/task_tracking.py` - Added proper session closing
2. `agents/researcher_agent.py` - Fixed Unicode emojis
3. `agents/coder_agent.py` - Fixed Unicode emojis
4. `agents/orchestrator.py` - Fixed Unicode emojis
5. `agents/mobile_agent.py` - Fixed Unicode emojis (if exists)
6. `utils/llm_service.py` - Fixed Unicode emojis

---

## Testing Recommendations

1. Add LLM API key to `.env`
2. Run a simple project: `python main.py --project "Test API" --objective "Create a simple REST endpoint"`
3. Check logs for:
   - No database connection warnings
   - No Unicode encoding errors
   - Coder agents receiving tasks
   - Code files being created
4. Check database `agent_tasks` table for task records
5. Check output folder for generated code files

