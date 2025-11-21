@echo off
REM Comprehensive commit script for Q2O Platform
REM This script stages all changes and prepares for commit to GitHub
REM Run this script: .\COMMIT_TO_GITHUB.bat

cd /d "%~dp0"

echo.
echo ================================================
echo   Q2O PLATFORM - GITHUB COMMIT SCRIPT
echo ================================================
echo.
echo This script will:
echo 1. Stage all modified and new files
echo 2. Show git status
echo 3. Create a comprehensive commit message
echo 4. Push to GitHub (if you approve)
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo ================================================
echo   STAGING ALL CHANGES
echo ================================================
echo.

REM Stage all changes (including new files)
git add -A

echo.
echo ================================================
echo   GIT STATUS
echo ================================================
echo.

git status --short

echo.
echo ================================================
echo   COMMIT MESSAGE PREVIEW
echo ================================================
echo.

set COMMIT_MSG=Week 3 Complete: Tenant Portal Foundation + Task Tracking System

set COMMIT_BODY=Major Milestones Achieved:
set COMMIT_BODY=%COMMIT_BODY%^
- Week 1-2: OTP Authentication, Project Management, Subscription Validation
set COMMIT_BODY=%COMMIT_BODY%^
- Week 3: Activation Code System, Project Execution, Status Page with GraphQL
set COMMIT_BODY=%COMMIT_BODY%^
- Task Tracking: Dedicated agent_tasks table with full agent integration
set COMMIT_BODY=%COMMIT_BODY%^
- GraphQL API: Real-time subscriptions with real database data
set COMMIT_BODY=%COMMIT_BODY%^
- Status Page: Tenant view with expandable progress bars, search, pagination
set COMMIT_BODY=%COMMIT_BODY%^
- Admin Dashboard: Activation code usage tracking display
set COMMIT_BODY=%COMMIT_BODY%^
- Security: Enhanced DB_DSN validation in CHECK_DASHBOARD_STATUS.bat
set COMMIT_BODY=%COMMIT_BODY%^
- Documentation: Updated README.md and PROJECT_STATUS_NOV20_2025.md

echo Title: %COMMIT_MSG%
echo.
echo Body:
echo %COMMIT_BODY%
echo.

echo ================================================
echo   READY TO COMMIT
echo ================================================
echo.
echo Do you want to commit these changes? (Y/N)
set /p CONFIRM=

if /i "%CONFIRM%" NEQ "Y" (
    echo.
    echo Commit cancelled.
    echo.
    echo To commit manually, run:
    echo   git commit -m "%COMMIT_MSG%" -m "%COMMIT_BODY%"
    echo.
    pause
    exit /b
)

echo.
echo ================================================
echo   COMMITTING CHANGES
echo ================================================
echo.

git commit -m "%COMMIT_MSG%" -m "%COMMIT_BODY%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Commit failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   COMMIT SUCCESSFUL
echo ================================================
echo.

echo Do you want to push to GitHub? (Y/N)
set /p PUSH_CONFIRM=

if /i "%PUSH_CONFIRM%" NEQ "Y" (
    echo.
    echo Push cancelled.
    echo.
    echo To push manually, run:
    echo   git push origin main
    echo   (or: git push origin master)
    echo.
    pause
    exit /b
)

echo.
echo ================================================
echo   PUSHING TO GITHUB
echo ================================================
echo.

REM Try to detect the default branch
git branch --show-current >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%b in ('git branch --show-current') do set CURRENT_BRANCH=%%b
    echo Pushing to branch: %CURRENT_BRANCH%
    git push origin %CURRENT_BRANCH%
) else (
    echo Attempting to push to 'main' branch...
    git push origin main 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Attempting to push to 'master' branch...
        git push origin master
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Push failed!
    echo.
    echo Possible reasons:
    echo - No remote configured
    echo - Authentication required
    echo - Branch name mismatch
    echo.
    echo To push manually, run:
    echo   git push origin YOUR_BRANCH_NAME
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   SUCCESS!
echo ================================================
echo.
echo All changes have been committed and pushed to GitHub!
echo.
echo Summary:
echo - Commit: %COMMIT_MSG%
echo - Branch: %CURRENT_BRANCH%
echo - Status: Pushed to GitHub
echo.
pause

