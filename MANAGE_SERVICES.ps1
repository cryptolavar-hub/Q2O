==========================================================================
# Q2O Service Manager - Individual Service Control
# Manage individual services: start, stop, restart, or status check
==========================================================================

param(
    [string]$Action = "",  # start, stop, restart, status, menu
    [string]$Service = ""  # licensing, dashboard, tenant, dashui, admin, all
)

# Service definitions
$Services = @{
    "licensing" = @{
        Name = "Licensing API"
        Port = 8080
        Command = "python start_api_windows.py"
        Directory = "addon_portal"
        Type = "python"
    }
    "dashboard" = @{
        Name = "Dashboard API"
        Port = 8000
        Command = "python -m uvicorn api.dashboard.main:app --host :: --port 8000 --reload"
        Directory = "."
        Type = "python"
    }
    "tenant" = @{
        Name = "Tenant Portal"
        Port = 3000
        Command = "npm run dev"
        Directory = "addon_portal\apps\tenant-portal"
        Type = "node"
    }
    "dashui" = @{
        Name = "Dashboard UI"
        Port = 3001
        Command = "npm run dev"
        Directory = "web\dashboard-ui"
        Type = "node"
    }
    "admin" = @{
        Name = "Admin Portal"
        Port = 3002
        Command = "npm run dev"
        Directory = "addon_portal\apps\admin-portal"
        Type = "node"
    }
}

function Get-ServiceStatus {
    param([string]$ServiceKey)
    
    $svc = $Services[$ServiceKey]
    $port = $svc.Port
    
    $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    
    if ($connection) {
        $processId = $connection.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        return @{
            Running = $true
            ProcessId = $processId
            ProcessName = $process.ProcessName
            Port = $port
        }
    }
    
    return @{
        Running = $false
        ProcessId = $null
        ProcessName = $null
        Port = $port
    }
}

function Stop-Q2OService {
    param([string]$ServiceKey)
    
    $svc = $Services[$ServiceKey]
    $status = Get-ServiceStatus -ServiceKey $ServiceKey
    
    if (-not $status.Running) {
        Write-Host "  [INFO] $($svc.Name) is not running" -ForegroundColor Cyan
        return $false
    }
    
    Write-Host "  [STOP] Stopping $($svc.Name) (PID: $($status.ProcessId))..." -ForegroundColor Yellow
    
    try {
        Stop-Process -Id $status.ProcessId -Force
        Start-Sleep -Seconds 2
        
        # Verify stopped
        $newStatus = Get-ServiceStatus -ServiceKey $ServiceKey
        if (-not $newStatus.Running) {
            Write-Host "  [OK] $($svc.Name) stopped successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  [WARNING] $($svc.Name) still running" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "  [ERROR] Failed to stop $($svc.Name): $_" -ForegroundColor Red
        return $false
    }
}

function Start-Q2OService {
    param([string]$ServiceKey)
    
    $svc = $Services[$ServiceKey]
    $status = Get-ServiceStatus -ServiceKey $ServiceKey
    
    if ($status.Running) {
        Write-Host "  [INFO] $($svc.Name) is already running (PID: $($status.ProcessId))" -ForegroundColor Cyan
        return $false
    }
    
    Write-Host "  [START] Starting $($svc.Name) on port $($svc.Port)..." -ForegroundColor Yellow
    
    try {
        # Navigate to service directory
        $originalDir = Get-Location
        Set-Location $svc.Directory
        
        # Start service in new PowerShell window
        $title = "Q2O - $($svc.Name)"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $svc.Command -WindowStyle Normal
        
        Set-Location $originalDir
        
        # Wait for service to start (max 15 seconds)
        $maxWait = 15
        $waited = 0
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 1
            $waited++
            
            $newStatus = Get-ServiceStatus -ServiceKey $ServiceKey
            if ($newStatus.Running) {
                Write-Host "  [OK] $($svc.Name) started successfully (took ${waited}s)" -ForegroundColor Green
                return $true
            }
        }
        
        Write-Host "  [WARNING] $($svc.Name) did not start within ${maxWait}s" -ForegroundColor Yellow
        return $false
        
    } catch {
        Write-Host "  [ERROR] Failed to start $($svc.Name): $_" -ForegroundColor Red
        Set-Location $originalDir
        return $false
    }
}

function Restart-Q2OService {
    param([string]$ServiceKey)
    
    $svc = $Services[$ServiceKey]
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Restarting $($svc.Name)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # Stop if running
    $stopped = Stop-Q2OService -ServiceKey $ServiceKey
    
    if ($stopped) {
        Start-Sleep -Seconds 2
    }
    
    # Start
    $started = Start-Q2OService -ServiceKey $ServiceKey
    
    if ($started) {
        Write-Host ""
        Write-Host "  ✅ $($svc.Name) restarted successfully!" -ForegroundColor Green
        Write-Host "  📍 URL: http://localhost:$($svc.Port)" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "  ❌ Failed to restart $($svc.Name)" -ForegroundColor Red
        Write-Host ""
    }
}

function Show-ServiceStatus {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Q2O Service Status" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($key in $Services.Keys | Sort-Object) {
        $svc = $Services[$key]
        $status = Get-ServiceStatus -ServiceKey $key
        
        if ($status.Running) {
            Write-Host "  [RUNNING] " -ForegroundColor Green -NoNewline
            Write-Host "$($svc.Name) " -NoNewline
            Write-Host "(Port: $($svc.Port), PID: $($status.ProcessId))" -ForegroundColor Gray
        } else {
            Write-Host "  [STOPPED] " -ForegroundColor Red -NoNewline
            Write-Host "$($svc.Name) " -NoNewline
            Write-Host "(Port: $($svc.Port))" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
}

function Show-Menu {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Q2O Service Manager - Interactive Menu" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Show current status
    Show-ServiceStatus
    
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Available Actions:" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Individual Services:" -ForegroundColor Yellow
    Write-Host "    1. Restart Licensing API (port 8080)" -ForegroundColor White
    Write-Host "    2. Restart Dashboard API (port 8000)" -ForegroundColor White
    Write-Host "    3. Restart Tenant Portal (port 3000)" -ForegroundColor White
    Write-Host "    4. Restart Dashboard UI (port 3001)" -ForegroundColor White
    Write-Host "    5. Restart Admin Portal (port 3002)" -ForegroundColor White
    Write-Host ""
    Write-Host "  Bulk Actions:" -ForegroundColor Yellow
    Write-Host "    A. Restart ALL services" -ForegroundColor White
    Write-Host "    S. Stop ALL services" -ForegroundColor White
    Write-Host "    R. Refresh status" -ForegroundColor White
    Write-Host ""
    Write-Host "    Q. Quit" -ForegroundColor White
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $choice = Read-Host "Enter your choice"
    
    switch ($choice.ToUpper()) {
        "1" { Restart-Q2OService -ServiceKey "licensing"; Show-Menu }
        "2" { Restart-Q2OService -ServiceKey "dashboard"; Show-Menu }
        "3" { Restart-Q2OService -ServiceKey "tenant"; Show-Menu }
        "4" { Restart-Q2OService -ServiceKey "dashui"; Show-Menu }
        "5" { Restart-Q2OService -ServiceKey "admin"; Show-Menu }
        "A" {
            Write-Host ""
            Write-Host "Restarting ALL services..." -ForegroundColor Yellow
            foreach ($key in @("licensing", "dashboard", "tenant", "dashui", "admin")) {
                Restart-Q2OService -ServiceKey $key
            }
            Show-Menu
        }
        "S" {
            Write-Host ""
            Write-Host "Stopping ALL services..." -ForegroundColor Yellow
            & "$PSScriptRoot\STOP_ALL_SERVICES.ps1"
            Show-Menu
        }
        "R" { Show-Menu }
        "Q" {
            Write-Host ""
            Write-Host "Exiting Service Manager..." -ForegroundColor Cyan
            Write-Host ""
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Show-Menu
        }
    }
}

# Main execution
if ($Action -eq "" -or $Action -eq "menu") {
    # Interactive menu mode
    Show-Menu
} elseif ($Action -eq "status") {
    # Show status only
    Show-ServiceStatus
} elseif ($Service -eq "" -or $Service -eq "all") {
    # Action on all services
    if ($Action -eq "stop") {
        foreach ($key in $Services.Keys) {
            Stop-Q2OService -ServiceKey $key
        }
    } elseif ($Action -eq "start") {
        foreach ($key in $Services.Keys) {
            Start-Q2OService -ServiceKey $key
        }
    } elseif ($Action -eq "restart") {
        foreach ($key in $Services.Keys) {
            Restart-Q2OService -ServiceKey $key
        }
    }
} else {
    # Action on specific service
    if ($Services.ContainsKey($Service)) {
        if ($Action -eq "stop") {
            Stop-Q2OService -ServiceKey $Service
        } elseif ($Action -eq "start") {
            Start-Q2OService -ServiceKey $Service
        } elseif ($Action -eq "restart") {
            Restart-Q2OService -ServiceKey $Service
        }
    } else {
        Write-Host "Unknown service: $Service" -ForegroundColor Red
        Write-Host "Available services: licensing, dashboard, tenant, dashui, admin" -ForegroundColor Yellow
    }
}

