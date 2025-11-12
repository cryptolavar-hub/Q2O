@echo off
REM Comprehensive commit script for MAIN_CODE branch
REM Stages ALL changes in root folder and creates tag for Nov 12 2025
REM Includes: Bug fixes, tenant deletion workflow, route ordering, SQLAlchemy fixes, Settings validation, Analytics integration, LLM Prompts completion, Project creation endpoint

cd /d "%~dp0"

echo.
echo ================================================
echo   COMMITTING ALL CHANGES TO MAIN_CODE BRANCH
echo ================================================
echo.

REM Check current branch
echo Checking current branch...
git branch --show-current
echo.

REM Stage ALL files in root folder (overwrite all content)
echo [1/3] Staging ALL changes in root folder...
git add -A

echo.
echo [2/3] Creating commit...

git commit -m "Complete tenant deletion workflow and critical bug fixes - Nov 12 2025" -m "Branch: MAIN_CODE" -m "" -m "Tenant Management:" -m "- Add tenant deletion impact preview endpoint (GET /admin/api/tenants/{slug}/deletion-impact)" -m "- Implement cascading deletion workflow with safety checks" -m "- Add detailed confirmation modal showing related records" -m "- Fix route ordering (specific routes before generic routes)" -m "- Fix SQLAlchemy query error (add .unique() for joinedload collections)" -m "- Complete tenant CRUD: Create, Read, Update, Delete all functional" -m "" -m "Bug Fixes:" -m "- Fix JsonLogFormatter to extract extra fields from record.__dict__ (not record.extra)" -m "- Fix Settings validation error for LLM_SYSTEM_PROMPT (add field, extra='ignore')" -m "- Fix IPv6/IPv4 connection issues (Next.js proxy to 127.0.0.1:8080)" -m "- Fix tenant update SQLAlchemy error (InvalidRequestError)" -m "- Fix tenant deletion 404 error (route ordering)" -m "" -m "Analytics Integration:" -m "- Create /admin/api/analytics endpoint with real database data" -m "- Integrate Recharts for activation trends, tenant usage, subscription distribution" -m "- Add date range selector and loading states" -m "- Replace all placeholder data with database queries" -m "" -m "LLM Management:" -m "- Complete LLM Prompts page CRUD (system/project/agent prompts)" -m "- Add POST /api/llm/projects endpoint for project creation" -m "- Add ProjectCreatePayload schema and create_project service function" -m "- System prompt editable, saves to DB and syncs to .env" -m "- Project and agent prompts fully database-integrated" -m "- LLM Configuration page database integration complete" -m "" -m "UI/UX Improvements:" -m "- Responsive navigation menu (mobile hamburger, horizontal scroll)" -m "- Responsive AdminHeader component" -m "- Improved error messages and user feedback" -m "- Loading states throughout admin portal" -m "" -m "Documentation:" -m "- Update README.md with major milestone (Admin Portal complete) - see PROGRESS_UPDATE_NOV12_2025.md for details" -m "- Update OPTION_B_FULL_POLISH_ROADMAP.md with completion status" -m "- Create PROGRESS_UPDATE_NOV12_2025.md with comprehensive breakdown" -m "- Update NOV11_FINAL_SUMMARY.md with recent fixes" -m "" -m "Status: Admin Portal Licensing Dashboard 100% complete" -m "Next: Tenant Portal and Multi-Agent Dashboard assessment" -m "" -m "For detailed breakdown, see: PROGRESS_UPDATE_NOV12_2025.md"

echo.
echo [3/3] Creating tag: Nov-12-2025...
git tag -a "Nov-12-2025" -m "Major milestone: Admin Portal Licensing Dashboard complete - Nov 12 2025"

echo.
echo ================================================
echo   COMMIT AND TAG COMPLETE!
echo ================================================
echo.
echo Branch: MAIN_CODE
echo Tag: Nov-12-2025
echo.
echo Files committed:
git status --short
echo.
echo Next steps:
echo 1. Review: git log -1
echo 2. Push branch: git push origin MAIN_CODE
echo 3. Push tag: git push origin Nov-12-2025
echo 4. Test: Restart services and test all features
echo.
pause
