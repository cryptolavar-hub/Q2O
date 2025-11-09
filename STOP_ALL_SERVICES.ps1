# =========================================================================
# STOP_ALL_SERVICES.ps1
# Q2O Platform - Intelligent Service Shutdown Script
# =========================================================================
# This script:
# 1. Detects which services are currently running
# 2. Stops only the services that are running
# 3. Provides graceful shutdown with delays
# 4. Shows detailed status for each service
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Q2O Platform - Service Shutdown Script" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

$ServicesStopped = 0
$ServicesNotRunning = 0

# =========================================================================
# PHASE 1: DETECT RUNNING SERVICES
# =========================================================================

Write-Host "PHASE 1: Detecting Running Services..." -ForegroundColor Yellow
Write-Host "==========================================================================" -ForegroundColor Gray
Write-Host ""

$ServicePorts = @{
    8080 = "Licensing API"
    8000 = "Dashboard API"
    3000 = "Tenant Portal"
    3001 = "Dashboard UI"
    3002 = "Admin Portal"
}

$RunningServices = @{}

foreach ($port in $ServicePorts.Keys | Sort-Object) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    $serviceName = $ServicePorts[$port]
    
    if ($connection) {
        Write-Host "  [RUNNING] Port $port - $serviceName" -ForegroundColor Green
        $RunningServices[$port] = $serviceName
    } else {
        Write-Host "  [STOPPED] Port $port - $serviceName (not running)" -ForegroundColor Gray
        $ServicesNotRunning++
    }
}

Write-Host ""

# Check PostgreSQL service
Write-Host "Checking PostgreSQL..." -ForegroundColor White
$pgService = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
if ($pgService -and $pgService.Status -eq "Running") {
    Write-Host "  [RUNNING] PostgreSQL 18 service" -ForegroundColor Green
    Write-Host "  [INFO] PostgreSQL will NOT be stopped (system service)" -ForegroundColor Cyan
} else {
    Write-Host "  [STOPPED] PostgreSQL 18 (not running or not installed)" -ForegroundColor Gray
}

Write-Host ""

# =========================================================================
# SUMMARY AND CONFIRMATION
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Detection Summary" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services Running:     $($RunningServices.Count)" -ForegroundColor $(if ($RunningServices.Count -gt 0) { "Green" } else { "Gray" })
Write-Host "  Services Stopped:     $ServicesNotRunning" -ForegroundColor Gray
Write-Host ""

if ($RunningServices.Count -eq 0) {
    Write-Host "==========================================================================" -ForegroundColor Yellow
    Write-Host "  NO SERVICES RUNNING" -ForegroundColor Yellow
    Write-Host "==========================================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "All services are already stopped. Nothing to do." -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

Write-Host "Services to stop:" -ForegroundColor White
foreach ($port in $RunningServices.Keys | Sort-Object) {
    Write-Host "  - Port $port : $($RunningServices[$port])" -ForegroundColor Gray
}
Write-Host ""

$confirmation = Read-Host "Stop all running services? (y/n)"
if ($confirmation -ne "y" -and $confirmation -ne "Y") {
    Write-Host "Shutdown cancelled by user." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# =========================================================================
# HELPER FUNCTION: STOP PROCESS BY PORT
# =========================================================================

function Stop-ProcessByPort {
    param(
        [int]$Port,
        [string]$ServiceName
    )
    
    try {
        # Find the connection and get the Process ID
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        
        if (-not $connection) {
            Write-Host "  [INFO] Port $Port not in use (already stopped)" -ForegroundColor Gray
            return $true
        }
        
        $processId = $connection.OwningProcess
        
        if (-not $processId -or $processId -eq 0) {
            Write-Host "  [ERROR] Could not find process ID for port $Port" -ForegroundColor Red
            return $false
        }
        
        # Get process details
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        if (-not $process) {
            Write-Host "  [ERROR] Process ID $processId not found" -ForegroundColor Red
            return $false
        }
        
        Write-Host "  Found process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Gray
        
        # Kill the process
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Host "  Sent SIGKILL to PID $processId" -ForegroundColor Gray
        
        # Wait and verify
        Start-Sleep -Seconds 2
        
        $stillRunning = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if (-not $stillRunning) {
            Write-Host "  [OK] $ServiceName stopped successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  [WARNING] Port $Port still in use after kill attempt" -ForegroundColor Yellow
            return $false
        }
        
    } catch {
        Write-Host "  [ERROR] Failed to stop: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# =========================================================================
# PHASE 2: GRACEFUL SHUTDOWN (ONE BY ONE)
# =========================================================================

Write-Host "PHASE 2: Stopping Services (Gracefully, One-by-One)..." -ForegroundColor Yellow
Write-Host "==========================================================================" -ForegroundColor Gray
Write-Host ""

$serviceIndex = 1

# Service 1: Licensing API (Port 8080)
if ($RunningServices.ContainsKey(8080)) {
    Write-Host "[$serviceIndex/$($RunningServices.Count)] Stopping Licensing API (port 8080)..." -ForegroundColor White
    if (Stop-ProcessByPort -Port 8080 -ServiceName "Licensing API") {
        $ServicesStopped++
    }
    Write-Host ""
    $serviceIndex++
}

# Service 2: Dashboard API (Port 8000)
if ($RunningServices.ContainsKey(8000)) {
    Write-Host "[$serviceIndex/$($RunningServices.Count)] Stopping Dashboard API (port 8000)..." -ForegroundColor White
    if (Stop-ProcessByPort -Port 8000 -ServiceName "Dashboard API") {
        $ServicesStopped++
    }
    Write-Host ""
    $serviceIndex++
}

# Service 3: Tenant Portal (Port 3000)
if ($RunningServices.ContainsKey(3000)) {
    Write-Host "[$serviceIndex/$($RunningServices.Count)] Stopping Tenant Portal (port 3000)..." -ForegroundColor White
    if (Stop-ProcessByPort -Port 3000 -ServiceName "Tenant Portal") {
        $ServicesStopped++
    }
    Write-Host ""
    $serviceIndex++
}

# Service 4: Dashboard UI (Port 3001)
if ($RunningServices.ContainsKey(3001)) {
    Write-Host "[$serviceIndex/$($RunningServices.Count)] Stopping Dashboard UI (port 3001)..." -ForegroundColor White
    if (Stop-ProcessByPort -Port 3001 -ServiceName "Dashboard UI") {
        $ServicesStopped++
    }
    Write-Host ""
    $serviceIndex++
}

# Service 5: Admin Portal (Port 3002)
if ($RunningServices.ContainsKey(3002)) {
    Write-Host "[$serviceIndex/$($RunningServices.Count)] Stopping Admin Portal (port 3002)..." -ForegroundColor White
    if (Stop-ProcessByPort -Port 3002 -ServiceName "Admin Portal") {
        $ServicesStopped++
    }
    Write-Host ""
    $serviceIndex++
}

# =========================================================================
# PHASE 3: VERIFICATION
# =========================================================================

Write-Host "PHASE 3: Verifying Shutdown..." -ForegroundColor Yellow
Write-Host "==========================================================================" -ForegroundColor Gray
Write-Host ""

$stillRunning = @()
foreach ($port in $ServicePorts.Keys) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "  [WARNING] Port $port still in use - $($ServicePorts[$port])" -ForegroundColor Yellow
        $stillRunning += $port
    } else {
        Write-Host "  [OK] Port $port available - $($ServicePorts[$port]) stopped" -ForegroundColor Green
    }
}

Write-Host ""

# =========================================================================
# FINAL SUMMARY
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Shutdown Summary" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services Stopped:     $ServicesStopped" -ForegroundColor Green
Write-Host "  Still Running:        $($stillRunning.Count)" -ForegroundColor $(if ($stillRunning.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

if ($stillRunning.Count -gt 0) {
    Write-Host "==========================================================================" -ForegroundColor Yellow
    Write-Host "  WARNING: Some Services Still Running" -ForegroundColor Yellow
    Write-Host "==========================================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ports still in use: $($stillRunning -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual cleanup options:" -ForegroundColor White
    Write-Host "  1. Close PowerShell windows manually" -ForegroundColor Gray
    Write-Host "  2. Kill all node processes: " -ForegroundColor Gray
    Write-Host "     Get-Process | Where-Object {`$_.ProcessName -eq 'node'} | Stop-Process -Force" -ForegroundColor Gray
    Write-Host "  3. Kill all python processes: " -ForegroundColor Gray
    Write-Host "     Get-Process | Where-Object {`$_.ProcessName -eq 'python'} | Stop-Process -Force" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "==========================================================================" -ForegroundColor Green
    Write-Host "  ALL SERVICES STOPPED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "==========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "All Quick2Odoo services have been gracefully shut down." -ForegroundColor White
    Write-Host ""
    Write-Host "To start services again:" -ForegroundColor White
    Write-Host "  START_ALL.bat" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Note: PostgreSQL 18 service was not stopped (system service)" -ForegroundColor Cyan
Write-Host "      To stop PostgreSQL: net stop postgresql-x64-18" -ForegroundColor Gray
Write-Host ""
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to close this window"

