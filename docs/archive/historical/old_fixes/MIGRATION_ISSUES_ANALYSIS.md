# Migration Issues Analysis - November 25, 2025

## Critical Issues Identified from Logs

### 1. Database Connection Leaks (CRITICAL)
**From logs**: `api_2025-11-25.log`

**Symptoms**:
- `PendingRollbackError: Can't reconnect until invalid transaction is rolled back`
- `The garbage collector is trying to clean up non-checked-in connection`
- Multiple connections in `INTRANS` state being dropped

**Location**: `addon_portal/api/graphql/resolvers.py` - `system_metrics_stream` subscription

**Impact**: 
- GraphQL subscriptions failing
- Tenant Dashboard unable to get real-time updates
- Database connection pool exhaustion

**Root Cause**: GraphQL subscriptions not properly handling transaction rollbacks on errors

---

### 2. Completion Percentage Showing Long Decimals
**From logs**: `api_2025-11-25run2.log`

**Example**: `'completion_percentage': 51.69491525423729`

**Issue**: Backend is returning raw float values instead of rounded percentages

**Location**: 
- `addon_portal/api/services/agent_task_service.py` - `calculate_project_progress()`
- `addon_portal/api/graphql/resolvers.py` - Project resolver

**Impact**: Tenant Dashboard displays ugly long decimal numbers instead of clean percentages

**Fix Applied**: ✅ Frontend now rounds to whole numbers, but backend should also round

---

### 3. Migration 008: execution_started_at Field
**Migration File**: `addon_portal/migrations_manual/008_add_project_execution_fields.sql`

**Fields Added**:
- `execution_status` (pending, running, completed, failed, paused)
- `execution_started_at` (TIMESTAMP)
- `execution_completed_at` (TIMESTAMP)
- `execution_error` (TEXT)
- `output_folder_path` (VARCHAR(500))

**Critical Usage**: 
- Used in `calculate_project_progress()` to filter tasks by execution run
- Prevents showing stale data from previous runs
- **CRITICAL**: If this field is NULL or migration fails, dashboard shows wrong data

**Potential Issues**:
- If migration partially fails, `execution_started_at` might be NULL
- Old projects might not have this field set
- Dashboard queries might fail if field doesn't exist

---

### 4. GraphQL Context Leaks
**From logs**: `api_2025-11-25.log`

**Warning**: `GraphQL context deleted without __aexit__ being called - potential connection leak`

**Location**: `addon_portal/api/graphql/context.py`

**Impact**: Database sessions not properly closed, leading to connection pool exhaustion

**Previous Fix**: `GraphQLContextCleanupMiddleware` was added, but may not be working for subscriptions

---

## What Was Working Before Migrations

### Tenant Dashboard Features (From Documentation)
1. **Real-Time Updates** (November 19, 2025):
   - GraphQL subscriptions for task updates
   - Project selector with search
   - Automatic progress bar updates
   - System metrics streaming

2. **Project Execution Tracking**:
   - `execution_started_at` filtering (prevents stale data)
   - Task progress calculation
   - Project status updates

3. **Percentage Display**:
   - Should show whole numbers (0-100)
   - Progress bars with smooth animations
   - Success rate and completion rate metrics

---

## Migration-Related Breakages

### Pattern Observed:
1. **Migration runs** → Adds new fields
2. **Code expects fields** → Queries fail if fields don't exist
3. **Old data incompatible** → NULL values cause issues
4. **Connection leaks** → Database pool exhausted
5. **Dashboard breaks** → Can't display data

### Specific Issues:

1. **execution_started_at NULL Values**:
   - Old projects created before migration don't have `execution_started_at`
   - `calculate_project_progress()` filters by this field
   - If NULL, might exclude all tasks or include wrong tasks

2. **GraphQL Subscription Failures**:
   - `system_metrics_stream` failing with `PendingRollbackError`
   - Tenant Dashboard can't get real-time updates
   - Falls back to polling, but that also fails

3. **Connection Pool Exhaustion**:
   - Multiple connection leaks from GraphQL subscriptions
   - Database connections not properly closed
   - System becomes unresponsive

---

## Recommendations

### Immediate Fixes Needed:

1. **Fix GraphQL Subscription Error Handling**:
   - Add proper rollback() calls in subscription error handlers
   - Ensure connections are closed even on errors
   - Add retry logic for transient errors

2. **Handle NULL execution_started_at**:
   - Update `calculate_project_progress()` to handle NULL gracefully
   - Set default `execution_started_at` for old projects
   - Migration should backfill this field

3. **Round Percentages in Backend**:
   - Update `calculate_project_progress()` to return rounded percentages
   - Update GraphQL resolvers to round before returning
   - Consistent formatting across all endpoints

4. **Migration Safety Checks**:
   - Verify all required fields exist before using them
   - Backfill NULL values for old records
   - Add database constraints to prevent NULL where needed

---

## Files to Check/Update

1. **`addon_portal/api/graphql/resolvers.py`**: ✅ FIXED
   - ✅ Added rollback() in `system_metrics_stream` error handler
   - ✅ Round `average_success_rate` to whole number
   - ✅ Round `completion_percentage` to whole number in project resolver

2. **`addon_portal/api/services/agent_task_service.py`**: ✅ FIXED
   - ✅ Round `completion_percentage` to whole number
   - ⚠️ Handle NULL `execution_started_at` gracefully (needs verification)

3. **`addon_portal/api/graphql/context.py`**: ⚠️ PARTIAL
   - Has cleanup logic but `__aexit__` not always called for subscriptions
   - Warning logged but connection still leaks

4. **Migration 008**: ⚠️ NEEDS BACKFILL
   - Add backfill for `execution_started_at` on existing projects
   - Set default value for old records

5. **Frontend (`addon_portal/apps/tenant-portal/src/pages/status.tsx`)**: ✅ FIXED
   - ✅ Round all percentage displays to whole numbers

---

## Testing Checklist

After fixes:
- [ ] Run project execution - verify no connection leaks
- [ ] Check Tenant Dashboard - verify percentages are whole numbers
- [ ] Verify GraphQL subscriptions work without errors
- [ ] Test with old projects (created before migration)
- [ ] Verify `execution_started_at` filtering works correctly
- [ ] Check database connection pool usage

---

**Last Updated**: November 25, 2025  
**Status**: Analysis Complete - Fixes Needed

