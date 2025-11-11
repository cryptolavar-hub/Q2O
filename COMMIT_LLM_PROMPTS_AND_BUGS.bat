@echo off
REM Commit script for API bug fixes and LLM prompts page rewrite
REM Run this script manually: .\COMMIT_LLM_PROMPTS_AND_BUGS.bat

cd /d "%~dp0"

echo.
echo ================================================
echo   COMMITTING API BUG FIXES AND LLM PROMPTS
echo ================================================
echo.

REM Show current status first
echo [INFO] Current git status:
git status --short
echo.

REM Stage all modified and new files
echo [1/3] Staging all changes...
git add -A

REM Show what will be committed
echo.
echo [2/3] Files staged for commit:
git status --short
echo.

REM Check if there are any changes to commit
git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo ================================================
    echo   NO CHANGES TO COMMIT!
    echo ================================================
    echo.
    echo All files are already committed or there are no changes.
    echo.
    pause
    exit /b 0
)

REM Commit with detailed message
echo [3/3] Creating commit...
echo.

git commit -m "Fix critical API bugs and complete LLM prompts page rewrite" ^
  -m "Bug Fixes:" ^
  -m "- Fixed activation code generation endpoint (/admin/api/codes/generate)" ^
  -m "- Fixed code revocation to use DELETE with code_id parameter" ^
  -m "- Fixed LLM config to use /api/llm/system and /api/llm/projects endpoints" ^
  -m "- Updated codes page to pass code.id for revocation" ^
  -m "- Fixed .gitignore to allow TypeScript lib directories" ^
  -m "" ^
  -m "LLM Prompts Page:" ^
  -m "- Complete rewrite with database integration (650+ lines)" ^
  -m "- System, Project, and Agent prompt management" ^
  -m "- Full CRUD functionality with PostgreSQL backend" ^
  -m "- Modern UI with design system components (Card, Button)" ^
  -m "- Proper error handling and validation" ^
  -m "" ^
  -m "Backend:" ^
  -m "- Updated admin_api.py with proper exception handling" ^
  -m "- Fixed ActivationCode.revoked_at field usage" ^
  -m "" ^
  -m "Documentation:" ^
  -m "- Added comprehensive bug fix documentation" ^
  -m "- Added LLM prompts page implementation summary" ^
  -m "- Added session update documentation" ^
  -m "- Added commit helper scripts"

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
    echo Error code: %ERRORLEVEL%
    echo.
    echo Possible reasons:
    echo - Git configuration issue
    echo - No changes to commit (already committed)
    echo.
    echo Check status: git status
    echo.
)

pause
