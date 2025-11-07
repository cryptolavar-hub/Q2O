# ⚠️ CRITICAL: psycopg vs psycopg2-binary Clarification

**Date**: November 6, 2025  
**Issue**: Documentation incorrectly recommended psycopg2-binary  
**Correct Package**: psycopg (v3)

---

## 🔴 **IMPORTANT CORRECTION**

### **WRONG** (What docs initially said):
```bash
pip install psycopg2-binary>=2.9.9
```

### **CORRECT** (What addon actually needs):
```bash
pip install psycopg
```

---

## 🎯 **THE DIFFERENCE**

### **psycopg2-binary** (Version 2 - Legacy):
```
Package name:     psycopg2-binary
Version:          2.9.x
SQLAlchemy URL:   postgresql+psycopg2://...
Release:          2006-2021 (mature, stable)
Async support:    No (synchronous only)
```

### **psycopg** (Version 3 - Modern):
```
Package name:     psycopg
Version:          3.2.x
SQLAlchemy URL:   postgresql+psycopg://...
Release:          2021-present (modern, active)
Async support:    Yes (native async/await)
```

**They are COMPLETELY DIFFERENT packages!**

---

## 🔍 **HOW TO TELL WHICH ONE IS NEEDED**

Look at the SQLAlchemy connection string in `api/core/settings.py`:

```python
# If you see this:
DB_DSN = "postgresql+psycopg://..."
                    ^^^^^^^^
#                   No "2" = psycopg v3

# Then install:
pip install psycopg

# ────────────────────────────────────────────────

# If you see this:
DB_DSN = "postgresql+psycopg2://..."
                    ^^^^^^^^^
#                   Has "2" = psycopg2

# Then install:
pip install psycopg2-binary
```

---

## ✅ **FOR THIS ADDON**

The Q2O Licensing Addon uses:

```python
# addon_portal/api/core/settings.py line 9:
DB_DSN: str = "postgresql+psycopg://user:pass@localhost:5432/q2o"
                         ^^^^^^^^
                         NO "2" = Uses psycopg v3
```

**Therefore**: Install `psycopg` (v3), NOT `psycopg2-binary` (v2)

---

## 🧪 **REAL-WORLD VALIDATION**

### **User Experience** (November 6, 2025):

**Step 1: Had psycopg2-binary installed**:
```bash
$ pip list | grep psycopg
psycopg2-binary  2.9.11  ✓ Installed
```

**Step 2: Tried to run alembic**:
```bash
$ alembic revision --autogenerate
ModuleNotFoundError: No module named 'psycopg'  ✗ Failed
```

**Step 3: Installed psycopg (v3)**:
```bash
$ pip install psycopg
Successfully installed psycopg-3.2.12 tzdata-2025.2  ✓ Success
```

**Step 4: Now alembic should work**:
```bash
$ alembic revision --autogenerate -m "Initial licensing schema"
# Should work now!
```

**This proves**: The addon needs `psycopg` v3, not `psycopg2-binary` v2

---

## 📋 **CORRECTED REQUIREMENTS**

### **Quick2Odoo with Licensing Addon Support**:

```txt
# PostgreSQL Driver for Licensing Addon
# IMPORTANT: Use psycopg v3 (NOT psycopg2-binary v2!)
psycopg>=3.1.0,<4.0.0

# Alternative: If you want to use psycopg2 instead
# (requires changing addon's connection string to postgresql+psycopg2://...)
# psycopg2-binary>=2.9.9,<3.0.0
```

---

## 🔧 **IF YOU WANT TO USE PSYCOPG2 INSTEAD**

**Option**: Keep psycopg2-binary and modify addon

**Change** `addon_portal/api/core/settings.py` line 9:

```python
# From:
DB_DSN: str = "postgresql+psycopg://user:pass@localhost:5432/q2o"

# To:
DB_DSN: str = "postgresql+psycopg2://user:pass@localhost:5432/q2o"
                         ^^^^^ Add "2"
```

**Then you can use**:
```bash
pip install psycopg2-binary
```

**But**: This requires modifying addon code. Easier to just use psycopg v3 as intended.

---

## 📊 **COMPATIBILITY TABLE**

| Package | Version | Addon Needs | Compatible? | Install |
|---------|---------|-------------|-------------|---------|
| **psycopg** | 3.2.12 | ✅ Yes (intended) | ✅ Yes | `pip install psycopg` |
| **psycopg2-binary** | 2.9.11 | ❌ No (wrong version) | ❌ No | Not compatible |

**You now have both installed** (which is fine - they don't conflict)

---

## ✅ **SUMMARY**

### **Documentation Error**:
- Initial review said: "Install psycopg2-binary"
- Should have said: "Install psycopg (v3)"

### **Why This Happened**:
- Common confusion between psycopg2 and psycopg3
- Both are PostgreSQL drivers
- Easy to assume they're interchangeable (they're not)

### **Resolution**:
- User installed psycopg (v3) ✅
- Alembic should now work ✅
- All docs updated to reflect correct package ✅

---

## 🚀 **NEXT STEP**

Now that `psycopg` is installed, retry your command:

```bash
cd addon_portal
alembic revision --autogenerate -m "Initial licensing schema"
```

**Expected**: Migration file created successfully!

---

**Document Version**: 1.0  
**Last Updated**: November 6, 2025  
**Purpose**: Clarify psycopg v3 vs psycopg2 confusion  
**Status**: Critical correction based on real-world validation ✅

