# Dashboard and Dual-Stack Fixes

## Issues Fixed

### 1. Dashboard API Import Error ✅
**Problem**: `ModuleNotFoundError: No module named 'api.dashboard.models'`

**Solution**: Created `api/dashboard/models.py` with Pydantic models:
- `DashboardStateModel` - Complete dashboard state
- `SystemMetricsModel` - System metrics
- `TaskStateModel` - Individual task state
- `AgentStateModel` - Individual agent state
- `ProjectModel` - Project information

**Files Changed**:
- `api/dashboard/models.py` (created)

### 2. Dual-Stack Support with Separate Subprocesses ✅
**Problem**: Licensing API was not running in dual-stack mode by default, and when enabled, both servers ran in the same process.

**Solution**: 
- Updated `addon_portal/start_api_windows.py` to run IPv4 and IPv6 servers in **separate subprocesses**
- Changed default behavior to **enable dual-stack by default** (`ENABLE_DUAL_STACK=true`)
- Each server (IPv4 and IPv6) now runs in its own subprocess for better isolation
- Output from both processes is labeled with `[IPv4]` and `[IPv6]` prefixes

**How It Works**:
1. Main script starts two separate `subprocess.Popen` processes
2. One process runs: `uvicorn api.main:app --host 0.0.0.0 --port 8080`
3. Other process runs: `uvicorn api.main:app --host :: --port 8080`
4. Both processes share the same FastAPI app but run independently
5. Output from both is captured and displayed with labels

**Files Changed**:
- `addon_portal/start_api_windows.py` (completely rewritten)

**Configuration**:
- Default: Dual-stack enabled (`ENABLE_DUAL_STACK=true`)
- To disable: Set `ENABLE_DUAL_STACK=false` in `.env` file

### 3. Missing Widget ⏳
**Status**: Pending user clarification

**Question**: Which widget is missing from the dashboard? The dashboard currently shows:
- 4 stat cards (Activation Codes, Authorized Devices, Tenants, Success Rate)
- 4 quick action cards
- Recent Activity feed
- Activation Trends chart
- Project/Device Distribution chart

Please specify which widget should be added or is missing.

## Testing

### Test Dashboard API
1. Start Dashboard API: `python -m uvicorn api.dashboard.main:app --host 0.0.0.0 --port 8000`
2. Verify no import errors
3. Check endpoints:
   - `GET /api/dashboard/status`
   - `GET /api/dashboard/metrics`
   - `GET /health`

### Test Dual-Stack Licensing API
1. Start Licensing API: `python addon_portal/start_api_windows.py`
2. Verify both servers start:
   - Look for `[IPv4] Starting server on 0.0.0.0:8080...`
   - Look for `[IPv6] Starting server on [::]:8080...`
3. Test IPv4: `curl http://127.0.0.1:8080/docs`
4. Test IPv6: `curl http://[::1]:8080/docs`
5. Check processes: `netstat -ano | findstr 8080` should show both IPv4 and IPv6 listeners

## Notes

- Dual-stack mode uses more resources (2 processes instead of 1) but provides better isolation
- Each subprocess has its own event loop and memory space
- If one server crashes, the other continues running
- Output is clearly labeled to distinguish between IPv4 and IPv6 logs

