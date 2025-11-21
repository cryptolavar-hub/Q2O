@echo off
setlocal enabledelayedexpansion
REM Diagnostic script to check dashboard status
REM Run this to see what's working and what's broken

cd /d "%~dp0"

echo.
echo ================================================
echo   DASHBOARD STATUS CHECK
echo ================================================
echo.

echo [1/4] Checking if backend API is running...
curl -s http://127.0.0.1:8080/admin/api/dashboard-stats >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Backend API is responding
) else (
    echo    ✗ Backend API is NOT responding
    echo    → Start the backend API first!
    goto :end
)

echo.
echo [2/4] Testing dashboard stats endpoint...
curl -s http://127.0.0.1:8080/admin/api/dashboard-stats | findstr /C:"totalCodes" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Dashboard stats endpoint working
) else (
    echo    ✗ Dashboard stats endpoint failing
)

echo.
echo [3/4] Testing recent activities endpoint...
curl -s http://127.0.0.1:8080/admin/api/recent-activities | findstr /C:"activities" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Recent activities endpoint working
) else (
    echo    ✗ Recent activities endpoint failing
    echo    → May need to run migration 006
)

echo.
echo [4/4] Checking if platform_events table exists...

REM Find psql.exe - Try multiple methods
set PSQL_PATH=
set PSQL_FOUND=0

REM Method 1: Check if psql is in PATH
where psql >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PSQL_PATH=psql
    set PSQL_FOUND=1
) else (
    REM Method 2: Check common PostgreSQL installation paths (check multiple versions)
    REM Check versions 18 down to 12
    for /L %%v in (18,-1,12) do (
        if exist "C:\Program Files\PostgreSQL\%%v\bin\psql.exe" (
            set "PSQL_PATH=C:\Program Files\PostgreSQL\%%v\bin\psql.exe"
            set PSQL_FOUND=1
            goto :found_psql
        )
    )
    
    REM Method 3: Check Program Files (x86) for 32-bit installations
    for /L %%v in (18,-1,12) do (
        if exist "C:\Program Files (x86)\PostgreSQL\%%v\bin\psql.exe" (
            set "PSQL_PATH=C:\Program Files (x86)\PostgreSQL\%%v\bin\psql.exe"
            set PSQL_FOUND=1
            goto :found_psql
        )
    )
)

:found_psql
if %PSQL_FOUND% EQU 0 (
    echo    ✗ psql.exe not found - cannot check database
    echo    → Run: .\RUN_MIGRATION_006.bat to create platform_events table
    goto :end
)

REM Database connection settings - MUST be read from .env file (security requirement)
REM No hardcoded passwords allowed!

REM Check if .env file exists (at project root: C:\Q2O_Combined\.env)
if not exist ".env" (
    echo    ✗ .env file not found in project root
    echo    → Cannot check database without credentials
    echo    → Create .env at project root with DB_DSN=postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Initialize variables
set DB_DSN=
set DB_HOST=
set DB_PORT=
set DB_NAME=
set DB_USER=
set DB_PASSWORD=

REM Read DB_DSN from .env file (at project root)
for /f "delims=" %%a in ('powershell -Command "if (Test-Path '.env') { Get-Content '.env' | Where-Object { $_ -match '^DB_DSN=' } | ForEach-Object { $_.Split('=',2)[1] } }"') do (
    set DB_DSN=%%a
)

REM Verify DB_DSN was found
if "%DB_DSN%"=="" (
    echo    ✗ DB_DSN not found in .env file
    echo    → Add DB_DSN=postgresql+psycopg://user:password@host:port/database to .env at project root
    goto :end
)

REM Parse connection details from DB_DSN: postgresql+psycopg://user:password@host:port/database
REM Use robust parsing that handles special characters in passwords (:, @, etc.)
REM Strategy: Find the LAST @ (separates credentials from host), then split by FIRST : (separates user from password)
REM This works because: password can contain : or @, but host cannot contain @, and port is always numeric
for /f "delims=" %%a in ('powershell -Command "$dsn='%DB_DSN%'; $parts = $dsn -replace '^[^:]+://', ''; $atPos = $parts.LastIndexOf('@'); if ($atPos -lt 0) { 'ERROR' } else { $userPass = $parts.Substring(0, $atPos); $colonPos = $userPass.IndexOf(':'); if ($colonPos -lt 0) { 'ERROR' } else { $userPass.Substring($colonPos + 1) } }"') do (
    set DB_PASSWORD=%%a
)

for /f "delims=" %%a in ('powershell -Command "$dsn='%DB_DSN%'; $parts = $dsn -replace '^[^:]+://', ''; $atPos = $parts.LastIndexOf('@'); if ($atPos -lt 0) { 'ERROR' } else { $userPass = $parts.Substring(0, $atPos); $colonPos = $userPass.IndexOf(':'); if ($colonPos -lt 0) { $userPass } else { $userPass.Substring(0, $colonPos) } }"') do (
    set DB_USER=%%a
)

for /f "delims=" %%a in ('powershell -Command "$dsn='%DB_DSN%'; $parts = $dsn -replace '^[^:]+://', ''; $atPos = $parts.LastIndexOf('@'); if ($atPos -lt 0) { 'ERROR' } else { $afterAt = $parts.Substring($atPos + 1); if ($afterAt -match '^([^:]+):(\d+)/(.+)$') { $matches[1] } else { 'ERROR' } }"') do (
    set DB_HOST=%%a
)

for /f "delims=" %%a in ('powershell -Command "$dsn='%DB_DSN%'; $parts = $dsn -replace '^[^:]+://', ''; $atPos = $parts.LastIndexOf('@'); if ($atPos -lt 0) { 'ERROR' } else { $afterAt = $parts.Substring($atPos + 1); if ($afterAt -match '^([^:]+):(\d+)/(.+)$') { $matches[2] } else { 'ERROR' } }"') do (
    set DB_PORT=%%a
)

for /f "delims=" %%a in ('powershell -Command "$dsn='%DB_DSN%'; $parts = $dsn -replace '^[^:]+://', ''; $atPos = $parts.LastIndexOf('@'); if ($atPos -lt 0) { 'ERROR' } else { $afterAt = $parts.Substring($atPos + 1); if ($afterAt -match '^([^:]+):(\d+)/(.+)$') { $matches[3] } else { 'ERROR' } }"') do (
    set DB_NAME=%%a
)

REM Verify all connection details were parsed successfully
REM Check DB_PASSWORD
if "%DB_PASSWORD%"=="ERROR" (
    echo    ✗ Failed to parse password from DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

if "%DB_PASSWORD%"=="" (
    echo    ✗ Password not found in DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Check DB_USER
if "%DB_USER%"=="ERROR" (
    echo    ✗ Failed to parse username from DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

if "%DB_USER%"=="" (
    echo    ✗ Username not found in DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Check DB_HOST
if "%DB_HOST%"=="ERROR" (
    echo    ✗ Failed to parse host from DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

if "%DB_HOST%"=="" (
    echo    ✗ Host not found in DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Check DB_PORT
if "%DB_PORT%"=="ERROR" (
    echo    ✗ Failed to parse port from DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

if "%DB_PORT%"=="" (
    echo    ✗ Port not found in DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Validate DB_PORT is numeric
echo %DB_PORT% | findstr /R "^[0-9][0-9]*$" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    ✗ Port must be numeric, got: %DB_PORT%
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Check DB_NAME
if "%DB_NAME%"=="ERROR" (
    echo    ✗ Failed to parse database name from DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

if "%DB_NAME%"=="" (
    echo    ✗ Database name not found in DB_DSN
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    goto :end
)

REM Final validation check - ensure all parameters are valid before psql execution
REM This prevents psql from being called with invalid parameters
set VALIDATION_FAILED=0

if "%DB_HOST%"=="ERROR" set VALIDATION_FAILED=1
if "%DB_HOST%"=="" set VALIDATION_FAILED=1
if "%DB_PORT%"=="ERROR" set VALIDATION_FAILED=1
if "%DB_PORT%"=="" set VALIDATION_FAILED=1
if "%DB_USER%"=="ERROR" set VALIDATION_FAILED=1
if "%DB_USER%"=="" set VALIDATION_FAILED=1
if "%DB_NAME%"=="ERROR" set VALIDATION_FAILED=1
if "%DB_NAME%"=="" set VALIDATION_FAILED=1
if "%DB_PASSWORD%"=="ERROR" set VALIDATION_FAILED=1
if "%DB_PASSWORD%"=="" set VALIDATION_FAILED=1

REM Validate port is numeric (additional check)
echo %DB_PORT% | findstr /R "^[0-9][0-9]*$" >nul 2>&1
if %ERRORLEVEL% NEQ 0 set VALIDATION_FAILED=1

if %VALIDATION_FAILED% EQU 1 (
    echo    ✗ Database connection parameters are invalid
    echo    → Cannot execute psql with invalid parameters
    echo    → DB_DSN format should be: postgresql+psycopg://user:password@host:port/database
    echo    → Parsed values: HOST=%DB_HOST% PORT=%DB_PORT% USER=%DB_USER% DB=%DB_NAME%
    goto :end
)

REM Set PGPASSWORD environment variable
set PGPASSWORD=%DB_PASSWORD%

REM Check if platform_events table exists
"!PSQL_PATH!" -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'platform_events');" 2>nul | findstr /C:"t" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ✓ platform_events table exists
) else (
    echo    ✗ platform_events table does NOT exist
    echo    → Run: .\RUN_MIGRATION_006.bat to create it
)

REM Clear password from environment
set PGPASSWORD=

:end
echo.
echo ================================================
echo   CHECK COMPLETE
echo ================================================
echo.
echo Next steps:
echo 1. If backend not running: Start Licensing API service
echo 2. If endpoints failing: Check backend logs
echo 3. If recent-activities empty: Run .\RUN_MIGRATION_006.bat
echo.
pause

