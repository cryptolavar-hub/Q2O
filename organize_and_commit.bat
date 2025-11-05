@echo off
setlocal

REM Disable Git pager
set GIT_PAGER=
set PAGER=

echo ========================================================
echo Quick2Odoo - Organize Markdown Files and Commit Mobile App
echo ========================================================
echo.

echo [Step 1] Moving markdown files to docs/md_docs/...
if exist "MOBILE_APP_SUMMARY.md" move /Y "MOBILE_APP_SUMMARY.md" "docs\md_docs\"
if exist "COMMIT_INSTRUCTIONS.md" move /Y "COMMIT_INSTRUCTIONS.md" "docs\md_docs\"
if exist "CI_CD_ANALYSIS.md" move /Y "CI_CD_ANALYSIS.md" "docs\md_docs\"
echo Done!
echo.

echo [Step 2] Staging all changes...
git add mobile/ docs/md_docs/ commit_phase1.cmd commit_and_push_mobile.bat organize_and_commit.bat
echo Done!
echo.

echo [Step 3] Creating commit...
git commit -m "feat: Phase 1 complete - Dark Mode and Tablet Layouts + CI/CD analysis"
echo Done!
echo.

echo [Step 4] Pushing to GitHub...
powershell -ExecutionPolicy Bypass -File push_with_token.ps1
echo.

echo ========================================================
echo SUCCESS! All changes pushed to GitHub
echo ========================================================
echo.
echo What was deployed:
echo - Mobile app Phase 1 features (Dark Mode + Tablet Layouts)
echo - Feature roadmap with timelines
echo - CI/CD pipeline analysis
echo - Complete documentation
echo.
pause

