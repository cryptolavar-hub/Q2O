# Lazy Loading Fix - November 19, 2025

## Problem

The Dashboard and Analytics pages were not loading data due to `MissingGreenlet` errors:

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here. 
Was IO attempted in an unexpected place?
```

## Root Cause

With async SQLAlchemy, **lazy loading does not work**. When code tries to access a relationship like `tenant.subscriptions`, SQLAlchemy attempts to lazy-load it, but this requires a greenlet context which isn't available in async mode.

The error occurred in:
1. `/admin/api/dashboard-stats` - accessing `tenant.subscriptions` without eager loading
2. `/admin/api/analytics` - accessing `tenant.subscriptions` without eager loading  
3. `/admin/api/tenants` (POST) - accessing `tenant.subscriptions` in `_load_subscription_details` without eager loading
4. `tenant_service.py` - missing `await` on `generate_otp` call

## Solution

### 1. Eager Loading with `selectinload`

All queries that need to access `tenant.subscriptions` now use `selectinload` to eagerly load the relationship:

```python
result = await db.execute(
    select(Tenant).options(selectinload(Tenant.subscriptions).selectinload(Subscription.plan))
)
all_tenants = result.scalars().unique().all()
```

### 2. Fixed Missing `await`

Added `await` to the `generate_otp` call in `create_tenant`:

```python
await generate_otp(new_tenant.slug, session)
```

### 3. Reload After Refresh

After `session.refresh()`, relationships may be cleared, so we reload the tenant with subscriptions:

```python
await session.refresh(new_tenant)
result = await session.execute(
    select(Tenant)
    .where(Tenant.id == new_tenant.id)
    .options(selectinload(Tenant.subscriptions).selectinload(Subscription.plan))
)
tenant_with_subs = result.scalar_one()
```

## Files Modified

1. **`addon_portal/api/routers/admin_api.py`**:
   - Added `selectinload` import
   - Added `Subscription` to imports
   - Fixed `get_dashboard_stats` to eagerly load subscriptions
   - Fixed `get_analytics` to eagerly load subscriptions

2. **`addon_portal/api/services/tenant_service.py`**:
   - Fixed missing `await` on `generate_otp` call
   - Fixed `create_tenant` to reload tenant with subscriptions after refresh
   - Fixed `update_tenant` to reload tenant with subscriptions after refresh

## Verification

After restarting the API server, the Dashboard and Analytics pages should now:
- ✅ Load dashboard statistics correctly
- ✅ Display analytics data for all date ranges
- ✅ Show tenant subscription information
- ✅ Create tenants without errors

## Important Notes

- **Always use `selectinload` or `joinedload`** when accessing relationships in async SQLAlchemy
- **Never access lazy-loaded relationships** directly - they will fail with `MissingGreenlet` error
- **Reload relationships after `session.refresh()`** if you need to access them
- **Use `.unique()`** when using `selectinload` to avoid duplicate results from joins

