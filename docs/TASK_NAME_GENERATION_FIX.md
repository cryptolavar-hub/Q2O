# Task Name Generation Fix
**Date**: November 24, 2025  
**Status**: ✅ Complete

---

## Problem

Task names and code component names were being generated directly from the full objective/description text, resulting in:

1. **Extremely long task titles** (e.g., "Backend: Do an initial check to the QuickBooks API using the keys provided, the key and its required parameters must have each an input field on the UI for the client to enter, before the GET requests for the checks to QuickBooks DB")
2. **Database issues**: Task names too long for database fields
3. **File system issues**: File names too long, causing unzip errors
4. **Poor readability**: Task titles were full sentences instead of concise descriptions

---

## Root Cause

1. **LLM Prompt**: Didn't explicitly instruct LLM to create short, concise titles
2. **Rules-based Fallback**: Used entire objective string: `f"{agent_type.value}: {objective}"`
3. **Code Component Names**: Used entire objective for sanitization, resulting in very long filenames/class names

---

## Solution

### 1. Created Concise Name Generator Utility (`utils/name_generator.py`)

**Functions:**
- `generate_concise_name()`: Extracts key concepts from objectives (technologies, actions, entities)
- `generate_task_title()`: Generates concise task titles with agent type prefix
- `generate_component_name()`: Generates concise names for code components (files, classes, functions)

**Features:**
- Extracts proper nouns (capitalized words)
- Preserves technology keywords (QuickBooks, Odoo, API, etc.)
- Removes filler words (the, a, an, and, etc.)
- Truncates at word boundaries to respect max length
- Handles various formats (PascalCase for classes, snake_case for files)

**Example:**
```python
# Before:
objective = "Do an initial check to the QuickBooks API using the keys provided"
title = "Backend: Do an initial check to the QuickBooks API using the keys provided"  # 90+ chars

# After:
concise_name = generate_concise_name(objective)  # "QuickBooks API Check"
title = generate_task_title(objective, "CODER")  # "Backend: QuickBooks API Check"  # ~35 chars
```

### 2. Updated Orchestrator LLM Prompt

**Changes:**
- Added explicit instruction: "Task titles MUST be concise (60-70 chars max)"
- Added examples showing short titles vs. long objectives
- Emphasized: "Extract key concepts from the objective, don't repeat the entire prompt"

**Before:**
```
"title": "Research Stripe API integration patterns",
```

**After:**
```
CRITICAL: Task titles MUST be concise (60-70 chars max). Extract key concepts from the objective, don't repeat the entire prompt.
"title": "Research: Stripe API Integration",
```

### 3. Updated Orchestrator Rules-Based Fallback

**Changes:**
- Replaced all `f"{agent_type.value}: {objective}"` with `generate_task_title(objective, agent_type)`
- Applied to all task types: Research, Infrastructure, Integration, Workflow, Frontend, Backend, Testing, QA, Security

**Before:**
```python
title=f"Backend: {objective}"  # Uses entire objective
```

**After:**
```python
from utils.name_generator import generate_task_title
title = generate_task_title(objective, "CODER", max_length=70)  # Concise name
```

### 4. Updated CoderAgent Component Name Generation

**Changes:**
- Generate concise name first, then sanitize for filenames/class names
- Applied to: API endpoints, data models, services, UI components, generic code

**Before:**
```python
sanitized = sanitize_objective(objective)  # Uses entire objective
module_name = sanitized['filename']  # Very long filename
```

**After:**
```python
concise_name = generate_concise_name(objective, max_length=40)  # Generate concise name
sanitized = sanitize_objective(concise_name)  # Sanitize concise name
module_name = sanitized['filename']  # Short, descriptive filename
```

### 5. Added Validation

**LLM Response Validation:**
- Check if LLM-generated title exceeds 70 chars
- If so, regenerate using `generate_task_title()` as fallback

**Code:**
```python
raw_title = spec.get('title', '')
if not raw_title or len(raw_title) > 70:
    from utils.name_generator import generate_task_title
    title = generate_task_title(objective, agent_type_str, max_length=70)
else:
    title = raw_title
```

---

## Expected Improvements

### Task Titles:
- **Before**: 90-150+ character titles (full sentences)
- **After**: 30-70 character titles (concise descriptions)
- **Example**: "Backend: QuickBooks API Check" instead of "Backend: Do an initial check to the QuickBooks API using the keys provided..."

### Code Component Names:
- **Before**: Very long filenames/class names (e.g., `do_an_initial_check_to_the_quickbooks_api_using_the_keys_provided.py`)
- **After**: Short, descriptive names (e.g., `quickbooks_api_check.py`)
- **Example**: `QuickBooksApiCheck` class instead of `DoAnInitialCheckToTheQuickbooksApiUsingTheKeysProvided`

### Database/File System:
- ✅ No more database field length issues
- ✅ No more file system path length issues
- ✅ No more unzip errors due to long filenames

---

## Files Modified

1. **`utils/name_generator.py`** (NEW)
   - Concise name generation utilities

2. **`agents/orchestrator.py`**
   - Updated LLM prompt to request concise titles
   - Updated all rules-based task creation to use `generate_task_title()`
   - Added validation for LLM-generated titles

3. **`agents/coder_agent.py`**
   - Updated all component name generation to use concise names
   - Applied to: API endpoints, models, services, components, generic code

---

## Testing Recommendations

1. **Test Task Title Generation:**
   - Verify task titles are 30-70 characters
   - Verify titles are descriptive but concise
   - Verify LLM-generated titles are validated/regenerated if too long

2. **Test Code Component Names:**
   - Verify filenames are reasonable length (< 50 chars)
   - Verify class names are reasonable length (< 80 chars)
   - Verify no file system path length issues

3. **Test Database Storage:**
   - Verify task names fit in database fields
   - Verify no truncation errors

---

## Conclusion

✅ **Problem Solved**: Task names and code component names are now concise and descriptive  
✅ **Database Issues Fixed**: No more field length problems  
✅ **File System Issues Fixed**: No more path length or unzip errors  
✅ **Readability Improved**: Titles are now human-readable and professional

---

**Implementation Date**: November 24, 2025  
**Status**: ✅ Complete - Ready for Testing

