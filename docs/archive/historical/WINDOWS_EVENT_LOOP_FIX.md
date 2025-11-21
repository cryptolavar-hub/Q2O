# Windows Event Loop Fix - November 19, 2025

## Problem

The Admin Dashboard was not loading data due to a Windows-specific event loop incompatibility:

```
psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.
Please use a compatible event loop, for instance by running 'asyncio.run(..., loop_factory=asyncio.SelectorEventLoop(selectors.SelectSelector()))'
```

## Root Cause

On Windows, Python defaults to `ProactorEventLoop`, but `psycopg` (the async PostgreSQL driver) requires `SelectorEventLoop`. The event loop policy must be set **BEFORE** uvicorn creates the event loop, which happens when uvicorn starts.

## Solution

Created a multi-layered fix:

### 1. Event Loop Fix Module (`addon_portal/api/_event_loop_fix.py`)
- Sets the event loop policy to `WindowsSelectorEventLoopPolicy` on Windows
- Imported at the very top of `main.py` before any other imports

### 2. Windows Startup Script (`addon_portal/start_api_windows.py`)
- Sets the event loop policy BEFORE importing uvicorn
- Wraps uvicorn startup to ensure correct policy
- Used by all automated startup scripts

### 3. Updated Startup Scripts
- `START_ALL_SERVICES.ps1` - Uses `start_api_windows.py`
- `RESTART_SERVICE.ps1` - Uses `start_api_windows.py`
- `MANAGE_SERVICES.ps1` - Uses `start_api_windows.py`

### 4. Batch File (`addon_portal/START_API.bat`)
- Simple batch file for manual API starts
- Uses the Windows startup script

## How to Start the API

### Option 1: Use the Batch File (Recommended)
```cmd
cd addon_portal
START_API.bat
```

### Option 2: Use the Python Script Directly
```cmd
cd addon_portal
python start_api_windows.py
```

### Option 3: Use Automated Scripts
```cmd
START_ALL.bat
```

## Verification

After starting the API, check the logs for:
```
✓ Windows event loop policy set to SelectorEventLoop
Starting Q2O Licensing API on 0.0.0.0:8080...
Using SelectorEventLoop for Windows compatibility
```

The Admin Dashboard should now load data correctly without the `ProactorEventLoop` error.

## Files Modified

1. `addon_portal/api/_event_loop_fix.py` (NEW)
2. `addon_portal/api/main.py` (Updated - imports fix module first)
3. `addon_portal/start_api_windows.py` (NEW)
4. `addon_portal/START_API.bat` (NEW)
5. `START_ALL_SERVICES.ps1` (Updated)
6. `RESTART_SERVICE.ps1` (Updated)
7. `MANAGE_SERVICES.ps1` (Updated)

## Important Notes

- **The API server MUST be restarted** for this fix to take effect
- The fix only applies to Windows systems
- All existing startup scripts have been updated to use the new wrapper
- Manual uvicorn commands should use `start_api_windows.py` instead of direct uvicorn calls

