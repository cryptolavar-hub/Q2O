@echo off
REM Add DB_DSN to .env file if it's missing
REM This fixes the database connection issue

cd /d "%~dp0"

echo.
echo ================================================
echo   ADDING DB_DSN TO .env FILE
echo ================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ✗ .env file not found!
    echo → Creating .env from template...
    copy "addon_portal\env.example.txt" ".env" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo    ✗ Failed to create .env file
        echo    → Please create .env manually at: C:\Q2O_Combined\.env
        goto :end
    )
    echo    ✓ .env file created
    echo.
)

REM Check if DB_DSN already exists
findstr /C:"DB_DSN=" ".env" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ DB_DSN already exists in .env
    echo.
    echo Current DB_DSN value:
    powershell -Command "Get-Content .env | Select-String '^DB_DSN=' | Select-Object -First 1"
    echo.
    echo If you need to update it, edit .env manually.
    goto :end
)

echo [1/2] DB_DSN not found in .env
echo [2/2] Adding DB_DSN to .env...
echo.

REM Try to extract password from RUN_MIGRATION_007.bat using PowerShell
set "DB_PASSWORD=YOUR_PASSWORD_HERE"
if exist "RUN_MIGRATION_007.bat" (
    REM Use PowerShell to extract and clean the password
    for /f "delims=" %%p in ('powershell -Command "$line = Get-Content 'RUN_MIGRATION_007.bat' | Select-String 'MIGRATION007_DB_PASSWORD=' | Select-Object -First 1; if ($line) { $pass = $line.ToString().Split('=',2)[1].Trim('\"'); $pass = $pass -replace '\\^', ''; Write-Output $pass }"') do (
        set "DB_PASSWORD=%%p"
    )
)

REM Add DB_DSN to .env file (append at the end)
echo. >> ".env"
echo # Database Configuration >> ".env"
echo DB_DSN=postgresql+psycopg://q2o_user:%DB_PASSWORD%@localhost:5432/q2o >> ".env"

if %ERRORLEVEL% EQU 0 (
    echo    ✓ DB_DSN added to .env
    echo.
    echo ================================================
    echo   DB_DSN ADDED
    echo ================================================
    echo.
    if "%DB_PASSWORD%"=="YOUR_PASSWORD_HERE" (
        echo The DB_DSN has been added with placeholder password.
        echo.
        echo You MUST update YOUR_PASSWORD_HERE with your actual PostgreSQL password.
        echo.
        echo Edit .env and change:
        echo    DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD_HERE@localhost:5432/q2o
        echo.
        echo To (example):
        echo    DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o
        echo.
    ) else (
        echo The DB_DSN has been added with password from RUN_MIGRATION_007.bat
        echo.
        echo Please verify the password is correct in .env:
        powershell -Command "Get-Content .env | Select-String '^DB_DSN=' | Select-Object -First 1"
        echo.
        echo If the password is incorrect, edit .env and update it.
        echo.
    )
    echo After updating the password:
    echo 1. Restart the backend API
    echo 2. Test the Admin Dashboard
    echo.
) else (
    echo    ✗ Failed to add DB_DSN to .env
    echo    → Please add it manually:
    echo    → DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD@localhost:5432/q2o
    echo.
)

:end
pause

