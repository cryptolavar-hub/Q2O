@echo off
REM Fix Database Connection Issue - SQLite vs PostgreSQL
REM This script helps diagnose and fix the database connection problem

cd /d "%~dp0"

echo.
echo ================================================
echo   DATABASE CONNECTION DIAGNOSIS & FIX
echo ================================================
echo.

REM Check if .env file exists
if exist ".env" (
    echo [1/3] ✓ .env file found
    echo.
    echo Checking for DB_DSN...
    findstr /C:"DB_DSN=" ".env" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [2/3] ✓ DB_DSN found in .env
        echo.
        echo Current DB_DSN value:
        powershell -Command "Get-Content .env | Select-String '^DB_DSN=' | Select-Object -First 1"
        echo.
        echo [3/3] Checking database type...
        findstr /C:"sqlite" ".env" >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo    ✗ PROBLEM FOUND: DB_DSN is set to SQLite!
            echo    → The application should use PostgreSQL
            echo    → Update .env file with PostgreSQL connection string
            echo.
            echo    Required format:
            echo    DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
            echo.
        ) else (
            findstr /C:"postgresql" ".env" >nul 2>&1
            if %ERRORLEVEL% EQU 0 (
                echo    ✓ DB_DSN is set to PostgreSQL
                echo    → Configuration looks correct
                echo    → Restart the backend API to apply changes
                echo.
            ) else (
                echo    ? Unknown database type in DB_DSN
                echo    → Please verify DB_DSN format
                echo.
            )
        )
    ) else (
        echo [2/3] ✗ PROBLEM FOUND: DB_DSN not found in .env
        echo    → The application will use SQLite default
        echo    → Add DB_DSN to .env file
        echo.
        echo    Required format:
        echo    DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
        echo.
    )
) else (
    echo [1/3] ✗ PROBLEM FOUND: .env file not found!
    echo    → The application will use SQLite default
    echo    → Create .env file at project root
    echo.
    echo    Location: C:\Q2O_Combined\.env
    echo.
    echo    Copy from: addon_portal\env.example.txt
    echo    Then add your DB_DSN:
    echo    DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
    echo.
)

echo ================================================
echo   NEXT STEPS
echo ================================================
echo.
echo 1. Ensure .env file exists at: C:\Q2O_Combined\.env
echo 2. Add/Update DB_DSN to use PostgreSQL:
echo    DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
echo 3. Replace YOUR_PASSWORD with your actual PostgreSQL password
echo 4. Restart the backend API
echo 5. Verify Admin Dashboard works
echo.
pause

