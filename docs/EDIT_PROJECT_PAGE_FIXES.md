# Edit Project Page Fixes

**Date:** November 26, 2025  
**Status:** ✅ COMPLETED  
**Priority:** HIGH

## Problems Identified

1. **GraphQL Resolver Error**: `AttributeError: 'AgentTask' object has no attribute 'updated_at'`
   - The resolver was trying to access `task.updated_at` but `AgentTask` model only has `created_at`, `started_at`, `completed_at`, and `failed_at`
   - This was causing GraphQL queries to fail, potentially affecting the edit page

2. **"Project not found" Error on Edit Page**
   - The edit page was showing "Project not found" error even when project data was loaded
   - Form fields were populated with project data, but the error message was still displayed
   - This suggested a state management issue where error state wasn't being cleared properly

3. **Project Name Display Issue**
   - User reported that project name wasn't showing as when created
   - The project name field showed "CMS SOLUTIONS" but the URL had `nextjs-cms-website-and-backend`
   - This is actually correct behavior: `client_name` (display name) vs `project_id` (slug identifier)

## Solutions Implemented

### 1. Fixed GraphQL Resolver - AgentTask.updated_at Error

**File:** `addon_portal/api/graphql/resolvers.py`

**Problem:**
```python
# Line 427 - ERROR: AgentTask doesn't have updated_at
if task.updated_at:
    if not agent_task_counts[agent_type]["last_activity"] or task.updated_at > agent_task_counts[agent_type]["last_activity"]:
        agent_task_counts[agent_type]["last_activity"] = task.updated_at
```

**Solution:**
```python
# Track last activity (most recent task update)
# AgentTask doesn't have updated_at, use completed_at, started_at, or created_at
last_activity = None
if task.completed_at:
    last_activity = task.completed_at
elif task.started_at:
    last_activity = task.started_at
elif task.created_at:
    last_activity = task.created_at

if last_activity:
    if not agent_task_counts[agent_type]["last_activity"] or last_activity > agent_task_counts[agent_type]["last_activity"]:
        agent_task_counts[agent_type]["last_activity"] = last_activity
```

**Impact:**
- ✅ GraphQL queries now work correctly
- ✅ Agent activity tracking uses correct timestamp fields
- ✅ No more AttributeError exceptions

### 2. Improved Edit Page Error Handling

**File:** `addon_portal/apps/tenant-portal/src/pages/projects/edit/[id].tsx`

**Changes:**
1. **Clear project state before fetching**: `setProject(null)` at start of fetch
2. **Clear form data on error**: Reset form data when fetch fails
3. **Clear error on success**: `setError(null)` after successful fetch
4. **Better error message**: Added helpful text suggesting session refresh

**Before:**
```typescript
const fetchProject = async (projectId: string) => {
  try {
    setLoading(true);
    setError(null);
    const data = await getProject(projectId);
    setProject(data);
    setFormData({...});
  } catch (err) {
    setError(errorMessage);
    // Project state and formData not cleared
  }
};
```

**After:**
```typescript
const fetchProject = async (projectId: string) => {
  try {
    setLoading(true);
    setError(null);
    setProject(null);  // Clear project state before fetching
    const data = await getProject(projectId);
    setProject(data);
    setFormData({...});
    setError(null);  // Clear any previous errors on success
  } catch (err) {
    setError(errorMessage);
    setProject(null);  // Clear project state on error
    setFormData({  // Clear form data on error
      name: '',
      client_name: '',
      description: '',
      objectives: '',
      status: 'pending',
    });
  }
};
```

**Impact:**
- ✅ No more stale data when errors occur
- ✅ Clear error state management
- ✅ Better user experience with helpful error messages

### 3. Project Name vs Project ID Clarification

**Understanding:**
- **`project_id`**: Unique identifier (slug), e.g., `nextjs-cms-website-and-backend`
- **`client_name`**: Display name, e.g., `CMS SOLUTIONS`
- **Frontend `name` field**: Mapped from `client_name` (line 151 in `projects.ts`)

**This is correct behavior:**
- The URL uses `project_id` (slug) for routing
- The form displays `client_name` (display name) in the "Project Name" field
- Both are correct - they serve different purposes

## Files Modified

1. `addon_portal/api/graphql/resolvers.py`
   - Fixed `AgentTask.updated_at` AttributeError
   - Use `completed_at`, `started_at`, or `created_at` for last activity tracking

2. `addon_portal/apps/tenant-portal/src/pages/projects/edit/[id].tsx`
   - Improved error handling and state management
   - Clear project and form data on error
   - Clear error on success
   - Better error messages

3. `addon_portal/api/services/llm_config_service.py`
   - Fixed SQLAlchemy async error in `update_project`
   - Added eager loading of `tenant` relationship to prevent lazy load errors

## Testing

### Test Case 1: GraphQL Resolver
```python
# Should not raise AttributeError
project = await project_resolver(id="test-project")
# Should successfully track agent last_activity using completed_at/started_at/created_at
```

### Test Case 2: Edit Page Error Handling
```typescript
// Test 1: Successful load
// - Project state should be set
// - Form data should be populated
// - Error should be null

// Test 2: Failed load (404)
// - Project state should be null
// - Form data should be empty
// - Error should be set with message

// Test 3: Session expired
// - Should logout user
// - Should clear all state
```

### Test Case 3: Project Name Display
```typescript
// Verify that:
// - URL uses project_id (slug): /projects/edit/nextjs-cms-website-and-backend
// - Form field shows client_name: "CMS SOLUTIONS"
// - Both are correct and serve different purposes
```

## Related Issues

- **GraphQL Connection Leak**: The connection leak warnings in logs are separate issues that were previously addressed but may need further investigation
- **Tenant Scoping**: The API endpoint correctly scopes projects by `tenant_id`, ensuring tenants can only access their own projects

### 4. Fixed SQLAlchemy Async Error in Update Project

**File:** `addon_portal/api/services/llm_config_service.py`

**Problem:**
```
greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?
```

**Root Cause:**
- The `update_project` function was not eagerly loading the `tenant` relationship
- When `_serialize_project` accessed `project.tenant.name` and `project.tenant.slug`, it triggered a lazy load
- Lazy loading in async SQLAlchemy requires `greenlet_spawn`, which wasn't available in this context

**Solution:**
```python
# BEFORE (missing tenant eager load):
stmt = (
    select(LLMProjectConfig)
    .options(selectinload(LLMProjectConfig.agent_configs))
    .where(LLMProjectConfig.project_id == project_id)
)

# AFTER (with tenant eager load):
stmt = (
    select(LLMProjectConfig)
    .options(selectinload(LLMProjectConfig.agent_configs))
    .options(selectinload(LLMProjectConfig.tenant))  # Eagerly load tenant for serialization
    .where(LLMProjectConfig.project_id == project_id)
)
```

**Impact:**
- ✅ No more "greenlet_spawn" errors when updating projects
- ✅ Tenant information is properly loaded before serialization
- ✅ Consistent with `get_project` function (which already had this fix)

## Notes

- The `AgentTask` model structure:
  - `created_at`: When task was created
  - `started_at`: When agent started working (nullable)
  - `completed_at`: When task was completed (nullable)
  - `failed_at`: When task failed (nullable)
  - **No `updated_at` field** - this was the source of the error

- The edit page now properly handles:
  - Loading states
  - Error states
  - Success states
  - State cleanup on errors

