# Comprehensive Issues List - Q2O Admin Portal

**Date:** November 18, 2025  
**Status:** Critical - Multiple breaking issues affecting all services

---

## 🔴 CRITICAL ISSUES (Blocking All Functionality)

### 1. **Database Does Not Exist - CRITICAL BLOCKER** ⚠️
**Location:** PostgreSQL server  
**Error:** `FATAL: database "quick2odoo" does not exist`  
**Impact:** **ALL API endpoints fail** - Every database operation returns this error  
**Root Cause:** The database `quick2odoo` specified in `DB_DSN` does not exist in PostgreSQL  
**Fix Required:**
- Run `python create_database.py` to create the database
- OR update `DB_DSN` in `.env` to point to an existing database
- After creating database, run migrations to create tables

**Files Affected:**
- **ALL** API endpoints fail
- Tenant queries fail
- LLM project listing fails
- Analytics endpoints fail
- Dashboard stats fail
- OTP generation fails
- Every database operation fails

**Log Evidence:**
```
2025-11-18 16:44:17 [ERROR] api.services.tenant_service: tenant_query_failed
2025-11-18 16:44:35 [ERROR] api.core.exceptions: unexpected_error
FATAL: database "quick2odoo" does not exist
```

---

### 2. **Database Connection - Missing PostgreSQL Driver**
**Location:** `addon_portal/api/core/db.py`, `addon_portal/requirements.txt`  
**Error:** `ImportError: no pq wrapper available`  
**Impact:** API cannot connect to PostgreSQL database  
**Root Cause:** `psycopg>=3.1.0,<4.0.0` in requirements.txt but `psycopg[binary]` not installed  
**Fix Required:**
- Install: `pip install "psycopg[binary]>=3.1.0,<4.0.0"`
- OR update requirements.txt to: `psycopg[binary]>=3.1.0,<4.0.0`

**Files Affected:**
- All database operations fail
- All API endpoints return errors
- Frontend shows empty data

---

### 2. **Database DSN Configuration Mismatch**
**Location:** `C:\Q2O_Combined\.env`  
**Error:** Application defaults to SQLite instead of PostgreSQL  
**Impact:** All data operations hit wrong database  
**Root Cause:** 
- `.env` has `DATABASE_URL` but code expects `DB_DSN`
- DSN format mismatch: `postgresql://` vs `postgresql+psycopg://`

**Current State:**
- `.env` contains: `DATABASE_URL=postgresql://q2o_user:Q2OPostgres2025!@localhost:5432/quick2odoo`
- Code expects: `DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025!@localhost:5432/quick2odoo`

**Fix Required:**
- Add/Update `.env`: `DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025!@localhost:5432/quick2odoo`
- Ensure `settings.py` reads `DB_DSN` (already configured)

---

### 3. **Frontend Error Display - [object Object]**
**Location:** `addon_portal/apps/admin-portal/src/pages/tenants.tsx`  
**Error:** Red error box showing `[object Object]` instead of readable error message  
**Impact:** Users cannot understand what went wrong  
**Root Cause:** Error object being displayed directly without string extraction

**Current Code Issue:**
- Error handling in `loadTenants` catches errors but may display Error object directly
- Error response from API may be an object that needs parsing

**Fix Required:**
- Ensure all error messages are extracted as strings
- Add proper error parsing in all API client functions
- Verify error display logic in tenants.tsx (lines 90-99)

**Files Affected:**
- `addon_portal/apps/admin-portal/src/pages/tenants.tsx` (line 73: `errorMessage` state)
- `addon_portal/apps/admin-portal/src/lib/api.ts` (error handling in all fetch calls)

---

## 🟠 HIGH PRIORITY ISSUES (Breaking Specific Features)

### 4. **Tenant Query Failures**
**Location:** `addon_portal/api/services/tenant_service.py:136`  
**Error:** `tenant_query_failed` logged repeatedly  
**Impact:** Tenant list page shows empty table  
**Root Cause:** SQLAlchemy query failing - likely due to:
- Database connection issues (see Issue #1, #2)
- Missing tables in PostgreSQL database
- Relationship loading issues (`selectinload` on subscriptions)

**Log Evidence:**
```
2025-11-18 15:14:38 [ERROR] api.services.tenant_service: tenant_query_failed
2025-11-18 15:14:38 [ERROR] api.core.exceptions: business_logic_error
```

**Fix Required:**
- Verify PostgreSQL connection works
- Check if `tenants`, `subscriptions`, `plans` tables exist
- Verify relationships are properly configured in models

---

### 5. **LLM Management - Project Listing Failures**
**Location:** `addon_portal/api/routers/llm_management.py:77`  
**Error:** `unexpected_error` logged when listing LLM projects  
**Impact:** LLM Management page cannot load projects  
**Root Cause:** Database query failures in `list_projects` function

**Log Evidence:**
```
2025-11-18 15:14:46 [INFO] api.routers.llm_management: list_llm_projects
2025-11-18 15:14:46 [ERROR] api.core.exceptions: unexpected_error
```

**Fix Required:**
- Check `llm_project_config` table exists
- Verify `list_projects` function in `llm_config_service.py` handles errors properly
- Add specific error logging to identify exact failure point

---

### 6. **Platform Events Table Missing**
**Location:** `addon_portal/api/routers/admin_api.py:223`  
**Error:** `platform_events table not found, returning empty activities`  
**Impact:** Dashboard "Recent Activity" section is empty  
**Root Cause:** Migration 006 not run or table doesn't exist in PostgreSQL

**Log Evidence:**
```
2025-11-18 15:14:53 [WARNING] api.routers.admin_api: platform_events table not found, returning empty activities
```

**Fix Required:**
- Run migration: `addon_portal/migrations_manual/006_create_platform_events_table.sql`
- OR verify table exists in PostgreSQL: `SELECT * FROM platform_events LIMIT 1;`

---

### 7. **Activation Codes - Empty Display**
**Location:** `addon_portal/apps/admin-portal/src/pages/codes.tsx`  
**Error:** "No activation codes yet" displayed  
**Impact:** Cannot view or manage activation codes  
**Root Cause:** 
- Database connection issues (see Issue #1, #2)
- OR no codes in database
- OR query failing silently

**Fix Required:**
- Verify database connection
- Check `activation_codes` table exists and has data
- Verify `/admin/api/codes` endpoint works

---

### 8. **OTP Generation Failures**
**Location:** `addon_portal/api/routers/tenant_api.py`  
**Error:** `otp_generation_error` logged  
**Impact:** Tenant Portal login fails  
**Root Cause:** OTP generation service failing

**Log Evidence:**
```
2025-11-18 15:14:17 [ERROR] api.routers.tenant_api: otp_generation_error
```

**Fix Required:**
- Check `tenant_auth_service.py` - `generate_otp` function
- Verify tenant has email/phone configured
- Check SMTP configuration if email delivery enabled

---

## 🟡 MEDIUM PRIORITY ISSUES (Functional but Needs Fix)

### 9. **Exception Handler - Generic Error Messages**
**Location:** `addon_portal/api/core/exceptions.py:95`  
**Issue:** Generic "An unexpected error occurred" message  
**Impact:** Difficult to debug issues  
**Root Cause:** Exception handler catches all exceptions but doesn't log full traceback

**Current Code:**
```python
LOGGER.error("unexpected_error", extra={"exception": str(exc), "path": request.url.path, "method": request.method})
```

**Fix Required:**
- Add full traceback to logs
- Include exception type in response (in development mode)
- Add request body/query params to error context

---

### 10. **Frontend Error Handling - Inconsistent**
**Location:** Multiple files in `addon_portal/apps/admin-portal/src/`  
**Issue:** Different error handling patterns across pages  
**Impact:** Inconsistent user experience  
**Root Cause:** No centralized error handling utility

**Files Affected:**
- `pages/tenants.tsx` - Has error handling but may show [object Object]
- `pages/codes.tsx` - May not handle all error cases
- `pages/llm/configuration.tsx` - Error handling exists but may need improvement

**Fix Required:**
- Create centralized error handler utility
- Standardize error message extraction
- Add error boundary components

---

### 11. **Database Schema - Missing Columns**
**Location:** `addon_portal/api/models/licensing.py`  
**Issue:** Code expects columns that may not exist in PostgreSQL  
**Impact:** Queries fail with "column does not exist" errors  
**Root Cause:** Migrations not run or out of sync

**Potential Missing Columns:**
- `tenants.email` (Migration 007)
- `tenants.phone_number` (Migration 007)
- `tenants.otp_delivery_method` (Migration 007)
- `activation_codes.code_plain` (may be missing)

**Fix Required:**
- Verify all migrations have been run
- Check PostgreSQL schema matches models
- Run missing migrations

---

### 12. **API Response Format - Inconsistent Error Structure**
**Location:** `addon_portal/api/core/exceptions.py`  
**Issue:** Some endpoints return `{detail: "message"}` while others return `{errorCode, message, detail}`  
**Impact:** Frontend error parsing fails  
**Root Cause:** FastAPI default error format vs custom BusinessLogicError format

**Fix Required:**
- Standardize all error responses
- Update frontend to handle both formats
- OR update all endpoints to use custom exceptions

---

## 🔵 LOW PRIORITY ISSUES (Polish & Optimization)

### 13. **Logging - Missing Context**
**Location:** `addon_portal/api/core/logging.py`  
**Issue:** Some log entries don't include enough context  
**Impact:** Difficult to trace issues  
**Fix Required:**
- Add request ID to all logs
- Include user/tenant context where applicable
- Add correlation IDs for request tracing

---

### 14. **Frontend - Loading States**
**Location:** Multiple pages  
**Issue:** Some pages don't show loading indicators  
**Impact:** Poor UX when data is loading  
**Fix Required:**
- Add loading spinners to all data-fetching operations
- Show skeleton loaders for better perceived performance

---

### 15. **Database Connection Pooling**
**Location:** `addon_portal/api/core/db.py`  
**Issue:** Basic connection pooling, no configuration  
**Impact:** Potential connection exhaustion under load  
**Fix Required:**
- Configure connection pool size
- Add connection timeout settings
- Monitor connection pool metrics

---

## 📋 SUMMARY OF IMMEDIATE FIXES REQUIRED

### Priority 1 (Must Fix Now):
1. ✅ Install `psycopg[binary]` driver
2. ✅ Update `.env` with correct `DB_DSN` format
3. ✅ Fix frontend `[object Object]` error display
4. ✅ Verify PostgreSQL database has all required tables

### Priority 2 (Fix After Priority 1):
5. Run missing database migrations
6. Fix tenant query failures
7. Fix LLM project listing
8. Fix OTP generation

### Priority 3 (Polish):
9. Improve error handling consistency
10. Add better logging
11. Standardize API error responses

---

## 🔧 QUICK FIX SCRIPT

Create a script to:
1. Install psycopg[binary]
2. Verify .env has DB_DSN
3. Test database connection
4. List all tables
5. Check for missing migrations

---

## 📝 TESTING CHECKLIST

After fixes, verify:
- [ ] Database connection works
- [ ] Tenant list page loads data
- [ ] Tenant create/edit works
- [ ] Activation codes page loads
- [ ] LLM Management page loads projects
- [ ] Dashboard shows recent activities
- [ ] Error messages are readable (not [object Object])
- [ ] OTP generation works
- [ ] All API endpoints return proper error formats

