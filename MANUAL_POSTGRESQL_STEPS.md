# 🔧 Manual PostgreSQL Installation for Q2O Combined

**Status**: Installation cancelled - Manual setup ready  
**Time Needed**: 30-45 minutes at your pace

---

## 🎯 **Which PostgreSQL Version?**

| Version | Status | Best For |
|---------|--------|----------|
| **PostgreSQL 18** | Latest (Sept 2025) | Cutting edge, newest features |
| **PostgreSQL 17** ⭐ | Stable (Sept 2024) | **RECOMMENDED** - Best balance |
| **PostgreSQL 16** | Very Stable (Sept 2023) | Maximum stability, proven |

**Recommendation**: Use **PostgreSQL 17** for best balance of features and stability.

---

## 📥 **STEP 1: Download PostgreSQL**

### **Official Download Page:**
https://www.postgresql.org/download/windows/

### **Direct Downloads:**

**PostgreSQL 17** (Recommended):
- https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Select: PostgreSQL 17.x for Windows x86-64

**PostgreSQL 18** (Latest):
- https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Select: PostgreSQL 18.x for Windows x86-64

**PostgreSQL 16** (Most Stable):
- https://sbp.enterprisedb.com/getfile.jsp?fileid=1258649

**File Size**: ~300-350 MB

---

## 🔧 **STEP 2: Install PostgreSQL**

### **Installation Settings** (Use These Exact Values):

| Step | Setting | Value |
|------|---------|-------|
| 1. Welcome | | Click "Next" |
| 2. Installation Directory | | `C:\Program Files\PostgreSQL\17` (or 16/18) |
| 3. Select Components | | ✅ PostgreSQL Server<br>✅ pgAdmin 4<br>✅ Stack Builder<br>✅ Command Line Tools |
| 4. Data Directory | | Keep default |
| 5. **Password** ⭐ | postgres user password | **`Q2OPostgres2025!`** |
| 6. Port | | `5432` (default) |
| 7. Locale | | Keep default |
| 8. Summary | | Click "Next" → "Install" |

**Note**: Installation directory will be version-specific (16, 17, or 18)

**IMPORTANT**: 
- ⭐ Use password: **`Q2OPostgres2025!`**
- Write it down!
- You'll need it for database setup

---

## ✅ **STEP 3: Verify Installation**

After installation completes:

```powershell
# Test PostgreSQL is installed (adjust version number as needed)

# For PostgreSQL 17 (recommended):
"C:\Program Files\PostgreSQL\17\bin\psql" --version

# For PostgreSQL 18 (latest):
"C:\Program Files\PostgreSQL\18\bin\psql" --version

# For PostgreSQL 16 (most stable):
"C:\Program Files\PostgreSQL\16\bin\psql" --version

# Should output: psql (PostgreSQL) 17.x (or 16.x/18.x)
```

**Note**: Replace version number in all commands below with your installed version (16, 17, or 18)

---

## 🗄️ **STEP 4: Create Q2O Database**

### **Method A: Using pgAdmin 4 (GUI - Easier)**

1. **Open pgAdmin 4**
   - Start Menu → PostgreSQL (your version) → pgAdmin 4
   - Master password: Same as postgres password

2. **Connect to PostgreSQL Server**
   - Left panel: Servers → PostgreSQL (your version)
   - Right-click → Connect
   - Password: `Q2OPostgres2025!`

3. **Create Database**
   - Right-click "Databases" → Create → Database
   - Name: `q2o`
   - Owner: `postgres`
   - Click "Save"

4. **Create User**
   - Right-click "Login/Group Roles" → Create → Login/Group Role
   - General tab:
     - Name: `q2o_user`
   - Definition tab:
     - Password: `Q2OPostgres2025!`
   - Privileges tab:
     - ✅ Can login?
   - Click "Save"

5. **Grant Permissions**
   - Right-click `q2o` database → Properties
   - Security tab → Click "+"
   - Grantee: `q2o_user`
   - Privileges: Check ALL
   - Click "Save"

### **Method B: Using psql (Command Line)**

```powershell
# Open psql
"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres

# Enter password: Q2OPostgres2025!

# Run these SQL commands:
```

```sql
-- Create database
CREATE DATABASE q2o;

-- Create user
CREATE USER q2o_user WITH PASSWORD 'Q2OPostgres2025!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE q2o TO q2o_user;

-- Connect to q2o database
\c q2o

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO q2o_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO q2o_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO q2o_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO q2o_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO q2o_user;

-- Exit
\q
```

---

## 🔐 **STEP 5: Create .env File**

### **Create file: `addon_portal\.env`**

```bash
# PostgreSQL Configuration (Production)
DB_DSN=postgresql+psycopg2://q2o_user:Q2OPostgres2025!@localhost:5432/q2o

# Application
APP_NAME=Quick2Odoo
ENV=production

# JWT (Update these for production!)
JWT_ISSUER=q2o-auth
JWT_AUDIENCE=q2o-clients
JWT_PRIVATE_KEY=CHANGE_ME_RSA_PRIV_PEM
JWT_PUBLIC_KEY=CHANGE_ME_RSA_PUB_PEM
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600

# Stripe (Update with real keys!)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Activation Codes
ACTIVATION_CODE_PEPPER=CHANGE_ME_ACTIVATION_PEPPER

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://quick2odoo.com

# Session
SESSION_SECRET=CHANGE_ME_SESSION_SECRET
```

**To create this file:**

**Option A: PowerShell**
```powershell
# Copy template
notepad addon_portal\.env

# Paste the content above and save
```

**Option B: CMD**
```cmd
copy addon_portal\env.example.txt addon_portal\.env
notepad addon_portal\.env
# Update the DB_DSN line
```

---

## 🧪 **STEP 6: Seed PostgreSQL Database**

```powershell
cd addon_portal
python quick_setup.py
cd ..
```

**Expected Output:**
```
======================================================================
  Q2O Licensing System - Quick Setup
======================================================================

Database: postgresql+psycopg2://q2o_user:***@localhost:5432/q2o

Creating database tables...
[OK] Tables created successfully

Seeding demo data...
[OK] Created 3 subscription plans
[OK] Created demo tenant: demo
[OK] Created active subscription (Pro - 50 migrations/month)
[OK] Created 3 activation codes:
   XXXX-XXXX-XXXX-XXXX
   XXXX-XXXX-XXXX-XXXX
   XXXX-XXXX-XXXX-XXXX
[OK] Created usage rollup for 2025-11

[SUCCESS] Demo data seeded successfully!
```

---

## 🔄 **STEP 7: Test Both Databases**

### **Test PostgreSQL:**
```powershell
# Make sure .env has PostgreSQL connection
cd addon_portal
python -m uvicorn api.main:app --port 8080

# Visit: http://localhost:8080/docs
# Try health check endpoint
```

### **Switch to SQLite:**
```powershell
# Edit addon_portal\.env
# Change DB_DSN to:
DB_DSN=sqlite:///./q2o_licensing.db

# Restart API
python -m uvicorn api.main:app --port 8080

# Should work with SQLite database
```

### **Switch Back to PostgreSQL:**
```powershell
# Edit addon_portal\.env
# Change DB_DSN back to:
DB_DSN=postgresql+psycopg2://q2o_user:Q2OPostgres2025!@localhost:5432/q2o

# Restart API
```

---

## ✅ **Verification Checklist**

After installation, verify:

- [ ] PostgreSQL 16 installed
- [ ] pgAdmin 4 opens successfully
- [ ] Can connect to PostgreSQL 16 server
- [ ] Database `q2o` exists
- [ ] User `q2o_user` exists
- [ ] Can login with q2o_user
- [ ] File `addon_portal\.env` created
- [ ] `python quick_setup.py` runs successfully
- [ ] 7 tables created in q2o database
- [ ] Demo data seeded
- [ ] Licensing API starts with PostgreSQL
- [ ] Can switch between SQLite and PostgreSQL

---

## 📊 **View Data in pgAdmin 4**

1. Open pgAdmin 4
2. Connect to PostgreSQL 16
3. Expand: Databases → q2o → Schemas → public → Tables
4. Right-click any table → View/Edit Data → First 100 Rows

You should see:
- ✅ 3 subscription plans
- ✅ 1 demo tenant
- ✅ 1 active subscription
- ✅ 3 activation codes
- ✅ 1 usage rollup

---

## 🎯 **After Installation - Tell Me**

Once you've completed the installation, tell me and I will:

1. ✅ Test both database connections
2. ✅ Verify data consistency between SQLite and PostgreSQL
3. ✅ Update startup script to support both
4. ✅ Create switching helper scripts
5. ✅ Document production deployment

---

## 🆘 **Troubleshooting**

### **Can't connect to PostgreSQL**
```powershell
# Check if service is running
sc query postgresql-x64-16

# Start service if stopped
net start postgresql-x64-16
```

### **Port 5432 already in use**
- Another PostgreSQL instance running
- Change port in `postgresql.conf`
- Update `.env` with new port

### **Password authentication failed**
```powershell
# Reset password in pgAdmin 4
# Or via psql:
"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres
ALTER USER q2o_user WITH PASSWORD 'Q2OPostgres2025!';
```

### **Database creation fails**
- Make sure you're connected as `postgres` user
- Check permissions in pgAdmin 4
- Try closing and reopening pgAdmin 4

---

## 📚 **Resources**

- **Full Documentation**: See `POSTGRESQL_SETUP.md`
- **PostgreSQL Docs**: https://www.postgresql.org/docs/16/
- **pgAdmin Docs**: https://www.pgadmin.org/docs/

---

## ⏭️ **Next Steps After You Install**

1. Install PostgreSQL using steps above
2. Create q2o database and user
3. Create `.env` file
4. Run `python quick_setup.py`
5. Tell me it's done
6. I'll verify and set up database switching

---

**Take your time with the installation. When you're done, let me know and I'll complete the setup!** ✅

**Current Status**: 
- ✅ SQLite database working (can use now)
- ⏳ PostgreSQL ready to install manually (at your pace)

