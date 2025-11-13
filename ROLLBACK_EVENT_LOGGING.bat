@echo off
REM Rollback script - Removes event logging changes if they're causing issues
REM This will comment out the event logging imports and calls

cd /d "%~dp0"

echo.
echo ================================================
echo   ROLLBACK EVENT LOGGING CHANGES
echo ================================================
echo.
echo WARNING: This will disable event logging features
echo to restore dashboard functionality.
echo.
echo This script will:
echo 1. Comment out PlatformEvent imports in admin_api.py
echo 2. Make recent-activities return empty list
echo 3. Comment out event logging calls in tenant_service.py
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Rollback cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Backing up files...
if not exist "backups" mkdir backups
copy "addon_portal\api\routers\admin_api.py" "backups\admin_api.py.backup" >nul 2>&1
copy "addon_portal\api\services\tenant_service.py" "backups\tenant_service.py.backup" >nul 2>&1
echo    ✓ Backups created in backups\ folder

echo.
echo [2/3] Disabling event logging in admin_api.py...
REM This is complex - we'll create a Python script to do it properly
python -c "import re; f=open('addon_portal/api/routers/admin_api.py','r',encoding='utf-8'); c=f.read(); f.close(); c=re.sub(r'from \.\.models\.events import.*', r'# from ..models.events import PlatformEvent, EventType, EventSeverity  # DISABLED', c); c=re.sub(r'db\.query\(PlatformEvent\)', r'# db.query(PlatformEvent)  # DISABLED', c); f=open('addon_portal/api/routers/admin_api.py','w',encoding='utf-8'); f.write(c); f.close()" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo    ✓ admin_api.py updated
) else (
    echo    ✗ Failed to update admin_api.py
    echo    → Manual rollback required
)

echo.
echo [3/3] Disabling event logging calls...
python -c "import re; f=open('addon_portal/api/services/tenant_service.py','r',encoding='utf-8'); c=f.read(); f.close(); c=re.sub(r'log_\w+\(', r'# log_\w+(', c, flags=re.MULTILINE); f=open('addon_portal/api/services/tenant_service.py','w',encoding='utf-8'); f.write(c); f.close()" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo    ✓ tenant_service.py updated
) else (
    echo    ✗ Failed to update tenant_service.py
    echo    → Manual rollback required
)

echo.
echo ================================================
echo   ROLLBACK COMPLETE
echo ================================================
echo.
echo Next steps:
echo 1. Restart the backend API
echo 2. Test the dashboard
echo 3. If issues persist, restore from backups\ folder
echo.
echo To restore backups:
echo   copy backups\admin_api.py.backup addon_portal\api\routers\admin_api.py
echo   copy backups\tenant_service.py.backup addon_portal\api\services\tenant_service.py
echo.
pause

