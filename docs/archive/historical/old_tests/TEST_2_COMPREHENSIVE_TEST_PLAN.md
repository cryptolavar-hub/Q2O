# Test 2: Comprehensive Test Plan
**Date**: November 24, 2025  
**Status**: Ready for Execution  
**Purpose**: Verify all recent fixes (JSON parsing, name generation, code quality)

---

## 🎯 Test Objectives

### Primary Goals:
1. ✅ Verify robust JSON parsing works (no more parsing failures)
2. ✅ Verify concise name generation (task titles, code components)
3. ✅ Verify full descriptions preserved for agents
4. ✅ Verify code quality improvements
5. ✅ Verify end-to-end project execution

---

## 📋 Pre-Test Checklist

### Environment Setup:
- [ ] API server restarted (to load latest code)
- [ ] Database running and accessible
- [ ] `.env` file configured correctly
- [ ] LLM API keys configured (at least one: Gemini, OpenAI, or Anthropic)
- [ ] Test tenant created in database
- [ ] Test project workspace directory exists

### Code Verification:
- [ ] `utils/json_parser.py` exists (robust JSON parser)
- [ ] `utils/name_generator.py` exists (concise name generator)
- [ ] `agents/orchestrator.py` updated (uses robust parser + concise names)
- [ ] `agents/researcher_agent.py` updated (uses robust parser)
- [ ] `agents/coder_agent.py` updated (uses concise names)

---

## 🧪 TEST SUITE 1: JSON Parsing Robustness

### Test 1.1: Orchestrator LLM Task Breakdown JSON Parsing

**Objective**: Verify Orchestrator successfully parses LLM responses even with malformed JSON

**Steps**:
1. Create a project with multiple objectives
2. Monitor logs for JSON parsing attempts
3. Verify tasks are created successfully
4. Check for JSON parsing errors

**Expected Results**:
- ✅ LLM task breakdown succeeds (or falls back gracefully)
- ✅ No "Failed to parse LLM task breakdown" errors
- ✅ Tasks created successfully (even if LLM fails, rules-based fallback works)
- ✅ JSON parsing uses multiple strategies (markdown extraction, repair, fallback)

**Success Criteria**:
- [ ] No JSON parsing errors in logs
- [ ] Tasks created successfully
- [ ] If LLM fails, rules-based fallback works

**Logs to Check**:
```
# Should see:
- "Successfully parsed JSON after repair" OR
- "Successfully parsed JSON using json5" OR
- "Extracted N valid JSON objects" OR
- "Created N tasks from project breakdown" (rules-based fallback)
```

---

### Test 1.2: Research Agent LLM JSON Parsing

**Objective**: Verify Research Agent successfully parses LLM research responses

**Steps**:
1. Create a project requiring research
2. Monitor Research Agent logs
3. Verify research data is complete
4. Check for JSON parsing errors

**Expected Results**:
- ✅ Research Agent parses LLM responses successfully
- ✅ Research data is complete (key findings, documentation URLs, code examples)
- ✅ No "Failed to parse LLM JSON response" errors
- ✅ Falls back to text parsing if JSON fails

**Success Criteria**:
- [ ] Research tasks complete successfully
- [ ] Research data includes key findings
- [ ] No JSON parsing errors in Research Agent logs
- [ ] Research data accessible to other agents

**Logs to Check**:
```
# Should see:
- "[LLM] LLM research completed successfully: N findings"
- "[LLM] Successfully parsed JSON after repair" OR
- "[LLM] JSON parsing failed, attempting text extraction" (acceptable fallback)
```

---

## 🧪 TEST SUITE 2: Name Generation

### Test 2.1: Task Title Generation

**Objective**: Verify task titles are concise (30-70 chars) but descriptive

**Steps**:
1. Create a project with long objectives
2. Check task titles in database
3. Verify titles are concise
4. Verify titles are still descriptive

**Expected Results**:
- ✅ Task titles are 30-70 characters
- ✅ Titles are descriptive (not just truncated)
- ✅ Titles extract key concepts (technologies, actions)
- ✅ No full objective text in titles

**Success Criteria**:
- [ ] All task titles < 70 characters
- [ ] Titles are readable and descriptive
- [ ] No database field length errors
- [ ] Titles follow pattern: "{AgentType}: {ConciseDescription}"

**Example**:
```
Objective: "Do an initial check to the QuickBooks API using the keys provided, the key and its required parameters must have each an input field on the UI for the client to enter, before the GET requests for the checks to QuickBooks DB"

Expected Title: "Backend: QuickBooks API Check" (35 chars) ✅
NOT: "Backend: Do an initial check to the QuickBooks API..." (150+ chars) ❌
```

---

### Test 2.2: Code Component Name Generation

**Objective**: Verify code components (files, classes, functions) use concise names

**Steps**:
1. Execute a project with code generation
2. Check generated filenames
3. Check generated class names
4. Check generated function names
5. Verify no filesystem path length issues

**Expected Results**:
- ✅ Filenames are concise (< 50 chars)
- ✅ Class names are concise (< 80 chars)
- ✅ Function names are concise (< 50 chars)
- ✅ No filesystem path length errors
- ✅ No unzip errors due to long filenames

**Success Criteria**:
- [ ] All filenames < 50 characters
- [ ] All class names < 80 characters
- [ ] All function names < 50 characters
- [ ] Files can be created/accessed without errors
- [ ] No path length issues

**Example**:
```
Objective: "Do an initial check to the QuickBooks API using the keys provided..."

Expected:
- Filename: quickbooks_api_check.py (25 chars) ✅
- Class: QuickBooksApiCheck (20 chars) ✅
- Function: get_quickbooks_api_check (25 chars) ✅

NOT:
- Filename: do_an_initial_check_to_the_quickbooks_api_using_the_keys_provided.py (80+ chars) ❌
```

---

### Test 2.3: Full Description Preservation

**Objective**: Verify agents receive full descriptions despite concise titles

**Steps**:
1. Create a project with detailed objectives
2. Check task descriptions in database
3. Check task metadata for full objective
4. Verify agents use full descriptions for code generation

**Expected Results**:
- ✅ Task descriptions contain full objective text
- ✅ Task metadata contains full objective
- ✅ Agents receive full descriptions
- ✅ Code docstrings contain full objectives

**Success Criteria**:
- [ ] Task descriptions are full (not truncated)
- [ ] Metadata contains full objective
- [ ] Generated code docstrings contain full objectives
- [ ] Agents have complete context

**Verification**:
```python
# Check database:
SELECT title, description, metadata FROM agent_tasks WHERE project_id = '...';

# title should be concise (30-70 chars)
# description should be full (150+ chars)
# metadata->>'objective' should be full (150+ chars)
```

---

## 🧪 TEST SUITE 3: Code Quality

### Test 3.1: LLM Task Breakdown Quality

**Objective**: Verify LLM-based task breakdown creates optimal tasks

**Steps**:
1. Create a project with complex objectives
2. Monitor Orchestrator logs for LLM breakdown
3. Verify tasks are well-structured
4. Verify dependencies are correct
5. Verify agent assignments are appropriate

**Expected Results**:
- ✅ LLM breakdown succeeds (or graceful fallback)
- ✅ Tasks are logically structured
- ✅ Dependencies are correct
- ✅ Agent assignments are appropriate
- ✅ Task sequence is optimal

**Success Criteria**:
- [ ] LLM breakdown succeeds OR rules-based fallback works
- [ ] Tasks have proper dependencies
- [ ] Research tasks come before implementation tasks
- [ ] Coder tasks are created for backend work
- [ ] Task sequence makes sense

---

### Test 3.2: Research Data Completeness

**Objective**: Verify research data is complete and useful

**Steps**:
1. Execute a project requiring research
2. Check research results in database
3. Verify research data includes key findings
4. Verify research data includes documentation URLs
5. Verify research data includes code examples

**Expected Results**:
- ✅ Research data is complete
- ✅ Key findings are present
- ✅ Documentation URLs are provided
- ✅ Code examples are included (if applicable)
- ✅ Research data is accessible to other agents

**Success Criteria**:
- [ ] Research results contain key findings
- [ ] Documentation URLs are present
- [ ] Research data is stored in database
- [ ] Other agents can access research data

---

### Test 3.3: Code Generation Quality

**Objective**: Verify generated code uses concise names but full context

**Steps**:
1. Execute a project with code generation
2. Check generated code files
3. Verify class/function names are concise
4. Verify docstrings contain full objectives
5. Verify code is functional

**Expected Results**:
- ✅ Code identifiers are concise
- ✅ Docstrings contain full objectives
- ✅ Code is syntactically correct
- ✅ Code follows best practices

**Success Criteria**:
- [ ] Class names are concise and readable
- [ ] Function names are concise and readable
- [ ] Docstrings contain full objectives
- [ ] Code is syntactically valid
- [ ] Code follows Python conventions

---

## 🧪 TEST SUITE 4: End-to-End Integration

### Test 4.1: Complete Project Execution

**Objective**: Verify complete project execution from start to finish

**Steps**:
1. Create a new project via API
2. Execute the project
3. Monitor execution logs
4. Verify project completes successfully
5. Check generated files
6. Verify project status updates

**Expected Results**:
- ✅ Project starts successfully
- ✅ Tasks are created
- ✅ Tasks execute successfully
- ✅ Code is generated
- ✅ Project status updates to "completed"
- ✅ Files are generated correctly

**Success Criteria**:
- [ ] Project execution starts without errors
- [ ] All tasks are created
- [ ] All tasks complete successfully
- [ ] Project status updates to "completed"
- [ ] Generated files are accessible
- [ ] No critical errors in logs

---

### Test 4.2: Error Handling & Recovery

**Objective**: Verify system handles errors gracefully

**Steps**:
1. Create a project with invalid LLM API keys
2. Monitor error handling
3. Verify fallback mechanisms work
4. Verify project still completes (with reduced quality)

**Expected Results**:
- ✅ System handles LLM failures gracefully
- ✅ Falls back to rules-based breakdown
- ✅ Falls back to templates for code generation
- ✅ Project completes (with reduced quality)
- ✅ Errors are logged but don't crash system

**Success Criteria**:
- [ ] No system crashes
- [ ] Errors are logged clearly
- [ ] Fallback mechanisms work
- [ ] Project completes (even if with reduced quality)

---

## 📊 Test Execution Steps

### Step 1: Prepare Test Environment
```bash
# 1. Restart API server
cd addon_portal
uvicorn api.main:app --reload

# 2. Verify database connection
psql -U q2o_user -d q2o -c "SELECT COUNT(*) FROM projects;"

# 3. Check environment variables
cat .env | grep -E "ENABLE_TASK_TRACKING|DATABASE_URL|GOOGLE_API_KEY"
```

### Step 2: Create Test Project
```bash
# Use Tenant Portal UI or API to create project:
# Project Name: "Test 2 - JSON Parsing & Name Generation"
# Objectives:
#   1. "Do an initial check to the QuickBooks API using the keys provided, the key and its required parameters must have each an input field on the UI for the client to enter, before the GET requests for the checks to QuickBooks DB"
#   2. "Create a NextJs interface to Perform these tasks"
#   3. "Connect the Backend and UI using an SQLite Database"
```

### Step 3: Execute Project
```bash
# Execute via Tenant Portal UI or API
# Monitor logs in real-time
tail -f logs/api_*.log
tail -f Tenant_Projects/*/execution_stdout.log
```

### Step 4: Verify Results

**Check Database:**
```sql
-- Check task titles (should be concise)
SELECT title, LENGTH(title) as title_length, description, LENGTH(description) as desc_length
FROM agent_tasks
WHERE project_id = 'test-2-json-parsing-name-generation'
ORDER BY created_at;

-- Verify titles are < 70 chars
SELECT COUNT(*) as long_titles
FROM agent_tasks
WHERE project_id = 'test-2-json-parsing-name-generation'
AND LENGTH(title) > 70;

-- Check research data completeness
SELECT task_name, 
       metadata->>'research_id' as research_id,
       metadata->>'key_findings' as findings
FROM agent_tasks
WHERE agent_type = 'researcher'
AND project_id = 'test-2-json-parsing-name-generation';
```

**Check Generated Files:**
```bash
# Check filenames (should be concise)
find Tenant_Projects/test-2-*/generated -type f -name "*.py" | head -10

# Check class names in code (should be concise)
grep -r "class " Tenant_Projects/test-2-*/generated/*.py | head -10

# Check function names (should be concise)
grep -r "def " Tenant_Projects/test-2-*/generated/*.py | head -10

# Check docstrings (should contain full objectives)
grep -A 5 '"""' Tenant_Projects/test-2-*/generated/*.py | head -20
```

**Check Logs:**
```bash
# Check for JSON parsing errors
grep -i "failed to parse\|json.*error\|json.*failed" logs/api_*.log Tenant_Projects/*/execution_stdout.log

# Check for name generation
grep -i "generate.*name\|concise.*name" logs/api_*.log Tenant_Projects/*/execution_stdout.log

# Check for successful task creation
grep -i "created.*tasks\|task.*created" logs/api_*.log Tenant_Projects/*/execution_stdout.log
```

---

## ✅ Success Criteria Summary

### Critical (Must Pass):
- [ ] No JSON parsing errors in logs
- [ ] All task titles < 70 characters
- [ ] All filenames < 50 characters
- [ ] Full descriptions preserved in database
- [ ] Project completes successfully
- [ ] No filesystem path length errors

### Important (Should Pass):
- [ ] LLM task breakdown succeeds (or graceful fallback)
- [ ] Research data is complete
- [ ] Code identifiers are concise
- [ ] Code docstrings contain full objectives
- [ ] Task dependencies are correct

### Nice to Have:
- [ ] LLM parsing succeeds on first attempt
- [ ] Research data includes code examples
- [ ] Generated code is high quality
- [ ] Task sequence is optimal

---

## 📝 Test Report Template

### Test Execution Log:
```
Date: ___________
Tester: ___________
Project ID: ___________

Test Suite 1: JSON Parsing Robustness
- [ ] Test 1.1: Orchestrator JSON Parsing - PASS / FAIL
- [ ] Test 1.2: Research Agent JSON Parsing - PASS / FAIL

Test Suite 2: Name Generation
- [ ] Test 2.1: Task Title Generation - PASS / FAIL
- [ ] Test 2.2: Code Component Names - PASS / FAIL
- [ ] Test 2.3: Full Description Preservation - PASS / FAIL

Test Suite 3: Code Quality
- [ ] Test 3.1: LLM Task Breakdown Quality - PASS / FAIL
- [ ] Test 3.2: Research Data Completeness - PASS / FAIL
- [ ] Test 3.3: Code Generation Quality - PASS / FAIL

Test Suite 4: End-to-End Integration
- [ ] Test 4.1: Complete Project Execution - PASS / FAIL
- [ ] Test 4.2: Error Handling & Recovery - PASS / FAIL

Issues Found:
1. ___________
2. ___________

Overall Status: PASS / FAIL
```

---

## 🚀 Quick Test Command

**For Quick Verification:**
```bash
# Run a simple test project
python main.py \
  --project "Quick Test" \
  --objective "Create a simple API endpoint for user authentication" \
  --output-folder ./test_quick \
  --project-id quick-test-$(date +%s) \
  --tenant-id 1

# Check results
echo "Task Titles:"
grep "title" test_quick/tasks.json | head -5

echo "Generated Files:"
find test_quick/generated -type f | head -5
```

---

## 📚 Related Documentation

- `docs/TEST_1_ISSUES_AND_FIXES.md` - Previous test issues
- `docs/TEST_1_CODE_QUALITY_ANALYSIS.md` - Code quality analysis
- `docs/TASK_NAME_GENERATION_FIX.md` - Name generation fix details
- `docs/CODE_GENERATION_NAME_PATTERN.md` - Code generation pattern guide

---

**Status**: Ready for Execution ✅  
**Priority**: HIGH  
**Estimated Time**: 2-3 hours for full test suite

