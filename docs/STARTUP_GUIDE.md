# 🚀 Quick2Odoo Startup Guide

**Quick Start**: Just double-click `START_ALL.bat` and everything happens automatically!

---

## ✨ **What the Startup Script Does**

### **Phase 1: Verification Checks (10 checks)**
1. ✅ Working directory verification
2. ✅ Git status check
3. ✅ Git remote configuration
4. ✅ Python version (3.10-3.13)
5. ✅ Required directories (agents/, api/, etc.)
6. ✅ Required files (main.py, config.json, etc.)
7. ✅ Python dependencies (fastapi, uvicorn, etc.)
8. ✅ Node.js availability
9. ✅ Port availability (8080, 8000, 3000, 8081)
10. ✅ Licensing database exists and valid

### **Phase 2: Start Services (if checks pass)**
1. 🔐 **Licensing API** (Port 8080)
2. 📊 **Dashboard API** (Port 8000)
3. 🎨 **Tenant Portal** (Port 3000)
4. 📱 **Mobile App** (Metro Bundler)

### **Phase 3: Open Browser**
- Automatically opens all service URLs in your default browser
- Shows admin pages and API documentation

---

## 🎯 **How to Use**

### **Option 1: Double-Click (Easiest)**
```
Just double-click: START_ALL.bat
```

### **Option 2: Command Line**
```cmd
START_ALL.bat
```

### **Option 3: PowerShell Direct**
```powershell
.\START_ALL_SERVICES.ps1
```

---

## 📊 **What to Expect**

### **If Everything Passes:**
```
==========================================================================
  ALL CHECKS PASSED - Starting services...
==========================================================================

[1/4] Licensing API...
  [OK] Started in new window

[2/4] Core API / Dashboard...
  [OK] Started in new window

[3/4] Tenant Portal Frontend...
  [OK] Started in new window

[4/4] Mobile App...
  [OK] Started in new window

==========================================================================
  ALL SERVICES STARTED SUCCESSFULLY!
==========================================================================
```

**Result**: 4-5 new PowerShell windows will open, each running a service.

### **If Verification Fails:**
```
==========================================================================
  VERIFICATION FAILED - Cannot start services
==========================================================================

  Errors: 2

Please fix the errors above and run this script again.
```

**Result**: Script stops, shows what needs to be fixed.

---

## 🔧 **Common Issues & Fixes**

### **Issue 1: Python not found**
```
[ERROR] Python not found
```
**Fix**: Install Python 3.10+ from https://www.python.org/downloads/

### **Issue 2: Missing dependencies**
```
[ERROR] Missing: fastapi
```
**Fix**: Run `pip install -r requirements.txt`

### **Issue 3: Database missing**
```
[ERROR] Licensing database not found
```
**Fix**: Run setup:
```cmd
cd addon_portal
python quick_setup.py
```

### **Issue 4: Ports already in use**
```
[WARNING] Port 8080 is already in use
```
**Fix**: Stop services using those ports, or change ports in config files.

### **Issue 5: Node.js not found**
```
[WARNING] Node.js not found
```
**Fix**: Install Node.js 20.x LTS from https://nodejs.org/
- Frontend and Mobile services will be skipped if Node.js is not available
- Backend services (Python) will still start

### **Issue 6: PowerShell execution policy**
```
cannot be loaded because running scripts is disabled
```
**Fix**: Run as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🌐 **Service URLs**

After startup completes, access services here:

| Service | URL | Description |
|---------|-----|-------------|
| **Licensing API** | http://localhost:8080/docs | FastAPI admin interface |
| **Dashboard API** | http://localhost:8000/docs | Real-time monitoring API |
| **Tenant Portal** | http://localhost:3000 | Customer-facing portal |
| **Mobile Metro** | Terminal only | React Native bundler |

---

## 🎫 **Demo Credentials**

Use these to test the Licensing API:

- **Tenant Slug**: `demo`
- **Activation Codes**:
  - `12RY-S55W-4MZR-KP2J`
  - `RAH5-YRGA-4P38-AIJ4`
  - `HVZ7-E8GB-DV6W-03EW`

---

## 🛑 **How to Stop Services**

### **Option 1: Close Windows**
Close each PowerShell window (4-5 windows)

### **Option 2: Ctrl+C**
Press `Ctrl+C` in each PowerShell window

### **Option 3: Kill All (Emergency)**
```powershell
# Stop all uvicorn processes
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"} | Stop-Process -Force

# Stop all node processes
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force
```

---

## 📋 **Verification Checklist**

The script checks these automatically, but here's what it's looking for:

- [ ] Working directory is `C:\Q2O_Combined`
- [ ] Git repository initialized and clean
- [ ] Python 3.10-3.13 installed
- [ ] All required directories exist
- [ ] All required files exist
- [ ] Python dependencies installed
- [ ] Node.js available (optional)
- [ ] Ports 8080, 8000, 3000, 8081 available
- [ ] Licensing database exists and valid

---

## 🎨 **What You'll See**

### **1. Licensing API (Port 8080)**
- FastAPI Swagger documentation
- License management endpoints
- Device activation
- Usage tracking

### **2. Dashboard API (Port 8000)**
- WebSocket connection status
- Real-time metrics
- System health monitoring

### **3. Tenant Portal (Port 3000)**
- **NEW STYLING!** Pink-to-purple gradient background
- White cards with shadows
- Green gradient buttons
- Modern responsive UI

### **4. Mobile App (Metro)**
- React Native bundler
- Run `npm run android` or `npm run ios` to launch
- QR code for Expo Go testing

---

## 🔄 **Restart Services**

To restart everything:

1. Stop all services (close windows or Ctrl+C)
2. Run `START_ALL.bat` again

To restart just one service:

```powershell
# Licensing API
cd addon_portal
python -m uvicorn api.main:app --port 8080

# Dashboard API
python -m uvicorn api.dashboard.main:app --port 8000

# Tenant Portal
cd addon_portal/apps/tenant-portal
npm run dev

# Mobile App
cd mobile
npm start
```

---

## 📖 **Next Steps After Startup**

### **1. Test Licensing API**
- Visit: http://localhost:8080/docs
- Try GET `/api/v1/health` endpoint
- Test activation with demo codes

### **2. Test Tenant Portal**
- Visit: http://localhost:3000
- Check the new pink-to-purple gradient styling
- Explore branding preview and usage meters

### **3. Test Dashboard**
- Visit: http://localhost:8000/docs
- Try WebSocket connection
- View real-time metrics

### **4. Run a Migration**
```bash
python main.py --project "Test Migration" --objective "Test feature"
```

---

## 🎯 **Troubleshooting Tips**

### **Services start but pages don't load?**
- Wait 30 seconds for services to fully initialize
- Check PowerShell windows for error messages
- Verify ports in browser DevTools (F12)

### **Tenant Portal shows errors?**
- Check if Node.js version is 18.x or 20.x
- Run `npm install` in `addon_portal/apps/tenant-portal/`
- Check `.env.example` for required environment variables

### **Mobile app won't start?**
- Ensure Android SDK or Xcode is installed
- Check React Native environment setup
- Try `npm cache clean --force` then `npm install`

### **Database errors?**
- Verify `addon_portal/q2o_licensing.db` exists
- If corrupt, run setup again:
  ```bash
  cd addon_portal
  python quick_setup.py
  ```

---

## 📚 **Additional Resources**

- **Full Session Context**: `SESSION_HANDOFF_NOV_7_2025.md`
- **Quick Start Guide**: `QUICK_START_HERE.md`
- **Main Documentation**: `README.md`
- **Architecture Guide**: `docs/COMPLETE_SYSTEM_WORKFLOW.md`

---

## ✅ **Success Criteria**

You know everything is working when:

1. ✅ All 10 verification checks pass
2. ✅ 4-5 PowerShell windows open successfully
3. ✅ Browser opens 3 tabs automatically
4. ✅ Licensing API shows Swagger UI
5. ✅ Dashboard API shows documentation
6. ✅ Tenant Portal shows pink-to-purple gradient
7. ✅ No error messages in PowerShell windows

---

**Created**: November 7, 2025  
**Version**: 1.0  
**Status**: Ready to use! 🚀

---

**Quick Command**: `START_ALL.bat` ← Just run this!

