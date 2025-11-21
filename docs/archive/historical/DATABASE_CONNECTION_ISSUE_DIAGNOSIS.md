# Database Connection Issue - Critical Diagnosis

## 🔴 **ROOT CAUSE IDENTIFIED**

The Admin Dashboard is broken because **the application is connecting to SQLite instead of PostgreSQL**.

### Evidence from Logs:
```
sqlite3.OperationalError: no such column: tenants.email
sqlite3.OperationalError: no such column: activation_codes.code_plain
sqlite3.OperationalError: no such table: llm_project_config
sqlite3.OperationalError: no such table: llm_system_config
sqlite3.OperationalError: no such table: platform_events
```

### Why This Happened:

1. **Default Configuration**: `addon_portal/api/core/settings.py` line 25 has:
   ```python
   DB_DSN: str = "sqlite:///./q2o_licensing.db"  # SQLite default!
   ```

2. **Missing Environment Variable**: If `.env` file doesn't contain `DB_DSN`, the application uses the SQLite default.

3. **Database Schema Mismatch**: 
   - SQLite database doesn't have the new columns (`email`, `phone_number`, `otp_delivery_method`)
   - SQLite database doesn't have LLM tables (`llm_project_config`, `llm_system_config`)
   - SQLite database doesn't have `platform_events` table
   - SQLite database doesn't have `code_plain` column (it was removed in favor of `code_hash`)

## ✅ **SOLUTION**

### Step 1: Verify `.env` File Exists and Contains `DB_DSN`

The `.env` file must be at: `C:\Q2O_Combined\.env`

It must contain:
```env
DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
```

### Step 2: Restart Backend API

After setting `DB_DSN` in `.env`, restart the backend API to load the new configuration.

### Step 3: Verify Database Connection

The application should now connect to PostgreSQL instead of SQLite.

## 🔍 **VERIFICATION**

To verify the fix worked:
1. Check logs - should see PostgreSQL connection, not SQLite
2. Admin Dashboard should load without errors
3. All endpoints should work correctly

## ⚠️ **IMPORTANT NOTES**

- **Migration 007** was run on PostgreSQL, but the app was using SQLite
- All migrations need to be run on the **correct database** (PostgreSQL)
- The SQLite database (`q2o_licensing.db`) should be deleted or ignored

