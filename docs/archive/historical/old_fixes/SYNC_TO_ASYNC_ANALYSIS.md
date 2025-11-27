# Sync to Async Operations Analysis

**Date:** November 26, 2025  
**Status:** ✅ **IMPLEMENTED** - See `docs/ASYNC_CONVERSION_IMPLEMENTATION.md` for details

## Executive Summary

This document identifies areas of the system where synchronous operations are being used when they should be asynchronous for optimal performance and scalability in the FastAPI-based SaaS platform.

## Critical Issues (High Priority)

### 1. HTTP Requests Using `requests` Library (CRITICAL)

**Location:** `agents/researcher_agent.py`, `utils/recursive_researcher.py`

**Problem:**
- Synchronous `requests.get()` calls block the event loop
- Multiple sequential HTTP requests cause significant delays
- Prevents concurrent request handling

**Current Code:**
```python
# agents/researcher_agent.py:271, 300
response = requests.get(url, params=params, timeout=10)
response = requests.get(url, headers=headers, params=params, timeout=10)

# utils/recursive_researcher.py:198
response = requests.get(url, timeout=self.request_timeout, headers={...})
```

**Recommended Fix:**
```python
# Use httpx for async HTTP requests
import httpx

async def _search_google_async(self, query: str, num_results: int) -> List[Dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # ... rest of logic
```

**Impact:** **HIGH** - HTTP requests are I/O-bound and should never block the event loop

**Files Affected:**
- `agents/researcher_agent.py` (lines 271, 300, 1254)
- `utils/recursive_researcher.py` (line 198)

---

### 2. `time.sleep()` in Async Contexts (MEDIUM-HIGH)

**Location:** `agents/researcher_agent.py`, `agents/base_agent.py`, `utils/retry.py`

**Problem:**
- `time.sleep()` blocks the entire event loop
- Prevents other async operations from running
- Causes unnecessary delays in concurrent operations

**Current Code:**
```python
# agents/researcher_agent.py:333
time.sleep(delay)

# agents/base_agent.py:272
time.sleep(delay)

# utils/retry.py:51
time.sleep(min(delay, max_delay))
```

**Recommended Fix:**
```python
# Use asyncio.sleep() in async functions
await asyncio.sleep(delay)
```

**Impact:** **MEDIUM-HIGH** - Blocks event loop, prevents concurrency

**Files Affected:**
- `agents/researcher_agent.py` (line 333) - In `_search_duckduckgo()` method
- `agents/base_agent.py` (line 272) - In retry logic
- `utils/retry.py` (line 51) - In retry decorator

**Note:** `utils/load_balancer.py:152` uses `time.sleep()` in a separate thread, which is acceptable.

---

### 3. Synchronous File I/O in Async Functions (MEDIUM)

**Location:** `addon_portal/api/services/project_execution_service.py`

**Problem:**
- File reads in async functions block the event loop
- Multiple file reads could be done concurrently

**Current Code:**
```python
# addon_portal/api/services/project_execution_service.py:335, 375
with open(stderr_log, 'r', encoding='utf-8', errors='ignore') as f:
    stderr_content = f.read()

with open(stdout_log, 'r', encoding='utf-8', errors='ignore') as f:
    stdout_content = f.read()
```

**Recommended Fix:**
```python
# Use aiofiles for async file I/O
import aiofiles

async with aiofiles.open(stderr_log, 'r', encoding='utf-8', errors='ignore') as f:
    stderr_content = await f.read()

async with aiofiles.open(stdout_log, 'r', encoding='utf-8', errors='ignore') as f:
    stdout_content = await f.read()
```

**Impact:** **MEDIUM** - File I/O is I/O-bound but typically fast; less critical than HTTP requests

**Files Affected:**
- `addon_portal/api/services/project_execution_service.py` (lines 335, 375)

**Note:** Agent file writes (in `agents/*.py`) are typically OK as sync since they run in subprocesses, not the FastAPI event loop.

---

## Lower Priority Issues

### 4. File I/O in Agent Code (LOW)

**Location:** Various agent files (`agents/coder_agent.py`, `agents/frontend_agent.py`, etc.)

**Status:** **ACCEPTABLE** - These operations run in subprocesses (`main.py`), not in the FastAPI event loop, so synchronous file I/O is acceptable here.

**Note:** If agents are ever refactored to run in the same event loop as FastAPI, these should be converted to async.

---

## Implementation Priority

### Phase 1: Critical (Do First)
1. ✅ **Convert HTTP requests to async** (`agents/researcher_agent.py`, `utils/recursive_researcher.py`)
   - Replace `requests` with `httpx.AsyncClient`
   - Update all `_search_*()` methods to be async
   - Update callers to use `await`

### Phase 2: High Priority
2. ✅ **Replace `time.sleep()` with `asyncio.sleep()`** in async contexts
   - `agents/researcher_agent.py:333`
   - `agents/base_agent.py:272`
   - `utils/retry.py:51` (if used in async context)

### Phase 3: Medium Priority
3. ✅ **Convert file I/O to async** in FastAPI services
   - `addon_portal/api/services/project_execution_service.py`
   - Use `aiofiles` library

---

## Dependencies Required

To implement these fixes, add to `requirements.txt`:
```txt
httpx>=0.25.0  # For async HTTP requests
aiofiles>=23.0.0  # For async file I/O
```

---

## Testing Considerations

1. **HTTP Requests:**
   - Test concurrent research operations
   - Verify rate limiting still works
   - Check error handling

2. **Sleep Operations:**
   - Verify retry logic still works correctly
   - Test exponential backoff timing

3. **File I/O:**
   - Test log reading in project execution service
   - Verify file encoding handling

---

## Notes

- **Agent Subprocesses:** Most agent code runs in subprocesses via `main.py`, so sync operations there are acceptable. Focus on FastAPI service code first.
- **Thread Safety:** The load balancer's `time.sleep()` in a separate thread is acceptable.
- **Database Operations:** Already migrated to async (see `docs/archive/historical/ASYNC_MIGRATION_COMPLETE.md`).

---

## Summary

**Total Issues Found:** 3 critical areas  
**High Priority:** 2 (HTTP requests, sleep in async)  
**Medium Priority:** 1 (file I/O in async)  
**Low Priority:** 0 (agent file I/O is acceptable)

**Status:** ✅ **IMPLEMENTED** - See `docs/ASYNC_CONVERSION_IMPLEMENTATION.md` for complete implementation details.

**Estimated Impact:**
- **Performance:** Significant improvement in concurrent request handling
- **Scalability:** Better resource utilization under load
- **User Experience:** Faster response times for research operations

---

## Implementation Status

✅ **All recommendations have been implemented.** See `docs/ASYNC_CONVERSION_IMPLEMENTATION.md` for:
- Complete implementation details
- Code examples and patterns
- Testing considerations
- Performance improvements
- Migration notes

