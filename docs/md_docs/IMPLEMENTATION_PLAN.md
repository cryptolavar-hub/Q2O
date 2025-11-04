# Implementation Plan - Multi-Agent System Fixes
## Detailed Roadmap Based on GitHub Copilot Assessment

## Phase 1: Critical Fixes (Week 1) - DO NOW

### ✅ 1.1 FastAPI Unification (IN PROGRESS)
**Status**: Partially Complete
- ✅ `coder_agent.py` - Fixed (FastAPI only)
- ❌ `integration_agent.py` - Still uses Flask for route registration
- ❌ Update all route registration functions to FastAPI
- ❌ Remove all Flask imports

**Files to Fix**:
- `agents/integration_agent.py` - Lines 110, 256-287, 659, 787-817, 848, 900-926
- Remove `Flask` imports
- Convert `register_*_routes(app: Flask, ...)` to FastAPI routers
- Update route decorators from `@app.route` to `@router.get/post/put/delete`

**Approach**: Convert route registration to FastAPI router pattern

---

### ✅ 1.2 Requirements & Dependencies (COMPLETE)
**Status**: ✅ Complete
- ✅ Created proper `requirements.txt` with pinned versions
- ✅ Added FastAPI, pytest, security tools, code quality tools

**No further action needed**

---

### 1.3 Template System with Jinja2 (HIGH PRIORITY)
**Status**: Not Started

**Approach**:
1. Create `templates/` directory structure
2. Extract inline templates to Jinja2 files
3. Create template renderer utility
4. Update all agents to use renderer

**Directory Structure**:
```
templates/
├── api/
│   ├── fastapi_endpoint.j2
│   ├── fastapi_router.j2
│   ├── sqlalchemy_model.j2
│   └── service.j2
├── frontend/
│   ├── nextjs_page.j2
│   ├── react_component.j2
│   └── nextauth_config.j2
├── infrastructure/
│   ├── terraform_main.j2
│   ├── terraform_waf.j2
│   ├── terraform_variables.j2
│   ├── helm_values.j2
│   └── helm_chart.j2
├── integration/
│   ├── qbo_oauth.j2
│   ├── qbo_client.j2
│   ├── odoo_client.j2
│   └── stripe_billing.j2
└── workflow/
    ├── temporal_workflow.j2
    ├── temporal_activity.j2
    └── worker_main.j2
```

**Implementation Steps**:
1. Create `utils/template_renderer.py` with Jinja2 environment
2. Extract templates from:
   - `agents/coder_agent.py` → api/ templates
   - `agents/frontend_agent.py` → frontend/ templates
   - `agents/infrastructure_agent.py` → infrastructure/ templates
   - `agents/integration_agent.py` → integration/ templates
   - `agents/workflow_agent.py` → workflow/ templates
3. Update each agent to use `TemplateRenderer.render()` instead of inline strings
4. Add template validation (syntax checking)

**Files to Modify**:
- Create `utils/template_renderer.py`
- Update `agents/coder_agent.py`
- Update `agents/frontend_agent.py`
- Update `agents/infrastructure_agent.py`
- Update `agents/integration_agent.py`
- Update `agents/workflow_agent.py`

---

### 1.4 Pytest Conversion (HIGH PRIORITY)
**Status**: Not Started

**Current Issues**:
- Uses `subprocess` to run unittest
- Uses `sys.path` hacks
- Fragile import handling

**Approach**:
1. Update `testing_agent.py` to generate pytest-compatible tests
2. Use pytest fixtures instead of unittest.TestCase
3. Proper PYTHONPATH handling
4. Use pytest discovery instead of subprocess

**Implementation Steps**:
1. Create pytest test template (`templates/test_pytest.j2`)
2. Update `_generate_test_content()` to use pytest format
3. Update `_execute_test()` to use pytest runner with proper PYTHONPATH
4. Add `pytest.ini` or `pyproject.toml` configuration generation
5. Support async tests for FastAPI endpoints

**Files to Modify**:
- `agents/testing_agent.py` - Complete rewrite of test generation/execution
- Create `templates/test_pytest.j2`

---

### 1.5 Infrastructure Validation (MEDIUM PRIORITY)
**Status**: Not Started

**Approach**:
1. Add Terraform validation (terraform fmt, validate)
2. Add Helm linting (helm lint)
3. Gracefully skip if tools not installed
4. Add validation to InfrastructureAgent

**Implementation Steps**:
1. Create `utils/infrastructure_validator.py`
2. Add `validate_terraform()` method
3. Add `validate_helm()` method
4. Update `InfrastructureAgent.process_task()` to validate after creation
5. Add optional validation flag (skip if tools missing)

**Files to Modify**:
- Create `utils/infrastructure_validator.py`
- Update `agents/infrastructure_agent.py`

---

## Phase 2: Security & Quality (Week 2)

### 2.1 Security Agent Enhancement (HIGH PRIORITY)
**Status**: Not Started

**Current Issues**:
- Only regex-based checks
- False positives/negatives
- No real security scanning

**Approach**:
1. Integrate bandit for Python security scanning
2. Integrate semgrep for pattern-based scanning
3. Keep regex checks as initial filter
4. Add dependency scanning (safety, pip-audit)

**Implementation Steps**:
1. Update `requirements.txt` (already done - bandit, semgrep, safety)
2. Create `utils/security_scanner.py`:
   - `scan_with_bandit(file_path)` → Returns issues
   - `scan_with_semgrep(file_path)` → Returns issues
   - `scan_dependencies()` → Uses safety/pip-audit
3. Update `SecurityAgent._review_file_security()`:
   - Run regex checks first (quick filter)
   - Run bandit scan
   - Run semgrep scan
   - Aggregate results
4. Add security scanning to CI/CD

**Files to Modify**:
- Create `utils/security_scanner.py`
- Update `agents/security_agent.py`

---

### 2.2 QA Agent Enhancement (MEDIUM PRIORITY)
**Status**: Not Started

**Approach**:
1. Add mypy for type checking
2. Add ruff for linting (already in requirements)
3. Add black for formatting checks
4. Integrate with static analysis results

**Implementation Steps**:
1. Create `utils/code_quality_scanner.py`:
   - `check_types_with_mypy(file_path)` → Type errors
   - `lint_with_ruff(file_path)` → Linting issues
   - `check_format_with_black(file_path)` → Formatting issues
2. Update `QAAgent._review_file()` to include:
   - Existing regex checks
   - mypy type checking
   - ruff linting
   - black formatting
3. Aggregate all quality metrics

**Files to Modify**:
- Create `utils/code_quality_scanner.py`
- Update `agents/qa_agent.py`

---

### 2.3 Secrets Management (HIGH PRIORITY)
**Status**: Not Started

**Approach**:
1. Generate `.env.example` files
2. Ensure no hardcoded secrets in templates
3. Add secrets placeholder validation
4. Update all agents to use placeholders

**Implementation Steps**:
1. Create `utils/secrets_validator.py`:
   - `validate_no_secrets(code)` → Check for hardcoded secrets
   - `extract_env_vars(code)` → Extract env var usage
   - `generate_env_example(env_vars)` → Generate .env.example
2. Update template renderer to use placeholders:
   - `{{ SECRET_KEY }}` instead of actual values
   - `{{ DATABASE_URL }}` placeholder
3. Add validation in SecurityAgent to check for secrets
4. Generate `.env.example` for each generated project

**Files to Modify**:
- Create `utils/secrets_validator.py`
- Update all templates to use placeholders
- Update `agents/security_agent.py`

---

## Phase 3: CI/CD & Polish (Week 3)

### 3.1 CI/CD Pipeline (HIGH PRIORITY)
**Status**: Not Started

**Approach**:
1. Create `.github/workflows/ci.yml`
2. Add all checks: linting, type checking, security, tests
3. Add infrastructure validation
4. Add dependency scanning

**Implementation Steps**:
1. Create `.github/workflows/ci.yml`:
   - Lint with ruff
   - Type check with mypy
   - Security scan with bandit/semgrep
   - Run tests with pytest
   - Validate Terraform (if files exist)
   - Validate Helm (if charts exist)
   - Dependency scanning with safety
2. Add matrix strategy for Python versions
3. Add caching for dependencies
4. Add PR/push triggers

**Files to Create**:
- `.github/workflows/ci.yml`

---

### 3.2 Configurable Project Layout (MEDIUM PRIORITY)
**Status**: Not Started

**Approach**:
1. Create project layout configuration
2. Make directory structure configurable
3. Add layout detection from existing projects
4. Update all agents to use configurable paths

**Implementation Steps**:
1. Create `config/project_layouts.py`:
   - Default layout (api/, web/, infra/, etc.)
   - Custom layout support
   - Layout detection
2. Create `config/project_config.py`:
   - Load layout from config file
   - Environment variable override
   - Command-line override
3. Update all agents to read from config instead of hardcoded paths

**Files to Create/Modify**:
- Create `config/project_layouts.py`
- Create `config/project_config.py`
- Update all agents to use config

---

### 3.3 Consistent Error Handling (LOW PRIORITY)
**Status**: Not Started

**Approach**:
1. Standardize error handling patterns
2. Add proper exception types
3. Update generated code templates
4. Add error logging consistency

**Implementation Steps**:
1. Create `utils/exceptions.py`:
   - Custom exception classes
   - Error handling utilities
2. Update generated code templates to use consistent error handling
3. Update all agents to use consistent error handling

**Files to Create/Modify**:
- Create `utils/exceptions.py`
- Update templates
- Update agents

---

## Implementation Order

### Day 1-2: Critical FastAPI Fix
- [x] Fix `coder_agent.py` (DONE)
- [ ] Fix `integration_agent.py` (NEXT)
- [ ] Remove all Flask references
- [ ] Test FastAPI generation

### Day 3-4: Template System
- [ ] Create `templates/` directory
- [ ] Create `utils/template_renderer.py`
- [ ] Extract templates from agents
- [ ] Update agents to use renderer
- [ ] Test template rendering

### Day 5: Pytest Conversion
- [ ] Create pytest test template
- [ ] Update `testing_agent.py`
- [ ] Fix test execution
- [ ] Test pytest generation

### Day 6-7: Infrastructure Validation
- [ ] Create `utils/infrastructure_validator.py`
- [ ] Add Terraform validation
- [ ] Add Helm validation
- [ ] Update InfrastructureAgent

### Week 2: Security & Quality
- [ ] Security Agent with bandit/semgrep
- [ ] QA Agent with mypy/ruff
- [ ] Secrets validation
- [ ] CI/CD pipeline

### Week 3: Polish
- [ ] Configurable layouts
- [ ] Error handling
- [ ] Documentation

---

## Testing Strategy

After each fix:
1. Run `quick_test.py` to verify basic functionality
2. Run `test_agent_system.py` to verify end-to-end
3. Check generated code for correct patterns
4. Verify no regressions

---

## Success Criteria

- ✅ All Flask references removed
- ✅ All templates externalized to Jinja2
- ✅ All tests use pytest
- ✅ Security scanning with real tools
- ✅ CI/CD pipeline passes
- ✅ No hardcoded secrets
- ✅ Proper dependency management

