# Workspace Security Guarantee System

## Overview

This document describes the **HARD GUARANTEE** system that prevents project-generated code from corrupting the platform's own code space.

## Critical Rules

1. **ALL project files MUST be written to `Tenant_Projects/{project_id}/`**
2. **NO files can be written outside the project workspace**
3. **Path traversal attacks are blocked**
4. **System folders are protected**

## Implementation

### Core Module: `utils/safe_file_writer.py`

All file writes by agents MUST go through this module. It provides:

- `validate_workspace_path()` - Ensures workspace is within Tenant_Projects
- `validate_file_path()` - Ensures file path is safe and within workspace
- `safe_write_file()` - The ONLY function agents should use to write files
- `safe_write_file_binary()` - For binary files

### BaseAgent Integration

All agents inherit from `BaseAgent`, which provides:

- `safe_write_file()` method - Wraps the safe_file_writer module
- Workspace path validation on initialization
- Automatic security checks on every file write

### Protected Resources

#### Protected System Folders
These folders CANNOT be written to by project code:
- `addon_portal`, `agents`, `api`, `config`, `docs`, `demos`, `infra`, `k8s`, `logs`, `mobile`, `research`, `shared`, `src`, `templates`, `tests`, `test_workspace`, `tools`, `utils`, `web`, `zbin`, `.github`, `.git`, `__pycache__`, `node_modules`, `venv`, `.venv`

#### Protected System Files
These files CANNOT be overwritten:
- `main.py`, `README.md`, `requirements.txt`, `config.json`, `.env`, `.gitignore`, and all system test/config files

## Usage

### For Agents

**ALWAYS use `self.safe_write_file()` instead of direct file operations:**

```python
# ❌ WRONG - Direct file write (will be blocked)
with open(os.path.join(self.workspace_path, "file.py"), 'w') as f:
    f.write(content)

# ✅ CORRECT - Safe file write
self.safe_write_file("file.py", content)
```

### For AgentSystem Initialization

Workspace path is automatically validated in `AgentSystem.__init__()`:

```python
# Workspace MUST be within Tenant_Projects/{project_id}/
workspace_path = f"Tenant_Projects/{project_id}"
system = AgentSystem(workspace_path=workspace_path, project_id=project_id)
```

## Security Violations

If any security rule is violated, a `WorkspaceSecurityError` is raised immediately:

```python
from utils.safe_file_writer import WorkspaceSecurityError

try:
    safe_write_file("../../main.py", "malicious code", workspace_path)
except WorkspaceSecurityError as e:
    print(f"SECURITY VIOLATION: {e}")
    # File write is BLOCKED
```

## Examples of Blocked Operations

1. **Writing outside Tenant_Projects:**
   ```python
   # ❌ BLOCKED
   safe_write_file("../../main.py", content, workspace_path=".")
   ```

2. **Path traversal:**
   ```python
   # ❌ BLOCKED
   safe_write_file("../../../main.py", content, workspace_path)
   ```

3. **Writing to protected folders:**
   ```python
   # ❌ BLOCKED
   safe_write_file("../agents/malicious.py", content, workspace_path)
   ```

4. **Overwriting system files:**
   ```python
   # ❌ BLOCKED
   safe_write_file("../../README.md", content, workspace_path)
   ```

## Migration Guide

All agents need to be updated to use `self.safe_write_file()`:

1. **CoderAgent** - Update `_implement_code_async()` method
2. **TestingAgent** - Update `_create_test_file()` method
3. **MobileAgent** - Update `_write_file()` method
4. **WorkflowAgent** - Update file writing methods
5. **ResearcherAgent** - Update `_save_research_results()` method
6. **FrontendAgent** - Update file writing methods
7. **All other agents** - Update any file writing code

## Testing

To verify the security system works:

```python
from utils.safe_file_writer import safe_write_file, WorkspaceSecurityError

# This should work
safe_write_file("test.py", "content", workspace_path="Tenant_Projects/test_project")

# This should raise WorkspaceSecurityError
try:
    safe_write_file("../../main.py", "content", workspace_path="Tenant_Projects/test_project")
except WorkspaceSecurityError:
    print("Security system working correctly!")
```

## Status

✅ **IMPLEMENTED** - Core security module created
✅ **INTEGRATED** - BaseAgent and AgentSystem updated
🔄 **IN PROGRESS** - Migrating all agents to use safe_write_file()

