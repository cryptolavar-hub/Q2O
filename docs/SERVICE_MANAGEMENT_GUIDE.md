# Service Management Guide - Quick2Odoo

**Last Updated**: November 8, 2025  
**Version**: 3.0 (Sequential Startup with Dependency Hierarchy)

---

## 🎯 **Quick Reference**

| Action | Command | What It Does |
|--------|---------|--------------|
| **Start All** | `START_ALL.bat` | Starts all services (with intelligent detection) |
| **Stop All** | `STOP_ALL.bat` | Stops all running services gracefully |
| **Restart All** | `RESTART_ALL.bat` | Stops then starts all services |
| **Check Status** | `DATABASE_STATUS.bat` | Check current database configuration |

---

## 🚀 **Starting Services**

### **Command:**
```cmd
START_ALL.bat
```

### **What Happens:**

**Phase 1: Verification (10 checks)**
- ✅ Working directory
- ✅ Git status
- ✅ Python version
- ✅ Dependencies
- ✅ **Service detection** (checks if already running)
- ✅ Database status
- ✅ Dual-stack IPv4/IPv6

**Phase 2: Interactive Options (if services running)**
```
Services already running on ports: 8080, 8000, 3000, 3001, 3002

What would you like to do?
  1 - Skip starting (use existing services)
  2 - Restart all services (stop and restart)
  3 - Start only stopped services

Enter choice (1-3):
```

**Choice 1** - Use Existing:
- Quick exit
- No changes
- Services keep running

**Choice 2** - Restart All:
- Stops services one-by-one (2 second delays)
- Starts all services fresh
- Opens browser windows

**Choice 3** - Selective:
- Skips running services
- Starts only stopped services
- Opens URLs for new services only

**Phase 3: Sequential Service Startup (Dependency Order)**

Services start **one-by-one** in dependency order with 15-second verification:

```
[0/5] PostgreSQL 18 (Database Foundation)
      Dependencies: None (system service)
      Verified: Running on port 5432

[1/5] Licensing API (Port 8080)
      Dependencies: PostgreSQL (5432)
      Starting... Verifying... [OK] Listening on port 8080

[2/5] Dashboard API (Port 8000)
      Dependencies: None (WebSocket backend)
      Starting... Verifying... [OK] Listening on port 8000

[3/5] Tenant Portal (Port 3000)
      Dependencies: Licensing API (8080)
      Starting... Verifying... [OK] Listening on port 3000

[4/5] Dashboard UI (Port 3001)
      Dependencies: Dashboard API (8000)
      Starting... Verifying... [OK] Listening on port 3001

[5/5] Admin Portal (Port 3002)
      Dependencies: Licensing API (8080)
      Starting... Verifying... [OK] Listening on port 3002

Service Startup Summary:
  Services Started: 5
  Services Failed:  0
  Services Skipped: 0
```

**Key Features:**
- ✅ Sequential startup (not parallel)
- ✅ Dependency order respected
- ✅ 15-second verification per service
- ✅ Port listening check (5 attempts × 3 seconds)
- ✅ Fails fast if service won't start

---

## 🛑 **Stopping Services**

### **Command:**
```cmd
STOP_ALL.bat
```

### **What Happens:**

**Phase 1: Detection**
```
PHASE 1: Detecting Running Services...

[RUNNING] Port 8080 - Licensing API
[RUNNING] Port 8000 - Dashboard API
[RUNNING] Port 3000 - Tenant Portal
[RUNNING] Port 3001 - Dashboard UI
[RUNNING] Port 3002 - Admin Portal
[STOPPED] Port 8081 - Mobile App (not running)

Detection Summary:
  Services Running: 5
  Services Stopped: 1

Services to stop:
  - Port 8080 : Licensing API
  - Port 8000 : Dashboard API
  - Port 3000 : Tenant Portal
  - Port 3001 : Dashboard UI
  - Port 3002 : Admin Portal

Stop all running services? (y/n):
```

**Phase 2: Graceful Shutdown (One-by-One)**
```
[1/5] Stopping Licensing API (port 8080)...
  (waits 2 seconds)
  [OK] Licensing API stopped successfully

[2/5] Stopping Dashboard API (port 8000)...
  (waits 2 seconds)
  [OK] Dashboard API stopped successfully

[3/5] Stopping Tenant Portal (port 3000)...
  (waits 2 seconds)
  [OK] Tenant Portal stopped successfully

[4/5] Stopping Dashboard UI (port 3001)...
  (waits 2 seconds)
  [OK] Dashboard UI stopped successfully

[5/5] Stopping Admin Portal (port 3002)...
  (waits 2 seconds)
  [OK] Admin Portal stopped successfully
```

**Phase 3: Verification**
```
PHASE 3: Verifying Shutdown...

[OK] Port 8080 available - Licensing API stopped
[OK] Port 8000 available - Dashboard API stopped
[OK] Port 3000 available - Tenant Portal stopped
[OK] Port 3001 available - Dashboard UI stopped
[OK] Port 3002 available - Admin Portal stopped

Shutdown Summary:
  Services Stopped: 5
  Still Running: 0

ALL SERVICES STOPPED SUCCESSFULLY!
```

**Safety Features:**
- ✅ Only stops services that are running
- ✅ Confirms before stopping
- ✅ Stops one-by-one with 2-second delays
- ✅ Verifies each service stopped
- ✅ Never stops PostgreSQL (system service)
- ✅ Shows warnings if ports still in use

---

## 🔄 **Restarting Services**

### **Command:**
```cmd
RESTART_ALL.bat
```

### **What Happens:**

**Step 1: Stop**
- Runs `STOP_ALL_SERVICES.ps1`
- Graceful shutdown of all services

**Step 2: Wait**
- 3-second delay for clean shutdown

**Step 3: Start**
- Runs `START_ALL_SERVICES.ps1`
- Fresh start of all services

**Use Case:**
- When you updated code
- When configuration changed
- When services are misbehaving

---

## 📊 **Service Status Check**

### **Manual Check:**
```powershell
# Check which ports are listening
netstat -an | findstr "LISTENING" | findstr ":8080 :8000 :3000 :3001 :3002 :5432"

# Check running processes
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"}
```

### **Expected Output (All Running):**
```
TCP    0.0.0.0:3000    LISTENING    (IPv4 - Tenant Portal)
TCP    [::]:3000       LISTENING    (IPv6 - Tenant Portal)
TCP    0.0.0.0:3001    LISTENING    (IPv4 - Dashboard UI)
TCP    [::]:3001       LISTENING    (IPv6 - Dashboard UI)
TCP    0.0.0.0:3002    LISTENING    (IPv4 - Admin Portal)
TCP    [::]:3002       LISTENING    (IPv6 - Admin Portal)
TCP    0.0.0.0:5432    LISTENING    (IPv4 - PostgreSQL)
TCP    [::]:5432       LISTENING    (IPv6 - PostgreSQL)
TCP    0.0.0.0:8000    LISTENING    (IPv4 - Dashboard API)
TCP    [::]:8000       LISTENING    (IPv6 - Dashboard API)
TCP    0.0.0.0:8080    LISTENING    (IPv4 - Licensing API)
TCP    [::]:8080       LISTENING    (IPv6 - Licensing API)
```

---

## 🔧 **Troubleshooting**

### **Issue 1: Services Won't Stop**

**Symptoms**: `STOP_ALL.bat` shows warnings about ports still in use

**Solution**: Force kill processes
```powershell
# Kill all Node.js services
Get-Process | Where-Object {$_.ProcessName -eq "node"} | Stop-Process -Force

# Kill all Python services
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

---

### **Issue 2: Port Already in Use on Start**

**Symptoms**: `START_ALL.bat` detects services running

**Solution**: Choose appropriate option
- **Option 1**: Use existing (fastest)
- **Option 2**: Restart all (clean slate)
- **Option 3**: Start only stopped (selective)

---

### **Issue 3: Services Start But Don't Respond**

**Symptoms**: Ports listening but browser shows errors

**Solution**: Restart services
```cmd
RESTART_ALL.bat
```

---

### **Issue 4: PostgreSQL Won't Stop**

**PostgreSQL is a system service** - not stopped by STOP_ALL script

**To stop PostgreSQL manually:**
```cmd
net stop postgresql-x64-18
```

**To start PostgreSQL manually:**
```cmd
net start postgresql-x64-18
```

---

## 📋 **Service Lifecycle Commands**

### **Complete Lifecycle:**
```cmd
# 1. Start everything
START_ALL.bat

# 2. Work on your project...

# 3. Stop everything
STOP_ALL.bat

# 4. Make changes to code...

# 5. Restart for fresh start
RESTART_ALL.bat
```

### **Selective Control:**
```cmd
# Start only what you need
START_ALL.bat
  → Choose option 3 (start only stopped)

# Stop everything
STOP_ALL.bat
```

---

## 🏗️ **Service Dependency Hierarchy**

Services start in **dependency order** to ensure all requirements are met:

```
┌─────────────────────────────────────────────────────┐
│ Layer 0: Database (Foundation)                      │
│ ┌─────────────────────────────────────┐             │
│ │ PostgreSQL 18 (Port 5432)           │             │
│ │ - System service                     │             │
│ │ - Always running                     │             │
│ └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────┐
│ Layer 1: Backend APIs                               │
│ ┌────────────────────┐    ┌────────────────────┐   │
│ │ Licensing API      │    │ Dashboard API      │   │
│ │ (Port 8080)        │    │ (Port 8000)        │   │
│ │ Depends: PostgreSQL│    │ Depends: None      │   │
│ └────────────────────┘    └────────────────────┘   │
└─────────────────────────────────────────────────────┘
           ▼                            ▼
┌─────────────────────────────────────────────────────┐
│ Layer 2: Frontend Applications                      │
│ ┌────────────────┐ ┌────────────────┐ ┌──────────┐ │
│ │ Tenant Portal  │ │ Dashboard UI   │ │ Admin    │ │
│ │ (Port 3000)    │ │ (Port 3001)    │ │ Portal   │ │
│ │ Depends: 8080  │ │ Depends: 8000  │ │ (3002)   │ │
│ └────────────────┘ └────────────────┘ │ Dep: 8080│ │
│                                        └──────────┘ │
└─────────────────────────────────────────────────────┘
```

**Startup Order (Sequential):**
1. **PostgreSQL** (5432) → Database foundation
2. **Licensing API** (8080) → Requires PostgreSQL
3. **Dashboard API** (8000) → Independent (WebSocket backend)
4. **Tenant Portal** (3000) → Requires Licensing API
5. **Dashboard UI** (3001) → Requires Dashboard API
6. **Admin Portal** (3002) → Requires Licensing API

**Why Sequential?**
- ✅ Dependencies are always met
- ✅ Frontend apps connect to ready APIs
- ✅ Reduces "connection refused" errors
- ✅ Each service gets 15 seconds to stabilize
- ✅ Fail-fast if a dependency won't start

---

## 🌐 **Network Binding Information**

All services use **dual-stack binding** (IPv4 + IPv6):

| Service | IPv4 Bind | IPv6 Bind | Access |
|---------|-----------|-----------|--------|
| Licensing API | 0.0.0.0:8080 | [::]:8080 | localhost:8080 |
| Dashboard API | 0.0.0.0:8000 | [::]:8000 | localhost:8000 |
| Tenant Portal | 0.0.0.0:3000 | [::]:3000 | localhost:3000 |
| Dashboard UI | 0.0.0.0:3001 | [::]:3001 | localhost:3001 |
| Admin Portal | 0.0.0.0:3002 | [::]:3002 | localhost:3002 |
| PostgreSQL 18 | 0.0.0.0:5432 | [::]:5432 | localhost:5432 |

**Benefits:**
- Works on IPv4-only networks
- Works on IPv6-only networks
- Works on dual-stack networks
- Future-proof for IPv6 adoption

---

## ⚡ **Quick Commands**

```cmd
# Start
START_ALL.bat

# Stop
STOP_ALL.bat

# Restart
RESTART_ALL.bat

# Check what's running
netstat -an | findstr "LISTENING" | findstr ":8080 :8000 :3000 :3001 :3002"
```

---

## 📖 **Best Practices**

### **Development Workflow:**
1. Start services once in the morning: `START_ALL.bat`
2. Leave them running while you work
3. Stop when done for the day: `STOP_ALL.bat`

### **After Code Changes:**
1. Use `RESTART_ALL.bat` for clean restart
2. Or manually close/restart specific service window

### **Before Git Commit:**
1. No need to stop services
2. Git operations work with services running

### **Production Deployment:**
- Use systemd (Linux) or Windows Services
- These scripts are for development only

---

## 🎯 **Service Management Features**

✅ **Intelligent Detection** - Knows what's running  
✅ **No Duplicates** - Won't start if already running  
✅ **Graceful Shutdown** - One-by-one with delays  
✅ **Verification** - Confirms each service stopped  
✅ **User Control** - Interactive options  
✅ **Safety** - Never stops PostgreSQL automatically  
✅ **Dual-Stack** - IPv4 + IPv6 on all services  

---

**Document Version**: 1.0  
**Created**: November 7, 2025  
**Status**: Complete ✅

---

**Quick Commands:**
- **Start**: `START_ALL.bat`
- **Stop**: `STOP_ALL.bat`
- **Restart**: `RESTART_ALL.bat`

