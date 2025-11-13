@echo off
REM Run Migration 005: Add tenant scoping to projects
REM Direct path version - uses full PostgreSQL path

cd /d "%~dp0"

echo ================================================
echo   Q2O Database Migration 005
echo   Add Tenant Scoping to Projects
echo ================================================
echo.

set PSQL_PATH="C:\Program Files\PostgreSQL\18\bin\psql.exe"

REM Check if PostgreSQL exists at this path
if not exist %PSQL_PATH% (
    echo ERROR: PostgreSQL not found at %PSQL_PATH%
    echo Please update the PSQL_PATH variable in this script.
    echo.
    pause
    exit /b 1
)

echo [INFO] Using PostgreSQL at: %PSQL_PATH%
echo.

REM Database connection settings (update these if needed)
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=q2o
set DB_USER=q2o_user
set DB_PASSWORD=Q2OPostgres2025!

REM Try to read from .env file if it exists
if exist "addon_portal\.env" (
    echo [INFO] Reading database connection from .env file...
    for /f "tokens=2 delims==" %%a in ('findstr /C:"DB_DSN=" "addon_portal\.env"') do (
        set DB_DSN=%%a
    )
    
    REM Parse password from DB_DSN: postgresql+psycopg://user:password@host:port/database
    for /f "tokens=2 delims=:" %%a in ("%DB_DSN%") do (
        set DB_USER_PASS=%%a
    )
    for /f "tokens=2 delims=:" %%a in ("%DB_USER_PASS%") do (
        set DB_PASSWORD=%%a
    )
    REM Clean up password
    set DB_PASSWORD=%DB_PASSWORD:@=%
    set DB_PASSWORD=%DB_PASSWORD:/=%
)

REM Set PGPASSWORD environment variable (psql will use this automatically)
set PGPASSWORD=%DB_PASSWORD%

echo Database Settings:
echo   Host: %DB_HOST%
echo   Port: %DB_PORT%
echo   Database: %DB_NAME%
echo   User: %DB_USER%
echo   Password: ******** (from .env)
echo.

echo [1/2] Running migration script...
echo.

REM Run the migration script
%PSQL_PATH% -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f "addon_portal\migrations_manual\005_add_tenant_scoping_to_projects.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo   MIGRATION SUCCESSFUL!
    echo ================================================
    echo.
    echo [2/2] Verifying migration...
    echo.
    
    REM Verify the migration
    %PSQL_PATH% -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'llm_project_config' AND column_name IN ('tenant_id', 'activation_code_id');"
    
    echo.
    echo Migration complete! Check the output above to verify columns were added.
    echo.
) else (
    echo.
    echo ================================================
    echo   MIGRATION FAILED!
    echo ================================================
    echo.
    echo Possible issues:
    echo 1. Database connection failed (check host, port, user, password)
    echo 2. Database does not exist
    echo 3. User does not have permission
    echo 4. Tables already exist (migration may have already been run)
    echo.
    echo You can also run the SQL manually:
    echo 1. Open pgAdmin or another PostgreSQL client
    echo 2. Connect to your database
    echo 3. Open: addon_portal\migrations_manual\005_add_tenant_scoping_to_projects.sql
    echo 4. Execute the script
    echo.
)

pause

