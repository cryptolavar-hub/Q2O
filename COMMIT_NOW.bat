@echo off
REM Helper script to commit current licensing API refactor

cd /d "%~dp0"

echo Staging all changes...
git add addon_portal/api/core/logging.py
git add addon_portal/api/core/exceptions.py
git add addon_portal/api/schemas/__init__.py
git add addon_portal/api/schemas/tenant.py
git add addon_portal/api/schemas/llm.py
git add addon_portal/api/services/__init__.py
git add addon_portal/api/services/tenant_service.py
git add addon_portal/api/services/llm_config_service.py
git add addon_portal/api/utils/env_manager.py
git add addon_portal/api/routers/admin_api.py
git add addon_portal/api/routers/llm_management.py
git add addon_portal/api/main.py
git add addon_portal/apps/admin-portal/package.json
git add addon_portal/apps/admin-portal/src/lib/api.ts
git add addon_portal/apps/admin-portal/src/pages/index.tsx
git add addon_portal/apps/admin-portal/src/pages/tenants.tsx
git add addon_portal/apps/admin-portal/.eslintrc.json
git add addon_portal/migrations_manual/004_add_llm_config_tables.sql
git add RUN_LLM_MIGRATION.ps1
git add INSTALL_ADMIN_PORTAL_DEPS.ps1
git add PROGRESS_UPDATE_NOV11_AFTERNOON.md

echo.
echo Committing...
git commit -m "Refactor licensing API with service layer, structured logging, and DB-backed LLM config" -m "- Add structured JSON logging (core/logging.py)" -m "- Add custom exception hierarchy with FastAPI handlers (core/exceptions.py)" -m "- Implement tenant service layer with pagination, search, validation (services/tenant_service.py)" -m "- Implement LLM config service with DB + .env integration (services/llm_config_service.py)" -m "- Add Pydantic schemas with strict validation (schemas/tenant.py, schemas/llm.py)" -m "- Refactor admin_api.py to use service layer and typed responses" -m "- Rewrite llm_management.py router with database-backed endpoints" -m "- Modernize dashboard page with design system components" -m "- Complete tenant page rewrite: pagination, search, filter, modals" -m "- Add Zod validation to frontend API client" -m "- Create LLM config database migration (004_add_llm_config_tables.sql)" -m "- Add migration runner script (RUN_LLM_MIGRATION.ps1)" -m "- Add ESLint configuration for admin portal"

echo.
echo Commit complete!
pause

