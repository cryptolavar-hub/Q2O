@echo off
REM Simple staging script - stages all changes for manual commit
REM Run this script: .\STAGE_ALL_CHANGES.bat
REM Then commit manually: git commit -m "Your message"

cd /d "%~dp0"

echo.
echo ================================================
echo   STAGING ALL CHANGES
echo ================================================
echo.

REM Stage all modified and new files
git add -A

echo.
echo ================================================
echo   STAGING COMPLETE!
echo ================================================
echo.

echo Files staged:
git status --short
echo.

echo Next steps:
echo 1. Review changes: git status
echo 2. Commit manually: git commit -m "Your commit message"
echo 3. Or use: .\COMMIT_LLM_PROMPTS_AND_BUGS.bat
echo.

pause

