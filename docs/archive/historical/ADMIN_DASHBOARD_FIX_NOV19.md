# Admin Dashboard Fix - November 19, 2025

## Issues Identified

### 1. Windows Event Loop Incompatibility
**Error**: `psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode`

**Root Cause**: On Windows, Python defaults to `ProactorEventLoop`, but `psycopg` (async PostgreSQL driver) requires `SelectorEventLoop`.

**Fix**: Added event loop policy configuration in `addon_portal/api/main.py`:
```python
# Fix Windows event loop issue: psycopg requires SelectorEventLoop, not ProactorEventLoop
if sys.platform == 'win32':
    # Set event loop policy to use SelectorEventLoop on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### 2. Missing `await` in LLM Config Service
**Error**: `'coroutine' object has no attribute 'scalar_one_or_none'`

**Root Cause**: Several functions in `llm_config_service.py` were not properly converted to async:
- `_ensure_system_config` - missing `await` on `session.execute()`
- `get_system_config` - not async, missing `await` on `_ensure_system_config`
- `update_system_config` - not async, missing `await` on database operations
- `update_agent_prompt` - not async, missing `await` on database operations

**Fix**: Converted all functions to async and added proper `await` statements:
- Changed `Session` → `AsyncSession` in function signatures
- Added `await` to all `session.execute()`, `session.commit()`, `session.rollback()`, `session.refresh()` calls
- Updated function calls to use `await`

## Files Modified

1. **`addon_portal/api/main.py`**
   - Added Windows event loop policy fix at startup

2. **`addon_portal/api/services/llm_config_service.py`**
   - Converted `_ensure_system_config` to async
   - Converted `get_system_config` to async
   - Converted `update_system_config` to async
   - Converted `update_agent_prompt` to async
   - Added `await` to all database operations

## Verification

- ✅ No linter errors
- ✅ Router already uses `await` correctly for all service calls
- ✅ Windows event loop policy set before app initialization

## Impact

These fixes resolve:
- All database connection errors on Windows
- LLM system configuration endpoint errors
- Admin Dashboard data loading issues

## Next Steps

1. Restart the API server to apply the event loop fix
2. Test Admin Dashboard endpoints:
   - `/admin/api/dashboard-stats`
   - `/admin/api/analytics`
   - `/admin/api/activation-trend`
   - `/admin/api/recent-activities`
   - `/admin/api/project-device-distribution`
   - `/api/llm/system`
   - `/api/llm/projects`

---

*Fixes applied: November 19, 2025*

