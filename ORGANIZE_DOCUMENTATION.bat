@echo off
REM =========================================================================
REM Q2O Documentation Organization Script
REM =========================================================================
REM This script organizes all markdown files into appropriate folders:
REM   - Current status reports -> docs/status_reports/
REM   - Implementation summaries -> docs/implementation_summaries/
REM   - Current relevant docs -> docs/
REM   - Historical/outdated docs -> docs/archive/historical/
REM =========================================================================

cd /d "%~dp0"

echo.
echo ================================================
echo   Q2O Documentation Organization
echo ================================================
echo.
echo This script will move markdown files to:
echo   - docs/status_reports/ (current status reports)
echo   - docs/implementation_summaries/ (implementation summaries)
echo   - docs/ (current relevant documentation)
echo   - docs/archive/historical/ (historical/outdated docs)
echo.
echo README.md will remain in root folder.
echo.
pause

REM Create directories if they don't exist
if not exist "docs\status_reports" mkdir "docs\status_reports"
if not exist "docs\implementation_summaries" mkdir "docs\implementation_summaries"
if not exist "docs\archive\historical" mkdir "docs\archive\historical"

echo.
echo Creating directories...
echo.

REM =========================================================================
REM MOVE CURRENT STATUS REPORTS
REM =========================================================================
echo Moving current status reports to docs/status_reports/...
if exist "PROJECT_STATUS_NOV20_2025.md" (
    move "PROJECT_STATUS_NOV20_2025.md" "docs\status_reports\" >nul 2>&1
    echo   [OK] PROJECT_STATUS_NOV20_2025.md
)

REM =========================================================================
REM MOVE CURRENT RELEVANT DOCS TO docs/
REM =========================================================================
echo.
echo Moving current relevant docs to docs/...
if exist "NEXT_STEPS_PROFILE_BILLING.md" (
    move "NEXT_STEPS_PROFILE_BILLING.md" "docs\" >nul 2>&1
    echo   [OK] NEXT_STEPS_PROFILE_BILLING.md
)

REM =========================================================================
REM MOVE IMPLEMENTATION SUMMARIES
REM =========================================================================
echo.
echo Moving implementation summaries to docs/implementation_summaries/...
if exist "REAL_DATA_IMPLEMENTATION_SUMMARY.md" (
    move "REAL_DATA_IMPLEMENTATION_SUMMARY.md" "docs\implementation_summaries\" >nul 2>&1
    echo   [OK] REAL_DATA_IMPLEMENTATION_SUMMARY.md
)
if exist "PROJECT_EXECUTION_IMPLEMENTATION_SUMMARY.md" (
    move "PROJECT_EXECUTION_IMPLEMENTATION_SUMMARY.md" "docs\implementation_summaries\" >nul 2>&1
    echo   [OK] PROJECT_EXECUTION_IMPLEMENTATION_SUMMARY.md
)

REM =========================================================================
REM MOVE HISTORICAL PROGRESS UPDATES
REM =========================================================================
echo.
echo Moving historical progress updates to docs/archive/historical/...
if exist "PROGRESS_UPDATE_NOV13_2025.md" (
    move "PROGRESS_UPDATE_NOV13_2025.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] PROGRESS_UPDATE_NOV13_2025.md
)
if exist "PROGRESS_UPDATE_NOV12_2025.md" (
    move "PROGRESS_UPDATE_NOV12_2025.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] PROGRESS_UPDATE_NOV12_2025.md
)
if exist "PROGRESS_UPDATE_NOV11_AFTERNOON.md" (
    move "PROGRESS_UPDATE_NOV11_AFTERNOON.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] PROGRESS_UPDATE_NOV11_AFTERNOON.md
)
if exist "GLOBAL_STATUS_NOV13_2025.md" (
    move "GLOBAL_STATUS_NOV13_2025.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] GLOBAL_STATUS_NOV13_2025.md
)

REM =========================================================================
REM MOVE HISTORICAL FIX SUMMARIES
REM =========================================================================
echo.
echo Moving historical fix summaries to docs/archive/historical/...
if exist "ADMIN_DASHBOARD_FIX_NOV19.md" (
    move "ADMIN_DASHBOARD_FIX_NOV19.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ADMIN_DASHBOARD_FIX_NOV19.md
)
if exist "ADMIN_DASHBOARD_FIX_SUMMARY.md" (
    move "ADMIN_DASHBOARD_FIX_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ADMIN_DASHBOARD_FIX_SUMMARY.md
)
if exist "OTP_VALIDATION_FIX_NOV19.md" (
    move "OTP_VALIDATION_FIX_NOV19.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] OTP_VALIDATION_FIX_NOV19.md
)
if exist "LAZY_LOADING_FIX_NOV19.md" (
    move "LAZY_LOADING_FIX_NOV19.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] LAZY_LOADING_FIX_NOV19.md
)
if exist "ACTIVATION_CODE_ASSIGNMENT_FIX.md" (
    move "ACTIVATION_CODE_ASSIGNMENT_FIX.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ACTIVATION_CODE_ASSIGNMENT_FIX.md
)
if exist "RUN_PROJECT_BUTTON_FIX.md" (
    move "RUN_PROJECT_BUTTON_FIX.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] RUN_PROJECT_BUTTON_FIX.md
)
if exist "DASHBOARD_FIX_SUMMARY.md" (
    move "DASHBOARD_FIX_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] DASHBOARD_FIX_SUMMARY.md
)
if exist "CRITICAL_FIX_SUMMARY.md" (
    move "CRITICAL_FIX_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] CRITICAL_FIX_SUMMARY.md
)
if exist "FINAL_FIX_SUMMARY.md" (
    move "FINAL_FIX_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] FINAL_FIX_SUMMARY.md
)
if exist "ISSUE_FIX_SUMMARY.md" (
    move "ISSUE_FIX_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ISSUE_FIX_SUMMARY.md
)
if exist "BREADCRUMBS_IMPLEMENTATION_SUMMARY.md" (
    move "BREADCRUMBS_IMPLEMENTATION_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] BREADCRUMBS_IMPLEMENTATION_SUMMARY.md
)

REM =========================================================================
REM MOVE HISTORICAL MIGRATION DOCS
REM =========================================================================
echo.
echo Moving historical migration docs to docs/archive/historical/...
if exist "MIGRATION_005_SUCCESS.md" (
    move "MIGRATION_005_SUCCESS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] MIGRATION_005_SUCCESS.md
)
if exist "MIGRATION_007_SUCCESS.md" (
    move "MIGRATION_007_SUCCESS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] MIGRATION_007_SUCCESS.md
)
if exist "MIGRATION_ALTERNATIVE_METHOD.md" (
    move "MIGRATION_ALTERNATIVE_METHOD.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] MIGRATION_ALTERNATIVE_METHOD.md
)
if exist "RUN_MIGRATION_005_MANUAL.md" (
    move "RUN_MIGRATION_005_MANUAL.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] RUN_MIGRATION_005_MANUAL.md
)
if exist "ASYNC_MIGRATION_COMPLETE.md" (
    move "ASYNC_MIGRATION_COMPLETE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ASYNC_MIGRATION_COMPLETE.md
)
if exist "ASYNC_MIGRATION_STATUS.md" (
    move "ASYNC_MIGRATION_STATUS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ASYNC_MIGRATION_STATUS.md
)
if exist "ASYNC_MIGRATION_PLAN.md" (
    move "ASYNC_MIGRATION_PLAN.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ASYNC_MIGRATION_PLAN.md
)

REM =========================================================================
REM MOVE HISTORICAL IMPLEMENTATION SUMMARIES
REM =========================================================================
echo.
echo Moving historical implementation summaries to docs/archive/historical/...
if exist "TENANT_CREATION_COMPLETE.md" (
    move "TENANT_CREATION_COMPLETE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] TENANT_CREATION_COMPLETE.md
)
if exist "PHASE1_DATABASE_UPDATES_COMPLETE.md" (
    move "PHASE1_DATABASE_UPDATES_COMPLETE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] PHASE1_DATABASE_UPDATES_COMPLETE.md
)
if exist "DAY1_COMPLETE_SUMMARY.md" (
    move "DAY1_COMPLETE_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] DAY1_COMPLETE_SUMMARY.md
)
if exist "NOV11_FINAL_SUMMARY.md" (
    move "NOV11_FINAL_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] NOV11_FINAL_SUMMARY.md
)

REM =========================================================================
REM MOVE HISTORICAL STATUS/UPDATE DOCS
REM =========================================================================
echo.
echo Moving historical status/update docs to docs/archive/historical/...
if exist "STATUS_PAGE_REALTIME_UPDATE.md" (
    move "STATUS_PAGE_REALTIME_UPDATE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] STATUS_PAGE_REALTIME_UPDATE.md
)
if exist "GRAPHQL_STATUS_PAGE_SETUP.md" (
    move "GRAPHQL_STATUS_PAGE_SETUP.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] GRAPHQL_STATUS_PAGE_SETUP.md
)
if exist "GRAPHQL_DEPENDENCY_ISSUE.md" (
    move "GRAPHQL_DEPENDENCY_ISSUE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] GRAPHQL_DEPENDENCY_ISSUE.md
)
if exist "WINDOWS_EVENT_LOOP_FIX.md" (
    move "WINDOWS_EVENT_LOOP_FIX.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] WINDOWS_EVENT_LOOP_FIX.md
)

REM =========================================================================
REM MOVE HISTORICAL SECURITY FIX DOCS
REM =========================================================================
echo.
echo Moving historical security fix docs to docs/archive/historical/...
if exist "SECURITY_FIX_VERIFICATION.md" (
    move "SECURITY_FIX_VERIFICATION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] SECURITY_FIX_VERIFICATION.md
)
if exist "SECURITY_FIX_PASSWORD_PARSING.md" (
    move "SECURITY_FIX_PASSWORD_PARSING.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] SECURITY_FIX_PASSWORD_PARSING.md
)
if exist "SECURITY_FIX_HARDCODED_PASSWORDS.md" (
    move "SECURITY_FIX_HARDCODED_PASSWORDS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] SECURITY_FIX_HARDCODED_PASSWORDS.md
)

REM =========================================================================
REM MOVE HISTORICAL DATABASE/ENV DOCS
REM =========================================================================
echo.
echo Moving historical database/ENV docs to docs/archive/historical/...
if exist "DATABASE_CONNECTION_ISSUE_DIAGNOSIS.md" (
    move "DATABASE_CONNECTION_ISSUE_DIAGNOSIS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] DATABASE_CONNECTION_ISSUE_DIAGNOSIS.md
)
if exist "CREATE_DATABASE_INSTRUCTIONS.md" (
    move "CREATE_DATABASE_INSTRUCTIONS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] CREATE_DATABASE_INSTRUCTIONS.md
)
if exist "ENV_PATH_FIX_SUMMARY.md" (
    move "ENV_PATH_FIX_SUMMARY.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ENV_PATH_FIX_SUMMARY.md
)
if exist "ENV_CONSOLIDATION_VERIFICATION.md" (
    move "ENV_CONSOLIDATION_VERIFICATION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ENV_CONSOLIDATION_VERIFICATION.md
)
if exist "ENV_VARIABLES_COMPLETE_REFERENCE.md" (
    move "ENV_VARIABLES_COMPLETE_REFERENCE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] ENV_VARIABLES_COMPLETE_REFERENCE.md
)
if exist "TENANT_UPDATE_VERIFICATION.md" (
    move "TENANT_UPDATE_VERIFICATION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] TENANT_UPDATE_VERIFICATION.md
)

REM =========================================================================
REM MOVE OTHER HISTORICAL DOCS
REM =========================================================================
echo.
echo Moving other historical docs to docs/archive/historical/...
if exist "COMPREHENSIVE_ISSUES_LIST.md" (
    move "COMPREHENSIVE_ISSUES_LIST.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] COMPREHENSIVE_ISSUES_LIST.md
)
if exist "DEEP_ASSESSMENT_REPORT_NOV11_2025.md" (
    move "DEEP_ASSESSMENT_REPORT_NOV11_2025.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] DEEP_ASSESSMENT_REPORT_NOV11_2025.md
)
if exist "DOCUMENTATION_AUDIT_NOV13_2025.md" (
    move "DOCUMENTATION_AUDIT_NOV13_2025.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] DOCUMENTATION_AUDIT_NOV13_2025.md
)
if exist "DOCUMENTATION_UPDATE_COMPLETE_NOV13.md" (
    move "DOCUMENTATION_UPDATE_COMPLETE_NOV13.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] DOCUMENTATION_UPDATE_COMPLETE_NOV13.md
)
if exist "SESSION_UPDATE_LLM_PROMPTS.md" (
    move "SESSION_UPDATE_LLM_PROMPTS.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] SESSION_UPDATE_LLM_PROMPTS.md
)
if exist "LLM_PROMPTS_PAGE_COMPLETE.md" (
    move "LLM_PROMPTS_PAGE_COMPLETE.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] LLM_PROMPTS_PAGE_COMPLETE.md
)
if exist "OPTION_B_FULL_POLISH_ROADMAP.md" (
    move "OPTION_B_FULL_POLISH_ROADMAP.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] OPTION_B_FULL_POLISH_ROADMAP.md
)
if exist "TENANT_PROJECT_ARCHITECTURE_PROPOSAL.md" (
    move "TENANT_PROJECT_ARCHITECTURE_PROPOSAL.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] TENANT_PROJECT_ARCHITECTURE_PROPOSAL.md
)
if exist "TENANT_PROJECT_IMPLEMENTATION_PLAN.md" (
    move "TENANT_PROJECT_IMPLEMENTATION_PLAN.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] TENANT_PROJECT_IMPLEMENTATION_PLAN.md
)
if exist "TENANT_DASHBOARD_FEATURES.md" (
    move "TENANT_DASHBOARD_FEATURES.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] TENANT_DASHBOARD_FEATURES.md
)
if exist "SCALABLE_PLANS_SOLUTION.md" (
    move "SCALABLE_PLANS_SOLUTION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] SCALABLE_PLANS_SOLUTION.md
)
if exist "TIMEZONE_CONFIGURATION.md" (
    move "TIMEZONE_CONFIGURATION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] TIMEZONE_CONFIGURATION.md
)
if exist "EVENT_LOGGING_AND_DATA_CONSISTENCY_FIX.md" (
    move "EVENT_LOGGING_AND_DATA_CONSISTENCY_FIX.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] EVENT_LOGGING_AND_DATA_CONSISTENCY_FIX.md
)
if exist "API_BUGS_FIXED.md" (
    move "API_BUGS_FIXED.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] API_BUGS_FIXED.md
)
if exist "LLM_PROVIDERS_INSTALLATION.md" (
    move "LLM_PROVIDERS_INSTALLATION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] LLM_PROVIDERS_INSTALLATION.md
)
if exist "OTP_DELIVERY_IMPLEMENTATION.md" (
    move "OTP_DELIVERY_IMPLEMENTATION.md" "docs\archive\historical\" >nul 2>&1
    echo   [OK] OTP_DELIVERY_IMPLEMENTATION.md
)

REM =========================================================================
REM SUMMARY
REM =========================================================================
echo.
echo ================================================
echo   DOCUMENTATION ORGANIZATION COMPLETE
echo ================================================
echo.
echo Files have been moved to appropriate locations:
echo   - docs/status_reports/ (current status reports)
echo   - docs/implementation_summaries/ (implementation summaries)
echo   - docs/ (current relevant documentation)
echo   - docs/archive/historical/ (historical/outdated docs)
echo.
echo README.md remains in root folder.
echo.
echo Next steps:
echo   1. Review the organization
echo   2. Commit changes: git add -A && git commit -m "docs: Organize documentation structure"
echo   3. Push to GitHub: git push origin MAIN_CODE
echo.
pause
