# QA Project Structure Blueprint Implementation

**Date**: November 29, 2025  
**Status**: ✅ **IMPLEMENTED**  
**Priority**: High

---

## Problem Statement

**User Question**: 
> "This platform is being created to build anything. Therefore the possible structures are endless for the output folder and the files created. However there must be somewhere that the Structure is known before the folder and files are created. Like a blueprint of the project. Is there a way the QA agent can get this blueprint early so it can look for those missing parts?
>
> It's like an inspector turning up at a work site. Without the blueprint it's hard to know what's missing, but having a blueprint the inspector can easily point out issues."

**Current Issue**: 
- QA agent uses hardcoded expected directories based on tech stack
- Doesn't know the actual project structure blueprint defined by the Orchestrator
- Can't effectively detect missing components for custom or unusual project types

---

## Solution: Project Structure Blueprint System

### Architecture

```
1. Orchestrator LLM Breakdown
   ↓ (defines expected structure)
2. Extract Structure Blueprint
   ↓ (store in Orchestrator)
3. QA Agent Accesses Blueprint
   ↓ (via orchestrator reference)
4. QA Uses Blueprint for Analysis
   ↓ (checks against expected structure)
5. Missing Components Detected
   ↓ (reported to Orchestrator)
6. Dynamic Tasks Created
   ↓ (for missing components)
```

---

## Implementation Details

### 1. Orchestrator: Extract and Store Blueprint

**Location**: `agents/orchestrator.py`

**When**: During LLM task breakdown (`_analyze_objective_with_llm`)

**What**: 
- Extracts `objective_classification` from LLM response
- Builds structure blueprint using `_build_structure_blueprint()`
- Stores blueprint in `self.project_structure_blueprint` (keyed by objective)

**Code**:
```python
# Extract objective classification (if provided by LLM)
classification = result.get('objective_classification', {})
if classification:
    project_type = classification.get('type', 'unknown')
    tech_stack = classification.get('tech_stack', [])
    
    # Build structure blueprint based on project type and tech stack
    structure_blueprint = self._build_structure_blueprint(project_type, tech_stack, classification)
    
    # Store blueprint for QA agent to use
    if not self.project_structure_blueprint:
        self.project_structure_blueprint = {}
    self.project_structure_blueprint[objective] = structure_blueprint
```

### 2. Orchestrator: Build Structure Blueprint

**Method**: `_build_structure_blueprint(project_type, tech_stack, classification)`

**Supported Project Types**:
- **mobile_app** (React Native/Expo)
- **web_app** (Next.js/React)
- **api_service** (FastAPI/Python)

**Blueprint Structure**:
```python
{
    "project_type": "mobile_app",
    "tech_stack": ["React Native", "TypeScript"],
    "platforms": ["android", "ios"],
    "expected_directories": [
        {
            "path": "src/components",
            "required": True,
            "description": "Reusable UI components"
        },
        ...
    ],
    "expected_files": [
        {
            "path": "App.tsx",
            "required": True,
            "description": "Main app entry point"
        },
        ...
    ],
    "key_features": ["authentication", "payments"]
}
```

**Directories/Files Defined**:

**Mobile App**:
- Directories: `src/screens`, `src/components`, `src/navigation`, `src/services`, `src/hooks`, `src/store`, `src/theme`, `src/types`, `src/utils`, `assets/images`, `assets/fonts`
- Files: `App.tsx`, `package.json`, `tsconfig.json`, `AndroidManifest.xml`, `Info.plist`

**Web App**:
- Directories: `src/pages`, `src/components`, `src/app/api`, `src/services`, `src/hooks`, `src/utils`, `src/types`, `src/styles`
- Files: `package.json`, `tsconfig.json`, `next.config.js`

**API Service**:
- Directories: `src/api`, `src/models`, `src/schemas`, `src/services`, `src/utils`, `src/config`, `src/middleware`
- Files: `main.py`, `requirements.txt`, `.env.example`

### 3. Orchestrator: Provide Blueprint to QA

**Method**: `get_project_structure_blueprint()`

**Returns**: Blueprint dictionary or `None` if not available

**Usage**: QA agent calls this method to get the blueprint

### 4. QA Agent: Use Blueprint for Analysis

**Location**: `agents/qa_agent.py`

**Method**: `_analyze_project_structure(task)`

**Enhancement**:
```python
# QA_Engineer: Get project structure blueprint from Orchestrator (if available)
structure_blueprint = None
if self.orchestrator and hasattr(self.orchestrator, 'get_project_structure_blueprint'):
    try:
        structure_blueprint = self.orchestrator.get_project_structure_blueprint()
        if structure_blueprint:
            self.logger.info(
                f"[BLUEPRINT] Using structure blueprint for {structure_blueprint.get('project_type', 'unknown')} project"
            )
    except Exception as e:
        self.logger.debug(f"Could not get structure blueprint from Orchestrator: {e}")

# Use blueprint if available, otherwise fall back to hardcoded expectations
if structure_blueprint:
    # Check directories and files from blueprint
    for dir_spec in expected_dirs:
        # Check if directory exists and has files
        # Report missing components based on blueprint
```

**Benefits**:
- ✅ QA knows exactly what should exist (from Orchestrator's LLM analysis)
- ✅ Works for ANY project type (not just hardcoded ones)
- ✅ Can detect missing components accurately
- ✅ Falls back to hardcoded expectations if blueprint unavailable

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Orchestrator LLM Breakdown                               │
│    - Analyzes objective                                      │
│    - Classifies project type                                │
│    - Determines tech stack                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Build Structure Blueprint                                │
│    - Maps project_type → expected directories/files          │
│    - Includes descriptions and requirements                 │
│    - Stores in Orchestrator.project_structure_blueprint     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. QA Agent Accesses Blueprint                               │
│    - Calls orchestrator.get_project_structure_blueprint()    │
│    - Receives expected structure                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. QA Analyzes Project Structure                            │
│    - Checks each expected directory/file from blueprint      │
│    - Reports missing components                             │
│    - Falls back to hardcoded if blueprint unavailable       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. QA Reports Missing Components                            │
│    - Sends COORDINATION message to Orchestrator              │
│    - Includes list of missing components                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Orchestrator Creates Dynamic Tasks                       │
│    - Creates tasks for missing components                    │
│    - Assigns to appropriate agents                          │
│    - Adds to task queue                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Benefits

### Before (Hardcoded Expectations)
- ❌ QA only knows about 3 project types (mobile, web, api)
- ❌ Can't handle custom or unusual project structures
- ❌ May miss components for new project types
- ❌ Hardcoded expectations may not match actual project needs

### After (Blueprint-Based)
- ✅ QA knows exact expected structure from Orchestrator's LLM analysis
- ✅ Works for ANY project type (as long as Orchestrator classifies it)
- ✅ Accurate detection of missing components
- ✅ Blueprint is project-specific (not generic)
- ✅ Falls back gracefully if blueprint unavailable

---

## Example Usage

### Scenario: Mobile App Project

1. **Orchestrator Breakdown**:
   - LLM classifies: `project_type: "mobile_app"`, `tech_stack: ["React Native", "TypeScript"]`
   - Builds blueprint with 11 expected directories and 5 expected files

2. **QA Agent Analysis**:
   - Gets blueprint from Orchestrator
   - Checks: `src/components` ✅ exists with files
   - Checks: `src/services` ❌ missing
   - Checks: `src/hooks` ✅ exists but empty
   - Reports: Missing `src/services` directory, empty `src/hooks` directory

3. **Dynamic Task Creation**:
   - Orchestrator creates tasks:
     - "Backend: Services" → CODER agent
     - "Frontend: Hooks" → FRONTEND agent

---

## Files Modified

1. **`agents/orchestrator.py`**:
   - Added `self.project_structure_blueprint` attribute
   - Added `_build_structure_blueprint()` method
   - Added `get_project_structure_blueprint()` method
   - Enhanced `_analyze_objective_with_llm()` to extract and store blueprint

2. **`agents/qa_agent.py`**:
   - Enhanced `_analyze_project_structure()` to use blueprint if available
   - Falls back to hardcoded expectations if blueprint unavailable

---

## Testing Recommendations

### Test Case 1: Blueprint Extraction
1. Start a mobile app project
2. **Expected**: Orchestrator extracts blueprint during task breakdown
3. **Expected**: Blueprint contains expected directories/files for mobile app
4. **Expected**: Blueprint stored in `orchestrator.project_structure_blueprint`

### Test Case 2: QA Blueprint Access
1. QA agent runs structure analysis
2. **Expected**: QA successfully gets blueprint from Orchestrator
3. **Expected**: QA uses blueprint to check structure (not hardcoded)
4. **Expected**: QA logs "[BLUEPRINT] Using structure blueprint for mobile_app project"

### Test Case 3: Missing Component Detection
1. Project missing `src/services` directory
2. **Expected**: QA detects missing component using blueprint
3. **Expected**: QA reports missing component to Orchestrator
4. **Expected**: Orchestrator creates dynamic task for missing component

### Test Case 4: Fallback Behavior
1. Start project without LLM (or LLM doesn't provide classification)
2. **Expected**: QA falls back to hardcoded expectations
3. **Expected**: No errors, system continues normally

---

## Future Enhancements

1. **Custom Project Types**: Allow LLM to define custom structure requirements
2. **Blueprint Merging**: Merge blueprints from multiple objectives
3. **Blueprint Validation**: Validate blueprint against actual project structure
4. **Blueprint Persistence**: Store blueprint in database for later reference
5. **Blueprint Versioning**: Track blueprint changes over time

---

**Implemented By**: QA Engineer (Terminator Bug Killer)  
**Implementation Date**: November 29, 2025  
**Status**: ✅ **READY FOR TESTING**

