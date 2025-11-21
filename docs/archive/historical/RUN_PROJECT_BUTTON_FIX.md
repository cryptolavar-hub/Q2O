# RUN PROJECT Button Fix - November 19, 2025

## Problem

After assigning an activation code to a project, the "RUN PROJECT" button remained disabled (not clickable) even though:
- ✅ Activation code was successfully assigned
- ✅ Project had all required fields (Name, Description, Objectives)
- ✅ According to implementation plan, projects with activation codes should be runnable

## Root Cause

The `ProjectResponse` schema and `_serialize_project()` function were **not including** `activation_code_id` and `execution_status` in the API response. The frontend checks these fields to determine if the RUN PROJECT button should be enabled:

**Frontend Logic** (`addon_portal/apps/tenant-portal/src/pages/projects/[id].tsx`):
```typescript
const canRunProject = (): { canRun: boolean; reason?: string } => {
  if (!project) return { canRun: false, reason: 'Project not loaded' };
  if (!project.activation_code_id) return { canRun: false, reason: 'Activation code required' };
  if (!project.name || !project.description || !project.objectives) {
    return { canRun: false, reason: 'Name, Description, and Objectives are required' };
  }
  if (project.execution_status === 'running') {
    return { canRun: false, reason: 'Project is already running' };
  }
  return { canRun: true };
};
```

**Problem**: Even though the backend was setting `project.activation_code_id = code.id`, this field was not being serialized in the response, so the frontend always saw it as `undefined`.

## Solution

### 1. Added Fields to `ProjectResponse` Schema
**File**: `addon_portal/api/schemas/llm.py`

Added two optional fields to the `ProjectResponse` model:
```python
activation_code_id: Optional[int] = None  # ID of assigned activation code
execution_status: Optional[str] = None  # pending, running, completed, failed, paused
```

### 2. Updated `_serialize_project()` Function
**File**: `addon_portal/api/services/llm_config_service.py`

Updated the serialization function to include these fields:
```python
def _serialize_project(project: LLMProjectConfig) -> ProjectResponse:
    return ProjectResponse(
        # ... existing fields ...
        activation_code_id=project.activation_code_id,  # Include activation code ID
        execution_status=project.execution_status,  # Include execution status
    )
```

## Files Modified

1. **`addon_portal/api/schemas/llm.py`**:
   - Added `activation_code_id: Optional[int] = None` to `ProjectResponse`
   - Added `execution_status: Optional[str] = None` to `ProjectResponse`

2. **`addon_portal/api/services/llm_config_service.py`**:
   - Updated `_serialize_project()` to include `activation_code_id` and `execution_status`

## Testing

✅ App imports successfully  
✅ No linter errors  
⚠️ **Requires API restart** to take effect

## Expected Behavior After Fix

1. **After Assigning Activation Code**: 
   - Frontend receives `activation_code_id` in the project response
   - RUN PROJECT button becomes enabled (if other conditions are met)

2. **Button Enable Conditions**:
   - ✅ `activation_code_id` is present
   - ✅ `name`, `description`, and `objectives` are all present
   - ✅ `execution_status` is not `'running'`

3. **Button Disable Conditions**:
   - ❌ No activation code assigned
   - ❌ Missing required fields (name, description, objectives)
   - ❌ Project is already running

## Related Endpoints

- `POST /api/tenant/projects/{project_id}/assign-activation-code` - Assign code to project
- `GET /api/tenant/projects/{project_id}` - Get project details (now includes activation_code_id and execution_status)
- `POST /api/tenant/projects/{project_id}/run` - Run project execution

## Impact

- **Before**: RUN PROJECT button always disabled after assigning activation code
- **After**: RUN PROJECT button correctly enables when all conditions are met

## Related Issues

This fix complements the earlier activation code assignment fix:
- `ACTIVATION_CODE_ASSIGNMENT_FIX.md` - Fixed async operations and code normalization
- This fix ensures the assigned code is visible to the frontend

