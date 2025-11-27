# Bug Found During Testing - Session 1
**Role**: QA_Engineer  
**Date**: November 26, 2025  
**Status**: Fixed

---

## BUG-009: AGENT_ACTIVITY_SUBSCRIPTION Missing projectId Parameter in GraphQL Definition

**Severity**: High  
**Found During**: Test preparation / Code review  
**Location**: `addon_portal/apps/tenant-portal/src/lib/graphql.ts:176-187`

---

### Problem Description

While preparing for TEST-003 (Subscription Project Filtering), I discovered that the GraphQL subscription definition for `AGENT_ACTIVITY_SUBSCRIPTION` was missing the `projectId` parameter, even though the code in `status.tsx` was trying to pass it.

**Before Fix**:
```typescript
// In graphql.ts:
export const AGENT_ACTIVITY_SUBSCRIPTION = `
  subscription AgentActivity {  // ❌ No projectId parameter!
    agentActivity {
      id
      agentType
      agentId
      eventType
      message
      timestamp
      taskId
    }
  }
`;

// In status.tsx (line 141):
variables: { projectId: selectedProjectId || null }  // ❌ Parameter not defined in GraphQL!
```

**Impact**:
- GraphQL subscription would fail or ignore the projectId variable
- Backend resolver might not receive projectId
- Agent activity from all projects would be shown instead of filtered
- BUG-004 fix was incomplete

---

### Solution

Updated the GraphQL subscription definition to accept and use the `projectId` parameter:

**After Fix**:
```typescript
// QA_Engineer: Added projectId parameter to filter agent activity by project
export const AGENT_ACTIVITY_SUBSCRIPTION = `
  subscription AgentActivity($projectId: String) {
    agentActivity(projectId: $projectId) {
      id
      agentType
      agentId
      eventType
      message
      timestamp
      taskId
    }
  }
`;
```

---

### Files Modified

1. `addon_portal/apps/tenant-portal/src/lib/graphql.ts`
   - Updated `AGENT_ACTIVITY_SUBSCRIPTION` to accept `$projectId: String` parameter
   - Updated `agentActivity` resolver call to pass `projectId: $projectId`

---

### Verification

- ✅ GraphQL subscription definition now matches usage in `status.tsx`
- ✅ No linter errors
- ✅ Consistent with other subscriptions (`TASK_UPDATES_SUBSCRIPTION`, `SYSTEM_METRICS_STREAM_SUBSCRIPTION`)

---

### Related Bugs

- **BUG-004**: This bug was discovered while verifying BUG-004 fix
- BUG-004 fix in `status.tsx` was correct, but incomplete without this GraphQL definition update

---

### Testing Notes

This fix needs to be tested with:
- Backend API running
- WebSocket connection established
- Verify projectId is properly passed to backend
- Verify agent activity is filtered by project

---

**Role**: QA_Engineer  
**Status**: ✅ Fixed  
**Next**: Test with backend API running

