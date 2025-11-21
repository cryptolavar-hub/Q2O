@echo off
REM =========================================================================
REM Q2O Documentation Reorganization - Commit Script
REM =========================================================================
REM This script stages, commits, and optionally pushes all documentation
REM reorganization changes to GitHub.
REM =========================================================================

cd /d "%~dp0"

echo.
echo ================================================
echo   Q2O Documentation Reorganization
echo   Git Commit & Push
echo ================================================
echo.

REM Stage all changes
echo [1/4] Staging all changes...
git add -A
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to stage files. Exiting.
    pause
    exit /b 1
)
echo   [OK] All files staged
echo.

REM Show status
echo [2/4] Current Git Status:
git status --short
echo.

REM Confirm commit
set /p confirm_commit="[3/4] Do you want to commit these changes? (y/n): "
if /i "%confirm_commit%" NEQ "y" (
    echo Commit cancelled.
    goto :end
)

REM Commit with comprehensive message
echo.
echo [3/4] Committing changes...
git commit -m "docs: Complete documentation reorganization and updates" ^
-m "Documentation Organization:" ^
-m "- Moved current status reports to docs/status_reports/" ^
-m "- Moved implementation summaries to docs/implementation_summaries/" ^
-m "- Moved current relevant docs to docs/" ^
-m "- Moved historical/outdated docs to docs/archive/historical/" ^
-m "- Created README.md files in docs/, docs/archive/, docs/md_docs/" ^
-m "" ^
-m "Documentation Updates:" ^
-m "- Updated root README.md with current state (Week 3 complete, 60% overall)" ^
-m "- Updated Platform Architecture diagram (GraphQL, Task Tracking)" ^
-m "- Updated Platform Evolution Timeline (Phase 3: Tenant Portal Week 1-3)" ^
-m "- Updated Development Roadmap (Week 4-5 in progress)" ^
-m "- Updated Business Model section (current implementation status)" ^
-m "- Fixed all documentation links to point to docs/ folder" ^
-m "" ^
-m "Comprehensive Project Assessment Updates:" ^
-m "- Updated date to November 20, 2025" ^
-m "- Updated version to 4.1" ^
-m "- Updated Key Metrics (GraphQL, Task Tracking, 9 migrations)" ^
-m "- Updated Current Platform State (Week 1-3 complete)" ^
-m "- Updated Recent Enhancements (Tenant Portal Foundation)" ^
-m "- Updated Technology Stack (GraphQL, psutil, async SQLAlchemy)" ^
-m "- Updated Development Velocity (Week 1-3 achievements)" ^
-m "- Updated Competitive Analysis (Q2O Platform branding)" ^
-m "- Updated Conclusion with current status and launch target" ^
-m "" ^
-m "Status: Week 3 Complete (60% overall) | Target Launch: Late Dec 2025 - Early Jan 2026"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to commit changes. Exiting.
    pause
    exit /b 1
)
echo   [OK] Changes committed successfully
echo.

REM Confirm push
set /p confirm_push="[4/4] Do you want to push these changes to GitHub? (y/n): "
if /i "%confirm_push%" NEQ "y" (
    echo Push cancelled.
    goto :end
)

REM Push to GitHub
echo.
echo [4/4] Pushing changes to GitHub...
git push origin MAIN_CODE
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to push to GitHub. Please check your connection or credentials.
    pause
    exit /b 1
)
echo   [OK] Successfully pushed to GitHub
echo.

:end
echo.
echo ================================================
echo   Operation Complete
echo ================================================
echo.
echo Summary:
echo   - Documentation files organized
echo   - README.md updated with current state
echo   - Comprehensive Project Assessment updated
echo   - Changes committed to git
if "%confirm_push%"=="y" (
    echo   - Changes pushed to GitHub
) else (
    echo   - Changes NOT pushed (run: git push origin MAIN_CODE)
)
echo.
pause

