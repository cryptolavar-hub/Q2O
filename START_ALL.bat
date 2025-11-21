@echo off
REM =========================================================================
REM START_ALL.bat
REM Q2O - Simplified Launcher
REM =========================================================================
REM This batch file launches the comprehensive PowerShell startup script
REM =========================================================================

echo.
echo =========================================================================
echo  Q2O - Starting All Services
echo =========================================================================
echo.
echo  This will:
echo  1. Run verification checks (git, python, dependencies, ports, etc.)
echo  2. Start all services if checks pass
echo  3. Open service URLs in browser
echo.
echo =========================================================================
echo.

REM Execute the PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0START_ALL_SERVICES.ps1"

REM Check if PowerShell script succeeded
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Startup script failed. See errors above.
    pause
    exit /b 1
)

exit /b 0

