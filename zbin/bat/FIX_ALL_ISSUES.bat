@echo off
REM Comprehensive Fix Script for Q2O Admin Portal Issues
REM Date: November 18, 2025

cd /d "%~dp0"

echo.
echo ================================================
echo   Q2O ADMIN PORTAL - COMPREHENSIVE FIX SCRIPT
echo ================================================
echo.

REM ================================================
REM STEP 1: Install psycopg[binary] driver
REM ================================================
echo [1/6] Installing PostgreSQL driver (psycopg[binary])...
python -m pip install "psycopg[binary]>=3.1.0,<4.0.0"
if %ERRORLEVEL% NEQ 0 (
    echo    ✗ Failed to install psycopg[binary]
    echo    → Please install manually: pip install "psycopg[binary]>=3.1.0,<4.0.0"
    goto :error
)
echo    ✓ psycopg[binary] installed successfully
echo.

REM ================================================
REM STEP 2: Verify .env file exists and has DB_DSN
REM ================================================
echo [2/6] Checking .env file configuration...
if not exist ".env" (
    echo    ✗ .env file not found at C:\Q2O_Combined\.env
    echo    → Please create .env file with DB_DSN
    goto :error
)

REM Use Python script to fix DB_DSN (handles special characters properly)
echo    → Running fix_db_dsn.py to verify/fix DB_DSN...
python fix_db_dsn.py
if %ERRORLEVEL% NEQ 0 (
    echo    ✗ Failed to run fix_db_dsn.py
    echo    → Please run manually: python fix_db_dsn.py
    goto :error
)

REM Verify DB_DSN is complete (contains @localhost)
findstr /C:"DB_DSN=" ".env" | findstr /C:"@localhost" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    ✗ DB_DSN is still incomplete after fix
    echo    → Please check .env file manually
    goto :error
)
echo    ✓ DB_DSN verified and complete
echo.

REM ================================================
REM STEP 3: Test database connection
REM ================================================
echo [3/6] Testing PostgreSQL database connection...
python -c "from sqlalchemy import create_engine, inspect; from addon_portal.api.core.settings import settings; engine = create_engine(settings.DB_DSN); insp = inspect(engine); tables = insp.get_table_names(); print('✓ Connected successfully'); print(f'Found {len(tables)} tables')"
if %ERRORLEVEL% NEQ 0 (
    echo    ✗ Database connection failed
    echo    → Check DB_DSN in .env file
    echo    → Verify PostgreSQL is running
    echo    → Verify database 'quick2odoo' exists
    goto :error
)
echo    ✓ Database connection successful
echo.

REM ================================================
REM STEP 4: List all tables in database
REM ================================================
echo [4/6] Checking database schema...
python -c "from sqlalchemy import create_engine, inspect; from addon_portal.api.core.settings import settings; engine = create_engine(settings.DB_DSN); insp = inspect(engine); tables = sorted(insp.get_table_names()); print('Tables found:'); [print(f'  - {t}') for t in tables]"
if %ERRORLEVEL% NEQ 0 (
    echo    ⚠ Could not list tables (connection may have failed)
) else (
    echo    ✓ Schema check complete
)
echo.

REM ================================================
REM STEP 5: Check for required tables
REM ================================================
echo [5/6] Verifying required tables exist...
python -c "from sqlalchemy import create_engine, inspect; from addon_portal.api.core.settings import settings; engine = create_engine(settings.DB_DSN); insp = inspect(engine); tables = set(insp.get_table_names()); required = {'tenants', 'activation_codes', 'devices', 'subscriptions', 'plans', 'llm_project_config', 'llm_system_config', 'platform_events'}; missing = required - tables; print('Required tables:'); [print(f'  {'✓' if t in tables else '✗'} {t}') for t in sorted(required)]; print(f'\nMissing tables: {len(missing)}'); [print(f'  - {t}') for t in sorted(missing)] if missing else None"
if %ERRORLEVEL% NEQ 0 (
    echo    ⚠ Could not verify tables
) else (
    echo    ✓ Table verification complete
)
echo.

REM ================================================
REM STEP 6: Check for missing columns
REM ================================================
echo [6/6] Checking for missing columns in tenants table...
python -c "from sqlalchemy import create_engine, inspect; from addon_portal.api.core.settings import settings; engine = create_engine(settings.DB_DSN); insp = inspect(engine); if 'tenants' in insp.get_table_names(): cols = {c['name'] for c in insp.get_columns('tenants')}; required_cols = {'email', 'phone_number', 'otp_delivery_method'}; missing = required_cols - cols; print('Tenants table columns:'); print(f'  Required: {sorted(required_cols)}'); print(f'  Missing: {sorted(missing) if missing else \"None\"}'); print(f'  {'✓ All required columns present' if not missing else '✗ Missing columns - run migration 007'}')"
if %ERRORLEVEL% NEQ 0 (
    echo    ⚠ Could not check columns
) else (
    echo    ✓ Column check complete
)
echo.

REM ================================================
REM SUCCESS
REM ================================================
echo ================================================
echo   FIX SCRIPT COMPLETED
echo ================================================
echo.
echo Next steps:
echo   1. Restart the backend API server
echo   2. Refresh the Admin Portal in your browser
echo   3. Check if tenant list page loads data
echo   4. Verify error messages are readable (not [object Object])
echo.
echo If issues persist:
echo   - Check logs/api_*.log for detailed error messages
echo   - Verify PostgreSQL is running: pg_isready
echo   - Run missing migrations if tables/columns are missing
echo.
goto :end

:error
echo.
echo ================================================
echo   FIX SCRIPT FAILED
echo ================================================
echo.
echo Please resolve the errors above and run again.
echo.
goto :end

:end
pause

