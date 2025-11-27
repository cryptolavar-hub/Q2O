# Root Folder Analysis - Highlighted Folders

## Analysis Date: 2025-11-25

## Summary

Analyzed the highlighted folders in the root directory to determine which are **platform-related** (should be in GitHub) vs **project-generated** (should be cleaned up).

## Folder Classification

### ✅ PLATFORM FOLDERS (Should be in GitHub)

These folders are part of the platform codebase and should exist:

1. **`config`** ✅ PLATFORM
   - Contains system configuration files
   - Files: `pricing_config.json`, `quickbooks_to_odoo_mapping.json`, `sage_to_odoo_mapping.json`, etc.
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

2. **`demos`** ✅ PLATFORM
   - Contains demo/test code
   - Files: `llm_integration_poc/`, `test_llm_generation.py`, etc.
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

3. **`infra`** ✅ PLATFORM
   - Infrastructure as Code (Terraform)
   - Files: `terraform/azure/main.tf`, etc.
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

4. **`k8s`** ✅ PLATFORM
   - Kubernetes/Helm configurations
   - Files: `helm/` directory
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

5. **`logs`** ✅ PLATFORM (but contents are generated)
   - Platform folder structure
   - Contains generated log files (should be in .gitignore)
   - **Status**: Platform folder, log files are generated

6. **`mobile`** ✅ PLATFORM
   - System mobile code
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

7. **`shared`** ✅ PLATFORM
   - Shared code (Temporal workflows)
   - Files: `temporal_defs/workflows/backfill.py`
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

8. **`templates`** ✅ PLATFORM
   - Jinja2 templates for code generation
   - **Status**: Platform folder, documented in FILE_SYSTEM_STRUCTURE.md

### ⚠️ PROJECT-GENERATED FOLDERS (Should be cleaned up)

These folders/files were created by project execution and shouldn't be in root:

1. **`.coverage_reports`** ⚠️ PROJECT-GENERATED
   - Created by TestingAgent when running tests with coverage
   - Currently empty (no recent test runs)
   - **Location**: Should be in `Tenant_Projects/{project_id}/.coverage_reports/`
   - **Action**: Can be deleted (empty) or moved if it has content
   - **Note**: Should be added to .gitignore (currently not explicitly listed)

2. **`src/`** ⚠️ PROJECT-GENERATED FILES
   - Contains 3 Python files that look project-generated:
     - `follow_web3.py`
     - `mention_typical_user.py`
     - `responsive_design_mobile.py`
   - **Location**: These files should be in `Tenant_Projects/{project_id}/src/`
   - **Action**: Move these files to their correct project folders
   - **Note**: Root `src/` folder is NOT documented in FILE_SYSTEM_STRUCTURE.md

## Recommendations

### Immediate Actions

1. **Delete `.coverage_reports`** (empty folder)
   ```bash
   rmdir .coverage_reports
   ```

2. **Move `src/` files to correct projects**
   - Analyze which project these files belong to
   - Move to `Tenant_Projects/{project_id}/src/`
   - Delete root `src/` folder if empty

3. **Update .gitignore**
   - Add `.coverage_reports/` explicitly
   - Ensure `src/` at root level is not ignored (but project-generated files in it should be)

### Long-term

- Ensure TestingAgent creates `.coverage_reports` in project workspace, not root
- Verify all agents use `safe_write_file()` to prevent root folder corruption

## Verification

All platform folders match the documentation in `docs/FILE_SYSTEM_STRUCTURE.md`:
- ✅ `config` - Documented
- ✅ `demos` - Documented  
- ✅ `infra` - Documented
- ✅ `k8s` - Documented
- ✅ `logs` - Documented (as generated)
- ✅ `mobile` - Documented
- ✅ `shared` - Documented
- ✅ `templates` - Documented

Root `src/` folder is NOT documented, indicating it's project-generated.

