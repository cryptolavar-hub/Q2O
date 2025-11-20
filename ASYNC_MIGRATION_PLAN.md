# Async SQLAlchemy Migration Plan

## Status: IN PROGRESS

This document tracks the migration from synchronous to asynchronous SQLAlchemy for optimal SaaS scalability.

## Why Async?
- **High Scalability**: Handle thousands of concurrent requests
- **Non-blocking I/O**: Database queries don't block the event loop
- **Resource Efficiency**: Better CPU and memory utilization
- **GraphQL Performance**: Async resolvers work optimally with async sessions

## Migration Progress

### ✅ Completed
1. Database setup (`addon_portal/api/core/db.py`) - Migrated to `create_async_engine` and `AsyncSessionLocal`
2. Dependencies (`addon_portal/api/deps.py`) - Updated `get_db` to async
3. GraphQL Context (`addon_portal/api/graphql/context.py`) - Using `AsyncSession`
4. GraphQL DataLoaders (`addon_portal/api/graphql/dataloaders.py`) - Using `AsyncSession`
5. Requirements (`addon_portal/requirements.txt`) - Added `psycopg[async]` and `aiosqlite`
6. Tenant API Router (`addon_portal/api/routers/tenant_api.py`) - Updated to `AsyncSession`

### 🔄 In Progress
- Tenant Auth Service (`addon_portal/api/services/tenant_auth_service.py`) - Converting to async
- LLM Config Service (`addon_portal/api/services/llm_config_service.py`) - Converting to async
- Tenant Service (`addon_portal/api/services/tenant_service.py`) - Converting to async
- Project Execution Service (`addon_portal/api/services/project_execution_service.py`) - Converting to async

### ⏳ Pending
- All other routers (admin_api, llm_management, etc.) - Update to AsyncSession
- All other services - Convert to async functions
- All database queries - Add `await` and use `session.execute()` instead of `session.scalar()`

## Key Changes Required

### 1. Database Queries
**Before:**
```python
tenant = session.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
```

**After:**
```python
result = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
tenant = result.scalar_one_or_none()
```

### 2. Session Commits
**Before:**
```python
session.commit()
```

**After:**
```python
await session.commit()
```

### 3. Service Functions
**Before:**
```python
def generate_otp(tenant_slug: str, session: Session) -> None:
```

**After:**
```python
async def generate_otp(tenant_slug: str, session: AsyncSession) -> None:
```

### 4. Router Endpoints
**Before:**
```python
async def endpoint(db: Session = Depends(get_db)):
    service_function(param, db)
    db.commit()
```

**After:**
```python
async def endpoint(db: AsyncSession = Depends(get_db)):
    await service_function(param, db)
    await db.commit()
```

## Files Requiring Updates

### Routers (8 files)
- ✅ `addon_portal/api/routers/tenant_api.py`
- ⏳ `addon_portal/api/routers/admin_api.py`
- ⏳ `addon_portal/api/routers/llm_management.py`
- ⏳ `addon_portal/api/routers/usage.py`
- ⏳ `addon_portal/api/routers/licenses.py`
- ⏳ `addon_portal/api/routers/authz.py`
- ⏳ `addon_portal/api/routers/billing_stripe.py`
- ⏳ `addon_portal/api/routers/admin_pages.py`

### Services (10+ files)
- ⏳ `addon_portal/api/services/tenant_auth_service.py`
- ⏳ `addon_portal/api/services/tenant_service.py`
- ⏳ `addon_portal/api/services/llm_config_service.py`
- ⏳ `addon_portal/api/services/project_execution_service.py`
- ⏳ All other service files

## Testing Checklist
- [ ] All endpoints respond correctly
- [ ] Database queries execute without errors
- [ ] Transactions commit properly
- [ ] GraphQL API works
- [ ] No blocking operations remain
- [ ] Performance benchmarks show improvement

## Notes
- This is a breaking change - all code must be updated
- Test thoroughly after each service/router update
- Keep backups before major changes
- Update this document as progress is made

