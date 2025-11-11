@echo off
REM Commit script for API bug fixes and LLM prompts page rewrite
REM Run this script manually: .\COMMIT_LLM_PROMPTS_AND_BUGS.bat

cd /d "%~dp0"

echo.
echo ================================================
echo   COMMITTING API BUG FIXES AND LLM PROMPTS
echo ================================================
echo.

REM Stage critical bug fixes
echo [1/5] Staging API bug fixes...
git add addon_portal/apps/admin-portal/src/lib/api.ts
git add addon_portal/apps/admin-portal/src/pages/codes.tsx
git add addon_portal/apps/admin-portal/src/pages/llm/configuration.tsx

REM Stage LLM prompts page rewrite
echo [2/5] Staging LLM prompts page rewrite...
git add addon_portal/apps/admin-portal/src/pages/llm/prompts.tsx

REM Stage documentation
echo [3/5] Staging documentation...
git add API_BUGS_FIXED.md
git add LLM_PROMPTS_PAGE_COMPLETE.md
git add SESSION_UPDATE_LLM_PROMPTS.md
git add COMMIT_LLM_PROMPTS_AND_BUGS.bat

REM Stage any other related files (if they exist)
echo [4/5] Checking for other modified files...
git add addon_portal/apps/admin-portal/src/pages/llm/prompts.tsx 2>nul

echo.
echo [5/5] All files staged!
echo.

REM Show what will be committed
echo ================================================
echo   FILES TO BE COMMITTED:
echo ================================================
git status --short
echo.

REM Commit with detailed message
echo ================================================
echo   CREATING COMMIT...
echo ================================================
echo.

git commit -m "Fix critical API bugs and complete LLM prompts page rewrite" ^
  -m "Bug Fixes:" ^
  -m "- Fixed activation code generation endpoint (/admin/api/codes/generate)" ^
  -m "- Fixed code revocation to use DELETE with code_id parameter" ^
  -m "- Fixed LLM config to use /api/llm/system and /api/llm/projects endpoints" ^
  -m "- Updated codes page to pass code.id for revocation" ^
  -m "" ^
  -m "LLM Prompts Page:" ^
  -m "- Complete rewrite with database integration (650+ lines)" ^
  -m "- System, Project, and Agent prompt management" ^
  -m "- Full CRUD functionality with PostgreSQL backend" ^
  -m "- Modern UI with design system components (Card, Button)" ^
  -m "- Proper error handling and validation" ^
  -m "" ^
  -m "Documentation:" ^
  -m "- Added comprehensive bug fix documentation" ^
  -m "- Added LLM prompts page implementation summary" ^
  -m "- Added session update documentation"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo   COMMIT SUCCESSFUL! ✓
    echo ================================================
    echo.
    echo Next steps:
    echo 1. Review the commit: git show HEAD
    echo 2. Push to remote: git push
    echo 3. Test the changes:
    echo    - Visit http://localhost:3002/llm/prompts
    echo    - Test activation code generation
    echo    - Test code revocation
    echo.
) else (
    echo.
    echo ================================================
    echo   COMMIT FAILED! ✗
    echo ================================================
    echo.
    echo Possible reasons:
    echo - No changes to commit (all files already committed)
    echo - Git configuration issue
    echo.
    echo Check status: git status
    echo.
)

pause

