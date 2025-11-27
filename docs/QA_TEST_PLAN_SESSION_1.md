# QA Test Plan - Session 1 (Bug Fixes)
**Role**: QA_Engineer  
**Date**: November 26, 2025  
**Target File**: `addon_portal/apps/tenant-portal/src/pages/status.tsx`  
**Status**: Ready for Testing

---

## Test Objectives

Verify that all 7 bug fixes are working correctly:
1. ✅ Event listener cleanup (BUG-001)
2. ✅ useEffect dependency array (BUG-003)
3. ✅ Subscription project filtering (BUG-004)
4. ✅ Status normalization (BUG-005)
5. ✅ Emoji removal (BUG-006)
6. ✅ Task list clearing on project change (BUG-007)
7. ✅ Subscription error handling (BUG-008)

---

## Test Environment Setup

### Prerequisites
1. **Backend API Running** (Port 8080):
   ```powershell
   cd addon_portal
   python -m uvicorn api.main:app --port 8080
   ```

2. **Tenant Portal Running** (Port 3000):
   ```powershell
   cd addon_portal/apps/tenant-portal
   npm run dev
   ```

3. **Database**: PostgreSQL running with test data

4. **Browser**: Chrome/Edge with DevTools open (F12)

---

## Test Cases

### TEST-001: Event Listener Cleanup (BUG-001)
**Objective**: Verify scroll event listener is properly cleaned up

**Steps**:
1. Navigate to `/status` page
2. Open DevTools → Console
3. Scroll the page up and down multiple times
4. Navigate away from the page (go to another route)
5. Check console for any memory leak warnings
6. Navigate back to `/status` page
7. Repeat scrolling

**Expected Results**:
- ✅ No console errors or warnings
- ✅ No memory leak warnings in React DevTools
- ✅ Scroll position preserved during real-time updates
- ✅ Event listener properly removed on unmount

**Status**: ⬜ Not Tested

---

### TEST-002: useEffect Dependency Array (BUG-003)
**Objective**: Verify useEffect reacts to selectedProjectId changes

**Steps**:
1. Navigate to `/status` page
2. Open DevTools → Console
3. Check for React Hook warnings
4. Select a project from the dropdown
5. Change to a different project
6. Clear project selection
7. Select project again

**Expected Results**:
- ✅ No React Hook dependency warnings in console
- ✅ Projects load correctly when selectedProjectId changes
- ✅ Auto-select works when projects are available
- ✅ No infinite loops or excessive re-renders

**Status**: ⬜ Not Tested

---

### TEST-003: Subscription Project Filtering (BUG-004)
**Objective**: Verify subscriptions are filtered by selected project

**Steps**:
1. Navigate to `/status` page
2. Open DevTools → Network tab → WS (WebSocket)
3. Select Project A
4. Observe WebSocket messages in Network tab
5. Switch to Project B
6. Observe WebSocket messages change
7. Clear project selection
8. Verify subscriptions pause

**Expected Results**:
- ✅ Agent activity subscription includes `projectId` variable
- ✅ Task updates subscription includes `projectId` variable
- ✅ Metrics stream subscription includes `projectId` variable
- ✅ Subscriptions pause when no project selected
- ✅ Only data for selected project is displayed
- ✅ No data from other projects leaks through

**Status**: ⬜ Not Tested

---

### TEST-004: Status Normalization (BUG-005)
**Objective**: Verify status values are normalized consistently

**Steps**:
1. Navigate to `/status` page
2. Select a project with tasks
3. Check task status badges in Task Timeline
4. Verify status display is consistent
5. Check project status display
6. Inspect network responses for various status formats

**Expected Results**:
- ✅ Task statuses display correctly regardless of casing (COMPLETED, completed, Completed)
- ✅ Status badges show correct colors (green for completed, blue for in_progress, etc.)
- ✅ No "undefined" or "unknown" statuses displayed
- ✅ Status normalization handles: 'completed', 'done', 'in_progress', 'inprogress', 'running', 'failed', 'error'

**Status**: ⬜ Not Tested

---

### TEST-005: Emoji Removal (BUG-006)
**Objective**: Verify no emoji characters cause Windows parsing issues

**Steps**:
1. Navigate to `/status` page
2. Check all UI elements that previously had emojis:
   - Agent card icon
   - Completed tasks card icon
   - Success rate card icon
   - Active tasks card icon
   - Agent Activity section header
   - Task Timeline section header
   - System Metrics section header
3. Verify build succeeds on Windows
4. Check browser console for encoding errors

**Expected Results**:
- ✅ No emoji characters visible in UI
- ✅ Text alternatives display correctly (Agent, Complete, Chart, Active, etc.)
- ✅ No encoding errors in console
- ✅ Build succeeds without Windows parsing errors
- ✅ All icons replaced with descriptive text

**Status**: ⬜ Not Tested

---

### TEST-006: Task List Clearing on Project Change (BUG-007)
**Objective**: Verify task updates list clears when switching projects

**Steps**:
1. Navigate to `/status` page
2. Select Project A
3. Wait for tasks to appear in Task Timeline
4. Note the task count and task IDs
5. Switch to Project B
6. Verify Task Timeline shows only Project B's tasks
7. Switch back to Project A
8. Verify Project A's tasks reappear

**Expected Results**:
- ✅ Task Timeline clears immediately when project changes
- ✅ No tasks from previous project remain visible
- ✅ Only tasks for currently selected project are shown
- ✅ Task list repopulates correctly when switching back
- ✅ No stale data displayed

**Status**: ⬜ Not Tested

---

### TEST-007: Subscription Error Handling (BUG-008)
**Objective**: Verify subscription errors are properly logged

**Steps**:
1. Navigate to `/status` page
2. Open DevTools → Console
3. Select a project
4. Stop the backend API server (simulate connection failure)
5. Observe console for error messages
6. Restart backend API server
7. Verify subscriptions reconnect

**Expected Results**:
- ✅ Agent activity subscription errors logged to console with "QA_Engineer:" prefix
- ✅ Task updates subscription errors logged to console
- ✅ Metrics stream subscription errors logged to console
- ✅ Error messages are descriptive and include error details
- ✅ No silent failures
- ✅ Subscriptions attempt to reconnect when backend is available

**Status**: ⬜ Not Tested

---

## Integration Tests

### TEST-008: Full Page Functionality
**Objective**: Verify all fixes work together

**Steps**:
1. Navigate to `/status` page
2. Select a project
3. Scroll down the page
4. Wait for real-time updates
5. Switch projects multiple times
6. Scroll up and down during updates
7. Check console for errors
8. Verify all UI elements display correctly

**Expected Results**:
- ✅ All fixes work together without conflicts
- ✅ No console errors or warnings
- ✅ Real-time updates work correctly
- ✅ Scroll position preserved
- ✅ Project switching works smoothly
- ✅ All data displays correctly

**Status**: ⬜ Not Tested

---

## Browser Compatibility Tests

### TEST-009: Cross-Browser Testing
**Browsers to Test**:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if available)

**Steps**:
1. Run all test cases in each browser
2. Verify consistent behavior
3. Check for browser-specific issues

**Expected Results**:
- ✅ Consistent behavior across browsers
- ✅ No browser-specific errors
- ✅ Event listeners work correctly in all browsers

**Status**: ⬜ Not Tested

---

## Performance Tests

### TEST-010: Memory Leak Check
**Objective**: Verify no memory leaks from event listeners

**Steps**:
1. Open DevTools → Performance → Memory
2. Navigate to `/status` page
3. Select project
4. Scroll multiple times
5. Switch projects multiple times
6. Navigate away and back
7. Repeat 10 times
8. Check memory usage

**Expected Results**:
- ✅ No memory leaks detected
- ✅ Memory usage remains stable
- ✅ Event listeners properly cleaned up

**Status**: ⬜ Not Tested

---

## Regression Tests

### TEST-011: Existing Functionality Still Works
**Objective**: Verify bug fixes didn't break existing features

**Steps**:
1. Test all existing status page features:
   - Project selection
   - Real-time updates
   - Task timeline display
   - Agent activity display
   - System metrics display
   - Progress bars
   - Status badges

**Expected Results**:
- ✅ All existing features work as before
- ✅ No regressions introduced
- ✅ UI displays correctly

**Status**: ⬜ Not Tested

---

## Test Execution Log

**Date**: _______________  
**Tester**: QA_Engineer  
**Environment**: Windows 10, Node.js ___, Browser: ___

| Test ID | Status | Notes |
|---------|--------|-------|
| TEST-001 | ⬜ | |
| TEST-002 | ⬜ | |
| TEST-003 | ⬜ | |
| TEST-004 | ⬜ | |
| TEST-005 | ⬜ | |
| TEST-006 | ⬜ | |
| TEST-007 | ⬜ | |
| TEST-008 | ⬜ | |
| TEST-009 | ⬜ | |
| TEST-010 | ⬜ | |
| TEST-011 | ⬜ | |

---

## Test Results Summary

**Total Tests**: 11  
**Passed**: ___  
**Failed**: ___  
**Blocked**: ___  
**Not Run**: ___

---

## Issues Found During Testing

| Issue ID | Description | Severity | Status |
|----------|-------------|----------|--------|
| | | | |

---

## Sign-off

**QA_Engineer**: _______________  
**Date**: _______________  
**Status**: ⬜ Pass / ⬜ Fail / ⬜ Needs Retest

---

**Next Steps**:
- [ ] Execute all test cases
- [ ] Document results
- [ ] Fix any issues found
- [ ] Retest fixes
- [ ] Sign off on testing

