@echo off
REM =========================================================================
REM Q2O Licensing API - Windows Startup Script
REM =========================================================================
REM This script sets the Windows event loop policy BEFORE uvicorn starts,
REM ensuring psycopg async operations work correctly on Windows.
REM =========================================================================

echo.
echo =========================================================================
echo  Q2O Licensing API - Starting...
echo =========================================================================
echo.

cd /d "%~dp0"

REM Use the Windows-specific startup script
python start_api_windows.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start API server
    pause
    exit /b 1
)

exit /b 0

