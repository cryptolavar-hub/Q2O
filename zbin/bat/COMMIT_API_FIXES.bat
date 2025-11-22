@echo off
REM Commit API client fixes and gitignore update

cd /d "%~dp0"

echo Staging API fixes...
git add .gitignore
git add addon_portal/apps/admin-portal/src/lib/api.ts
git add addon_portal/api/routers/admin_api.py
git add COMMIT_NOW.bat
git add INSTALL_ADMIN_PORTAL_DEPS.ps1

echo.
echo Committing...
git commit -m "Fix activation code generation API and gitignore for TypeScript lib directories" -m "- Fix generateCodes to use correct endpoint /admin/api/codes/generate" -m "- Fix generateCodes to expect JSON response instead of redirect" -m "- Fix ActivationCode model field: revoked_at (not revoked)" -m "- Update .gitignore to allow TypeScript lib directories in apps" -m "- Add helper scripts for dependencies and commits"

echo.
echo Done!
pause

