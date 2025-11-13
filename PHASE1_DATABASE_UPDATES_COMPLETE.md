# Phase 1: Database Schema Updates - COMPLETE ✅
**Date**: November 12, 2025  
**Status**: Database Schema Ready for Migration

---

## ✅ **Completed Changes**

### **1. Database Migration Created**
- **File**: `addon_portal/migrations_manual/005_add_tenant_scoping_to_projects.sql`
- **Changes**:
  - ✅ Added `tenant_id` to `llm_project_config` (nullable for backward compatibility)
  - ✅ Added `activation_code_id` to `llm_project_config` (tracks which code activated the project)
  - ✅ Added `project_status`, `started_at`, `completed_at` fields
  - ✅ Created `tenant_sessions` table for OTP authentication
  - ✅ All indexes and foreign keys properly configured

### **2. Model Updates**
- **File**: `addon_portal/api/models/llm_config.py`
- **Changes**:
  - ✅ Added `tenant_id` column with foreign key to `tenants`
  - ✅ Added `activation_code_id` column with foreign key to `activation_codes`
  - ✅ Added `project_status`, `started_at`, `completed_at` fields
  - ✅ Added relationships: `tenant`, `activation_code`

### **3. Activation Code Service Created**
- **File**: `addon_portal/api/services/activation_code_service.py`
- **Features**:
  - ✅ Reusable `generate_codes()` function
  - ✅ Proper code hashing and secure generation
  - ✅ Format: `XXXX-XXXX-XXXX-XXXX` (e.g., `12RY-S55W-4MZR-KP2J`)
  - ✅ Supports TTL, labels, max_uses
  - ✅ Comprehensive error handling and logging

### **4. Tenant Service Updated**
- **File**: `addon_portal/api/services/tenant_service.py`
- **Changes**:
  - ✅ Auto-generates **10% of plan quota** activation codes when creating tenant
  - ✅ Minimum 1 code generated (even if quota is small)
  - ✅ Codes labeled "Auto-generated on tenant creation"
  - ✅ `max_uses=1` (one code = one project activation)
  - ✅ Non-blocking: tenant creation succeeds even if code generation fails

---

## 📋 **Migration Instructions**

### **Step 1: Run Migration**
```bash
cd addon_portal
# Connect to your PostgreSQL database
psql -U q2o_user -d q2o -f migrations_manual/005_add_tenant_scoping_to_projects.sql
```

### **Step 2: Verify Migration**
```sql
-- Check tenant_id was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'llm_project_config' AND column_name = 'tenant_id';

-- Check activation_code_id was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'llm_project_config' AND column_name = 'activation_code_id';

-- Check tenant_sessions table exists
SELECT table_name FROM information_schema.tables WHERE table_name = 'tenant_sessions';
```

---

## 🎯 **Key Features Implemented**

### **Activation Code Workflow** (Clarified)
- ✅ **One code = one project activation** (codes are consumed)
- ✅ **Auto-generation**: 10% of plan quota codes created when tenant is created
- ✅ **Format**: `12RY-S55W-4MZR-KP2J` (alphanumeric, no ambiguous chars)

### **Tenant Scoping**
- ✅ Projects linked to tenants via `tenant_id`
- ✅ Backward compatible: existing projects without `tenant_id` remain admin-only
- ✅ Cascade delete: deleting tenant deletes all tenant's projects

### **Project Activation Tracking**
- ✅ `activation_code_id` tracks which code was used to activate a project
- ✅ One code can activate one project (enforced by `max_uses=1`)

---

## 🔄 **Next Steps (Phase 2)**

1. **Tenant Authentication Service** (`tenant_auth_service.py`)
   - OTP generation and verification
   - Session token management
   - Session timeout handling

2. **Tenant API Router** (`tenant_api.py`)
   - `/api/tenant/auth/otp/generate`
   - `/api/tenant/auth/otp/verify`
   - `/api/tenant/projects` (CRUD)

3. **Update LLM Config Service**
   - Filter projects by `tenant_id` from session
   - Verify tenant ownership before CRUD operations

---

## 📊 **Database Schema Summary**

### **New Columns in `llm_project_config`**
```sql
tenant_id INTEGER NULL REFERENCES tenants(id) ON DELETE CASCADE
activation_code_id INTEGER NULL REFERENCES activation_codes(id) ON DELETE SET NULL
project_status VARCHAR(20) DEFAULT 'active'
started_at TIMESTAMP WITH TIME ZONE NULL
completed_at TIMESTAMP WITH TIME ZONE NULL
```

### **New Table: `tenant_sessions`**
```sql
CREATE TABLE tenant_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    otp_code VARCHAR(6),
    otp_expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## ✅ **Testing Checklist**

- [ ] Run migration script successfully
- [ ] Verify all columns exist
- [ ] Verify foreign keys work
- [ ] Test tenant creation (should auto-generate codes)
- [ ] Verify codes are in correct format
- [ ] Test backward compatibility (existing projects without tenant_id)

---

**Status**: Ready for Phase 2 (Backend API Updates)

