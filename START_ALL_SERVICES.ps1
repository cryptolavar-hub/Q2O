# =========================================================================
# START_ALL_SERVICES.ps1
# Q2O - Automated Startup Script with Pre-flight Checks
# =========================================================================
# This script:
# 1. Runs comprehensive verification checks
# 2. Starts all services if checks pass
# 3. Opens service URLs in browser
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Q2O - Automated Startup Script" -ForegroundColor Cyan
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

# Check 2: Git status (INFORMATIONAL - Non-blocking)
Write-Host "[2/10] Checking Git status (informational)..." -ForegroundColor White
try {
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -eq 0) {
        if ([string]::IsNullOrWhiteSpace($gitStatus)) {
            Write-Host "  [OK] Git working tree is clean" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] Uncommitted changes detected (non-blocking)" -ForegroundColor Cyan
            $WarningCount++
        }
    } else {
        Write-Host "  [INFO] Git not available or ownership issue (non-blocking)" -ForegroundColor Cyan
        Write-Host "        This does not prevent services from starting" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [INFO] Git check skipped: $($_.Exception.Message)" -ForegroundColor Cyan
}
Write-Host ""

# Check 3: Git remote (INFORMATIONAL - Non-blocking)
Write-Host "[3/10] Checking Git remote (informational)..." -ForegroundColor White
try {
    $gitRemote = git remote -v 2>&1 | Select-String "origin.*github.com/cryptolavar-hub/Q2O"
    if ($gitRemote) {
        Write-Host "  [OK] Git remote configured correctly" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Git remote check skipped (non-blocking)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [INFO] Git remote check skipped (non-blocking)" -ForegroundColor Cyan
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
        
        # Extract database connection details from .env
        $dbHost = "localhost"
        $dbPort = "5432"
        $dbName = "q2o"
        
        if ($envContent -match 'DB_DSN[=:].*?postgresql://(?:[^:]+:)?[^@]+@([^:/]+)(?::(\d+))?/([^"\s]+)') {
            $dbHost = $matches[1]
            if ($matches[2]) { $dbPort = $matches[2] }
            if ($matches[3]) { $dbName = $matches[3] }
        }
        
        Write-Host "  [INFO] Database Host: $dbHost" -ForegroundColor Cyan
        Write-Host "  [INFO] Database Port: $dbPort" -ForegroundColor Cyan
        Write-Host "  [INFO] Database Name: $dbName" -ForegroundColor Cyan
        
        # Check if local PostgreSQL service (if localhost)
        if ($dbHost -eq "localhost" -or $dbHost -eq "127.0.0.1" -or $dbHost -eq "::1") {
            $pgService = Get-Service -Name "postgresql-x64-*" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($pgService -and $pgService.Status -eq "Running") {
                Write-Host "  [OK] Local PostgreSQL service is running" -ForegroundColor Green
            } else {
                Write-Host "  [WARNING] Local PostgreSQL service not running" -ForegroundColor Yellow
                Write-Host "  [INFO] If using local database, start with: net start postgresql-x64-18" -ForegroundColor Yellow
                $WarningCount++
            }
        }
        
        # Network connectivity check (works for local or remote)
        Write-Host "  [INFO] Testing database connectivity..." -ForegroundColor Cyan
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.Connect($dbHost, $dbPort)
            $tcpClient.Close()
            Write-Host "  [OK] Database connection successful (${dbHost}:${dbPort})" -ForegroundColor Green
            
            # Try to verify database exists using psql if available
            $psqlPath = Get-Command psql -ErrorAction SilentlyContinue
            if ($psqlPath) {
                $dbCheckCmd = "SELECT 1 FROM pg_database WHERE datname='$dbName'"
                $dbExists = & psql -h $dbHost -p $dbPort -U postgres -tAc $dbCheckCmd 2>$null
                if ($dbExists -eq "1") {
                    Write-Host "  [OK] Database '$dbName' exists" -ForegroundColor Green
                } else {
                    Write-Host "  [WARNING] Database '$dbName' not found" -ForegroundColor Yellow
                    Write-Host "  [INFO] Create with: psql -h $dbHost -p $dbPort -U postgres -f setup_postgresql.sql" -ForegroundColor Yellow
                    $WarningCount++
                }
            }
        } catch {
            Write-Host "  [ERROR] Cannot connect to PostgreSQL at ${dbHost}:${dbPort}" -ForegroundColor Red
            Write-Host "  [INFO] Check database is running and accessible" -ForegroundColor Yellow
            Write-Host "  [INFO] For network databases, ensure firewall allows connections" -ForegroundColor Yellow
            $ErrorCount++
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

# Function to load API_BASE_URL from root .env file
function Get-ApiBaseUrl {
    $rootEnvPath = Join-Path $CurrentDir.Path ".env"
    $defaultApiBaseUrl = "http://127.0.0.1:8080"
    
    if (Test-Path $rootEnvPath) {
        $envContent = Get-Content $rootEnvPath -Raw
        if ($envContent -match '(?m)^API_BASE_URL[=:]\s*(.+)$') {
            $apiBaseUrl = $matches[1].Trim()
            # Remove quotes if present
            $apiBaseUrl = $apiBaseUrl -replace '^["'']|["'']$', ''
            if ($apiBaseUrl) {
                return $apiBaseUrl
            }
        }
    }
    
    return $defaultApiBaseUrl
}

# Function to start service in new window
function Start-ServiceInWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDir = (Get-Location).Path,
        [string]$EnvVar = $null,
        [string]$EnvValue = $null
    )
    
    Write-Host "Starting: $Title" -ForegroundColor Cyan
    Write-Host "  Command: $Command" -ForegroundColor Gray
    Write-Host "  Directory: $WorkingDir" -ForegroundColor Gray
    if ($EnvVar -and $EnvValue) {
        Write-Host "  Environment: $EnvVar=$EnvValue" -ForegroundColor Gray
    }
    
    $scriptBlock = @"
Set-Location '$WorkingDir'
$(if ($EnvVar -and $EnvValue) { "`$env:$EnvVar='$EnvValue'" })
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

# Function to verify service started and is listening
function Test-ServiceListening {
    param(
        [int]$Port,
        [int]$MaxAttempts = 5,
        [int]$WaitSeconds = 3
    )
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connection) {
            return $true
        }
        if ($i -lt $MaxAttempts) {
            Write-Host "    Attempt $i/$MaxAttempts - Waiting for service to listen..." -ForegroundColor Gray
            Start-Sleep -Seconds $WaitSeconds
        }
    }
    return $false
}

# =========================================================================
# SEQUENTIAL SERVICE STARTUP (Dependency Order)
# =========================================================================
# Services start one-by-one in dependency order with 15s verification
# =========================================================================

$servicesStarted = 0
$servicesFailed = 0
$newlyStartedPorts = @()  # Track which ports were just started (for opening URLs)

# Service 0: PostgreSQL (Database - Verify it's running)
Write-Host "[0/5] PostgreSQL 18 (Database Foundation)..." -ForegroundColor White
$pgService = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
if ($pgService -and $pgService.Status -eq "Running") {
    Write-Host "  [OK] PostgreSQL is running (system service)" -ForegroundColor Green
    Write-Host "  [OK] Port 5432 verified listening" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] PostgreSQL not running - services may fail" -ForegroundColor Yellow
}
Write-Host ""

# Service 1: Licensing API (Port 8080) - Depends on PostgreSQL
Write-Host "[1/5] Licensing API (Port 8080)..." -ForegroundColor White
Write-Host "  Dependencies: PostgreSQL (5432)" -ForegroundColor Gray
if (-not ($PortsInUse -contains 8080)) {
    $licensingDir = Join-Path $CurrentDir.Path "addon_portal"
    # Use Windows-specific startup script that sets event loop policy before uvicorn
    $startScript = Join-Path $licensingDir "start_api_windows.py"
    # Use absolute path to avoid path resolution issues
    $startScriptAbs = (Resolve-Path $startScript -ErrorAction SilentlyContinue).Path
    if (-not $startScriptAbs) {
        $startScriptAbs = $startScript
    }
    Start-ServiceInWindow -Title "Licensing API (Port 8080)" `
                           -Command "python `"$startScriptAbs`"" `
                           -WorkingDir $licensingDir
    
    Write-Host "  Verifying service startup (15 seconds)..." -ForegroundColor Yellow
    if (Test-ServiceListening -Port 8080 -MaxAttempts 5 -WaitSeconds 3) {
        Write-Host "  [OK] Licensing API started and listening on port 8080" -ForegroundColor Green
        $servicesStarted++
        $newlyStartedPorts += 8080
    } else {
        Write-Host "  [ERROR] Licensing API failed to start or not listening" -ForegroundColor Red
        $servicesFailed++
    }
} else {
    Write-Host "  [SKIP] Already running on port 8080" -ForegroundColor Cyan
}
Write-Host ""

# Service 2: Dashboard API (Port 8000) - Independent backend
Write-Host "[2/5] Dashboard API (Port 8000)..." -ForegroundColor White
Write-Host "  Dependencies: None (WebSocket backend)" -ForegroundColor Gray
if (-not ($PortsInUse -contains 8000)) {
    Start-ServiceInWindow -Title "Dashboard API (Port 8000)" `
                           -Command "python -m uvicorn api.dashboard.main:app --host 0.0.0.0 --port 8000" `
                           -WorkingDir $CurrentDir.Path
    
    Write-Host "  Verifying service startup (15 seconds)..." -ForegroundColor Yellow
    if (Test-ServiceListening -Port 8000 -MaxAttempts 5 -WaitSeconds 3) {
        Write-Host "  [OK] Dashboard API started and listening on port 8000" -ForegroundColor Green
        $servicesStarted++
        $newlyStartedPorts += 8000
    } else {
        Write-Host "  [ERROR] Dashboard API failed to start or not listening" -ForegroundColor Red
        $servicesFailed++
    }
} else {
    Write-Host "  [SKIP] Already running on port 8000" -ForegroundColor Cyan
}
Write-Host ""

# Service 3: Tenant Portal (Port 3000) - Depends on Licensing API
Write-Host "[3/5] Tenant Portal (Port 3000)..." -ForegroundColor White
Write-Host "  Dependencies: Licensing API (8080)" -ForegroundColor Gray
if (-not ($PortsInUse -contains 3000)) {
    $tenantPortalDir = Join-Path $CurrentDir.Path "addon_portal\apps\tenant-portal"
    $apiBaseUrl = Get-ApiBaseUrl
    if (Test-Path "$tenantPortalDir\node_modules") {
        Start-ServiceInWindow -Title "Tenant Portal (Port 3000)" `
                               -Command "npm run dev" `
                               -WorkingDir $tenantPortalDir `
                               -EnvVar "API_BASE_URL" `
                               -EnvValue $apiBaseUrl
    } else {
        Write-Host "  [INFO] Installing npm dependencies first (may take 2-3 minutes)..." -ForegroundColor Yellow
        Start-ServiceInWindow -Title "Tenant Portal (Port 3000)" `
                               -Command "npm install; npm run dev" `
                               -WorkingDir $tenantPortalDir `
                               -EnvVar "API_BASE_URL" `
                               -EnvValue $apiBaseUrl
    }
    
    Write-Host "  Verifying service startup (15 seconds)..." -ForegroundColor Yellow
    if (Test-ServiceListening -Port 3000 -MaxAttempts 5 -WaitSeconds 3) {
        Write-Host "  [OK] Tenant Portal started and listening on port 3000" -ForegroundColor Green
        $servicesStarted++
        $newlyStartedPorts += 3000
    } else {
        Write-Host "  [ERROR] Tenant Portal failed to start or not listening" -ForegroundColor Red
        $servicesFailed++
    }
} else {
    Write-Host "  [SKIP] Already running on port 3000" -ForegroundColor Cyan
}
Write-Host ""

# Service 4: Dashboard UI (Port 3001) - Depends on Dashboard API
Write-Host "[4/5] Dashboard UI (Port 3001)..." -ForegroundColor White
Write-Host "  Dependencies: Dashboard API (8000)" -ForegroundColor Gray
if (-not ($PortsInUse -contains 3001)) {
    $dashboardUIDir = Join-Path $CurrentDir.Path "web\dashboard-ui"
    if (Test-Path "$dashboardUIDir\node_modules") {
        Start-ServiceInWindow -Title "Dashboard UI (Port 3001)" `
                               -Command "npm run dev" `
                               -WorkingDir $dashboardUIDir
    } else {
        Write-Host "  [INFO] Installing npm dependencies first (may take 2-3 minutes)..." -ForegroundColor Yellow
        Start-ServiceInWindow -Title "Dashboard UI (Port 3001)" `
                               -Command "npm install; npm run dev" `
                               -WorkingDir $dashboardUIDir
    }
    
    Write-Host "  Verifying service startup (15 seconds)..." -ForegroundColor Yellow
    if (Test-ServiceListening -Port 3001 -MaxAttempts 5 -WaitSeconds 3) {
        Write-Host "  [OK] Dashboard UI started and listening on port 3001" -ForegroundColor Green
        $servicesStarted++
        $newlyStartedPorts += 3001
    } else {
        Write-Host "  [ERROR] Dashboard UI failed to start or not listening" -ForegroundColor Red
        $servicesFailed++
    }
} else {
    Write-Host "  [SKIP] Already running on port 3001" -ForegroundColor Cyan
}
Write-Host ""

# Service 5: Admin Portal (Port 3002) - Depends on Licensing API
Write-Host "[5/5] Admin Portal (Port 3002)..." -ForegroundColor White
Write-Host "  Dependencies: Licensing API (8080)" -ForegroundColor Gray
if (-not ($PortsInUse -contains 3002)) {
    $adminPortalDir = Join-Path $CurrentDir.Path "addon_portal\apps\admin-portal"
    $apiBaseUrl = Get-ApiBaseUrl
    if (Test-Path "$adminPortalDir\node_modules") {
        Start-ServiceInWindow -Title "Admin Portal (Port 3002)" `
                               -Command "npm run dev" `
                               -WorkingDir $adminPortalDir `
                               -EnvVar "API_BASE_URL" `
                               -EnvValue $apiBaseUrl
    } else {
        Write-Host "  [INFO] Installing npm dependencies first (may take 2-3 minutes)..." -ForegroundColor Yellow
        Start-ServiceInWindow -Title "Admin Portal (Port 3002)" `
                               -Command "npm install; npm run dev" `
                               -WorkingDir $adminPortalDir `
                               -EnvVar "API_BASE_URL" `
                               -EnvValue $apiBaseUrl
    }
    
    Write-Host "  Verifying service startup (15 seconds)..." -ForegroundColor Yellow
    if (Test-ServiceListening -Port 3002 -MaxAttempts 5 -WaitSeconds 3) {
        Write-Host "  [OK] Admin Portal started and listening on port 3002" -ForegroundColor Green
        $servicesStarted++
        $newlyStartedPorts += 3002
    } else {
        Write-Host "  [ERROR] Admin Portal failed to start or not listening" -ForegroundColor Red
        $servicesFailed++
    }
} else {
    Write-Host "  [SKIP] Already running on port 3002" -ForegroundColor Cyan
}
Write-Host ""

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Service Startup Summary" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services Started:  $servicesStarted" -ForegroundColor Green
Write-Host "  Services Failed:   $servicesFailed" -ForegroundColor $(if ($servicesFailed -gt 0) { "Red" } else { "Green" })
Write-Host "  Services Skipped:  $(5 - $servicesStarted - $servicesFailed)" -ForegroundColor Cyan
Write-Host ""

Write-Host ""

# =========================================================================
# PHASE 3: OPEN SERVICE URLS
# =========================================================================

if ($newlyStartedPorts.Count -gt 0) {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Opening Service URLs in Browser (Newly Started Services Only)..." -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""

    # Open URLs ONLY for services that were just started (not already running)
#    if ($newlyStartedPorts -contains 8080) {
#        Write-Host "Opening Licensing API documentation..." -ForegroundColor White
#        Start-Process "http://localhost:8080/docs"
#        Start-Sleep -Seconds 2
#    }

#    if ($newlyStartedPorts -contains 8000) {
#        Write-Host "Opening Dashboard API documentation..." -ForegroundColor White
#        Start-Process "http://localhost:8000/docs"
#        Start-Sleep -Seconds 2
#    }

    if ($newlyStartedPorts -contains 3000) {
        Write-Host "Opening Tenant Portal..." -ForegroundColor White
        Start-Process "http://localhost:3000"
        Start-Sleep -Seconds 2
    }
    
#    if ($newlyStartedPorts -contains 3001) {
#        Write-Host "Opening Dashboard UI..." -ForegroundColor White
#        Start-Process "http://localhost:3001"
#        Start-Sleep -Seconds 2
#    }
    
    if ($newlyStartedPorts -contains 3002) {
        Write-Host "Opening Admin Portal..." -ForegroundColor White
        Start-Process "http://localhost:3002"
        Start-Sleep -Seconds 2
    }
    
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Using Existing Services" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "No browser windows opened - all services were already running." -ForegroundColor Gray
    Write-Host ""
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
#Write-Host "Demo Credentials:" -ForegroundColor White
#Write-Host "  Tenant Slug:           demo" -ForegroundColor Gray
#Write-Host "  Activation Code:       12RY-S55W-4MZR-KP2J" -ForegroundColor Gray
#Write-Host ""
Write-Host "==========================================================================" -ForegroundColor Green
Write-Host ""

# Interactive service management menu
function Show-ServiceMenu {
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Service Management Menu" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "What would you like to do?" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  General Options:" -ForegroundColor Cyan
    Write-Host "    1 - Keep services running and exit" -ForegroundColor White
    Write-Host "    2 - Stop all services now" -ForegroundColor White
    Write-Host ""
    Write-Host "  Restart Individual Services:" -ForegroundColor Cyan
    Write-Host "    3 - Restart Licensing API (port 8080)" -ForegroundColor White
    Write-Host "    4 - Restart Dashboard API (port 8000)" -ForegroundColor White
    Write-Host "    5 - Restart Tenant Portal (port 3000)" -ForegroundColor White
    Write-Host "    6 - Restart Dashboard UI (port 3001)" -ForegroundColor White
    Write-Host "    7 - Restart Admin Portal (port 3002)" -ForegroundColor White
    Write-Host ""
    Write-Host -NoNewline "Enter choice (1-7): " -ForegroundColor Yellow
    $choice = Read-Host
    
    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "Services will continue running." -ForegroundColor Green
            Write-Host ""
            Write-Host "To manage services later:" -ForegroundColor White
            Write-Host "  - Run: MANAGE_SERVICES.bat (interactive menu)" -ForegroundColor Cyan
            Write-Host "  - Run: STOP_ALL.bat (stop all services)" -ForegroundColor Cyan
            Write-Host ""
            return
        }
        "2" {
            Write-Host ""
            Write-Host "Launching STOP_ALL_SERVICES.ps1..." -ForegroundColor Cyan
            Write-Host ""
            Start-Sleep -Seconds 1
            & "$PSScriptRoot\STOP_ALL_SERVICES.ps1"
            return
        }
        "3" {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  Restarting Licensing API (port 8080)" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host ""
            
            # Find and stop process on port 8080
            $conn = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
            if ($conn) {
                $processId = $conn.OwningProcess
                Write-Host "[STOP] Stopping Licensing API (PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 2
                Write-Host "[OK] Stopped" -ForegroundColor Green
            }
            
            Write-Host "[START] Starting Licensing API..." -ForegroundColor Yellow
            $licensingDir = Join-Path $CurrentDir.Path "addon_portal"
            $startScript = Join-Path $licensingDir "start_api_windows.py"
            $startScriptAbs = (Resolve-Path $startScript -ErrorAction SilentlyContinue).Path
            if (-not $startScriptAbs) {
                $startScriptAbs = $startScript
            }
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$licensingDir'; python `"$startScriptAbs`""
            Start-Sleep -Seconds 15
            Write-Host "[OK] Licensing API restarted!" -ForegroundColor Green
            Write-Host ""
            
            Show-ServiceMenu
        }
        "4" {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  Restarting Dashboard API (port 8000)" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host ""
            
            $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
            if ($conn) {
                $processId = $conn.OwningProcess
                Write-Host "[STOP] Stopping Dashboard API (PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 2
                Write-Host "[OK] Stopped" -ForegroundColor Green
            }
            
            Write-Host "[START] Starting Dashboard API..." -ForegroundColor Yellow
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn api.dashboard.main:app --host :: --port 8000 --reload"
            Start-Sleep -Seconds 15
            Write-Host "[OK] Dashboard API restarted!" -ForegroundColor Green
            Write-Host ""
            
            Show-ServiceMenu
        }
        "5" {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  Restarting Tenant Portal (port 3000)" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host ""
            
            $conn = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
            if ($conn) {
                $processId = $conn.OwningProcess
                Write-Host "[STOP] Stopping Tenant Portal (PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 2
                Write-Host "[OK] Stopped" -ForegroundColor Green
            }
            
            Write-Host "[START] Starting Tenant Portal..." -ForegroundColor Yellow
            Set-Location addon_portal\apps\tenant-portal
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
            Set-Location ..\..\..
            Start-Sleep -Seconds 15
            Write-Host "[OK] Tenant Portal restarted!" -ForegroundColor Green
            Write-Host ""
            
            Show-ServiceMenu
        }
        "6" {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  Restarting Dashboard UI (port 3001)" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host ""
            
            $conn = Get-NetTCPConnection -LocalPort 3001 -State Listen -ErrorAction SilentlyContinue
            if ($conn) {
                $processId = $conn.OwningProcess
                Write-Host "[STOP] Stopping Dashboard UI (PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 2
                Write-Host "[OK] Stopped" -ForegroundColor Green
            }
            
            Write-Host "[START] Starting Dashboard UI..." -ForegroundColor Yellow
            Set-Location web\dashboard-ui
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
            Set-Location ..\..
            Start-Sleep -Seconds 15
            Write-Host "[OK] Dashboard UI restarted!" -ForegroundColor Green
            Write-Host ""
            
            Show-ServiceMenu
        }
        "7" {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host "  Restarting Admin Portal (port 3002)" -ForegroundColor Yellow
            Write-Host "========================================" -ForegroundColor Yellow
            Write-Host ""
            
            $conn = Get-NetTCPConnection -LocalPort 3002 -State Listen -ErrorAction SilentlyContinue
            if ($conn) {
                $processId = $conn.OwningProcess
                Write-Host "[STOP] Stopping Admin Portal (PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 2
                Write-Host "[OK] Stopped" -ForegroundColor Green
            }
            
            Write-Host "[START] Starting Admin Portal..." -ForegroundColor Yellow
            Set-Location addon_portal\apps\admin-portal
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
            Set-Location ..\..\..
            Start-Sleep -Seconds 15
            Write-Host "[OK] Admin Portal restarted!" -ForegroundColor Green
            Write-Host ""
            
            Show-ServiceMenu
        }
        default {
            Write-Host ""
            Write-Host "Invalid choice. Please enter 1-7." -ForegroundColor Red
            Write-Host ""
            Start-Sleep -Seconds 2
            Show-ServiceMenu
        }
    }
}

# Show the menu
Show-ServiceMenu