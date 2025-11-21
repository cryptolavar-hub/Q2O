# Activation Code Assignment Fix - November 19, 2025

## Problem

When assigning an activation code to a project in the Tenant Portal, the system was returning:
- **Error**: "Invalid activation code." (HTTP 400)
- **Issue**: Code exists and is active in Admin Portal, but assignment fails

## Root Causes

### 1. Missing `await` on Async Operations
**Location**: `addon_portal/api/routers/tenant_api.py` lines 528-529, 541

**Issue**: 
- `db.commit()` and `db.refresh(project)` were called synchronously
- `get_project()` was called without `await`

**Fix**: Added `await` to all async operations:
```python
# Before
db.commit()
db.refresh(project)
return get_project(...)

# After
await db.commit()
await db.refresh(project)
return await get_project(...)
```

### 2. Code Format Normalization
**Location**: `addon_portal/api/routers/tenant_api.py` line 493

**Issue**: Activation codes might be entered with different formatting (case, spaces) than stored, causing hash mismatch.

**Fix**: Added code normalization before hashing:
```python
# Normalize code: uppercase, remove spaces, keep dashes
normalized_code = payload.activation_code.upper().strip().replace(" ", "")
code_hash = _hash_code(normalized_code)
```

### 3. Enhanced Error Logging
Added warning log when code is not found to help debug tenant_id mismatches:
```python
LOGGER.warning(
    "activation_code_not_found",
    extra={
        "tenant_id": tenant_info["tenant_id"],
        "code_provided": payload.activation_code,
        "normalized_code": normalized_code,
    }
)
```

## Files Modified

1. **`addon_portal/api/routers/tenant_api.py`**:
   - Fixed async operations (lines 528-529, 541)
   - Added code normalization (line 494)
   - Added error logging (lines 502-510)

## Testing

✅ Code compiles successfully  
⚠️ **Requires API restart** to take effect

## Expected Behavior After Fix

1. **Code Format Handling**: Codes entered with different case/spacing will be normalized
2. **Async Operations**: Database operations will complete correctly
3. **Better Debugging**: Logs will show tenant_id and code details when validation fails

## Potential Remaining Issues

If the error persists after restart, check:
1. **Tenant ID Mismatch**: Code belongs to different tenant than logged-in user
2. **Code Already Assigned**: Project already has an activation code
3. **Code Status**: Code is revoked, expired, or fully used

## Related Endpoints

- `POST /api/tenant/projects/{project_id}/assign-activation-code` - Assign code to project
- `GET /admin/api/codes` - List activation codes (Admin Portal)

