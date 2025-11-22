@echo off
REM =========================================================================
REM Check Current Database Configuration
REM =========================================================================

echo.
echo =========================================================================
echo  Current Database Status
echo =========================================================================
echo.

cd addon_portal

if exist .env (
    echo [OK] .env file exists
    echo.
    echo Current Configuration:
    findstr /C:"DB_DSN" .env
    echo.
    
    findstr /C:"sqlite" .env >nul
    if %ERRORLEVEL% == 0 (
        echo Database Type: SQLite
        echo Location: addon_portal\q2o_licensing.db
        if exist q2o_licensing.db (
            echo Status: [OK] Database file exists
        ) else (
            echo Status: [WARNING] Database file missing
        )
    ) else (
        echo Database Type: PostgreSQL
        echo Location: localhost:5432/q2o
        echo Service: postgresql-x64-18
    )
) else (
    echo [WARNING] .env file not found
    echo.
    echo Using default: SQLite
)

cd ..

echo.
echo =========================================================================
echo.
echo To switch databases:
echo   - SWITCH_TO_POSTGRESQL.bat
echo   - SWITCH_TO_SQLITE.bat
echo.
pause

