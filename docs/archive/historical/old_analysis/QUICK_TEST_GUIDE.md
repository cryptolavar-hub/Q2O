# Quick Test Guide - Agentic System Fixes

**Quick Reference**: How to test the critical bug fixes

---

## 🚀 Quick Start Testing

### 1. Test Event Loop Fixes (2 minutes)

```bash
# Start API server
cd addon_portal
uvicorn api.main:app --reload

# In another terminal, create a test project via API or UI
# Watch logs for errors - should see NO event loop errors
```

**What to Check**:
- ✅ No `RuntimeError: is bound to a different event loop`
- ✅ No `RuntimeWarning: coroutine was never awaited`
- ✅ Tasks created in database successfully

---

### 2. Test Coder Task Distribution (5 minutes)

**Test Project**:
- **Name**: "QuickBooks Integration Test"
- **Objective**: "QuickBooks OAuth integration"

**What to Check**:
```sql
-- Run this query after project starts
SELECT agent_type, task_name, status 
FROM agent_tasks 
WHERE project_id = '<your_project_id>'
ORDER BY created_at;
```

**Expected**:
- ✅ `researcher` task
- ✅ `integration` task  
- ✅ **`coder` task** ← THIS IS THE FIX!
- ✅ `testing` task

**If coder task missing**: Bug not fixed ❌  
**If coder task present**: Fix working ✅

---

### 3. Test Project Completion (5 minutes)

**Steps**:
1. Create and execute a project
2. Wait for completion (or check logs for "All tasks completed!")
3. Check database:

```sql
SELECT execution_status, execution_completed_at
FROM llm_project_configs
WHERE project_id = '<your_project_id>';
```

**Expected**:
- ✅ `execution_status` = 'completed' (not 'running')
- ✅ `execution_completed_at` = timestamp

**If status stays 'running'**: Bug not fixed ❌  
**If status = 'completed'**: Fix working ✅

---

### 4. Test Research Dependency Access (5 minutes)

**Test Project**:
- **Objective**: "Stripe API integration"

**What to Check in Logs**:
- Look for: `"Enriched task with research: X findings, Y examples"`
- Look for: `"Retrieved X research results from dependencies"`

**If these messages appear**: Fix working ✅  
**If no research context**: Bug not fixed ❌

---

### 5. Test File Discovery (5 minutes)

**Steps**:
1. Create project that generates code
2. Check output folder for test files
3. Verify tests match actual files

**What to Check**:
```bash
# List test files
ls -la Tenant_Projects/<project_id>/tests/

# Should see tests matching actual implementation files
# e.g., if api/endpoints.py exists, should see tests/test_endpoints.py
```

**If tests match files**: Fix working ✅  
**If tests for non-existent files**: Bug not fixed ❌

---

## 🎯 Critical Test Checklist

Run these tests in order:

- [ ] **Test 1**: Event Loop - No errors in logs
- [ ] **Test 2**: Coder Tasks - Coder tasks created for integration objectives
- [ ] **Test 3**: Project Status - Status updates to "completed"
- [ ] **Test 4**: Research Access - Research results accessible
- [ ] **Test 5**: File Discovery - Tests created for actual files

**All 5 tests must pass** for system to be considered fixed.

---

## 📊 Test Results Template

```
Test Date: ___________
Tester: ___________

Test 1 - Event Loop: [ ] PASS [ ] FAIL
Test 2 - Coder Tasks: [ ] PASS [ ] FAIL  
Test 3 - Project Status: [ ] PASS [ ] FAIL
Test 4 - Research Access: [ ] PASS [ ] FAIL
Test 5 - File Discovery: [ ] PASS [ ] FAIL

Overall: [ ] ALL PASS [ ] ISSUES FOUND

Issues:
1. ___________
2. ___________
```

---

## 🔍 Debugging Tips

### If Event Loop Errors Occur:
- Check database connection string
- Verify async/await usage
- Check for multiple event loops

### If Coder Tasks Missing:
- Check orchestrator logs for task breakdown
- Verify objective type detection
- Check `_needs_coder_task()` logic

### If Project Status Not Updating:
- Check process monitoring logs
- Verify subprocess completion
- Check database connection

### If Research Not Accessible:
- Verify orchestrator reference passed to agents
- Check task registry
- Verify dependency task IDs

### If Files Not Found:
- Check dependency task results
- Verify file paths in task metadata
- Check workspace path configuration

---

**Quick Test Guide Complete**  
**Run tests and report results!**

