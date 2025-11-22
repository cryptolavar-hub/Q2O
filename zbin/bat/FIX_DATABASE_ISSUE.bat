@echo off
REM Fix Database Issue - Create database or update DB_DSN
REM Date: November 18, 2025

cd /d "%~dp0"

echo.
echo ================================================
echo   FIX DATABASE ISSUE
echo ================================================
echo.
echo The database "quick2odoo" does not exist.
echo This is causing ALL API endpoints to fail.
echo.
echo Available databases found:
echo   - postgres
echo   - q2o
echo.
echo ================================================
echo   SOLUTION OPTIONS
echo ================================================
echo.
echo Option 1: Use existing "q2o" database (RECOMMENDED)
echo   This will update DB_DSN in .env to use "q2o"
echo.
echo Option 2: Create "quick2odoo" database manually
echo   You need to run this as postgres superuser:
echo     psql -U postgres -c "CREATE DATABASE quick2odoo;"
echo.
set /p choice="Choose option (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Updating DB_DSN to use "q2o" database...
    python -c "from pathlib import Path; env_path = Path(r'C:\Q2O_Combined\.env'); content = env_path.read_text(encoding='utf-8'); lines = content.split('\n'); new_lines = []; for line in lines: new_lines.append('DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o' if line.strip().startswith('DB_DSN=') else line); env_path.write_text('\n'.join(new_lines), encoding='utf-8'); print('✓ DB_DSN updated to use q2o database')"
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ✓ SUCCESS: DB_DSN updated to use "q2o" database
        echo.
        echo Next steps:
        echo   1. Restart the backend API
        echo   2. Test the Admin Portal
        echo   3. If tables are missing, run migrations
    ) else (
        echo ✗ Failed to update DB_DSN
    )
) else if "%choice%"=="2" (
    echo.
    echo ================================================
    echo   MANUAL DATABASE CREATION REQUIRED
    echo ================================================
    echo.
    echo Please run one of these commands as postgres superuser:
    echo.
    echo   psql -U postgres -c "CREATE DATABASE quick2odoo;"
    echo.
    echo OR in pgAdmin:
    echo   1. Connect as postgres user
    echo   2. Right-click Databases → Create → Database
    echo   3. Name: quick2odoo
    echo   4. Click Save
    echo.
    echo After creating the database:
    echo   1. Run migrations to create tables
    echo   2. Restart the backend API
    echo.
) else (
    echo Invalid choice. Exiting.
    goto :end
)

:end
pause

