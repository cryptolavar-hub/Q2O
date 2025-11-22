@echo off
REM Sync MAIN_CODE branch with full local project state and push to GitHub
REM This will overwrite MAIN_CODE on GitHub with your local state

cd /d "%~dp0"

echo.
echo ================================================
echo   SYNCING MAIN_CODE BRANCH TO GITHUB
echo ================================================
echo   This will overwrite MAIN_CODE on GitHub
echo   with your complete local project state
echo ================================================
echo.

REM Check if MAIN_CODE branch exists locally
git show-ref --verify --quiet refs/heads/MAIN_CODE
if %errorlevel% equ 0 (
    echo [1/5] MAIN_CODE branch exists locally. Switching to it...
    git checkout MAIN_CODE
) else (
    echo [1/5] MAIN_CODE branch does not exist locally. Creating it...
    git checkout -b MAIN_CODE
)

echo.
echo Current branch:
git branch --show-current
echo.

echo [2/5] Staging ALL changes in root folder...
git add -A

echo.
echo [3/5] Checking for changes to commit...
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo No changes to commit. All files are already committed.
) else (
    echo Changes detected. Creating commit...
    git commit -m "Complete project state sync - Nov 12 2025" -m "Branch: MAIN_CODE" -m "" -m "Full project synchronization - Complete local state:" -m "" -m "Tenant Management:" -m "- Complete CRUD operations (Create, Read, Update, Delete)" -m "- Tenant deletion workflow with impact preview" -m "- Cascading deletion with safety checks" -m "- Pagination, search, and filtering" -m "" -m "LLM Management:" -m "- POST /api/llm/projects endpoint for project creation" -m "- ProjectCreatePayload schema and create_project service" -m "- Complete CRUD for system/project/agent prompts" -m "- System prompt editable, saves to DB and syncs to .env" -m "- LLM Configuration page fully database-integrated" -m "" -m "Analytics Integration:" -m "- Database-backed analytics with Recharts" -m "- Activation trends, tenant usage, subscription distribution" -m "- Date range selector and loading states" -m "- Fixed API_BASE to use Next.js proxy (analytics.tsx, index.tsx)" -m "" -m "Bug Fixes:" -m "- Fix JsonLogFormatter to extract extra fields from record.__dict__" -m "- Fix Settings validation error for LLM_SYSTEM_PROMPT" -m "- Fix IPv6/IPv4 connection issues (Next.js proxy to 127.0.0.1:8080)" -m "- Fix tenant update SQLAlchemy error (InvalidRequestError)" -m "- Fix tenant deletion 404 error (route ordering)" -m "- Fix API_BASE hardcoded URLs (use Next.js proxy)" -m "" -m "UI/UX Improvements:" -m "- Responsive navigation menu (mobile hamburger, horizontal scroll)" -m "- Responsive AdminHeader component" -m "- Breadcrumbs on all pages" -m "- Design system components (Card, Button, Badge, StatCard)" -m "- Improved error messages and user feedback" -m "- Loading states throughout admin portal" -m "" -m "Infrastructure:" -m "- File-based logging system (logs/ directory)" -m "- Configurable logging levels (LOG_ENABLED, LOG_LEVEL)" -m "- Custom CORS middleware for OPTIONS handling" -m "- Service layer architecture (tenant_service, llm_config_service)" -m "- Structured exception handling" -m "" -m "This commit represents the complete, current state of the project" -m "as it exists on the local development machine." -m "" -m "Status: Admin Portal Licensing Dashboard 100% complete" -m "Date: November 12, 2025"
)

echo.
echo [4/5] Creating/updating tag: Nov-12-2025...
REM Delete tag if it exists locally, then create new one
git tag -d "Nov-12-2025" 2>nul
git tag -a "Nov-12-2025" -m "Major milestone: Complete project state - Admin Portal Licensing Dashboard 100% complete - Nov 12 2025"

echo.
echo [5/5] Pushing MAIN_CODE branch to GitHub (this will overwrite remote)...
echo WARNING: This will overwrite MAIN_CODE on GitHub with your local state
pause

git push origin MAIN_CODE --force

echo.
echo Pushing tag to GitHub...
git push origin Nov-12-2025 --force

echo.
echo ================================================
echo   SYNC COMPLETE!
echo ================================================
echo.
echo Branch: MAIN_CODE
echo Tag: Nov-12-2025
echo.
echo MAIN_CODE branch on GitHub now matches your local state.
echo.
echo Summary:
git log --oneline -1
echo.
echo Files status:
git status --short
echo.
pause

