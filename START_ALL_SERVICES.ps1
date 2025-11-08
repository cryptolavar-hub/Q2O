# =========================================================================
# START_ALL_SERVICES.ps1
# Quick2Odoo Combined - Automated Startup Script with Pre-flight Checks
# =========================================================================
# This script:
# 1. Runs comprehensive verification checks
# 2. Starts all services if checks pass
# 3. Opens service URLs in browser
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Quick2Odoo Combined - Automated Startup Script" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# =========================================================================
# PHASE 1: PRE-FLIGHT VERIFICATION CHECKS
# =========================================================================

Write-Host "PHASE 1: Running Pre-flight Verification Checks..." -ForegroundColor Yellow
Write-Host "==========================================================================" -ForegroundColor Gray
Write-Host ""

# Check 1: Verify we're in the correct directory
Write-Host "[1/10] Checking working directory..." -ForegroundColor White
$CurrentDir = Get-Location
if ($CurrentDir.Path -notlike "*Q2O_Combined*") {
    Write-Host "  [ERROR] Not in Q2O_Combined directory!" -ForegroundColor Red
    Write-Host "  Current: $CurrentDir" -ForegroundColor Red
    Write-Host "  Expected: C:\Q2O_Combined" -ForegroundColor Yellow
    $ErrorCount++
} else {
    Write-Host "  [OK] Working directory verified: $CurrentDir" -ForegroundColor Green
}
Write-Host ""

# Check 2: Git status
Write-Host "[2/10] Checking Git status..." -ForegroundColor White
try {
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -eq 0) {
        if ([string]::IsNullOrWhiteSpace($gitStatus)) {
            Write-Host "  [OK] Git working tree is clean" -ForegroundColor Green
        } else {
            Write-Host "  [WARNING] Uncommitted changes detected:" -ForegroundColor Yellow
            git status -s | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
            $WarningCount++
        }
    } else {
        Write-Host "  [ERROR] Git command failed" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "  [ERROR] Git not available: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}
Write-Host ""

# Check 3: Git remote
Write-Host "[3/10] Checking Git remote..." -ForegroundColor White
try {
    $gitRemote = git remote -v 2>&1 | Select-String "origin.*github.com/cryptolavar-hub/Q2O"
    if ($gitRemote) {
        Write-Host "  [OK] Git remote configured correctly" -ForegroundColor Green
        Write-Host "    $gitRemote" -ForegroundColor Gray
    } else {
        Write-Host "  [WARNING] Git remote not configured as expected" -ForegroundColor Yellow
        git remote -v | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        $WarningCount++
    }
} catch {
    Write-Host "  [ERROR] Could not check Git remote: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}
Write-Host ""

# Check 4: Python version
Write-Host "[4/10] Checking Python version..." -ForegroundColor White
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        $patch = [int]$Matches[3]
        
        if ($major -eq 3 -and $minor -ge 10) {
            Write-Host "  [OK] Python $major.$minor.$patch (supported: 3.10-3.13)" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Python $major.$minor.$patch not supported (need 3.10+)" -ForegroundColor Red
            $ErrorCount++
        }
    } else {
        Write-Host "  [ERROR] Could not parse Python version" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "  [ERROR] Python not found: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}
Write-Host ""

# Check 5: Required directories
Write-Host "[5/10] Checking required directories..." -ForegroundColor White
$RequiredDirs = @(
    "agents",
    "api",
    "addon_portal",
    "mobile",
    "docs",
    "config"
)
$MissingDirs = @()
foreach ($dir in $RequiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  [OK] Found: $dir" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing: $dir" -ForegroundColor Red
        $MissingDirs += $dir
        $ErrorCount++
    }
}
Write-Host ""

# Check 6: Required files
Write-Host "[6/10] Checking required files..." -ForegroundColor White
$RequiredFiles = @(
    "main.py",
    "requirements.txt",
    "README.md",
    "config.json",
    "addon_portal\q2o_licensing.db"
)
$MissingFiles = @()
foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] Found: $file" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing: $file" -ForegroundColor Red
        $MissingFiles += $file
        $ErrorCount++
    }
}
Write-Host ""

# Check 7: Python dependencies
Write-Host "[7/10] Checking Python dependencies..." -ForegroundColor White
$CriticalPackages = @("fastapi", "uvicorn", "pydantic", "sqlalchemy", "alembic")
$MissingPackages = @()
foreach ($pkg in $CriticalPackages) {
    try {
        $result = python -c "import $pkg" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Installed: $pkg" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Missing: $pkg" -ForegroundColor Red
            $MissingPackages += $pkg
            $ErrorCount++
        }
    } catch {
        Write-Host "  [ERROR] Could not check: $pkg" -ForegroundColor Red
        $MissingPackages += $pkg
        $ErrorCount++
    }
}
if ($MissingPackages.Count -gt 0) {
    Write-Host "  [INFO] To install missing packages: pip install -r requirements.txt" -ForegroundColor Yellow
}
Write-Host ""

# Check 8: Node.js availability
Write-Host "[8/10] Checking Node.js availability..." -ForegroundColor White
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Node.js $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Node.js not found (needed for frontend/mobile)" -ForegroundColor Yellow
        $WarningCount++
    }
} catch {
    Write-Host "  [WARNING] Node.js not available: $($_.Exception.Message)" -ForegroundColor Yellow
    $WarningCount++
}
Write-Host ""

# Check 9: Port availability
Write-Host "[9/10] Checking port availability..." -ForegroundColor White
$Ports = @(8080, 8000, 3000, 8081)
$PortsInUse = @()
foreach ($port in $Ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "  [WARNING] Port $port is already in use" -ForegroundColor Yellow
        $PortsInUse += $port
        $WarningCount++
    } else {
        Write-Host "  [OK] Port $port is available" -ForegroundColor Green
    }
}
Write-Host ""

# Check 10: Licensing database
Write-Host "[10/10] Checking licensing database..." -ForegroundColor White

# Check if .env exists and determine database type
$envPath = "addon_portal\.env"
$usingPostgreSQL = $false
$usingSQLite = $false

if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    if ($envContent -match "postgresql") {
        $usingPostgreSQL = $true
        Write-Host "  [INFO] Using PostgreSQL database" -ForegroundColor Cyan
        
        # Check if PostgreSQL service is running
        $pgService = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
        if ($pgService) {
            if ($pgService.Status -eq "Running") {
                Write-Host "  [OK] PostgreSQL 18 service is running" -ForegroundColor Green
            } else {
                Write-Host "  [WARNING] PostgreSQL 18 service is stopped" -ForegroundColor Yellow
                Write-Host "  [INFO] Start with: net start postgresql-x64-18" -ForegroundColor Yellow
                $WarningCount++
            }
        } else {
            Write-Host "  [WARNING] PostgreSQL 18 service not found" -ForegroundColor Yellow
            $WarningCount++
        }
    } elseif ($envContent -match "sqlite") {
        $usingSQLite = $true
        Write-Host "  [INFO] Using SQLite database" -ForegroundColor Cyan
        
        if (Test-Path "addon_portal\q2o_licensing.db") {
            $dbSize = (Get-Item "addon_portal\q2o_licensing.db").Length
            if ($dbSize -gt 0) {
                Write-Host "  [OK] SQLite database exists ($([math]::Round($dbSize/1KB, 2)) KB)" -ForegroundColor Green
            } else {
                Write-Host "  [ERROR] SQLite database is empty" -ForegroundColor Red
                $ErrorCount++
            }
        } else {
            Write-Host "  [ERROR] SQLite database not found" -ForegroundColor Red
            Write-Host "  [INFO] Run: cd addon_portal; python quick_setup.py" -ForegroundColor Yellow
            $ErrorCount++
        }
    }
} else {
    Write-Host "  [WARNING] .env file not found, checking default SQLite" -ForegroundColor Yellow
    $usingSQLite = $true
    
    if (Test-Path "addon_portal\q2o_licensing.db") {
        $dbSize = (Get-Item "addon_portal\q2o_licensing.db").Length
        Write-Host "  [OK] SQLite database exists ($([math]::Round($dbSize/1KB, 2)) KB)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] SQLite database not found" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# =========================================================================
# VERIFICATION SUMMARY
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Verification Summary" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Errors:   $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Red" })
Write-Host "  Warnings: $WarningCount" -ForegroundColor $(if ($WarningCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

# =========================================================================
# DECISION: PROCEED OR ABORT
# =========================================================================

if ($ErrorCount -gt 0) {
    Write-Host "==========================================================================" -ForegroundColor Red
    Write-Host "  VERIFICATION FAILED - Cannot start services" -ForegroundColor Red
    Write-Host "==========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the errors above and run this script again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor White
    Write-Host "  - Install Python 3.10+: https://www.python.org/downloads/" -ForegroundColor Gray
    Write-Host "  - Install dependencies: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "  - Setup database: cd addon_portal; python quick_setup.py" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

if ($WarningCount -gt 0) {
    Write-Host "Warnings detected. Continue anyway? (y/n): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Startup cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "==========================================================================" -ForegroundColor Green
Write-Host "  ALL CHECKS PASSED - Starting services..." -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Green
Write-Host ""

# =========================================================================
# PHASE 2: START ALL SERVICES
# =========================================================================

Write-Host "PHASE 2: Starting Services..." -ForegroundColor Yellow
Write-Host "==========================================================================" -ForegroundColor Gray
Write-Host ""

# Function to start service in new window
function Start-ServiceInWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDir = (Get-Location).Path
    )
    
    Write-Host "Starting: $Title" -ForegroundColor Cyan
    Write-Host "  Command: $Command" -ForegroundColor Gray
    Write-Host "  Directory: $WorkingDir" -ForegroundColor Gray
    
    $scriptBlock = @"
Set-Location '$WorkingDir'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ' $Title' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
$Command
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptBlock
    Start-Sleep -Seconds 2
    Write-Host "  [OK] Started in new window" -ForegroundColor Green
    Write-Host ""
}

# Service 1: Licensing API (Port 8080)
Write-Host "[1/4] Licensing API..." -ForegroundColor White
$licensingDir = Join-Path $CurrentDir.Path "addon_portal"
Start-ServiceInWindow -Title "Licensing API (Port 8080)" `
                       -Command "python -m uvicorn api.main:app --host :: --port 8080" `
                       -WorkingDir $licensingDir

# Service 2: Core API / Dashboard (Port 8000)
Write-Host "[2/4] Core API / Dashboard..." -ForegroundColor White
Start-ServiceInWindow -Title "Core API / Dashboard (Port 8000)" `
                       -Command "python -m uvicorn api.dashboard.main:app --host :: --port 8000" `
                       -WorkingDir $CurrentDir.Path

# Service 3: Tenant Portal Frontend (Port 3000)
Write-Host "[3/4] Tenant Portal Frontend..." -ForegroundColor White
if (Test-Path "node" -PathType Leaf) {
    $tenantPortalDir = Join-Path $CurrentDir.Path "addon_portal\apps\tenant-portal"
    if (Test-Path "$tenantPortalDir\node_modules") {
        Start-ServiceInWindow -Title "Tenant Portal (Port 3000)" `
                               -Command "npm run dev" `
                               -WorkingDir $tenantPortalDir
    } else {
        Write-Host "  [INFO] Installing npm dependencies first..." -ForegroundColor Yellow
        Start-ServiceInWindow -Title "Tenant Portal (Port 3000)" `
                               -Command "npm install; npm run dev" `
                               -WorkingDir $tenantPortalDir
    }
} else {
    Write-Host "  [SKIP] Node.js not available" -ForegroundColor Yellow
}

# Service 4: Mobile App (Metro Bundler)
Write-Host "[4/4] Mobile App (Metro Bundler)..." -ForegroundColor White
if (Test-Path "node" -PathType Leaf) {
    $mobileDir = Join-Path $CurrentDir.Path "mobile"
    Write-Host "  [INFO] Mobile app requires manual platform selection" -ForegroundColor Yellow
    Write-Host "  [INFO] After Metro starts, run: npm run android OR npm run ios" -ForegroundColor Yellow
    
    if (Test-Path "$mobileDir\node_modules") {
        Start-ServiceInWindow -Title "Mobile App (Metro Bundler)" `
                               -Command "npm start" `
                               -WorkingDir $mobileDir
    } else {
        Write-Host "  [INFO] Installing npm dependencies first..." -ForegroundColor Yellow
        Start-ServiceInWindow -Title "Mobile App (Metro Bundler)" `
                               -Command "npm install; npm start" `
                               -WorkingDir $mobileDir
    }
} else {
    Write-Host "  [SKIP] Node.js not available" -ForegroundColor Yellow
}

Write-Host ""

# =========================================================================
# PHASE 3: OPEN SERVICE URLS
# =========================================================================

if (-not $SkipStartup) {
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10

    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Opening Service URLs in Browser..." -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""

    # Open URLs for newly started services
    if (-not ($PortsInUse -contains 8080)) {
        Write-Host "Opening Licensing API documentation..." -ForegroundColor White
        Start-Process "http://localhost:8080/docs"
        Start-Sleep -Seconds 2
    }

    if (-not ($PortsInUse -contains 8000)) {
        Write-Host "Opening Dashboard API documentation..." -ForegroundColor White
        Start-Process "http://localhost:8000/docs"
        Start-Sleep -Seconds 2
    }

    if (-not ($PortsInUse -contains 3000)) {
        Write-Host "Opening Tenant Portal..." -ForegroundColor White
        Start-Process "http://localhost:3000"
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Green
    Write-Host "  Using Existing Services - No URLs opened" -ForegroundColor Green
    Write-Host "==========================================================================" -ForegroundColor Green
}

Write-Host ""

# =========================================================================
# FINAL SUMMARY
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Green
Write-Host "  ALL SERVICES STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor White
Write-Host "  1. Licensing API:      http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "  2. Dashboard API:      http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  3. Tenant Portal:      http://localhost:3000" -ForegroundColor Cyan
Write-Host "  4. Mobile (Metro):     Check the Mobile App window" -ForegroundColor Cyan
Write-Host ""
Write-Host "Demo Credentials:" -ForegroundColor White
Write-Host "  Tenant Slug:           demo" -ForegroundColor Gray
Write-Host "  Activation Code:       12RY-S55W-4MZR-KP2J" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services:" -ForegroundColor White
Write-Host "  - Close each PowerShell window" -ForegroundColor Gray
Write-Host "  - Or press Ctrl+C in each window" -ForegroundColor Gray
Write-Host ""
Write-Host "==========================================================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close this window (services will continue running)"
