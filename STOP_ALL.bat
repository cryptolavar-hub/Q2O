@echo off
REM =========================================================================
REM STOP_ALL.bat
REM Quick2Odoo Combined - Service Shutdown Launcher
REM =========================================================================
REM This batch file launches the PowerShell shutdown script
REM =========================================================================

echo.
echo =========================================================================
echo  Quick2Odoo Combined - Stopping All Services
echo =========================================================================
echo.
echo  This will:
echo  1. Detect which services are currently running
echo  2. Stop only the running services
echo  3. Verify shutdown was successful
echo.
echo =========================================================================
echo.

REM Execute the PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0STOP_ALL_SERVICES.ps1"

REM Check if PowerShell script succeeded
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Shutdown script failed. See errors above.
    pause
    exit /b 1
)

exit /b 0

