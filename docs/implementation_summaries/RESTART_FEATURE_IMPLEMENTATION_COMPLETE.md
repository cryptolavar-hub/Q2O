# Restart Feature & Failed Project Handling - Implementation Complete

## Date: November 21, 2025

## ✅ Implementation Summary

All requested features have been successfully implemented:

### 1. ✅ Failed Project Detection & Cleanup

**Backend Implementation:**
- **File:** `addon_portal/api/services/project_execution_service.py`
- **Function:** `cleanup_stuck_projects()`
- **Logic:**
  - Finds projects with `execution_status='running'` older than 24 hours (configurable via `PROJECT_EXECUTION_TIMEOUT_HOURS`)
  - Marks them as `failed` with appropriate error message
  - Sets `execution_completed_at` timestamp
  - Logs cleanup actions

**Scheduling:**
- **File:** `addon_portal/api/main.py`
- **Method:** FastAPI lifespan context manager
- **Frequency:** Runs every hour (NOT on startup as requested)
- **Implementation:** Background task using `asyncio.create_task()` with infinite loop

**Configuration:**
- Environment variable: `PROJECT_EXECUTION_TIMEOUT_HOURS` (default: 24 hours)

---

### 2. ✅ Restart Functionality (Failed Projects Only)

**Backend Implementation:**

1. **Service Function:**
   - **File:** `addon_portal/api/services/project_execution_service.py`
   - **Function:** `restart_project()`
   - **Validation:**
     - ✅ Only allows restart if `execution_status='failed'`
     - ✅ Validates activation code, subscription, required fields
     - ✅ Resets execution fields: `execution_status='pending'`, clears `execution_error`, resets timestamps
     - ✅ Reuses existing `execute_project()` logic

2. **API Endpoint:**
   - **File:** `addon_portal/api/routers/tenant_api.py`
   - **Endpoint:** `POST /api/tenant/projects/{project_id}/restart`
   - **Authentication:** Required (tenant session)
   - **Response:** Same format as `/run` endpoint

**Frontend Implementation:**

1. **API Client:**
   - **File:** `addon_portal/apps/tenant-portal/src/lib/projects.ts`
   - **Function:** `restartProject(projectId: string)`
   - **Error Handling:** Proper session expiration handling

2. **UI Components:**
   - **File:** `addon_portal/apps/tenant-portal/src/pages/projects/[id].tsx`
   - **Features:**
     - ✅ Restart button appears ONLY when `execution_status === 'failed'`
     - ✅ Run button hidden when project is failed (restart button shown instead)
     - ✅ Validation: `canRestartProject()` function
     - ✅ Loading state: `isRestarting`
     - ✅ Error handling and user feedback
     - ✅ Redirects to Status page after successful restart

---

## Key Features

### ✅ Failed Project Detection
- Projects stuck in "running" status for >24 hours are automatically marked as "failed"
- Cleanup runs every hour (not on startup)
- Prevents projects from staying in "running" status indefinitely

### ✅ Restart Functionality
- **Only failed projects** can be restarted (completed projects cannot be restarted)
- Restart button appears automatically when project status is "failed"
- Validates all requirements before restarting (activation code, subscription, fields)
- Resets execution state properly before restarting
- User-friendly error messages

### ✅ User Experience
- Clear visual distinction: Orange "🔄 RESTART PROJECT" button for failed projects
- Green "▶ RUN PROJECT" button for new/pending projects
- Loading states and error messages
- Automatic redirect to Status page after restart

---

## Files Modified

### Backend:
1. `addon_portal/api/services/project_execution_service.py`
   - Added `cleanup_stuck_projects()` function
   - Added `restart_project()` function
   - Added `PROJECT_EXECUTION_TIMEOUT_HOURS` configuration

2. `addon_portal/api/main.py`
   - Added lifespan context manager
   - Added `periodic_cleanup_task()` background task
   - Schedules cleanup to run every hour

3. `addon_portal/api/routers/tenant_api.py`
   - Added `restart_tenant_project()` endpoint
   - Imported `restart_project` service function

### Frontend:
1. `addon_portal/apps/tenant-portal/src/lib/projects.ts`
   - Added `restartProject()` API function

2. `addon_portal/apps/tenant-portal/src/pages/projects/[id].tsx`
   - Added `handleRestartProject()` handler
   - Added `canRestartProject()` validation function
   - Added restart button UI (only shows for failed projects)
   - Updated button logic to show restart OR run (not both)

---

## Testing Checklist

### Backend:
- [ ] Cleanup job runs every hour (check logs)
- [ ] Stuck projects (>24 hours) are marked as failed
- [ ] Restart endpoint validates failed status only
- [ ] Restart endpoint rejects completed projects
- [ ] Restart resets execution fields correctly
- [ ] Restart reuses execute_project logic

### Frontend:
- [ ] Restart button appears only for failed projects
- [ ] Run button hidden when project is failed
- [ ] Restart button validates requirements
- [ ] Loading state shows during restart
- [ ] Error messages display correctly
- [ ] Redirect to Status page works after restart

---

## Configuration

**Environment Variable:**
```bash
PROJECT_EXECUTION_TIMEOUT_HOURS=24  # Default: 24 hours
```

**To change timeout:**
Add to `.env` file:
```
PROJECT_EXECUTION_TIMEOUT_HOURS=48  # 48 hours instead of 24
```

---

## API Usage

### Restart a Failed Project:
```bash
POST /api/tenant/projects/{project_id}/restart
Headers:
  X-Session-Token: <session_token>

Response:
{
  "success": true,
  "message": "Project execution restarted successfully",
  "execution_id": 12345,
  "status": "running",
  "output_folder_path": "/path/to/output"
}
```

**Error Responses:**
- `400 Bad Request`: "Only failed projects can be restarted. Current status: completed"
- `404 Not Found`: "Project not found"
- `401 Unauthorized`: Session expired

---

## Next Steps

1. **Restart API Server** - Required for cleanup job to start
2. **Test Cleanup** - Wait 1 hour or manually trigger cleanup to verify stuck projects are detected
3. **Test Restart** - Create a failed project and verify restart button appears and works
4. **Monitor Logs** - Check for cleanup job execution every hour

---

## Notes

- Cleanup job starts 1 hour after server startup (not immediately)
- Projects must be stuck for >24 hours before being marked as failed
- Only projects with `execution_status='failed'` can be restarted
- Completed projects cannot be restarted (as requested)
- Restart button automatically replaces Run button for failed projects

