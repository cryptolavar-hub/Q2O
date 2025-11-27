# Q2O Agentic System - Comprehensive Test Plan

**Date**: November 21, 2025  
**Status**: READY FOR EXECUTION  
**Purpose**: Verify all critical bug fixes are working correctly

---

## Test Environment Setup

### Prerequisites
- [ ] Python 3.10+ installed
- [ ] PostgreSQL database running and accessible
- [ ] `.env` file configured with database credentials
- [ ] LLM API keys configured (optional but recommended)
- [ ] Project workspace directory exists

### Test Data Setup
- [ ] Create test tenant in database
- [ ] Create test subscription (active or trialing)
- [ ] Create test activation code
- [ ] Create test project configuration

---

## TEST SUITE 1: Event Loop & Task Tracking (Phase 1 Fixes)

### Test 1.1: Event Loop Conflict Resolution

**Objective**: Verify no event loop errors occur during task tracking

**Steps**:
1. Start FastAPI server (creates event loop)
2. Create a project via API
3. Execute project (triggers task tracking)
4. Monitor logs for event loop errors

**Expected Results**:
- ✅ No `RuntimeError: is bound to a different event loop` errors
- ✅ No `SAWarning: The garbage collector is trying to clean up non-checked-in connection` warnings
- ✅ Tasks created successfully in database
- ✅ Task status updates work correctly

**Test Command**:
```bash
# Start API server
cd addon_portal
uvicorn api.main:app --reload

# In another terminal, create and run project
# Use Tenant Portal UI or API endpoint
```

**Success Criteria**:
- [ ] No event loop errors in logs
- [ ] Tasks appear in `agent_tasks` table
- [ ] Task status updates work

---

### Test 1.2: Async Event Emission

**Objective**: Verify dashboard events are emitted without warnings

**Steps**:
1. Start FastAPI server
2. Create and execute a project
3. Monitor logs for runtime warnings
4. Check dashboard for real-time updates

**Expected Results**:
- ✅ No `RuntimeWarning: coroutine 'EventManager.emit_task_update' was never awaited` warnings
- ✅ Dashboard shows task updates in real-time
- ✅ Agent activity visible in dashboard
- ✅ No memory leaks

**Test Command**:
```bash
# Monitor logs while project runs
tail -f logs/app.log | grep -i "warning\|error\|coroutine"
```

**Success Criteria**:
- [ ] No runtime warnings about unawaited coroutines
- [ ] Dashboard events appear
- [ ] No memory leaks detected

---

## TEST SUITE 2: Task Distribution & Project Completion (Phase 2 Fixes)

### Test 2.1: Coder Agent Task Distribution

**Objective**: Verify coder agents receive tasks for integration objectives

**Test Cases**:

#### Test Case 2.1.1: Integration Objective
**Objective**: "QuickBooks migration to Odoo"

**Steps**:
1. Create project with objective: "QuickBooks migration to Odoo"
2. Execute project
3. Check orchestrator logs for task breakdown
4. Verify coder tasks created
5. Verify coder agents receive tasks

**Expected Results**:
- ✅ Orchestrator creates research task
- ✅ Orchestrator creates integration task
- ✅ **CRITICAL**: Orchestrator creates coder task (NEW FIX)
- ✅ Coder agents show active tasks
- ✅ Backend code generated

**Verification**:
```sql
-- Check agent_tasks table
SELECT agent_type, task_name, status 
FROM agent_tasks 
WHERE project_id = '<test_project_id>'
ORDER BY created_at;

-- Should see:
-- researcher: Research task
-- integration: Integration task
-- coder: Backend task (THIS IS THE FIX!)
-- testing: Test task
```

**Success Criteria**:
- [ ] Coder tasks created for integration objectives
- [ ] Coder agents show `Active: > 0`
- [ ] Backend code files generated

---

#### Test Case 2.1.2: Workflow Objective
**Objective**: "Create Temporal workflow for data sync"

**Steps**:
1. Create project with objective: "Create Temporal workflow for data sync"
2. Execute project
3. Verify coder tasks created

**Expected Results**:
- ✅ Workflow task created
- ✅ **CRITICAL**: Coder task created (NEW FIX)
- ✅ Backend code generated

**Success Criteria**:
- [ ] Coder tasks created
- [ ] Backend code generated

---

#### Test Case 2.1.3: Frontend Objective
**Objective**: "Create React dashboard for project management"

**Steps**:
1. Create project with objective: "Create React dashboard for project management"
2. Execute project
3. Verify coder tasks created

**Expected Results**:
- ✅ Frontend task created
- ✅ **CRITICAL**: Coder task created (NEW FIX)
- ✅ Backend API code generated

**Success Criteria**:
- [ ] Coder tasks created
- [ ] Backend API code generated

---

### Test 2.2: Project Completion Status

**Objective**: Verify project status updates correctly when process completes

**Steps**:
1. Create and execute a project
2. Monitor project status in database
3. Wait for process to complete
4. Verify status updates to "completed"

**Expected Results**:
- ✅ Project status starts as "running"
- ✅ Status updates to "completed" when process exits (exit code 0)
- ✅ Status updates to "failed" if process exits with error
- ✅ `execution_completed_at` timestamp set

**Verification**:
```sql
-- Check project status
SELECT project_id, execution_status, execution_started_at, execution_completed_at
FROM llm_project_configs
WHERE project_id = '<test_project_id>';

-- After completion, should show:
-- execution_status: 'completed'
-- execution_completed_at: <timestamp>
```

**Test Scenarios**:

#### Scenario 2.2.1: Successful Completion
- Create simple project that completes successfully
- Verify status = "completed"

#### Scenario 2.2.2: Failed Completion
- Create project that fails (invalid objective)
- Verify status = "failed"
- Verify error message stored

#### Scenario 2.2.3: Timeout Handling
- Create project that runs longer than timeout
- Verify status = "failed" with timeout error

**Success Criteria**:
- [ ] Status updates to "completed" on success
- [ ] Status updates to "failed" on error
- [ ] Completion timestamp set correctly
- [ ] Dashboard shows correct status

---

## TEST SUITE 3: Dependency Access & File Discovery (Phase 3 Fixes)

### Test 3.1: Research Dependency Access

**Objective**: Verify agents can access research results from dependencies

**Steps**:
1. Create project with objective requiring research (e.g., "Stripe API integration")
2. Execute project
3. Monitor logs for research completion
4. Check if dependent agents (coder, integration) use research results

**Expected Results**:
- ✅ Researcher agent completes research task
- ✅ Research results stored in task metadata
- ✅ Coder/Integration agents access research via orchestrator
- ✅ Code generation uses research context

**Verification**:
```python
# Check research results in task metadata
# Research task should have research_results in metadata
# Dependent tasks should have research_context in metadata
```

**Log Checks**:
- Look for: "Enriched task with research: X findings, Y examples"
- Look for: "Retrieved X research results from dependencies"

**Success Criteria**:
- [ ] Research results accessible to dependent agents
- [ ] Code generation uses research context
- [ ] No "orchestrator not found" errors

---

### Test 3.2: Testing Agent File Discovery

**Objective**: Verify testing agent finds actual implemented files

**Steps**:
1. Create project with code generation objective
2. Execute project
3. Monitor testing agent logs
4. Verify tests created for actual files
5. Verify test execution works

**Expected Results**:
- ✅ Testing agent finds files from dependency tasks
- ✅ Tests created for actual implemented files
- ✅ Test files exist in workspace
- ✅ Test execution succeeds

**Verification**:
```bash
# Check output folder for test files
ls -la Tenant_Projects/<project_id>/tests/

# Should see test files matching actual implementation files
```

**Log Checks**:
- Look for: "Found X implemented files to test"
- Look for: "Created test file: tests/test_<file>.py"
- Should NOT see: "No implemented files found"

**Success Criteria**:
- [ ] Tests created for actual files
- [ ] No tests for non-existent files
- [ ] Test execution successful

---

## TEST SUITE 4: End-to-End Integration Tests

### Test 4.1: Complete Project Execution

**Objective**: Verify full project lifecycle works correctly

**Test Project**: "QuickBooks to Odoo Migration"

**Steps**:
1. Create project with:
   - Name: "QuickBooks Migration"
   - Description: "Migrate QuickBooks data to Odoo"
   - Objectives: "QuickBooks API integration", "Odoo API integration", "Data mapping"
2. Execute project
3. Monitor all phases:
   - Task breakdown
   - Task distribution
   - Task execution
   - Task completion
   - Project completion

**Expected Results**:
- ✅ Tasks created correctly
- ✅ All agents receive appropriate tasks
- ✅ Research completed
- ✅ Code generated
- ✅ Tests created and executed
- ✅ Project status updates to "completed"
- ✅ Code files in output folder

**Verification Checklist**:
- [ ] Research tasks completed
- [ ] Integration tasks completed
- [ ] **Coder tasks completed** (CRITICAL FIX)
- [ ] Testing tasks completed
- [ ] QA tasks completed
- [ ] Project status = "completed"
- [ ] Code files exist in output folder
- [ ] Test files exist
- [ ] Dashboard shows all tasks completed

---

### Test 4.2: Multi-Objective Project

**Objective**: Verify system handles multiple objectives correctly

**Test Project**: Multiple objectives

**Steps**:
1. Create project with 3+ objectives
2. Execute project
3. Verify all objectives processed
4. Verify dependencies handled correctly

**Expected Results**:
- ✅ All objectives broken down into tasks
- ✅ Dependencies respected
- ✅ Tasks execute in correct order
- ✅ All tasks complete

---

### Test 4.3: Error Handling & Recovery

**Objective**: Verify error handling works correctly

**Test Scenarios**:

#### Scenario 4.3.1: Task Failure
- Create project with invalid objective
- Verify task fails gracefully
- Verify retry logic works
- Verify project status updates

#### Scenario 4.3.2: Agent Failure
- Simulate agent failure
- Verify load balancer routes to backup agent
- Verify task completes

#### Scenario 4.3.3: Database Connection Loss
- Simulate database connection loss
- Verify graceful degradation
- Verify recovery when connection restored

---

## TEST SUITE 5: Performance & Stress Tests

### Test 5.1: Concurrent Projects

**Objective**: Verify system handles multiple concurrent projects

**Steps**:
1. Create 5 projects simultaneously
2. Execute all projects
3. Monitor system performance
4. Verify all projects complete

**Expected Results**:
- ✅ All projects execute concurrently
- ✅ No resource exhaustion
- ✅ Database connections managed correctly
- ✅ All projects complete successfully

---

### Test 5.2: Large Project

**Objective**: Verify system handles large projects

**Steps**:
1. Create project with 20+ objectives
2. Execute project
3. Monitor performance
4. Verify all tasks complete

**Expected Results**:
- ✅ All tasks created
- ✅ Tasks distributed correctly
- ✅ No performance degradation
- ✅ Project completes successfully

---

### Test 5.3: Database Connection Pool

**Objective**: Verify database connection pool works correctly

**Steps**:
1. Execute project with 100+ tasks
2. Monitor database connections
3. Verify no connection leaks
4. Verify pool exhaustion doesn't occur

**Expected Results**:
- ✅ Connections properly closed
- ✅ No connection leaks
- ✅ Pool size remains stable
- ✅ No "connection pool exhausted" errors

---

## TEST SUITE 6: Dashboard & UI Tests

### Test 6.1: Real-Time Updates

**Objective**: Verify dashboard updates in real-time

**Steps**:
1. Open dashboard
2. Execute project
3. Monitor dashboard for updates
4. Verify task status updates appear

**Expected Results**:
- ✅ Task status updates appear in real-time
- ✅ Agent activity visible
- ✅ Progress bars update
- ✅ No page refresh needed

---

### Test 6.2: Project Status Display

**Objective**: Verify project status displays correctly

**Steps**:
1. Execute project
2. Check dashboard project list
3. Verify status updates
4. Verify completion status

**Expected Results**:
- ✅ Status shows "running" during execution
- ✅ Status updates to "completed" when done
- ✅ Status updates to "failed" on error
- ✅ Completion time displayed

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Database running and accessible
- [ ] Environment variables configured
- [ ] Test tenant created
- [ ] Test subscription active
- [ ] Test activation code available
- [ ] Logs directory exists

### Test Execution Order
1. [ ] Test Suite 1: Event Loop & Task Tracking
2. [ ] Test Suite 2: Task Distribution & Project Completion
3. [ ] Test Suite 3: Dependency Access & File Discovery
4. [ ] Test Suite 4: End-to-End Integration Tests
5. [ ] Test Suite 5: Performance & Stress Tests (Optional)
6. [ ] Test Suite 6: Dashboard & UI Tests

### Post-Test Verification
- [ ] All critical tests passed
- [ ] No errors in logs
- [ ] Database consistent
- [ ] Files generated correctly
- [ ] Dashboard working

---

## Test Data & Scripts

### Test Project Templates

#### Template 1: Simple API Project
```json
{
  "project_name": "Test API",
  "description": "Simple REST API",
  "objectives": ["Create user authentication endpoint", "Create CRUD endpoints"]
}
```

#### Template 2: Integration Project
```json
{
  "project_name": "Test Integration",
  "description": "QuickBooks Integration",
  "objectives": ["QuickBooks OAuth integration", "QuickBooks API client"]
}
```

#### Template 3: Full Stack Project
```json
{
  "project_name": "Test Full Stack",
  "description": "Complete application",
  "objectives": [
    "Backend API",
    "Frontend dashboard",
    "Database models",
    "Authentication"
  ]
}
```

---

## Success Metrics

### Critical Metrics (Must Pass)
- ✅ Zero event loop errors
- ✅ Zero unawaited coroutine warnings
- ✅ Coder tasks created for all code generation objectives
- ✅ Project status updates correctly
- ✅ Research results accessible
- ✅ Tests created for actual files

### Performance Metrics (Should Meet)
- ✅ Projects complete within reasonable time
- ✅ No database connection leaks
- ✅ Memory usage stable
- ✅ Dashboard updates within 1 second

---

## Known Issues & Workarounds

### Issue: LLM API Keys Not Configured
**Impact**: LLM features unavailable, falls back to templates  
**Workaround**: Configure at least one LLM API key in `.env`  
**Status**: Expected behavior, not a bug

### Issue: psutil Not Installed (Windows)
**Impact**: Process monitoring uses fallback method  
**Workaround**: Install psutil: `pip install psutil`  
**Status**: Fallback works, but psutil recommended

---

## Test Report Template

### Test Execution Report

**Date**: _______________  
**Tester**: _______________  
**Environment**: _______________

#### Test Results Summary
- Total Tests: ______
- Passed: ______
- Failed: ______
- Skipped: ______

#### Critical Tests
- [ ] Event Loop Conflicts: PASS / FAIL
- [ ] Async Event Emission: PASS / FAIL
- [ ] Coder Task Distribution: PASS / FAIL
- [ ] Project Completion: PASS / FAIL
- [ ] Research Access: PASS / FAIL
- [ ] File Discovery: PASS / FAIL

#### Issues Found
1. Issue: _______________
   - Severity: _______________
   - Steps to Reproduce: _______________
   - Expected: _______________
   - Actual: _______________

#### Recommendations
- _______________
- _______________

---

**Test Plan Complete**  
**Ready for Execution**

