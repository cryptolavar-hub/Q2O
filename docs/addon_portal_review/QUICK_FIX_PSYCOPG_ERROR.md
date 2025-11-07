# Quick Fix: psycopg "no pq wrapper available" Error

**Error**: `ImportError: no pq wrapper available`  
**Solution Time**: 2 minutes  
**Recommended**: Use psycopg2-binary (you already have it!)

---

## ⚡ **FASTEST FIX** (2 minutes)

You already have `psycopg2-binary 2.9.11` installed. Just use it!

### **Change 1 Line in Addon**:

**Edit**: `addon_portal/api/core/settings.py` (line 9)

```python
# Change from:
DB_DSN: str = "postgresql+psycopg://user:pass@localhost:5432/q2o"

# To:
DB_DSN: str = "postgresql+psycopg2://user:pass@localhost:5432/q2o"
                         ^^^^^ Add "2"
```

**Save the file**, then retry:

```bash
cd addon_portal
alembic revision --autogenerate -m "Initial licensing schema"
```

**Should work now!** ✅

---

## 🔍 **WHY THE ERROR HAPPENED**

### **psycopg v3 Architecture**:

```
psycopg (pure Python wrapper)
├─ Needs ONE of these implementations:
│  ├─ psycopg_c (C implementation) ✗ Not installed
│  ├─ psycopg_binary (compiled) ✗ Not installed
│  └─ libpq library (system-wide) ✗ Not found
```

When you ran `pip install psycopg`, it installed the **wrapper only**, not the implementations!

---

## ✅ **SOLUTION OPTIONS**

### **Option A: Use psycopg2-binary** (EASIEST - Recommended)

**You already have it installed!**

Just change the connection string (see above).

**Pros**:
- ✅ Already installed (psycopg2-binary 2.9.11)
- ✅ Bundles everything (no extra dependencies)
- ✅ 1-line change in addon
- ✅ Works immediately

---

### **Option B: Install psycopg with binary**

```bash
pip install "psycopg[binary]"
```

This installs `psycopg-binary` package alongside `psycopg`.

**Pros**:
- ✅ Uses psycopg v3 as addon intended
- ✅ No addon code changes

**Cons**:
- Larger package size
- Two PostgreSQL drivers installed (psycopg + psycopg2-binary)

---

### **Option C: Install libpq library** (Most Complex)

**Windows**:
1. Download PostgreSQL installer (includes libpq)
2. Add PostgreSQL bin to PATH
3. Retry

**Not recommended** - Options A or B are simpler.

---

## 🎯 **MY RECOMMENDATION**

### **Use psycopg2-binary** (Option A)

**Why**:
1. You already have it (2.9.11)
2. It's battle-tested and stable
3. Bundles all dependencies
4. Only requires 1-line change in addon
5. Works immediately

### **Steps**:

```bash
# 1. Uninstall psycopg v3 (to avoid confusion)
pip uninstall psycopg

# 2. Edit addon_portal/api/core/settings.py line 9:
#    Change "postgresql+psycopg://" to "postgresql+psycopg2://"

# 3. Retry alembic:
cd addon_portal
alembic revision --autogenerate -m "Initial licensing schema"
```

---

## 📝 **ALTERNATE: If You Want psycopg v3**

Install with binary extras:

```bash
pip uninstall psycopg
pip install "psycopg[binary]"
```

Then your connection string stays as-is (postgresql+psycopg://).

---

## ✅ **UPDATED REQUIREMENTS.TXT**

I've already updated Quick2Odoo's requirements.txt to include:

```txt
# PostgreSQL Database Driver (for licensing addon multi-tenancy)
# Use psycopg2-binary for simplicity (requires changing addon connection string)
psycopg2-binary>=2.9.9,<3.0.0
# OR use psycopg v3 with binary extras:
# psycopg[binary]>=3.1.0,<4.0.0
```

**Both options are documented!**

---

## 🚀 **QUICKEST PATH FORWARD**

```bash
# In addon_portal/api/core/settings.py:
DB_DSN: str = "postgresql+psycopg2://user:pass@localhost:5432/q2o"
                         ^^^^^ Just add "2"
```

**That's the only change needed!** Your existing psycopg2-binary will work.

---

**Document Version**: 1.0  
**Last Updated**: November 6, 2025  
**Status**: Quick fix for psycopg import error

