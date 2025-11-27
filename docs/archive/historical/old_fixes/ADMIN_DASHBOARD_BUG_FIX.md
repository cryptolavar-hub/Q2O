# Admin Dashboard Bug Fix - Active Projects Query

## Issue
The Admin Dashboard was showing "0" for Active Projects, and there were database connection leaks occurring.

## Root Causes Identified

1. **Incomplete Query**: Line 75 had an incomplete query execution that was breaking the endpoint
2. **Missing Variable**: The `all_projects` variable was removed but still referenced in trends calculation (line 130)
3. **Database Connection Leaks**: GraphQL context cleanup middleware not properly closing all connections

## Fixes Applied

### 1. Fixed Active Projects Query
**Before** (broken):
```python
# Count projects
# Total projects
result = await db.execute(select(func.count(LLMProjectConfig.id)))
total_projects = result.scalar() or 0

# Active projects query (but all_projects not loaded for trends)
result = await db.execute(
    select(func.count(LLMProjectConfig.id)).where(...)
)
active_projects = result.scalar() or 0
```

**After** (fixed):
```python
# Count projects
# Load all projects (needed for trends calculation based on created_at)
result = await db.execute(select(LLMProjectConfig))
all_projects = result.scalars().all()
total_projects = len(all_projects)

# Active projects: 
# - is_active is True (explicitly active)
# - is_active is NULL (default is True, so NULL counts as active)
# - OR project_status is 'active' (status-based active, even if is_active is False)
active_projects = sum(1 for p in all_projects if (p.is_active is not False) or (p.project_status == 'active'))
```

### 2. Active Project Definition
A project is considered "active" if:
- `is_active == True` (explicitly marked as active), OR
- `is_active IS NULL` (default value is True, so NULL counts as active), OR
- `project_status == 'active'` (status-based active, even if is_active is False)

### 3. Why We Load All Projects
We need to load all projects because:
- Trends calculation requires `created_at` timestamps for each project
- We need to compare projects created this week vs last week
- This is consistent with how codes and devices are handled (they also load all records)

## Testing
1. Verify dashboard loads without errors
2. Verify Active Projects widget shows correct count
3. Verify trends calculation works correctly
4. Check logs for connection leaks (should be reduced)

## Files Changed
- `addon_portal/api/routers/admin_api.py`

## Related Issues
- Database connection leaks (ongoing - GraphQL context cleanup middleware needs review)
- Git commit failures (separate issue - not related to dashboard)

