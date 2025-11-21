# Restart Feature & Failed Project Handling - Scope Assessment

## Requirements

1. **Failed Project Detection**: Projects that ran but didn't complete successfully must be marked as "Failed" (not stay "Running")
2. **Restart Functionality**: Allow restarting failed projects

## Current State Analysis

### ✅ Already Implemented (from previous fixes):
- Process monitoring function `_monitor_process_completion()` that marks projects as "failed" when process exits with non-zero code
- Database fields: `execution_status`, `execution_error`, `execution_completed_at`
- API endpoint: `POST /api/tenant/projects/{project_id}/run`

### ❌ Missing/Incomplete:

1. **Stuck Projects Detection**:
   - Projects stuck in "running" status for too long (e.g., process crashed but monitoring didn't catch it)
   - Need periodic cleanup job to detect and mark stuck projects as failed

2. **Restart Endpoint**:
   - No API endpoint for restarting failed/completed projects
   - Need to validate restart eligibility
   - Need to reset execution fields before restarting

3. **Frontend UI**:
   - No restart button visible
   - Need to add restart button to project detail page or status page
   - Need to handle restart API call

## Scope of Work

### **Priority 1: Failed Project Detection (MEDIUM effort)**

**Backend Changes:**
1. **Add cleanup job** to detect stuck projects:
   - Check for projects with `execution_status='running'` and `execution_started_at` older than X hours (e.g., 24 hours)
   - Verify process is actually dead (check process ID)
   - Mark as failed with appropriate error message
   - **Files to modify:**
     - `addon_portal/api/services/project_execution_service.py` - Add `cleanup_stuck_projects()` function
     - `addon_portal/api/main.py` or startup script - Schedule periodic cleanup task

2. **Improve process monitoring**:
   - Handle edge cases where process monitoring fails
   - Add timeout handling for monitoring function
   - **Files to modify:**
     - `addon_portal/api/services/project_execution_service.py` - Enhance `_monitor_process_completion()`

**Estimated Effort:** 2-3 hours

---

### **Priority 2: Restart Functionality (MEDIUM effort)**

**Backend Changes:**
1. **Add restart endpoint**:
   - `POST /api/tenant/projects/{project_id}/restart`
   - Validate project status (must be "failed" or "completed")
   - Reset execution fields: `execution_status='pending'`, clear `execution_error`, reset timestamps
   - Call `execute_project()` to restart
   - **Files to modify:**
     - `addon_portal/api/routers/tenant_api.py` - Add restart endpoint (~50 lines)

2. **Add restart service function** (optional, for reusability):
   - `addon_portal/api/services/project_execution_service.py` - Add `restart_project()` function (~30 lines)

**Frontend Changes:**
1. **Add restart button**:
   - Show restart button when `execution_status === 'failed'` or `execution_status === 'completed'`
   - Add to project detail page or status page
   - Handle API call and show loading/error states
   - **Files to modify:**
     - `addon_portal/apps/tenant-portal/src/lib/projects.ts` - Add `restartProject()` function (~20 lines)
     - `addon_portal/apps/tenant-portal/src/pages/status.tsx` or project detail page - Add restart button UI (~30 lines)

**Estimated Effort:** 2-3 hours

---

## Total Estimated Effort

**Total: 4-6 hours** of development work

**Breakdown:**
- Backend: 3-4 hours
- Frontend: 1-2 hours
- Testing: 1 hour

## Implementation Plan

### Phase 1: Failed Project Detection (Can be done independently)
1. Add cleanup function for stuck projects
2. Schedule periodic cleanup (every hour or on startup)
3. Test with manually stuck projects

### Phase 2: Restart Functionality (Depends on Phase 1)
1. Add restart API endpoint
2. Add restart service function
3. Add frontend restart button
4. Test restart flow end-to-end

## Risk Assessment

**Low Risk:**
- Restart endpoint is straightforward (reuses existing `execute_project()`)
- Frontend changes are minimal (just add button and API call)

**Medium Risk:**
- Cleanup job needs to be careful not to mark legitimately long-running projects as failed
- Process detection on Windows may need additional testing

## Recommendations

1. **Start with Phase 1** (Failed Project Detection) - This ensures projects don't stay stuck in "running" status
2. **Then implement Phase 2** (Restart) - This provides the user-facing functionality
3. **Add configuration** for timeout duration (e.g., `PROJECT_EXECUTION_TIMEOUT_HOURS=24`)

## Questions to Consider

1. **Timeout Duration**: How long should a project run before being considered "stuck"? (Recommendation: 24 hours)
2. **Restart Eligibility**: Should users be able to restart "completed" projects, or only "failed" ones? (Recommendation: Both)
3. **Cleanup Frequency**: How often should the cleanup job run? (Recommendation: Every hour or on API server startup)
4. **UI Location**: Where should the restart button appear? (Recommendation: Project detail page AND status page)

## Next Steps

If you approve this scope, I will:
1. Implement Phase 1 (Failed Project Detection)
2. Implement Phase 2 (Restart Functionality)
3. Add appropriate tests and documentation

**Would you like me to proceed with the implementation?**

