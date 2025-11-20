# Admin Dashboard Fix - Database Connection Issue

## 🔴 **CRITICAL ISSUE IDENTIFIED**

The Admin Dashboard is completely broken because **the application is connecting to SQLite instead of PostgreSQL**.

### Root Cause:
1. **`.env` file is missing** at `C:\Q2O_Combined\.env`
2. Without `.env`, the application uses the SQLite default: `sqlite:///./q2o_licensing.db`
3. SQLite database doesn't have:
   - New tenant columns (`email`, `phone_number`, `otp_delivery_method`)
   - LLM tables (`llm_project_config`, `llm_system_config`)
   - Platform events table (`platform_events`)
   - Updated activation codes schema

### Error Evidence:
```
sqlite3.OperationalError: no such column: tenants.email
sqlite3.OperationalError: no such column: activation_codes.code_plain
sqlite3.OperationalError: no such table: llm_project_config
sqlite3.OperationalError: no such table: llm_system_config
sqlite3.OperationalError: no such table: platform_events
```

## ✅ **IMMEDIATE FIX**

### Step 1: Create `.env` File

**Location**: `C:\Q2O_Combined\.env`

**Quick Setup**:
```batch
cd C:\Q2O_Combined
copy addon_portal\env.example.txt .env
```

### Step 2: Configure PostgreSQL Connection

Edit `.env` and ensure `DB_DSN` is set to PostgreSQL:

```env
DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
```

**Replace `YOUR_PASSWORD` with your actual PostgreSQL password.**

### Step 3: Restart Backend API

After creating/updating `.env`, **restart the backend API** to load the new configuration.

### Step 4: Verify Fix

1. Check logs - should see PostgreSQL connection (not SQLite)
2. Admin Dashboard should load without errors
3. All endpoints should work correctly

## 🔍 **Diagnostic Script**

Run `FIX_DATABASE_CONNECTION.bat` to diagnose the issue:
```batch
.\FIX_DATABASE_CONNECTION.bat
```

This script will:
- Check if `.env` file exists
- Verify `DB_DSN` is configured
- Identify if SQLite or PostgreSQL is being used
- Provide next steps

## ⚠️ **IMPORTANT NOTES**

1. **Migration 007** was run on PostgreSQL, but the app was using SQLite
2. All migrations need to be run on the **correct database** (PostgreSQL)
3. The SQLite database (`q2o_licensing.db`) should be deleted or ignored
4. The `.env` file **must be at the project root** (`C:\Q2O_Combined\.env`)

## 📋 **Complete .env Template**

See `addon_portal/env.example.txt` for the complete template with all required variables.

**Minimum required for database connection:**
```env
DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
```

## 🎯 **After Fix**

Once the database connection is fixed:
1. ✅ Admin Dashboard will load correctly
2. ✅ All tenant operations will work
3. ✅ Activation codes will work
4. ✅ LLM configuration will work
5. ✅ Analytics will work

---

**Status**: 🔴 **CRITICAL - BLOCKING ALL ADMIN OPERATIONS**

