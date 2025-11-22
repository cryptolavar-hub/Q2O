@echo off
REM Commit critical API bug fixes

cd /d "%~dp0"

echo.
echo ================================================
echo   COMMITTING CRITICAL API BUG FIXES
echo ================================================
echo.

git add .gitignore
git add addon_portal/apps/admin-portal/src/lib/api.ts
git add addon_portal/apps/admin-portal/src/pages/codes.tsx
git add addon_portal/apps/admin-portal/src/pages/llm/configuration.tsx
git add COMMIT_NOW.bat
git add COMMIT_API_FIXES.bat
git add STAGE_ALL.bat
git add NOV11_FINAL_SUMMARY.md
git add API_BUGS_FIXED.md

echo Staging complete!
echo.

git commit -m "Fix critical API endpoint mismatches in activation codes and LLM config" -m "Bug 1: Fixed generateCodes endpoint (now /admin/api/codes/generate with JSON)" -m "Bug 2: Fixed revokeCode to use DELETE /admin/api/codes/{code_id}" -m "Bug 3: Fixed LLM config to use /api/llm/system and /api/llm/projects" -m "- Updated codes page to pass code.id for revocation" -m "- Updated LLM config page to use new DB-backed endpoints" -m "- Fixed .gitignore to allow TypeScript lib directories" -m "- Added comprehensive bug fix documentation"

echo.
echo ================================================
echo   COMMIT SUCCESSFUL!
echo ================================================
echo.
echo Next steps:
echo 1. Run: git push
echo 2. Run: .\RUN_LLM_MIGRATION.ps1
echo 3. Test: .\START_ALL.bat
echo.
pause

