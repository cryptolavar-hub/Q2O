# GitHub vs Local File System - Root Folder Comparison

**Generated:** 1764082504.1995916

## Side-by-Side Comparison

| Item Name | In GitHub | In Local | Type | Notes |
|-----------|-----------|----------|------|-------|
| `.env` | NO | YES | FILE | IGNORED |
| `.env.example` | YES | YES | FILE |  |
| `.git` | NO | YES | DIR | NOT TRACKED |
| `.github` | YES | YES | DIR |  |
| `.gitignore` | YES | YES | FILE |  |
| `.llm_cache` | NO | YES | DIR | NOT TRACKED |
| `.llm_cost_state.json` | YES | YES | FILE |  |
| `.research_cache` | YES | YES | DIR |  |
| `INSTALL_ADMIN_PORTAL_DEPS.ps1` | YES | YES | FILE |  |
| `INSTALL_POSTGRESQL.ps1` | YES | YES | FILE |  |
| `MANAGE_SERVICES.ps1` | YES | YES | FILE |  |
| `README.md` | YES | YES | FILE |  |
| `RESTART_SERVICE.ps1` | YES | YES | FILE |  |
| `RUN_LLM_MIGRATION.ps1` | YES | YES | FILE |  |
| `START_ALL.bat` | YES | YES | FILE |  |
| `START_ALL_SERVICES.ps1` | YES | YES | FILE |  |
| `STOP_ALL.bat` | YES | YES | FILE |  |
| `STOP_ALL_SERVICES.ps1` | YES | YES | FILE |  |
| `Tenant_Projects` | NO | YES | DIR | PROJECT GENERATED (container for all projects, correctly not in git) |
| `addon_portal` | NO | YES | DIR | PLATFORM FOLDER (should be tracked in git) |
| `agents` | YES | YES | DIR |  |
| `api` | YES | YES | DIR |  |
| `check_database_schema.py` | YES | YES | FILE |  |
| `check_databases.py` | YES | YES | FILE |  |
| `check_tenant_sessions_schema.py` | YES | YES | FILE |  |
| `config` | YES | YES | DIR |  |
| `config.json` | YES | YES | FILE |  |
| `config_example.json` | YES | YES | FILE |  |
| `create_database.py` | YES | YES | FILE |  |
| `demos` | YES | YES | DIR |  |
| `diagnose_powershell.ps1` | YES | YES | FILE |  |
| `docs` | YES | YES | DIR |  |
| `env.example` | YES | YES | FILE |  |
| `env.llm.example.txt` | YES | YES | FILE |  |
| `fix_db_dsn.py` | YES | YES | FILE |  |
| `fix_powershell_pager.ps1` | YES | YES | FILE |  |
| `infra` | YES | YES | DIR |  |
| `learned_templates.db` | NO | YES | FILE | IGNORED |
| `logs` | YES | YES | DIR |  |
| `main.py` | YES | YES | FILE |  |
| `mobile` | YES | YES | DIR |  |
| `q2o_licensing.db` | NO | YES | FILE | IGNORED |
| `quick_test.py` | YES | YES | FILE |  |
| `requirements.txt` | YES | YES | FILE |  |
| `research` | YES | YES | DIR |  |
| `setup_postgresql.sql` | YES | YES | FILE |  |
| `shared` | YES | YES | DIR |  |
| `templates` | YES | YES | DIR |  |
| `test_agent_system.py` | YES | YES | FILE |  |
| `test_agents.py` | YES | YES | FILE |  |
| `test_config.json` | YES | YES | FILE |  |
| `test_database_connection.py` | YES | YES | FILE |  |
| `test_duckduckgo_search.py` | YES | YES | FILE |  |
| `test_python313_full_compatibility.py` | YES | YES | FILE |  |
| `test_research_agent_llm.py` | YES | YES | FILE |  |
| `test_researcher.json` | YES | YES | FILE |  |
| `test_small.json` | YES | YES | FILE |  |
| `test_task_tracking.py` | YES | YES | FILE |  |
| `test_workspace` | YES | YES | DIR |  |
| `tests` | YES | YES | DIR |  |
| `tools` | YES | YES | DIR |  |
| `update_db_dsn_to_q2o.py` | YES | YES | FILE |  |
| `update_password_in_env.py` | YES | YES | FILE |  |
| `utils` | YES | YES | DIR |  |
| `web` | YES | YES | DIR |  |
| `zbin` | YES | YES | DIR |  |

## Summary

- **Total items in GitHub:** 59
- **Total items in local:** 66
- **In both:** 59
- **GitHub only (missing locally):** 0
- **Local only (not tracked):** 4
- **Local ignored:** 3

## Notes

- **IGNORED**: Item is in .gitignore (intentionally excluded from git)
- **NOT TRACKED**: Item exists locally but is not in git (may need to be added or ignored)
- **PROJECT GENERATED**: Item is project-generated and should be in Tenant_Projects/{project_id}/ folder, not in root
- **PLATFORM FOLDER**: Item is a platform/system folder that should be tracked in git
- **MISSING LOCALLY**: Item is in git but doesn't exist locally (may need to be restored)

## Important Findings

1. **`k8s` folder**: Does not exist in root (correctly moved to Tenant_Projects projects)
2. **`Tenant_Projects`**: Container folder for all generated projects - correctly not tracked in git
3. **`addon_portal`**: Platform folder containing licensing system - should be tracked in git but is currently not
