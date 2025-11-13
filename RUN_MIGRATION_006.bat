@echo off
setlocal enabledelayedexpansion
REM Migration 006: Create Platform Events Table
REM Purpose: Database-backed event logging for all platform activities
REM Date: November 12, 2025

cd /d "%~dp0"

echo.
echo ================================================
echo   MIGRATION 006: PLATFORM EVENTS TABLE
echo ================================================
echo.
echo This migration creates the platform_events table
echo for database-backed event logging.
echo.

REM Hardcoded PostgreSQL path
set "PSQL_PATH=C:\Program Files\PostgreSQL\18\bin\psql.exe"
echo [DEBUG] Using hardcoded psql path: %PSQL_PATH%

REM Verify psql exists
if not exist "%PSQL_PATH%" (
    echo [ERROR] psql.exe not found at: %PSQL_PATH%
    echo.
    echo Please verify PostgreSQL 18 is installed at:
    echo C:\Program Files\PostgreSQL\18\
    echo.
    pause
    exit /b 1
)
echo [DEBUG] ✓ psql.exe found

REM Database connection settings (hardcoded defaults)
REM Note: Exclamation mark in password must be escaped or handled carefully
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=q2o
set DB_USER=q2o_user
set "DB_PASSWORD=Q2OPostgres2025^!"

echo [DEBUG] Default database credentials:
echo   Host: %DB_HOST%
echo   Port: %DB_PORT%
echo   Database: %DB_NAME%
echo   User: %DB_USER%
echo   Password: ******** (default)
echo.

REM Try to read DB_DSN from .env file
echo [DEBUG] Checking for .env file...
if exist "addon_portal\.env" (
    echo [DEBUG] ✓ .env file found
    echo [DEBUG] Attempting to parse DB_DSN...
    
    REM Extract DB_DSN line to temp file
    powershell -NoProfile -Command "Get-Content 'addon_portal\.env' | Where-Object { $_ -match '^DB_DSN=' } | Select-Object -First 1 | ForEach-Object { $_.Split('=',2)[1] }" > "%TEMP%\migration_dsn.txt" 2>nul
    
    REM Read DB_DSN from temp file
    if exist "%TEMP%\migration_dsn.txt" (
        set /p DB_DSN=<"%TEMP%\migration_dsn.txt"
        del "%TEMP%\migration_dsn.txt" >nul 2>&1
        
        echo [DEBUG] DB_DSN extracted successfully
        
        REM Parse credentials using PowerShell - write each to separate temp files
        if defined DB_DSN (
            echo [DEBUG] Parsing database credentials from DB_DSN...
            
            REM Extract password - PowerShell outputs it, batch reads it
            powershell -NoProfile -Command "$dsn='!DB_DSN!'; if ($dsn -match '://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)') { $matches[2] }" > "%TEMP%\migration_pass.txt" 2>nul
            if exist "%TEMP%\migration_pass.txt" (
                REM Read password - temporarily disable delayed expansion
                setlocal disabledelayedexpansion
                set /p DB_PASSWORD_TEMP=<"%TEMP%\migration_pass.txt"
                call endlocal & set "DB_PASSWORD=%%DB_PASSWORD_TEMP%%"
                del "%TEMP%\migration_pass.txt" >nul 2>&1
                echo [DEBUG] Password extracted from DB_DSN
            )
            
            REM Extract user
            powershell -NoProfile -Command "$dsn='!DB_DSN!'; if ($dsn -match '://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)') { $matches[1] }" > "%TEMP%\migration_user.txt" 2>nul
            if exist "%TEMP%\migration_user.txt" (
                set /p DB_USER=<"%TEMP%\migration_user.txt"
                del "%TEMP%\migration_user.txt" >nul 2>&1
            )
            
            REM Extract host
            powershell -NoProfile -Command "$dsn='!DB_DSN!'; if ($dsn -match '://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)') { $matches[3] }" > "%TEMP%\migration_host.txt" 2>nul
            if exist "%TEMP%\migration_host.txt" (
                set /p DB_HOST=<"%TEMP%\migration_host.txt"
                del "%TEMP%\migration_host.txt" >nul 2>&1
            )
            
            REM Extract port
            powershell -NoProfile -Command "$dsn='!DB_DSN!'; if ($dsn -match '://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)') { $matches[4] }" > "%TEMP%\migration_port.txt" 2>nul
            if exist "%TEMP%\migration_port.txt" (
                set /p DB_PORT=<"%TEMP%\migration_port.txt"
                del "%TEMP%\migration_port.txt" >nul 2>&1
            )
            
            REM Extract database name
            powershell -NoProfile -Command "$dsn='!DB_DSN!'; if ($dsn -match '://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)') { $matches[5] }" > "%TEMP%\migration_db.txt" 2>nul
            if exist "%TEMP%\migration_db.txt" (
                set /p DB_NAME=<"%TEMP%\migration_db.txt"
                del "%TEMP%\migration_db.txt" >nul 2>&1
            )
            
            echo [DEBUG] Parsed credentials from .env:
            echo   Host: !DB_HOST!
            echo   Port: !DB_PORT!
            echo   Database: !DB_NAME!
            echo   User: !DB_USER!
            echo   Password: ******** (from .env)
            echo.
        ) else (
            echo [WARNING] DB_DSN is empty, using defaults
        )
    ) else (
        echo [WARNING] Could not read DB_DSN from temp file, using defaults
    )
) else (
    echo [DEBUG] .env file not found, using default credentials
    echo.
)

REM Validate password is set
if not defined DB_PASSWORD (
    echo [WARNING] Password not set, using default
    set "DB_PASSWORD=Q2OPostgres2025^!"
)

echo [DEBUG] Final database connection settings:
echo   Host: !DB_HOST!
echo   Port: !DB_PORT!
echo   Database: !DB_NAME!
echo   User: !DB_USER!
echo   Password: ********
echo.

echo [1/2] Running migration script...
echo [DEBUG] psql path: %PSQL_PATH%
echo [DEBUG] Database host: !DB_HOST!
echo [DEBUG] Database port: !DB_PORT!
echo [DEBUG] Database name: !DB_NAME!
echo [DEBUG] Database user: !DB_USER!
echo [DEBUG] Password is set (hidden for security)
echo.

REM Set PGPASSWORD environment variable - NO PROMPTING ALLOWED
REM Extract password from .env and set PGPASSWORD using method that works with batch
echo [DEBUG] Setting PGPASSWORD from .env file (no prompting allowed)...
REM Extract password to temp file using PowerShell
powershell -NoProfile -Command "if (Test-Path 'addon_portal\.env') { $dsn = (Get-Content 'addon_portal\.env' | Where-Object { $_ -match '^DB_DSN=' } | Select-Object -First 1).Split('=',2)[1]; if ($dsn -match '://([^:]+):([^@]+)@') { $matches[2] | Out-File -FilePath '%TEMP%\pgpass_batch.txt' -Encoding ASCII -NoNewline } }" 2>nul

REM Read password from temp file WITHOUT delayed expansion to preserve special chars
if exist "%TEMP%\pgpass_batch.txt" (
    setlocal disabledelayedexpansion
    set /p PGPASSWORD_TEMP=<"%TEMP%\pgpass_batch.txt"
    call endlocal & set "PGPASSWORD=%%PGPASSWORD_TEMP%%"
    del "%TEMP%\pgpass_batch.txt" >nul 2>&1
    echo [DEBUG] ✓ PGPASSWORD set from .env file
) else (
    REM Fallback: Use default password
    echo [WARNING] Could not extract password from .env, using default
    set "PGPASSWORD=Q2OPostgres2025!"
)

REM Verify PGPASSWORD is set
if not defined PGPASSWORD (
    echo [ERROR] PGPASSWORD is not set! Migration will prompt for password.
    set "PGPASSWORD=Q2OPostgres2025!"
)

REM Test password authentication (should NOT prompt)
echo [DEBUG] Testing password authentication (no prompt expected)...
"%PSQL_PATH%" -h 127.0.0.1 -p !DB_PORT! -U !DB_USER! -d !DB_NAME! -c "SELECT 1;" >nul 2>&1
set TEST_EXIT_CODE=!ERRORLEVEL!
if !TEST_EXIT_CODE! EQU 0 (
    echo [DEBUG] ✓ Password authentication successful (no prompt occurred)
) else (
    echo [ERROR] Password authentication failed (exit code: !TEST_EXIT_CODE!)
    echo [ERROR] PGPASSWORD may not be set correctly - you may be prompted for password
)
echo.

REM Run the migration script
echo [DEBUG] Executing SQL migration...
echo [DEBUG] psql path: %PSQL_PATH%
echo [DEBUG] Connection: !DB_USER!@!DB_HOST!:!DB_PORT!/!DB_NAME!
echo [DEBUG] Using IPv4 address (127.0.0.1) to avoid IPv6 connection issues
echo.

REM Force IPv4 by using 127.0.0.1 instead of localhost
set DB_HOST_IP=127.0.0.1
if "!DB_HOST!"=="localhost" set DB_HOST_IP=127.0.0.1
if "!DB_HOST!"=="127.0.0.1" set DB_HOST_IP=127.0.0.1
if not "!DB_HOST!"=="localhost" if not "!DB_HOST!"=="127.0.0.1" set DB_HOST_IP=!DB_HOST!

echo [DEBUG] Connecting to: !DB_HOST_IP!:!DB_PORT!
"%PSQL_PATH%" -h !DB_HOST_IP! -p !DB_PORT! -U !DB_USER! -d !DB_NAME! -f "addon_portal\migrations_manual\006_create_platform_events_table.sql"
set MIGRATION_EXIT_CODE=!ERRORLEVEL!

echo [DEBUG] Migration exit code: !MIGRATION_EXIT_CODE!

if !MIGRATION_EXIT_CODE! EQU 0 (
    echo.
    echo ================================================
    echo   MIGRATION SUCCESSFUL!
    echo ================================================
    echo.
    echo [2/2] Verifying migration...
    echo.

    REM Verify the migration
    echo [DEBUG] Verifying table creation...
    "%PSQL_PATH%" -h !DB_HOST_IP! -p !DB_PORT! -U !DB_USER! -d !DB_NAME! -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'platform_events' AND column_name IN ('event_type', 'severity', 'title', 'created_at');"
    set VERIFY_EXIT_CODE=!ERRORLEVEL!
    
    echo [DEBUG] Verification exit code: !VERIFY_EXIT_CODE!
    
    if !VERIFY_EXIT_CODE! EQU 0 (
        echo [DEBUG] ✓ Verification successful - table exists with expected columns.
    ) else (
        echo [WARNING] Verification query failed, but migration may have succeeded.
    )

    echo.
    echo Migration complete! The platform_events table has been created.
    echo.
    echo Next steps:
    echo 1. Restart the backend API to load the new event model
    echo 2. Test event logging by creating/updating/deleting tenants
    echo 3. Check Recent Activities to see events appear
    echo.

    REM Clear password from environment and temp files
    set PGPASSWORD=
    if exist "%TEMP%\pgpass_batch.txt" del "%TEMP%\pgpass_batch.txt" >nul 2>&1
    if exist "%TEMP%\pgpass.txt" del "%TEMP%\pgpass.txt" >nul 2>&1
) else (
    echo.
    echo ================================================
    echo   MIGRATION FAILED!
    echo ================================================
    echo.
    echo [DEBUG] Migration failed with exit code: !MIGRATION_EXIT_CODE!
    echo.
    echo Possible issues:
    echo   1. Database connection failed (check host, port, user, password)
    echo   2. Database does not exist
    echo   3. User does not have permission
    echo   4. Table already exists (migration may have already been run)
    echo.
    echo Connection details used:
    echo   Host: !DB_HOST!
    echo   Port: !DB_PORT!
    echo   Database: !DB_NAME!
    echo   User: !DB_USER!
    echo.
    echo You can also run the SQL manually:
    echo 1. Open pgAdmin or another PostgreSQL client
    echo 2. Connect to your database
    echo 3. Open: addon_portal\migrations_manual\006_create_platform_events_table.sql
    echo 4. Execute the script
    echo.

    REM Clear password from environment and temp files
    set PGPASSWORD=
    if exist "%TEMP%\pgpass_batch.txt" del "%TEMP%\pgpass_batch.txt" >nul 2>&1
    if exist "%TEMP%\pgpass.txt" del "%TEMP%\pgpass.txt" >nul 2>&1
)

pause
