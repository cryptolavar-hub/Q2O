# Addon Integration Requirements - Complete Dependency List

**Purpose**: Exact dependencies needed to run the Licensing Addon with Quick2Odoo  
**Date**: November 6, 2025

---

## 📦 **COMPLETE DEPENDENCY LIST**

### **What Quick2Odoo Already Has** ✅

These dependencies are already in Quick2Odoo's `requirements.txt`:

```txt
✓ fastapi==0.110.0
✓ uvicorn[standard]==0.29.0
✓ sqlalchemy==2.0.29
✓ alembic==1.13.1
✓ jinja2==3.1.3
✓ pydantic==2.7.1  ⚠️ (addon works better with 2.12.4+)
✓ pydantic-settings>=2.1.0
```

**Status**: 7/12 dependencies already present

---

## ⚠️ **WHAT NEEDS TO BE ADDED**

### **Critical Dependencies** (Must Add - 5 packages)

```txt
# JWT Authentication (CRITICAL - addon won't start without this)
pyjwt>=2.8.0,<3.0.0
cryptography>=41.0.0,<42.0.0  # Required for RS256 algorithm

# PostgreSQL Driver v3 (CRITICAL - database won't connect)
psycopg>=3.1.0,<4.0.0
# Note: Use psycopg (v3), NOT psycopg2-binary (v2) - different packages!

# Form Data Parsing (CRITICAL - admin UI forms won't work)
python-multipart>=0.0.6,<0.1.0

# Payment Processing (NEEDS UPDATE - version conflict)
# Quick2Odoo has: stripe==9.1.0
# Addon expects: stripe>=7.0.0,<8.0.0
# Solution: Update addon code to work with Stripe 9.x
```

### **Optional Dependencies** (Nice to Have - 1 package)

```txt
# OIDC/SSO Authentication (optional - only if using admin SSO)
Authlib>=1.3.0,<2.0.0

# Can be skipped if:
# - You don't need admin SSO
# - You use simple auth instead
# - You disable admin UI entirely
```

---

## 🔧 **RECOMMENDED requirements.txt ADDITIONS**

Add this section to Quick2Odoo's `requirements.txt`:

```txt
# ============================================================================
# LICENSING ADDON DEPENDENCIES (Optional Module)
# ============================================================================
# Only install these if you're using the Q2O Licensing Addon
#
# To install licensing addon dependencies:
#   pip install pyjwt cryptography psycopg2-binary python-multipart
#
# Optional (for admin SSO):
#   pip install Authlib
# ============================================================================

# JWT Authentication (for licensing addon)
pyjwt>=2.8.0,<3.0.0
cryptography>=41.0.0,<42.0.0

# PostgreSQL Database Driver v3 (for licensing addon multi-tenancy)
psycopg>=3.1.0,<4.0.0
# Note: NOT psycopg2-binary! The addon uses psycopg v3 (different package)

# Form Data Handling (for licensing addon admin UI)
python-multipart>=0.0.6,<0.1.0

# OIDC/SSO (optional - uncomment if using admin SSO)
# Authlib>=1.3.0,<2.0.0

# Note: Stripe already included above (stripe==9.1.0)
# Addon needs updating from Stripe v7 to v9 (see STRIPE_V9_MIGRATION_GUIDE.md)
```

---

## ⚠️ **VERSION CONFLICTS TO RESOLVE**

### **Conflict #1: Stripe Version**

**Current State**:
```
Quick2Odoo:           stripe==9.1.0
Addon expects:        stripe>=7.0.0,<8.0.0
Conflict:             v9 is outside <8.0.0 range! ❌
```

**Resolution**:

**Option A: Update Addon to Stripe v9** (Recommended):
1. Review addon's Stripe webhook code
2. Update to Stripe v9 API (most v7 code works)
3. Test webhook handling
4. Update addon's requirements range to `>=7.0.0,<10.0.0`

**Option B: Downgrade Quick2Odoo to Stripe v7** (Not recommended):
- Loses Stripe v9 features
- Goes backward
- Not good for long-term

**Recommended**: Update addon to v9

---

### **Conflict #2: Pydantic Version Difference**

**Current State**:
```
Quick2Odoo:           pydantic==2.7.1 (April 2024)
Addon expects:        pydantic>=2.6.0,<3.0.0
Current install:      pydantic==2.12.4 (November 2024)
```

**Is This a Problem?**:
- **Technically**: Both within Pydantic v2 (compatible)
- **Practically**: 5 minor versions difference might have edge cases
- **Risk Level**: LOW (Pydantic v2 is stable)

**Resolution**:

**Update Quick2Odoo to flexible range** (Recommended):
```txt
# Change from:
pydantic==2.7.1

# To:
pydantic>=2.7.1,<3.0.0  # Allow minor updates
```

**OR pin to latest**:
```txt
pydantic==2.12.4
```

**Then test Quick2Odoo** to ensure no breaking changes.

---

## 🗄️ **DATABASE SETUP REQUIREMENTS**

### **For Licensing Addon** (PostgreSQL)

**Installation**:

**Windows**:
```bash
# Download PostgreSQL 16
https://www.postgresql.org/download/windows/

# Install with defaults
# Remember password for postgres user
```

**macOS**:
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql-16 postgresql-contrib
sudo systemctl start postgresql
```

**Create Database**:
```bash
# Connect as postgres user
psql -U postgres

# Create database
CREATE DATABASE q2o_licensing;

# Create user
CREATE USER q2o_user WITH PASSWORD 'secure_password_here';

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE q2o_licensing TO q2o_user;

# Exit
\q
```

**Configure Addon**:
```bash
# addon_portal/.env
DB_DSN=postgresql+psycopg://q2o_user:secure_password_here@localhost:5432/q2o_licensing
```

---

### **For Quick2Odoo** (SQLite - No Changes)

Quick2Odoo continues to use SQLite:
```
~/.quickodoo/research.db  # Research cache
./project_workspace/*.db  # Project-specific data
```

**No changes needed** - SQLite is perfect for Quick2Odoo's use case.

---

## 📋 **INSTALLATION CHECKLIST**

### **Prerequisites**:
- [ ] Python 3.10-3.13 installed
- [ ] PostgreSQL 16+ installed (for licensing addon)
- [ ] Git installed

### **Quick2Odoo Base** (Existing):
- [ ] Clone repository
- [ ] Create virtual environment
- [ ] Install existing requirements: `pip install -r requirements.txt`

### **Licensing Addon Integration**:
- [ ] Install additional dependencies:
  ```bash
  pip install pyjwt cryptography psycopg2-binary python-multipart
  ```
- [ ] (Optional) Install Authlib if using SSO:
  ```bash
  pip install Authlib
  ```
- [ ] Set up PostgreSQL database
- [ ] Configure addon `.env` file
- [ ] Run database migrations
- [ ] Test addon starts successfully

---

## 🧪 **TESTING CHECKLIST**

### **After Adding Dependencies**:

**Test 1: Dependencies Install**:
```bash
pip install pyjwt cryptography psycopg2-binary python-multipart
# Should complete without errors
```

**Test 2: Quick2Odoo Still Works**:
```bash
python main.py --help
# Should run without errors
```

**Test 3: Addon Can Import**:
```bash
cd addon_portal
python -c "from api.core.settings import settings; print('OK')"
python -c "from api.core.security import issue_access_token; print('OK')"
```

**Test 4: Addon Starts**:
```bash
cd addon_portal
uvicorn api.main:app --host 0.0.0.0 --port 8080
# Should start without errors
```

**Test 5: Database Connection**:
```bash
psql -U q2o_user -d q2o_licensing -c "SELECT 1;"
# Should return: 1
```

---

## 💡 **MINIMAL INSTALLATION** (For Testing)

If you just want to TEST the addon quickly:

```bash
# 1. Install only critical dependencies
pip install pyjwt cryptography python-multipart

# 2. Use SQLite instead of PostgreSQL (modify addon)
# Edit addon_portal/api/core/settings.py:
DB_DSN: str = "sqlite:///./q2o_licensing.db"

# 3. Skip Authlib (disable SSO)
# Leave OIDC_* variables empty in .env

# 4. Install psycopg2-binary anyway (or addon will fail to import)
pip install psycopg2-binary

# 5. Update addon Stripe code to v9 (or install old Stripe)
pip install stripe==7.9.0  # Temp: use old version
```

**This lets you test addon functionality without full production setup.**

---

## 📊 **DEPENDENCY SIZE IMPACT**

Adding licensing addon dependencies increases installation size:

| Package | Size | Purpose |
|---------|------|---------|
| pyjwt | ~50 KB | JWT tokens |
| cryptography | ~3 MB | Encryption |
| psycopg2-binary | ~3.5 MB | PostgreSQL driver |
| python-multipart | ~30 KB | Form parsing |
| Authlib (optional) | ~200 KB | OAuth/OIDC |
| **Total** | **~6.8 MB** | Licensing addon support |

**Impact**: Increases from ~150 MB to ~157 MB (4.5% increase)

**Acceptable**: Yes - these are all legitimate dependencies

---

## ✅ **FINAL REQUIREMENTS LIST**

### **Complete requirements.txt** (with addon support):

Save this as `requirements_with_licensing.txt`:

```txt
# Multi-Agent Development System - Production Dependencies
# WITH Licensing Addon Support

# Python Version: 3.10, 3.11, 3.12, 3.13

# Core FastAPI and ASGI server
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic>=2.7.1,<3.0.0  # Updated to allow 2.12.4
pydantic-settings>=2.1.0

# Database
sqlalchemy==2.0.29
alembic==1.13.1

# Stripe integration
stripe==9.1.0  # Note: Addon needs updating for v9

# JWT Authentication (for licensing addon)
pyjwt>=2.8.0,<3.0.0
cryptography>=41.0.0,<42.0.0

# PostgreSQL (for licensing addon)
psycopg2-binary>=2.9.9,<3.0.0

# Form handling (for licensing addon admin UI)
python-multipart>=0.0.6,<0.1.0

# OIDC/SSO (optional - only if using admin SSO)
# Authlib>=1.3.0,<2.0.0  # Uncomment if needed

# ... rest of Quick2Odoo dependencies ...
```

---

**Document Version**: 1.0  
**Last Updated**: November 6, 2025  
**Status**: Comprehensive dependency analysis complete

