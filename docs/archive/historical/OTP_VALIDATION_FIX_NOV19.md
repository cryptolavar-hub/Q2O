# OTP Validation Fix - November 19, 2025

## Problem

The Tenant Dashboard OTP validation was failing with a `MissingGreenlet` error:

```
greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?
```

**Error Location**: `/api/tenant/auth/otp/verify` endpoint

**Log Evidence**:
- OTP verification succeeded: `"otp_verified"` log entry
- But then error occurred: `"otp_verification_error"` with `MissingGreenlet` exception
- HTTP 500 Internal Server Error returned to client

## Root Cause

In `validate_session()` function (called after OTP verification), the code was accessing `tenant_session.tenant.slug` without eagerly loading the `tenant` relationship. With async SQLAlchemy, lazy loading doesn't work - relationships must be eagerly loaded using `selectinload` or `joinedload`.

**Problematic Code**:
```python
result = await session.execute(
    select(TenantSession)
    .join(Tenant)  # Join doesn't eagerly load the relationship
    .where(...)
)
tenant_session = result.scalar_one_or_none()
# Later: tenant_session.tenant.slug  # ❌ Lazy loading fails in async mode
```

## Solution

Added `selectinload(TenantSession.tenant)` to eagerly load the tenant relationship before accessing it:

**Fixed Code**:
```python
result = await session.execute(
    select(TenantSession)
    .options(selectinload(TenantSession.tenant))  # ✅ Eagerly load tenant
    .where(...)
)
tenant_session = result.scalar_one_or_none()
# Now: tenant_session.tenant.slug  # ✅ Works correctly
```

## Files Modified

1. **`addon_portal/api/services/tenant_auth_service.py`**:
   - Added `from sqlalchemy.orm import selectinload` import
   - Updated `validate_session()` to use `selectinload(TenantSession.tenant)`

## Testing

✅ App imports successfully  
✅ No linter errors  
⚠️ **Requires API restart** to take effect

## Impact

- **Before**: OTP verification failed with 500 error after successful OTP check
- **After**: OTP verification completes successfully and returns session token

## Related Issues

This is the same type of issue that was fixed earlier for:
- Admin Dashboard (`get_dashboard_stats`, `get_analytics`)
- Tenant service (`create_tenant`, `update_tenant`)

All lazy-loaded relationships must be eagerly loaded in async SQLAlchemy mode.

