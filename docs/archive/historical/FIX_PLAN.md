# Multi-Agent System Fix Plan
## Based on GitHub Copilot Assessment

## Priority 1: Critical Fixes (Must Fix)

### 1.1 Unify API Framework to FastAPI
- [ ] Remove all Flask references from code generation
- [ ] Update `coder_agent.py` to only generate FastAPI patterns
- [ ] Update `integration_agent.py` to use FastAPI
- [ ] Update `frontend_agent.py` API calls to match FastAPI
- [ ] Test: Verify all generated API code uses FastAPI

### 1.2 Add Real Dependencies
- [ ] Create proper `requirements.txt` with pinned versions
- [ ] Include: fastapi, uvicorn, pydantic, sqlalchemy, etc.
- [ ] Add development dependencies: pytest, black, mypy, ruff
- [ ] Add infrastructure: terraform (optional), helm (optional)
- [ ] Add security: bandit, semgrep
- [ ] Test: Verify all imports work

### 1.3 Externalize Templates with Jinja2
- [ ] Create `templates/` directory structure
- [ ] Convert inline templates to Jinja2 templates:
  - [ ] Infrastructure templates (Terraform, Helm)
  - [ ] API templates (FastAPI)
  - [ ] Frontend templates (Next.js/React)
  - [ ] Integration templates (OAuth, clients)
  - [ ] Workflow templates (Temporal)
- [ ] Create template renderer utility
- [ ] Update all agents to use template renderer
- [ ] Test: Verify templates render correctly

### 1.4 Convert Testing to Pytest
- [ ] Update `testing_agent.py` to generate pytest tests
- [ ] Remove subprocess unittest hacks
- [ ] Use proper PYTHONPATH handling
- [ ] Generate pytest-compatible test structure
- [ ] Add pytest configuration file
- [ ] Test: Verify tests run with pytest

### 1.5 Add Infrastructure Validation
- [ ] Add Terraform validation (terraform fmt, validate)
- [ ] Add Helm linting (helm lint)
- [ ] Gracefully skip if tools not installed
- [ ] Add validation to InfrastructureAgent
- [ ] Test: Verify validation works

## Priority 2: Security & Quality

### 2.1 Harden Security Agent
- [ ] Integrate bandit for Python security scanning
- [ ] Integrate semgrep for pattern-based scanning
- [ ] Keep regex checks as initial filter
- [ ] Add dependency scanning (safety, pip-audit)
- [ ] Test: Verify real security issues are caught

### 2.2 Improve QA Agent
- [ ] Add mypy for type checking
- [ ] Add ruff for linting
- [ ] Add black for formatting checks
- [ ] Integrate with static analysis results
- [ ] Test: Verify quality checks are accurate

### 2.3 Secrets Management
- [ ] Generate `.env.example` files
- [ ] Ensure no hardcoded secrets in templates
- [ ] Add secrets placeholder validation
- [ ] Update all agents to use placeholders
- [ ] Test: Verify no secrets in generated code

## Priority 3: Maintainability

### 3.1 Configurable Project Layout
- [ ] Create project layout configuration
- [ ] Make directory structure configurable
- [ ] Add layout detection from existing projects
- [ ] Update all agents to use configurable paths
- [ ] Test: Verify different layouts work

### 3.2 Consistent Error Handling
- [ ] Standardize error handling patterns
- [ ] Add proper exception types
- [ ] Update generated code templates
- [ ] Add error logging consistency
- [ ] Test: Verify error handling works

### 3.3 CI/CD Pipeline
- [ ] Create `.github/workflows/ci.yml`
- [ ] Add linting (ruff, black)
- [ ] Add type checking (mypy)
- [ ] Add security scanning (bandit, semgrep)
- [ ] Add infrastructure validation (terraform, helm)
- [ ] Add dependency scanning
- [ ] Test: Verify CI passes

## Implementation Order

**Week 1: Foundation**
1. Unify to FastAPI (1 day)
2. Add dependencies (1 day)
3. Externalize templates with Jinja2 (2 days)
4. Convert tests to pytest (1 day)

**Week 2: Quality & Security**
1. Infrastructure validation (1 day)
2. Harden Security Agent (1 day)
3. Improve QA Agent (1 day)
4. Secrets management (1 day)
5. CI/CD pipeline (1 day)

**Week 3: Polish**
1. Configurable layouts (2 days)
2. Consistent error handling (2 days)
3. Documentation updates (1 day)

## Files to Modify

### Critical (Do First)
- `agents/coder_agent.py` - FastAPI only, templates
- `agents/testing_agent.py` - Pytest conversion
- `agents/infrastructure_agent.py` - Templates, validation
- `requirements.txt` - Real dependencies
- Create `templates/` directory structure

### High Priority (Do Second)
- `agents/qa_agent.py` - Static analysis integration
- `agents/security_agent.py` - Real security tools
- `.github/workflows/ci.yml` - CI pipeline
- Add template renderer utility

### Medium Priority (Do Third)
- All agent files - Use template renderer
- Add configuration system
- Improve error handling
- Add unit tests for agents

