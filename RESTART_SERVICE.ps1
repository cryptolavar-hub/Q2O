# ==========================================================================
# Quick2Odoo Combined - Individual Service Restart Script
# ==========================================================================
# Restart a single service without affecting others
# Usage: .\RESTART_SERVICE.ps1 -ServiceName <service>
#
# Services: licensing, dashboard, tenant, dashui, admin
# ==========================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("licensing", "dashboard", "tenant", "dashui", "admin", "all")]
    [string]$ServiceName
)

$ErrorActionPreference = "Continue"

# Service definitions
$Services = @{
    "licensing" = @{
        Name = "Licensing API"
        Port = 8080
        Command = "python start_api_windows.py"
        WorkDir = "addon_portal"
        Type = "python"
    }
    "dashboard" = @{
        Name = "Dashboard API"
        Port = 8000
        Command = "python -m uvicorn api.dashboard.main:app --host :: --port 8000 --reload"
        WorkDir = "."
        Type = "python"
    }
    "tenant" = @{
        Name = "Tenant Portal"
        Port = 3000
        Command = "npm run dev"
        WorkDir = "addon_portal\apps\tenant-portal"
        Type = "node"
    }
    "dashui" = @{
        Name = "Dashboard UI"
        Port = 3001
        Command = "npm run dev"
        WorkDir = "web\dashboard-ui"
        Type = "node"
    }
    "admin" = @{
        Name = "Admin Portal"
        Port = 3002
        Command = "npm run dev"
        WorkDir = "addon_portal\apps\admin-portal"
        Type = "node"
    }
}

function Show-Menu {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Quick2Odoo - Individual Service Management" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select service to restart:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. Licensing API       (Port 8080)" -ForegroundColor Yellow
    Write-Host "  2. Dashboard API       (Port 8000)" -ForegroundColor Yellow
    Write-Host "  3. Tenant Portal       (Port 3000)" -ForegroundColor Yellow
    Write-Host "  4. Dashboard UI        (Port 3001)" -ForegroundColor Yellow
    Write-Host "  5. Admin Portal        (Port 3002)" -ForegroundColor Yellow
    Write-Host "  6. Restart ALL services" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  0. Cancel" -ForegroundColor Gray
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Stop-Service-ByPort {
    param([int]$Port)
    
    Write-Host "  [INFO] Stopping service on port $Port..." -ForegroundColor Cyan
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        
        if ($connections) {
            foreach ($conn in $connections) {
                $processId = $conn.OwningProcess
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                
                if ($process) {
                    Write-Host "  [INFO] Stopping process: $($process.Name) (PID: $processId)" -ForegroundColor Yellow
                    Stop-Process -Id $processId -Force -ErrorAction Stop
                    Start-Sleep -Seconds 2
                    Write-Host "  [OK] Service stopped" -ForegroundColor Green
                    return $true
                }
            }
        } else {
            Write-Host "  [INFO] Service not running on port $Port" -ForegroundColor Gray
            return $false
        }
    } catch {
        Write-Host "  [ERROR] Failed to stop service: $_" -ForegroundColor Red
        return $false
    }
    
    return $false
}

function Start-Service-Item {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Command,
        [string]$WorkDir
    )
    
    Write-Host "  [INFO] Starting $Name on port $Port..." -ForegroundColor Cyan
    
    # Start the service in new window
    $startArgs = @{
        FilePath = "powershell"
        ArgumentList = "-NoExit", "-Command", "cd '$WorkDir'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '$Name (Port $Port)' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; $Command"
        WindowStyle = "Normal"
    }
    
    Start-Process @startArgs
    
    # Wait and verify
    Write-Host "  [INFO] Waiting 15 seconds for service to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Verify it's listening
    $listening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    
    if ($listening) {
        Write-Host "  [OK] $Name is running on port $Port" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [WARNING] $Name may not have started (port $Port not listening)" -ForegroundColor Yellow
        return $false
    }
}

function Restart-SingleService {
    param([string]$ServiceKey)
    
    $service = $Services[$ServiceKey]
    
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Restarting: $($service.Name)" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Step 1: Stop
    Write-Host "[1/2] Stopping $($service.Name)..." -ForegroundColor White
    $wasStopped = Stop-Service-ByPort -Port $service.Port
    
    if ($wasStopped) {
        Write-Host "  [OK] Service stopped successfully" -ForegroundColor Green
    }
    Write-Host ""
    
    # Step 2: Start
    Write-Host "[2/2] Starting $($service.Name)..." -ForegroundColor White
    $started = Start-Service-Item -Name $service.Name -Port $service.Port -Command $service.Command -WorkDir $service.WorkDir
    Write-Host ""
    
    if ($started) {
        Write-Host "==========================================================================" -ForegroundColor Green
        Write-Host "  ✅ $($service.Name) restarted successfully!" -ForegroundColor Green
        Write-Host "==========================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Service URL: http://localhost:$($service.Port)" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "==========================================================================" -ForegroundColor Yellow
        Write-Host "  ⚠️  $($service.Name) restart may have issues" -ForegroundColor Yellow
        Write-Host "==========================================================================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Check the PowerShell window for errors" -ForegroundColor Yellow
        Write-Host ""
    }
}

# ==========================================================================
# MAIN EXECUTION
# ==========================================================================

Write-Host ""
Write-Host "Quick2Odoo Individual Service Restart" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# If no service specified, show menu
if (-not $ServiceName) {
    Show-Menu
    
    $choice = Read-Host "Enter choice (0-6)"
    
    switch ($choice) {
        "1" { $ServiceName = "licensing" }
        "2" { $ServiceName = "dashboard" }
        "3" { $ServiceName = "tenant" }
        "4" { $ServiceName = "dashui" }
        "5" { $ServiceName = "admin" }
        "6" { $ServiceName = "all" }
        "0" {
            Write-Host ""
            Write-Host "Cancelled." -ForegroundColor Gray
            Write-Host ""
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "[ERROR] Invalid choice" -ForegroundColor Red
            Write-Host ""
            exit 1
        }
    }
}

# Restart service(s)
if ($ServiceName -eq "all") {
    Write-Host ""
    Write-Host "Restarting ALL services..." -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($key in $Services.Keys | Sort-Object) {
        Restart-SingleService -ServiceKey $key
    }
    
} else {
    Restart-SingleService -ServiceKey $ServiceName
}

Write-Host ""
Write-Host "Press Enter to close this window..."
Read-Host

