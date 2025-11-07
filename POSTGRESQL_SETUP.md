# PostgreSQL Setup for Q2O Combined (Production)

**Objective**: Install and configure PostgreSQL 16 for production deployment

**Status**: 🔄 In Progress  
**Priority**: HIGH (Production Requirement)

---

## 🎯 Why PostgreSQL?

- ✅ **Production-grade**: Handles concurrent connections, large datasets
- ✅ **ACID compliance**: Data integrity and transactions
- ✅ **Scalability**: Supports millions of records
- ✅ **Backup/Recovery**: Enterprise-level data protection
- ✅ **Multi-tenant**: Perfect for licensing system with multiple tenants

**SQLite**: Great for development/testing, but not for production with multiple users

---

## 📥 Step 1: Download PostgreSQL

### **Option A: Official Installer (Recommended)**

1. Visit: https://www.postgresql.org/download/windows/
2. Click **"Download the installer"**
3. Download **PostgreSQL 16.x** (latest stable)
4. File: `postgresql-16.x-x-windows-x64.exe` (~300 MB)

### **Option B: Direct Link**

Download PostgreSQL 16.1:
- https://sbp.enterprisedb.com/getfile.jsp?fileid=1258649

---

## 🔧 Step 2: Install PostgreSQL

### **Installation Steps:**

1. **Run Installer** as Administrator
   - Right-click `postgresql-16.x-x-windows-x64.exe` → Run as Administrator

2. **Installation Directory** (Default is fine)
   - `C:\Program Files\PostgreSQL\16`

3. **Select Components** (Check all):
   - ✅ PostgreSQL Server
   - ✅ pgAdmin 4 (GUI management tool)
   - ✅ Stack Builder (optional)
   - ✅ Command Line Tools

4. **Data Directory** (Default is fine)
   - `C:\Program Files\PostgreSQL\16\data`

5. **Password** ⭐ **IMPORTANT**
   - Set password for `postgres` superuser
   - **REMEMBER THIS PASSWORD!** You'll need it.
   - Example: `Q2OPostgres2025!`
   - Write it down!

6. **Port** (Default: 5432)
   - Keep default: `5432`

7. **Locale** (Default)
   - Keep default locale

8. **Complete Installation**
   - Click **Next** → **Install** → **Finish**

---

## ✅ Step 3: Verify Installation

### **Open Command Prompt and test:**

```cmd
# Check if PostgreSQL is running
"C:\Program Files\PostgreSQL\16\bin\psql" --version

# Should output:
# psql (PostgreSQL) 16.1
```

### **Connect to PostgreSQL:**

```cmd
# Connect as postgres superuser
"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres

# Enter the password you set during installation
# You should see: postgres=#
```

If this works, PostgreSQL is installed correctly! ✅

Type `\q` to exit psql.

---

## 🗄️ Step 4: Create Q2O Database

### **Method 1: Using psql (Command Line)**

```cmd
# Connect to PostgreSQL
"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres

# Run these SQL commands:
```

```sql
-- Create the database
CREATE DATABASE q2o;

-- Create a dedicated user for Q2O
CREATE USER q2o_user WITH PASSWORD 'YOUR_SECURE_PASSWORD_HERE';

-- Grant all privileges to q2o_user on q2o database
GRANT ALL PRIVILEGES ON DATABASE q2o TO q2o_user;

-- Connect to q2o database
\c q2o

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO q2o_user;

-- Exit
\q
```

### **Method 2: Using pgAdmin 4 (GUI)**

1. **Open pgAdmin 4** (Start Menu → PostgreSQL 16 → pgAdmin 4)
2. **Connect** to PostgreSQL 16 server
   - Enter your postgres password
3. **Create Database**:
   - Right-click "Databases" → Create → Database
   - Name: `q2o`
   - Owner: `postgres`
   - Save
4. **Create User**:
   - Right-click "Login/Group Roles" → Create → Login/Group Role
   - General → Name: `q2o_user`
   - Definition → Password: `YOUR_SECURE_PASSWORD_HERE`
   - Privileges → Check "Can login?"
   - Save
5. **Grant Permissions**:
   - Right-click `q2o` database → Properties → Security
   - Click + to add privilege
   - Grantee: `q2o_user`
   - Privileges: ALL
   - Save

---

## 🔐 Step 5: Configure Q2O to Use PostgreSQL

### **Create `.env` file in `addon_portal/` directory:**

```bash
# Database Configuration (PostgreSQL)
DB_DSN=postgresql+psycopg2://q2o_user:YOUR_SECURE_PASSWORD_HERE@localhost:5432/q2o

# JWT Configuration
JWT_ISSUER=q2o-auth
JWT_AUDIENCE=q2o-clients
JWT_PRIVATE_KEY=CHANGE_ME_RSA_PRIV_PEM
JWT_PUBLIC_KEY=CHANGE_ME_RSA_PUB_PEM
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Activation Code Configuration
ACTIVATION_CODE_PEPPER=CHANGE_ME_ACTIVATION_PEPPER

# Session Configuration
SESSION_SECRET=CHANGE_ME_SESSION_SECRET

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://quick2odoo.com
```

**Replace**:
- `YOUR_SECURE_PASSWORD_HERE` → Your actual password for `q2o_user`

---

## 🧪 Step 6: Test PostgreSQL Connection

### **Run the database setup script:**

```cmd
cd C:\Q2O_Combined\addon_portal
python quick_setup.py
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
======================================================================
```

If you see this, **PostgreSQL is working!** ✅

---

## 🚀 Step 7: Start Services with PostgreSQL

```cmd
cd C:\Q2O_Combined
START_ALL.bat
```

All services will now use PostgreSQL instead of SQLite!

---

## 🔄 Switching Between SQLite (Dev) and PostgreSQL (Production)

### **Development Mode (SQLite)**
```bash
# In addon_portal/.env
DB_DSN=sqlite:///./q2o_licensing.db
```

### **Production Mode (PostgreSQL)**
```bash
# In addon_portal/.env
DB_DSN=postgresql+psycopg2://q2o_user:password@localhost:5432/q2o
```

The system automatically detects which database to use based on `.env` file!

---

## 📊 Step 8: Verify PostgreSQL Data

### **Using pgAdmin 4:**
1. Open pgAdmin 4
2. Connect to PostgreSQL 16
3. Expand: Databases → q2o → Schemas → public → Tables
4. You should see:
   - ✅ tenants
   - ✅ plans
   - ✅ subscriptions
   - ✅ devices
   - ✅ activation_codes
   - ✅ usage_events
   - ✅ monthly_usage_rollups

### **Using psql:**
```cmd
"C:\Program Files\PostgreSQL\16\bin\psql" -U q2o_user -d q2o

# List tables
\dt

# Count tenants
SELECT COUNT(*) FROM tenants;

# View activation codes
SELECT * FROM activation_codes;

# Exit
\q
```

---

## 🛡️ Security Best Practices

### **1. Strong Passwords**
- Database password: 20+ characters, mixed case, numbers, symbols
- Never commit passwords to git
- Use environment variables

### **2. Network Security**
- Firewall: Only allow connections from localhost (development)
- Production: Use SSL/TLS connections
- Restrict PostgreSQL to specific IP addresses

### **3. Backup Strategy**
```cmd
# Backup database
"C:\Program Files\PostgreSQL\16\bin\pg_dump" -U q2o_user -d q2o -F c -f q2o_backup.dump

# Restore database
"C:\Program Files\PostgreSQL\16\bin\pg_restore" -U q2o_user -d q2o -F c q2o_backup.dump
```

### **4. Regular Maintenance**
```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Check database size
SELECT pg_size_pretty(pg_database_size('q2o'));
```

---

## 🔧 Troubleshooting

### **Issue 1: "psql: command not found"**
**Solution**: Add PostgreSQL to PATH
```cmd
setx PATH "%PATH%;C:\Program Files\PostgreSQL\16\bin"
```
Restart Command Prompt.

### **Issue 2: "Connection refused"**
**Solution**: Check if PostgreSQL service is running
```cmd
# Check service status
sc query postgresql-x64-16

# Start service
net start postgresql-x64-16
```

### **Issue 3: "password authentication failed"**
**Solution**: Reset password
```cmd
# Connect as postgres
"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres

# Reset password
ALTER USER q2o_user WITH PASSWORD 'new_password';
```

### **Issue 4: "FATAL: database does not exist"**
**Solution**: Create database
```cmd
"C:\Program Files\PostgreSQL\16\bin\createdb" -U postgres q2o
```

### **Issue 5: Port 5432 already in use**
**Solution**: Change PostgreSQL port
1. Open `C:\Program Files\PostgreSQL\16\data\postgresql.conf`
2. Change `port = 5432` to `port = 5433`
3. Restart PostgreSQL service
4. Update `.env` with new port

---

## 📋 Checklist

- [ ] PostgreSQL 16 downloaded
- [ ] PostgreSQL installed with pgAdmin 4
- [ ] postgres superuser password set and saved
- [ ] PostgreSQL service running
- [ ] psql command works
- [ ] q2o database created
- [ ] q2o_user created with password
- [ ] Permissions granted to q2o_user
- [ ] .env file created with PostgreSQL connection string
- [ ] quick_setup.py ran successfully
- [ ] Tables created in PostgreSQL
- [ ] Demo data seeded
- [ ] pgAdmin 4 shows all tables
- [ ] Startup script runs with PostgreSQL

---

## 🎉 Success Criteria

You know PostgreSQL is set up correctly when:

1. ✅ `psql --version` shows PostgreSQL 16.x
2. ✅ pgAdmin 4 shows `q2o` database with 7 tables
3. ✅ `quick_setup.py` completes without errors
4. ✅ `START_ALL.bat` verifications pass
5. ✅ Licensing API connects to PostgreSQL
6. ✅ Tenant portal loads demo tenant data

---

## 🚀 Next Steps After PostgreSQL Setup

1. **Backup**: Set up automated daily backups
2. **Monitoring**: Configure pgAdmin alerts
3. **Optimization**: Tune PostgreSQL for production
4. **SSL**: Enable encrypted connections
5. **Replication**: Set up standby server (high availability)

---

## 📚 Resources

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/16/
- **pgAdmin Documentation**: https://www.pgadmin.org/docs/
- **SQLAlchemy + PostgreSQL**: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- **Production Checklist**: https://www.postgresql.org/docs/16/runtime-config.html

---

**Document Version**: 1.0  
**Created**: November 7, 2025  
**Status**: Ready for implementation  
**Estimated Time**: 30-45 minutes

---

**Ready to install? Follow Steps 1-8 above!** 🚀

