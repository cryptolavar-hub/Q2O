# Fixes: Orchestrator LLM File Type Determination

**Date**: November 27, 2025  
**Role**: QA_Engineer - Architecture Improvement  
**Status**: ✅ **COMPLETE**

---

## 🎯 **Problem**

The Coder Agent was receiving "generic" tasks because it relied on keyword matching to determine file types. This caused:
- Less tailored code generation
- Generic LLM prompts like "Task: generic: Implementation for..."
- Reduced code quality
- Inefficient use of LLM capabilities

---

## ✅ **Solution: Orchestrator LLM Determines File Types**

**Architectural Improvement**: The Orchestrator's LLM (which already understands task context) now determines file types during task breakdown, eliminating the need for the Coder Agent to guess.

---

## 📝 **Changes Made**

### **1. Enhanced Orchestrator LLM Prompt** (`agents/orchestrator.py`)

**Added**: Instructions for LLM to include `file_type` field for CODER tasks.

**Prompt Enhancement**:
```python
**CRITICAL FOR CODER TASKS:**
- For CODER tasks, you MUST include a "file_type" field indicating the type of code file to generate
- Valid file_types: "api" (FastAPI endpoints), "model" (SQLAlchemy models), "service" (business logic), "component" (React/Next.js components), "page" (Next.js pages), "generic" (only if truly generic)
- Choose file_type based on what the task actually needs:
  * "api" - for REST endpoints, API handlers, HTTP routes
  * "model" - for database schemas, data models, ORM classes
  * "service" - for business logic, data processing, utility functions
  * "component" - for React/Next.js UI components
  * "page" - for Next.js page routes
  * "generic" - only as last resort if task doesn't fit any category
- Example: "Backend: Store User Theme Preferences" → file_type: "service" (stores preferences, business logic)
- Example: "Backend: Chat Message API" → file_type: "api" (REST endpoints for messages)
- Example: "Backend: User Profile Model" → file_type: "model" (database model)
```

**JSON Schema Update**:
```json
{
  "agent_type": "CODER",
  "title": "Backend: Stripe API Client",
  "description": "Create Stripe API client with payment methods and webhook handlers",
  "tech_stack": ["Python", "Stripe API", "FastAPI"],
  "complexity": "high",
  "file_type": "api",  // ← NEW FIELD
  "dependencies": [0]
}
```

---

### **2. Task Metadata Enhancement** (`agents/orchestrator.py`)

**Added**: `file_type` extraction from LLM response and storage in task metadata.

**Code**:
```python
# QA_Engineer: Add file_type to metadata for CODER tasks (determined by LLM)
if agent_type == AgentType.CODER:
    file_type = spec.get('file_type', None)
    if file_type:
        task_metadata["file_type"] = file_type
        self.logger.debug(f"[LLM] Task {task_id} assigned file_type: {file_type}")
    else:
        # LLM didn't provide file_type - log warning but continue
        self.logger.warning(f"[LLM] Task {task_id} (CODER) missing file_type - Coder Agent will infer")
```

---

### **3. Coder Agent Uses Orchestrator's File Type** (`agents/coder_agent.py`)

**Added**: Coder Agent checks for `file_type` in task metadata first (preferred), falls back to keyword matching if not available.

**Code**:
```python
# QA_Engineer: Use file_type from Orchestrator's LLM if available (preferred over keyword matching)
file_type_from_orchestrator = metadata.get("file_type", None)
if file_type_from_orchestrator:
    self.logger.info(f"[ORCHESTRATOR] Using LLM-determined file_type: {file_type_from_orchestrator}")

# Generate code structure (with tech stack awareness)
# Pass file_type from Orchestrator if available
code_structure = self._plan_code_structure(
    description, objective, complexity, tech_stack, 
    file_type_hint=file_type_from_orchestrator
)
```

**Updated Method Signature**:
```python
def _plan_code_structure(self, description: str, objective: str, complexity: str, tech_stack: List[str] = None, file_type_hint: str = None) -> Dict[str, Any]:
```

**Logic**:
1. **If `file_type_hint` provided**: Use it directly (from Orchestrator's LLM)
2. **If not provided**: Fall back to keyword matching (for rules-based breakdown or backward compatibility)

---

## 🎯 **Benefits**

### **1. Intelligent File Type Determination**
- ✅ LLM understands task context and requirements
- ✅ Makes intelligent decisions based on task description
- ✅ No more guessing or keyword matching

### **2. Consistent Architecture**
- ✅ Single source of truth (Orchestrator's LLM)
- ✅ Coder Agent doesn't need to guess
- ✅ More maintainable and predictable

### **3. Better Code Generation**
- ✅ Specific LLM prompts: "Task: api: Chat Message API" instead of "Task: generic: Implementation for..."
- ✅ More tailored code generation
- ✅ Improved code quality

### **4. Backward Compatibility**
- ✅ Falls back to keyword matching if Orchestrator doesn't provide file_type
- ✅ Works with rules-based breakdown
- ✅ No breaking changes

---

## 📊 **Before vs After**

### **Before**:
```
Orchestrator → Creates task: "Backend: Store User Theme Preferences"
Coder Agent → Keyword matching → No keywords found → file_type = "generic"
LLM Prompt → "Task: generic: Implementation for Backend: Store User Theme Preferences"
Result → Generic code generation
```

### **After**:
```
Orchestrator LLM → Analyzes task → Determines: file_type = "service"
Task Metadata → { "file_type": "service" }
Coder Agent → Uses file_type from metadata → file_type = "service"
LLM Prompt → "Task: service: Store User Theme Preferences"
Result → Tailored service code generation
```

---

## 🧪 **Testing**

1. **Test LLM File Type Determination**:
   - Create tasks with various descriptions
   - Verify Orchestrator's LLM includes `file_type` in response
   - Check that file_type is appropriate for the task

2. **Test Coder Agent Integration**:
   - Verify Coder Agent uses file_type from metadata
   - Check that LLM prompts are specific (not "generic")
   - Verify code quality improves

3. **Test Backward Compatibility**:
   - Test with rules-based breakdown (no LLM)
   - Verify keyword matching still works
   - Check that tasks without file_type still function

---

## 📚 **Related Documentation**

- `docs/QA_BUG_REPORT_GENERIC_TASKS_CODER_AGENT.md` - Original bug report
- `agents/orchestrator.py` - Orchestrator implementation
- `agents/coder_agent.py` - Coder Agent implementation

---

## ✅ **Status**

- ✅ Orchestrator LLM prompt enhanced
- ✅ Task metadata includes file_type
- ✅ Coder Agent uses Orchestrator's file_type
- ✅ Backward compatibility maintained
- ✅ Documentation updated

**Next Steps**: Test with real projects to verify file types are correctly determined and code quality improves.

---

**Implemented By**: QA_Engineer - Architecture Improvement  
**Date**: November 27, 2025  
**Status**: ✅ **COMPLETE**

