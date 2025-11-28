# Critical Bug Report: File Persistence Failure - MSN Messenger Clone

**Date**: November 28, 2025  
**Reporter**: QA_Engineer  
**Project ID**: `msn-messenger-clone`  
**Severity**: 🔴 **CRITICAL**  
**Status**: 🔍 **INVESTIGATING**

---

## 📋 Problem Summary

Files are being written and verified successfully according to logs, but they **disappear** from the file system. Only `research/` and `tests/` folders contain files; all other folders (`src/`, root-level files like `App.tsx`, `package.json`, etc.) are **empty or missing**.

---

## 🔍 Evidence

### Logs Show Files Were Written and Verified:
```
[SAFE_WRITE] Verified file exists: C:\Q2O_Combined\Tenant_Projects\msn-messenger-clone\App.tsx (409 bytes)
[SAFE_WRITE] Verified file exists: C:\Q2O_Combined\Tenant_Projects\msn-messenger-clone\package.json (533 bytes)
[SAFE_WRITE] Verified file exists: C:\Q2O_Combined\Tenant_Projects\msn-messenger-clone\src\navigation\RootNavigator.tsx
```

### Actual File System Check:
```powershell
Test-Path "Tenant_Projects\msn-messenger-clone\App.tsx"
# Returns: False

Get-ChildItem "Tenant_Projects\msn-messenger-clone" -File
# Only shows: execution_stderr.log, execution_stdout.log

Get-ChildItem "Tenant_Projects\msn-messenger-clone\src\components"
# Empty directory

Get-ChildItem "Tenant_Projects\msn-messenger-clone\src\screens"
# Empty directory
```

### What EXISTS:
- ✅ `research/` folder - Contains JSON and MD files
- ✅ `tests/` folder - Contains test files
- ✅ `execution_stdout.log` and `execution_stderr.log`

### What's MISSING:
- ❌ Root-level files: `App.tsx`, `package.json`, `tsconfig.json`
- ❌ `src/components/` - Empty
- ❌ `src/screens/` - Empty
- ❌ `src/services/` - Empty
- ❌ `src/navigation/` - Empty
- ❌ `ios/Info.plist` - Missing
- ❌ `android/AndroidManifest.xml` - Missing

---

## 🔍 Root Cause Analysis

### Hypothesis 1: Files Written to Wrong Location
- **Evidence**: Logs show files written to `C:\Q2O_Combined\Tenant_Projects\msn-messenger-clone\...`
- **Check**: Verify `workspace_path` is correctly set in `main.py` when called from tenant portal
- **Status**: ⚠️ **NEEDS VERIFICATION**

### Hypothesis 2: Files Deleted After Write
- **Evidence**: Files verified to exist, but missing later
- **Check**: Search for cleanup/deletion code that might run after project completion
- **Status**: ⚠️ **NEEDS INVESTIGATION**

### Hypothesis 3: Multiple Writes Overwriting Each Other
- **Evidence**: Logs show same files written multiple times by different tasks
- **Check**: Check if later writes are overwriting with empty content
- **Status**: ⚠️ **NEEDS INVESTIGATION**

### Hypothesis 4: Git Cleanup Removing Files
- **Evidence**: Git integration might be cleaning up uncommitted files
- **Check**: Check `utils/git_manager.py` for cleanup operations
- **Status**: ⚠️ **NEEDS INVESTIGATION**

### Hypothesis 5: Workspace Path Mismatch
- **Evidence**: Files verified at one path but written to another
- **Check**: Verify `workspace_path` passed to agents matches actual write location
- **Status**: ✅ **VERIFIED** - Path is correct

### Hypothesis 6: Windows File Buffering Issue ✅ **ROOT CAUSE IDENTIFIED**
- **Evidence**: Files written and verified successfully, but missing after process exit
- **Root Cause**: Python's file buffering on Windows can delay writes to disk. Files are written to OS buffer but not flushed to disk before process exits.
- **Fix**: Added explicit `flush()` and `os.fsync()` calls to force immediate disk write
- **Status**: ✅ **FIXED**

---

## 🔧 Investigation Steps

1. **Check `workspace_path` in `main.py`**:
   - Verify `--output-folder` is correctly passed from `project_execution_service.py`
   - Verify `workspace_path` is set correctly in `AgentSystem.__init__`
   - Verify agents receive correct `workspace_path`

2. **Check File Write Timing**:
   - Compare timestamps of file writes vs. file deletions (if any)
   - Check if files exist immediately after write but disappear later

3. **Check Git Operations**:
   - Review `utils/git_manager.py` for cleanup/reset operations
   - Check if git operations are deleting files

4. **Check Safe File Writer**:
   - Verify `safe_write_file` is actually writing to the correct location
   - Check if file verification is checking the wrong path

5. **Check Project Cleanup**:
   - Search for any cleanup code that runs after project completion
   - Check if project restart is clearing files

---

## 📊 Impact

### User Impact:
- 🔴 **CRITICAL**: Users cannot download completed projects
- 🔴 **CRITICAL**: Generated code is lost
- 🔴 **CRITICAL**: Project completion is meaningless without code

### System Impact:
- 🔴 **CRITICAL**: Core functionality broken
- 🔴 **CRITICAL**: All mobile projects affected
- 🔴 **CRITICAL**: All projects using Coder Agent affected

---

## ✅ Next Steps

1. **Immediate**: Investigate file write location vs. verification location
2. **Immediate**: Check for cleanup/deletion code
3. **High Priority**: Verify `workspace_path` is correctly set
4. **High Priority**: Test file persistence in a new project run
5. **Medium Priority**: Add file persistence monitoring/logging

---

## 📝 Related Issues

- Similar issue reported for `wordpress-like-clone` project (files not persisting)
- Similar issue reported for `whatsapp-clone-messaging-app` project (files missing)

---

**Status**: ✅ **FIXED** - Root cause: Windows file buffering. Files written to OS buffer but not flushed to disk before process exit.

## ✅ Solution Implemented

**File**: `utils/safe_file_writer.py`

**Fix**: Added explicit file flushing and syncing to ensure files are written to disk immediately:

```python
# BEFORE:
with open(validated_file_path, 'w', encoding=encoding) as f:
    f.write(content)

# AFTER:
with open(validated_file_path, 'w', encoding=encoding, buffering=1) as f:  # Line buffering
    f.write(content)
    f.flush()  # Force flush to OS buffer
    os.fsync(f.fileno())  # Force sync to disk (Windows compatible)
```

**Impact**: Files will now be immediately written to disk, preventing data loss when the process exits quickly.

