# Active Projects Widget Data Fix

## Issue
The "Active Projects" widget was showing "0" when there should be project data displayed.

## Root Cause
The query was using `is_active == True` which:
1. Excludes projects where `is_active` is NULL (even though default is True)
2. Loads all projects into memory instead of using efficient SQL counting
3. Doesn't account for projects with `project_status == 'active'` as a fallback

## Solution

### Changed Query Logic
**Before**:
```python
result = await db.execute(select(LLMProjectConfig))
all_projects = result.scalars().all()
total_projects = len(all_projects)
active_projects = sum(1 for p in all_projects if p.is_active == True)
```

**After**:
```python
# Total projects - efficient SQL count
result = await db.execute(select(func.count(LLMProjectConfig.id)))
total_projects = result.scalar() or 0

# Active projects - efficient SQL query with proper NULL handling
result = await db.execute(
    select(func.count(LLMProjectConfig.id)).where(
        or_(
            LLMProjectConfig.is_active == True,
            LLMProjectConfig.is_active.is_(None),  # NULL counts as active (default)
            LLMProjectConfig.project_status == 'active'  # Status-based active
        )
    )
)
active_projects = result.scalar() or 0
```

### Improvements
1. **Efficient SQL Counting**: Uses `func.count()` instead of loading all projects
2. **NULL Handling**: Properly handles `is_active` being NULL (default is True)
3. **Status Fallback**: Includes projects with `project_status == 'active'` as active
4. **Performance**: Database-level counting instead of Python-level filtering

## Active Project Definition
A project is considered "active" if:
- `is_active == True` (explicitly marked as active), OR
- `is_active IS NULL` (default value is True, so NULL counts as active), OR
- `project_status == 'active'` (status-based active, even if is_active is False)

## Testing
1. Verify widget shows correct count
2. Test with projects where `is_active` is NULL
3. Test with projects where `is_active` is False but `project_status` is 'active'
4. Verify performance improvement (no loading all projects)

## Files Changed
- `addon_portal/api/routers/admin_api.py`

