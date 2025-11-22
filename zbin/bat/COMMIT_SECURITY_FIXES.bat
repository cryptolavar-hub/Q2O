@echo off
REM Quick commit script for security fixes
cd /d "%~dp0"

echo Staging security fix files...
git add CHECK_DASHBOARD_STATUS.bat
git add SECURITY_FIX_PASSWORD_PARSING.md
git add SECURITY_FIX_HARDCODED_PASSWORDS.md
git add docs/WEEK1_TEST_PLAN.md

echo.
echo Committing...
git commit -m "security: Fix hardcoded password and password parsing vulnerabilities" -m "- Remove hardcoded DB password from CHECK_DASHBOARD_STATUS.bat" -m "- Fix password parsing to handle special characters (:, @)" -m "- Add comprehensive Week 1 test plan"

echo.
echo Done!
