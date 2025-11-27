# QA Bug Report - Session 1
**Role**: QA_Engineer  
**Date**: November 26, 2025  
**Target File**: `addon_portal/apps/tenant-portal/src/pages/status.tsx`  
**Status**: Initial Review Complete

---

## Bug Report Summary

**Total Bugs Found**: 8  
**Critical**: 2  
**High**: 3  
**Medium**: 2  
**Low**: 1

---

## BUG-001: Event Listener Cleanup Mismatch
**Severity**: Medium  
**Location**: Line 67  
**Role**: QA_Engineer

**Issue**:
```typescript
window.addEventListener('scroll', handleScroll, { passive: true });
return () => window.removeEventListener('scroll', handleScroll);
```

**Problem**: The event listener is added with `{ passive: true }` option, but removed without specifying the same options. While this may work in most browsers, it's not guaranteed and could cause memory leaks in some environments.

**Impact**:
- Potential memory leak if cleanup doesn't match exactly
- Browser-specific behavior differences
- Not following React best practices

**Solution**:
```typescript
// QA_Engineer: Store handler reference for proper cleanup
const handleScroll = () => {
  scrollPositionRef.current = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
};

useEffect(() => {
  window.addEventListener('scroll', handleScroll, { passive: true });
  return () => window.removeEventListener('scroll', handleScroll);
}, []);
```

**Pros**:
- Proper cleanup matching addEventListener options
- Prevents potential memory leaks
- Follows React best practices

**Cons**:
- Slight code change required
- Need to verify handler reference stability

**Recommendation**: Fix - Low risk, high value for memory management

---

## BUG-002: Missing State Declaration
**Severity**: Critical  
**Location**: Line 82 (referenced but not declared in visible code)  
**Role**: QA_Engineer

**Issue**:
```typescript
const [projectSearch, setProjectSearch] = useState('');
```
This line appears to be missing from the code. Line 82 shows `const [loadingProjects, setLoadingProjects] = useState(true);` but `projectSearch` is used on lines 229, 355, 356, 359 without declaration visible.

**Problem**: If `projectSearch` state is not declared, this will cause a runtime error.

**Impact**:
- Runtime error: "projectSearch is not defined"
- Page will crash on load
- User cannot use search functionality

**Solution**:
```typescript
// QA_Engineer: Add missing state declaration
const [projectSearch, setProjectSearch] = useState('');
```

**Pros**:
- Fixes critical runtime error
- Enables search functionality
- Simple one-line fix

**Cons**:
- None - this is a required fix

**Recommendation**: Fix Immediately - Critical bug

---

## BUG-003: useEffect Dependency Array Missing selectedProjectId
**Severity**: High  
**Location**: Line 86-109  
**Role**: QA_Engineer

**Issue**:
```typescript
useEffect(() => {
  const loadProjects = async () => {
    // ... code that uses selectedProjectId on line 98
    if (activeProjects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(activeProjects[0].id);
    }
  };
  loadProjects();
}, []); // Empty dependency array
```

**Problem**: The effect uses `selectedProjectId` but doesn't include it in the dependency array. This means the effect only runs once on mount, and won't react to changes in `selectedProjectId`.

**Impact**:
- Effect doesn't react to `selectedProjectId` changes
- Potential stale closure issues
- React Hook warnings in development mode
- May not auto-select project correctly if `selectedProjectId` changes externally

**Solution**:
```typescript
// QA_Engineer: Add selectedProjectId to dependency array
useEffect(() => {
  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await listProjects(1, 100);
      const activeProjects = response.items.filter(
        p => p.execution_status === 'running' || p.status === 'active'
      );
      setAvailableProjects(activeProjects);
      
      // Only auto-select if no project is selected AND projects are available
      if (activeProjects.length > 0 && !selectedProjectId) {
        setSelectedProjectId(activeProjects[0].id);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoadingProjects(false);
    }
  };
  
  loadProjects();
}, [selectedProjectId]); // QA_Engineer: Include selectedProjectId in dependencies
```

**Pros**:
- Fixes React Hook dependency warning
- Ensures effect reacts to selectedProjectId changes
- Prevents stale closure bugs

**Cons**:
- Effect will re-run when selectedProjectId changes (may reload projects unnecessarily)
- Need to ensure this doesn't cause infinite loops

**Recommendation**: Fix with careful testing - Medium risk, high value

---

## BUG-004: Agent Activity Subscription Not Filtered by Project
**Severity**: High  
**Location**: Line 135  
**Role**: QA_Engineer

**Issue**:
```typescript
const [agentActivityResult] = useSubscription({ query: AGENT_ACTIVITY_SUBSCRIPTION });
```

**Problem**: The `AGENT_ACTIVITY_SUBSCRIPTION` doesn't filter by `projectId`, meaning it will show agent activity for ALL projects, not just the selected one. This contradicts the project-specific filtering used in other subscriptions.

**Impact**:
- Shows agent activity from all projects, not just selected project
- Inconsistent with other subscriptions (taskUpdatesResult, metricsStreamResult)
- User sees irrelevant agent activity
- Data confusion and potential security concern (showing other projects' data)

**Solution**:
```typescript
// QA_Engineer: Filter agent activity by selected project
const [agentActivityResult] = useSubscription({ 
  query: AGENT_ACTIVITY_SUBSCRIPTION,
  variables: { projectId: selectedProjectId || null },
  pause: !selectedProjectId, // Pause if no project selected
});
```

**Pros**:
- Consistent with other subscriptions
- Shows only relevant agent activity
- Better data isolation
- Improved user experience

**Cons**:
- Requires backend support for projectId filtering in AGENT_ACTIVITY_SUBSCRIPTION
- May need to update GraphQL schema

**Recommendation**: Fix - High priority for data consistency

---

## BUG-005: Inconsistent Status Casing
**Severity**: Medium  
**Location**: Line 288  
**Role**: QA_Engineer

**Issue**:
```typescript
status: task.status?.toLowerCase() || 'pending',
```

**Problem**: The code normalizes status to lowercase, but GraphQL may return uppercase values like 'COMPLETED', 'IN_PROGRESS', etc. The normalization happens inconsistently - some places expect uppercase, others lowercase.

**Impact**:
- Status comparisons may fail
- UI may not display correct status badges
- Inconsistent status handling throughout the codebase

**Solution**:
```typescript
// QA_Engineer: Normalize status consistently
const normalizeStatus = (status: string | undefined): 'pending' | 'in_progress' | 'completed' | 'failed' => {
  if (!status) return 'pending';
  const normalized = status.toLowerCase();
  if (normalized === 'completed' || normalized === 'done') return 'completed';
  if (normalized === 'in_progress' || normalized === 'inprogress' || normalized === 'running') return 'in_progress';
  if (normalized === 'failed' || normalized === 'error') return 'failed';
  return 'pending';
};

// Then use:
status: normalizeStatus(task.status),
```

**Pros**:
- Consistent status handling
- Handles both uppercase and lowercase inputs
- More robust status normalization

**Cons**:
- Requires helper function
- Need to ensure all status values are covered

**Recommendation**: Fix - Medium priority for consistency

---

## BUG-006: Emoji Characters in JSX (Windows Parsing Issue)
**Severity**: Critical  
**Location**: Lines 453, 462, 471, 480, 493, 503, 539, 543, 591  
**Role**: QA_Engineer

**Issue**:
Multiple emoji characters used directly in JSX:
- Line 453: `🤖` (robot emoji)
- Line 462: `✅` (checkmark emoji)
- Line 471: `📊` (chart emoji)
- Line 480: `⚡` (lightning emoji)
- Line 493: `👥` (people emoji)
- Line 503: `🤖` (robot emoji)
- Line 539: `📋` (clipboard emoji)
- Line 543: `📋` (clipboard emoji)
- Line 591: `📊` (chart emoji)

**Problem**: User specifically requested NO EMOJIS/ICONS in code due to Windows parsing issues. These emojis can cause encoding problems, build failures, or display issues on Windows systems.

**Impact**:
- Potential Windows build failures
- Encoding issues in source files
- Display problems on Windows systems
- Violates project requirements

**Solution**:
Replace all emojis with text alternatives or icon components:

```typescript
// QA_Engineer: Replace emojis with text/icons
// Line 453: Replace 🤖 with "Agent" or icon component
<div className="text-3xl">Agent</div>
// OR use an icon library like react-icons

// Line 462: Replace ✅ with "Complete" or checkmark icon
<div className="text-3xl">Complete</div>

// Line 471: Replace 📊 with "Chart" or chart icon
<div className="text-3xl">Chart</div>

// Line 480: Replace ⚡ with "Active" or lightning icon
<div className="text-3xl">Active</div>

// Line 493: Replace 👥 with "Agent Activity" text
<h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
  Agent Activity
  {activeAgents > 0 && (
    <span className="text-sm font-normal text-gray-500">
      ({activeAgents} active)
    </span>
  )}
</h2>

// Line 503: Replace 🤖 with "No Agents" text
<div className="text-center py-12">
  <div className="text-6xl mb-4">No Agents</div>
  <p className="text-gray-500">
    {connected ? 'No agents active yet...' : 'Connecting to dashboard...'}
  </p>
</div>

// Line 539: Replace 📋 with "Task Timeline" text
<h2 className="text-xl font-bold text-gray-900 mb-4">Task Timeline</h2>

// Line 543: Replace 📋 with "No Tasks" text
<div className="text-center py-12">
  <div className="text-6xl mb-4">No Tasks</div>
  <p className="text-gray-500">
    {connected ? 'No tasks yet...' : 'Waiting for tasks...'}
  </p>
</div>

// Line 591: Replace 📊 with "System Metrics" text
<h2 className="text-xl font-bold text-gray-900 mb-4">System Metrics</h2>
```

**Pros**:
- Fixes Windows compatibility issues
- Meets project requirements
- More accessible (screen readers can read text)
- No encoding issues

**Cons**:
- Less visually appealing (but can use icon libraries instead)
- Requires replacing multiple instances

**Recommendation**: Fix Immediately - Critical for Windows compatibility

---

## BUG-007: Task Updates List Not Cleared on Project Change
**Severity**: High  
**Location**: Lines 151-169  
**Role**: QA_Engineer

**Issue**:
```typescript
const [taskUpdatesList, setTaskUpdatesList] = useState<any[]>([]);
useEffect(() => {
  if (taskUpdatesResult.data?.taskUpdates) {
    shouldRestoreScrollRef.current = true;
    const update = taskUpdatesResult.data.taskUpdates;
    setTaskUpdatesList(prev => {
      // Updates list but never clears it
    });
  }
}, [taskUpdatesResult.data]);
```

**Problem**: When the user switches projects, `taskUpdatesList` is not cleared. This means tasks from the previous project will still be displayed when viewing a new project.

**Impact**:
- Shows tasks from previous project when switching projects
- Data confusion and incorrect task display
- User sees wrong project's tasks

**Solution**:
```typescript
// QA_Engineer: Clear task updates when project changes
useEffect(() => {
  // Clear task updates when project changes
  setTaskUpdatesList([]);
}, [selectedProjectId]);

useEffect(() => {
  if (taskUpdatesResult.data?.taskUpdates) {
    shouldRestoreScrollRef.current = true;
    const update = taskUpdatesResult.data.taskUpdates;
    setTaskUpdatesList(prev => {
      const existingIndex = prev.findIndex(t => t.id === update.id);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = update;
        return updated;
      }
      return [...prev, update];
    });
  }
}, [taskUpdatesResult.data]);
```

**Pros**:
- Clears old project's tasks when switching
- Shows only current project's tasks
- Better data isolation

**Cons**:
- Adds another useEffect
- Need to ensure timing is correct

**Recommendation**: Fix - High priority for data accuracy

---

## BUG-008: Missing Error Handling for GraphQL Subscriptions
**Severity**: Medium  
**Location**: Lines 135-143  
**Role**: QA_Engineer

**Issue**:
```typescript
const [agentActivityResult] = useSubscription({ query: AGENT_ACTIVITY_SUBSCRIPTION });
const [taskUpdatesResult] = useSubscription({
  query: TASK_UPDATES_SUBSCRIPTION,
  variables: { projectId: selectedProjectId || null },
});
const [metricsStreamResult] = useSubscription({ 
  query: SYSTEM_METRICS_STREAM_SUBSCRIPTION,
  variables: { projectId: selectedProjectId || null },
});
```

**Problem**: No error handling for subscription failures. If WebSocket connection fails or subscription errors occur, the user won't be notified and the UI may show stale or no data.

**Impact**:
- No user feedback on subscription failures
- Silent failures may go unnoticed
- Poor user experience
- Difficult to debug connection issues

**Solution**:
```typescript
// QA_Engineer: Add error handling for subscriptions
const [agentActivityResult] = useSubscription({ query: AGENT_ACTIVITY_SUBSCRIPTION });
const [taskUpdatesResult] = useSubscription({
  query: TASK_UPDATES_SUBSCRIPTION,
  variables: { projectId: selectedProjectId || null },
});
const [metricsStreamResult] = useSubscription({ 
  query: SYSTEM_METRICS_STREAM_SUBSCRIPTION,
  variables: { projectId: selectedProjectId || null },
});

// QA_Engineer: Handle subscription errors
useEffect(() => {
  if (agentActivityResult.error) {
    console.error('Agent activity subscription error:', agentActivityResult.error);
    // Optionally show user notification
  }
}, [agentActivityResult.error]);

useEffect(() => {
  if (taskUpdatesResult.error) {
    console.error('Task updates subscription error:', taskUpdatesResult.error);
  }
}, [taskUpdatesResult.error]);

useEffect(() => {
  if (metricsStreamResult.error) {
    console.error('Metrics stream subscription error:', metricsStreamResult.error);
  }
}, [metricsStreamResult.error]);
```

**Pros**:
- Better error visibility
- Easier debugging
- Can notify users of connection issues

**Cons**:
- Adds more useEffect hooks
- May need user-facing error notifications

**Recommendation**: Fix - Medium priority for reliability

---

## Summary

**Critical Bugs (Fix Immediately)**:
1. BUG-002: Missing State Declaration
2. BUG-006: Emoji Characters in JSX

**High Priority Bugs (Fix Soon)**:
3. BUG-003: useEffect Dependency Array
4. BUG-004: Agent Activity Subscription Not Filtered
5. BUG-007: Task Updates List Not Cleared

**Medium Priority Bugs (Fix When Possible)**:
6. BUG-001: Event Listener Cleanup
7. BUG-005: Inconsistent Status Casing
8. BUG-008: Missing Error Handling

---

**Next Steps**:
1. Review this bug report
2. Approve fixes for each bug
3. QA_Engineer will implement fixes one by one
4. Test each fix before moving to next bug

---

**Role**: QA_Engineer  
**Session**: 1  
**Status**: Awaiting Approval

