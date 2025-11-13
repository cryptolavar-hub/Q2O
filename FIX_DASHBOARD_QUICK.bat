@echo off
REM Quick fix script - Makes recent-activities endpoint safe
REM This ensures the dashboard works even if migration 006 hasn't been run

cd /d "%~dp0"

echo.
echo ================================================
echo   QUICK DASHBOARD FIX
echo ================================================
echo.
echo This script ensures the dashboard works even if
echo the platform_events table doesn't exist yet.
echo.
echo The fix has already been applied to admin_api.py
echo to handle missing tables gracefully.
echo.
echo [1/1] Verifying fix is in place...

findstr /C:"ProgrammingError" "addon_portal\api\routers\admin_api.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Error handling is in place
    echo    ✓ Dashboard should work now
) else (
    echo    ✗ Fix not found - may need manual update
    echo    → Check admin_api.py recent-activities endpoint
)

echo.
echo ================================================
echo   NEXT STEPS
echo ================================================
echo.
echo 1. Restart the backend API
echo 2. Test the dashboard at http://localhost:3002
echo 3. If recent-activities is empty, run: .\RUN_MIGRATION_006.bat
echo.
echo The dashboard will work, but Recent Activities will be empty
echo until migration 006 is run to create the platform_events table.
echo.
pause

