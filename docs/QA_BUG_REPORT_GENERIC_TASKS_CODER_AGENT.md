# Bug Report: Coder Agent Receiving Generic Tasks Instead of Specific Ones

**Date**: November 27, 2025  
**Role**: QA_Engineer - Bug Hunter  
**Severity**: 🟡 **HIGH**  
**Status**: 🔍 **ANALYZING**

---

## 🐛 Bug Summary

**Issue**: Coder Agent is receiving "generic" tasks instead of specific, tailored tasks. LLM logs show many tasks with "Task: generic: Implementation for..." instead of specific types like "api", "model", "service", etc.

**Evidence**:
- OpenAI logs show: `Task: generic: Implementation for with the same features (o...`
- OpenAI logs show: `Task: generic: Implementation for with basic Chat features T...`
- OpenAI logs show: `Task: generic: Implementation for Groups Technology Stack:...`
- OpenAI logs show: `Task: generic: Implementation for Build a WhatsApp like clo...`
- All tasks use `gpt-4o-mini-2024-07-18` model
- Tasks are generating code but with generic prompts

**Impact**: 
- **Less tailored code generation**: Generic tasks produce less specific code
- **Reduced code quality**: Generic templates may not match the actual requirements
- **Inefficient LLM usage**: Generic prompts may not leverage LLM capabilities optimally
- **Poor task descriptions**: Tasks don't reflect their true nature (API, model, service, etc.)

---

## 🔍 Root Cause Analysis

### **Problem: Keyword-Based File Type Detection**

**Location**: `agents/coder_agent.py`, `_plan_code_structure` method (lines 177-314)

**How It Works**:
1. Coder Agent receives a task with a description
2. `_plan_code_structure` analyzes the description using keyword matching
3. If keywords like "api", "model", "service", "page", "component" are found, it creates specific file types
4. **If NO keywords match, it defaults to "generic"** (lines 296-312)

**Example**:
```python
# Task description: "Backend: Store User Theme Preferences"
# Keyword check: "api" not found, "model" not found, "service" not found
# Result: file_type = "generic"
# LLM prompt: "Task: generic: Implementation for Backend: Store User Theme Preferences"
```

**Why This Happens**:
1. Orchestrator creates task descriptions like "Backend: Store User Theme Preferences"
2. These descriptions don't contain explicit keywords like "api", "model", "service"
3. `_plan_code_structure` can't determine the file type from keywords
4. Falls back to "generic" type
5. LLM receives generic prompt instead of specific one

**Tasks Affected**:
- Tasks with descriptions that don't contain explicit keywords
- Tasks like "Backend: Store User Theme Preferences" (should be "service" or "api")
- Tasks like "Backend: Chat Message API" (should be "api")
- Tasks like "Backend: User Profile API" (should be "api" or "model")

---

## 🔧 Proposed Solutions

### **Solution 1: Improve Keyword Matching** ⚠️ **PARTIAL FIX**

**Action**: Expand keyword matching to include more patterns.

**Implementation**:
- Add "backend" → "api" or "service"
- Add "store" → "service" or "model"
- Add "preferences" → "service" or "model"
- Add "chat" → "api" or "service"
- Add "message" → "api" or "model"

**Pros**:
- Quick fix, no LLM calls needed
- Maintains current architecture

**Cons**:
- Still relies on keyword matching (fragile)
- May misclassify some tasks
- Doesn't understand context

**Status**: ⏳ **PENDING**

---

### **Solution 2: Use LLM for File Type Detection** ✅ **RECOMMENDED**

**Action**: Use LLM to analyze task description and determine appropriate file type.

**Implementation**:
1. Before `_plan_code_structure`, call LLM to analyze task description
2. LLM determines: file type, file path, description
3. Use LLM's analysis instead of keyword matching

**Pros**:
- **Intelligent**: Understands context and requirements
- **Accurate**: Better file type detection
- **Tailored**: Specific prompts for LLM code generation
- **Future-proof**: Handles new task types automatically

**Cons**:
- Adds LLM call overhead (but can be cached)
- Requires LLM to be available

**Status**: ⏳ **PENDING**

---

### **Solution 3: Enhance Task Descriptions from Orchestrator** ✅ **RECOMMENDED**

**Action**: Improve Orchestrator's LLM prompt to include file type hints in task descriptions.

**Implementation**:
1. Update Orchestrator's LLM prompt to include file type in task descriptions
2. Format: "Backend API: Store User Theme Preferences" instead of "Backend: Store User Theme Preferences"
3. Coder Agent can extract file type from description

**Pros**:
- **Upstream fix**: Fixes the root cause
- **No Coder Agent changes**: Works with existing keyword matching
- **Better task descriptions**: More informative for all agents

**Cons**:
- Requires Orchestrator changes
- May need to update existing task descriptions

**Status**: ⏳ **PENDING**

---

### **Solution 4: Use Tech Stack and Metadata** ⚠️ **PARTIAL FIX**

**Action**: Use task's tech_stack and metadata to determine file type.

**Implementation**:
1. Check `task.tech_stack` for technologies
2. Check `task.metadata` for hints
3. Use tech stack to infer file type (e.g., FastAPI → "api", SQLAlchemy → "model")

**Pros**:
- Uses existing task data
- No LLM calls needed
- Works with current architecture

**Cons**:
- Still may not be specific enough
- Doesn't understand task context

**Status**: ⏳ **PENDING**

---

## 📝 Recommended Approach

**Combination of Solutions 2 and 3**:

1. **Short-term**: Improve keyword matching (Solution 1) + Use tech stack (Solution 4)
2. **Long-term**: Enhance Orchestrator task descriptions (Solution 3) + Use LLM for file type detection (Solution 2)

**Priority**: 
- **High**: Fix keyword matching to handle common patterns
- **Medium**: Enhance Orchestrator task descriptions
- **Low**: Add LLM-based file type detection (for complex cases)

---

## 🧪 Testing Plan

1. **Test Keyword Matching**:
   - Create tasks with various descriptions
   - Verify file types are correctly detected
   - Check that "generic" is only used when truly generic

2. **Test LLM Prompts**:
   - Verify LLM receives specific prompts (not "generic")
   - Check code quality improves with specific prompts
   - Monitor LLM usage and costs

3. **Test Task Descriptions**:
   - Verify Orchestrator creates descriptive task descriptions
   - Check that file types can be inferred from descriptions
   - Ensure backward compatibility

---

## 📚 Related Documentation

- `agents/coder_agent.py` - Coder Agent implementation
- `agents/orchestrator.py` - Orchestrator task breakdown
- `docs/QA_BUG_REPORT_CODER_AGENT_MISSING_FILES.md` - Previous Coder Agent issues

---

**Reported By**: QA_Engineer - Bug Hunter  
**Date**: November 27, 2025  
**Status**: 🔍 **ANALYZING - AWAITING FIX DECISION**

