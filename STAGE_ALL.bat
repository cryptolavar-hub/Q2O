@echo off
cd /d "%~dp0"
git add .gitignore
git add addon_portal/apps/admin-portal/src/lib/api.ts
git add addon_portal/api/routers/admin_api.py
git add COMMIT_NOW.bat
git add COMMIT_API_FIXES.bat
git add STAGE_ALL.bat
git add NOV11_FINAL_SUMMARY.md
echo All files staged!
git status -sb

