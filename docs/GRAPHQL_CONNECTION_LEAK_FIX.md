# GraphQL Context Connection Leak Fix

## Issue
GraphQL requests were causing database connection leaks. Logs showed:
- `"GraphQL context deleted without __aexit__ being called - potential connection leak"`
- `"The garbage collector is trying to clean up non-checked-in connection"` errors

## Root Cause
Strawberry GraphQL should automatically call `__aexit__` on the context object when using it as an async context manager. However, in some cases (especially with errors, subscriptions, or edge cases), `__aexit__` was not being called, leaving database sessions open and causing connection pool exhaustion.

## Solution
Implemented a two-layer defense:

### 1. Enhanced Context Class (`addon_portal/api/graphql/context.py`)
- Added `_cleaned_up` flag to track cleanup status
- Added explicit `cleanup()` method that can be called by middleware
- Enhanced `__aexit__` to check if already cleaned up (prevents double cleanup)
- Store context in `request.state` when created for middleware access

### 2. Cleanup Middleware (`addon_portal/api/middleware/graphql_cleanup.py`)
- Created `GraphQLContextCleanupMiddleware` that runs after each GraphQL request
- Uses `try/finally` to ensure cleanup even if request raises an exception
- Calls `context.cleanup()` if available, or directly closes the database session
- Integrated into FastAPI app in `addon_portal/api/main.py`

## Implementation Details

### Context Storage
```python
# In get_graphql_context()
if request:
    request.state.graphql_context = context
```

### Middleware Cleanup
```python
# In GraphQLContextCleanupMiddleware.dispatch()
finally:
    if request.url.path.startswith("/graphql"):
        if hasattr(request.state, 'graphql_context'):
            context = request.state.graphql_context
            if hasattr(context, 'cleanup'):
                await context.cleanup()
```

### Explicit Cleanup Method
```python
async def cleanup(self):
    """Explicit cleanup method that can be called by middleware"""
    if self._cleaned_up:
        return
    
    try:
        if self.db:
            await self.db.rollback()
            await self.db.close()
    finally:
        self._cleaned_up = True
        self.db = None
```

## Testing
After this fix:
1. GraphQL requests should no longer leak database connections
2. The `__aexit__` method will still be called by Strawberry when possible
3. The middleware ensures cleanup even if `__aexit__` is not called
4. No double cleanup occurs (tracked by `_cleaned_up` flag)

## Files Modified
1. `addon_portal/api/graphql/context.py` - Enhanced context class with cleanup tracking
2. `addon_portal/api/middleware/graphql_cleanup.py` - New middleware for cleanup
3. `addon_portal/api/main.py` - Integrated cleanup middleware

## Status
✅ **FIXED** - Database connection leaks from GraphQL requests should now be prevented.

