@echo off
REM =========================================================================
REM RESTART_ALL.bat
REM Quick2Odoo Combined - Service Restart
REM =========================================================================
REM Stops all services, then starts them fresh
REM =========================================================================

echo.
echo =========================================================================
echo  Quick2Odoo Combined - Restart All Services
echo =========================================================================
echo.
echo  This will:
echo  1. Stop all running services
echo  2. Wait for clean shutdown
echo  3. Start all services fresh
echo.
echo =========================================================================
echo.

REM Stop all services
echo Step 1: Stopping services...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0STOP_ALL_SERVICES.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to stop services.
    pause
    exit /b 1
)

echo.
echo Step 2: Waiting for clean shutdown...
timeout /t 3 /nobreak

echo.
echo Step 3: Starting services...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0START_ALL_SERVICES.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start services.
    pause
    exit /b 1
)

exit /b 0

