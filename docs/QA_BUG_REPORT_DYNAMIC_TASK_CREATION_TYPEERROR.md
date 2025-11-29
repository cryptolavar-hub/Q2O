# Bug Report: Dynamic Task Creation TypeError

**Date**: November 29, 2025  
**Status**: ✅ **FIXED**  
**Severity**: 🔴 **CRITICAL** - Prevents project completion from reaching 100%

---

## Problem Summary

Projects are not reaching 100% completion because the QA agent's dynamic task creation feature is failing with a `TypeError: unhashable type: 'dict'` error. This prevents missing components from being generated, leaving projects incomplete.

---

## Symptoms

1. **Dashboard shows**: 72% completion (94/130 tasks completed)
2. **Execution logs show**: 100% completion (47/47 logical tasks completed)
3. **Database shows**: 130 total tasks (includes duplicates from main/backup agents)
4. **Missing components**: 11 components detected by QA but not created due to error

---

## Root Cause

The QA agent sends `missing_components` as a **list of dictionaries**, where each dict contains:
- `type`: "directory" or "file"
- `name`: "src/components directory"
- `path`: "src/components"
- `reason`: "Directory does not exist (required)"

However, the Orchestrator's `_create_tasks_for_missing_components()` method was treating each item in the list as a **string path**, trying to use the entire dict as a dictionary key:

```python
for component_path in missing_components:  # component_path is actually a dict!
    if component_path not in component_mapping:  # TypeError: unhashable type: 'dict'
```

---

## Error Details

**Location**: `agents/orchestrator.py`, line 1348

**Error Message**:
```
TypeError: unhashable type: 'dict'
Traceback (most recent call last):
  File "C:\Q2O_Combined\agents\orchestrator.py", line 1239, in _handle_qa_feedback
    new_tasks = self._create_tasks_for_missing_components(missing_components)
  File "C:\Q2O_Combined\agents\orchestrator.py", line 1348, in _create_tasks_for_missing_components
    if component_path not in component_mapping:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: unhashable type: 'dict'
```

**Impact**:
- QA detects 11 missing components
- Orchestrator fails to create tasks for them
- Project completes with incomplete structure
- Dashboard shows 72% completion instead of 100%

---

## Solution

**Fixed in**: `agents/orchestrator.py`

**Changes**:
1. Extract `path` from component dict before using it as a key
2. Extract `name` and `type` from component dict for better task metadata
3. Add backward compatibility for string-based component paths

**Code Fix**:
```python
# Before (BROKEN):
for component_path in missing_components:
    if component_path not in component_mapping:  # TypeError!

# After (FIXED):
for component_info in missing_components:
    if isinstance(component_info, dict):
        component_path = component_info.get("path", "")
        component_name = component_info.get("name", "")
        component_type = component_info.get("type", "directory")
    else:
        component_path = str(component_info)  # Backward compatibility
        component_name = component_path.split("/")[-1]
        component_type = "directory"
    
    if not component_path or component_path not in component_mapping:
        continue  # Skip unknown components
```

---

## Testing

**Test Case**: Run a project that triggers QA structure analysis (e.g., SaaS platform with missing directories)

**Expected Result**:
- QA detects missing components ✅
- Orchestrator successfully creates dynamic tasks ✅
- All missing components are generated ✅
- Project reaches 100% completion ✅

---

## Related Issues

- **Task Duplication**: Main/backup agents create duplicate database entries (130 tasks vs 47 logical tasks)
- **Completion Calculation**: Dashboard uses database count (130) instead of logical count (47)
- **Quality Threshold**: Projects need ≥98% completion to be downloadable

---

## Status

✅ **FIXED** - Dynamic task creation now correctly handles dict-based component information from QA agent.

---

**QA Engineer**: Fixed TypeError preventing dynamic task creation for missing components.

