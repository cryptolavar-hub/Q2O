# QA Bug Report: Status Page Search Not Finding Failed Projects

**Date**: November 29, 2025  
**Status**: ✅ **FIXED**  
**Severity**: Medium  
**Priority**: High

---

## Problem Description

**Issue**: Failed projects are not appearing in the search results on the Status page of the Tenant Dashboard.

**User Report**: 
> "I am not seeing the failed project in the search list. I can imagine that not all project would show here because the list can be very long. So the search should work in finding this project to see its status and other details."

---

## Root Cause Analysis

### Issue 1: Project Filtering Before Search

**Location**: `addon_portal/apps/tenant-portal/src/pages/status.tsx` (lines 116-119)

**Problem**: The Status page was filtering projects to only show "running" or "active" projects BEFORE the search could work:

```typescript
// OLD CODE (BROKEN):
const response = await listProjects(1, 100);
// Filter to only active/running projects
const activeProjects = response.items.filter(
  p => p.execution_status === 'running' || p.status === 'active'
);
setAvailableProjects(activeProjects);
```

**Impact**: 
- Failed projects were filtered out before being added to `availableProjects`
- Search only worked on `availableProjects`, so failed projects never appeared
- Users couldn't find failed projects to view their status/details

### Issue 2: Limited Search Scope

**Location**: `addon_portal/apps/tenant-portal/src/pages/status.tsx` (lines 350-352)

**Problem**: Search only checked `name` and `id` fields:

```typescript
// OLD CODE (LIMITED):
const filteredProjects = availableProjects.filter(p =>
  p.name.toLowerCase().includes(projectSearch.toLowerCase()) ||
  p.id.toLowerCase().includes(projectSearch.toLowerCase())
);
```

**Impact**:
- Search didn't check `client_name`, `description`, or other fields
- Backend search API (which searches comprehensively) wasn't being used

---

## Solution Implemented

### Fix 1: Load ALL Projects (Not Just Running)

**Change**: Removed the filter that excluded failed/completed projects:

```typescript
// NEW CODE (FIXED):
const response = await listProjects(1, 100);
// QA_Engineer: Include ALL projects (running, failed, completed, etc.) for search
// Default to showing running projects, but allow search to find any project
setAvailableProjects(response.items);

// Auto-select first RUNNING project if available (preference for active projects)
const runningProject = response.items.find(
  p => p.execution_status === 'running' || p.status === 'active'
);
setSelectedProjectId(runningProject?.id || response.items[0].id);
```

**Result**: All projects are now loaded and available for search.

### Fix 2: Enhanced Search with Backend API

**Change**: Added backend search API integration with debouncing:

```typescript
// NEW CODE (ENHANCED):
const [searchResults, setSearchResults] = useState<Project[]>([]);
const [isSearching, setIsSearching] = useState(false);

// Use backend search API when search query is 2+ characters
useEffect(() => {
  const performSearch = async () => {
    if (projectSearch.trim().length >= 2) {
      // Backend search searches: name, description, project_id, custom_instructions
      setIsSearching(true);
      try {
        const response = await listProjects(1, 100, projectSearch.trim());
        setSearchResults(response.items);
      } catch (err) {
        console.error('Search failed:', err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };
  
  // Debounce search to avoid too many API calls
  const timeoutId = setTimeout(performSearch, 300);
  return () => clearTimeout(timeoutId);
}, [projectSearch]);
```

**Result**: Search now uses comprehensive backend search API.

### Fix 3: Enhanced Frontend Filtering

**Change**: Expanded frontend search to include more fields:

```typescript
// NEW CODE (ENHANCED):
const filteredProjects = projectSearch.trim().length >= 2 && searchResults.length > 0
  ? searchResults  // Use backend search results (comprehensive)
  : projectSearch.trim().length > 0
  ? availableProjects.filter(p =>
      p.name?.toLowerCase().includes(projectSearch.toLowerCase()) ||
      p.id?.toLowerCase().includes(projectSearch.toLowerCase()) ||
      p.client_name?.toLowerCase().includes(projectSearch.toLowerCase()) ||
      p.description?.toLowerCase().includes(projectSearch.toLowerCase())
    )
  : availableProjects;  // Show all projects when no search
```

**Result**: Frontend search now checks `name`, `id`, `client_name`, and `description`.

### Fix 4: Status Color Coding

**Change**: Added color-coded status indicators in search results:

```typescript
// NEW CODE (ENHANCED):
const status = project.execution_status || project.status;
const statusColor = 
  status === 'failed' ? 'text-red-600' :
  status === 'completed' ? 'text-green-600' :
  status === 'running' ? 'text-blue-600' :
  status === 'paused' ? 'text-yellow-600' :
  'text-gray-600';

// Display status with color
<div className={`text-xs ${statusColor} mt-1 font-medium`}>
  Status: {status}
</div>
```

**Result**: Users can easily identify project status in search results.

---

## Testing Recommendations

### Test Case 1: Search for Failed Project
1. Create a project that fails
2. Go to Status page
3. Search for the failed project by name or ID
4. **Expected**: Failed project appears in search results with red "failed" status
5. **Expected**: Can select failed project to view its details

### Test Case 2: Search by Client Name
1. Create a project with a specific client_name
2. Go to Status page
3. Search for the project using client_name
4. **Expected**: Project appears in search results

### Test Case 3: Search by Description
1. Create a project with a specific description
2. Go to Status page
3. Search for keywords from the description
4. **Expected**: Project appears in search results

### Test Case 4: Backend Search API
1. Search for a project with 2+ characters
2. **Expected**: Backend search API is called (check network tab)
3. **Expected**: Results include projects matching name, description, project_id, or custom_instructions

### Test Case 5: Status Colors
1. Search for projects with different statuses
2. **Expected**: 
   - Failed projects show red status
   - Completed projects show green status
   - Running projects show blue status
   - Paused projects show yellow status

---

## Files Modified

1. **`addon_portal/apps/tenant-portal/src/pages/status.tsx`**
   - Removed filter that excluded failed/completed projects
   - Added backend search API integration
   - Enhanced frontend search to include more fields
   - Added status color coding in search results
   - Added loading state for search

---

## Impact Assessment

### Before Fix
- ❌ Failed projects not searchable
- ❌ Limited search scope (only name/id)
- ❌ No backend search API usage
- ❌ No status color coding

### After Fix
- ✅ All projects searchable (including failed/completed)
- ✅ Comprehensive search (name, id, client_name, description, custom_instructions)
- ✅ Backend search API integration
- ✅ Status color coding for easy identification
- ✅ Debounced search to reduce API calls

---

## Additional Improvements

1. **Debouncing**: Search is debounced (300ms) to avoid excessive API calls
2. **Loading State**: Shows "Searching..." indicator during backend search
3. **Fallback**: Frontend filtering works if backend search fails
4. **Status Visibility**: Color-coded status makes it easy to identify project state

---

**Bug Fixed By**: QA Engineer (Terminator Bug Killer)  
**Fix Date**: November 29, 2025  
**Status**: ✅ **READY FOR TESTING**

