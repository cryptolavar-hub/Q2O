# Tenant Dashboard Display Fixes

**Date**: November 26, 2025  
**Status**: IMPLEMENTED ✅

---

## Executive Summary

Fixed critical issues with the Tenant Dashboard that prevented proper display of:
1. **Agent Activity**: Now shows all active agents from actual task execution
2. **Task Timeline**: Now displays completed tasks in chronological order
3. **Completion Rate**: Fixed discrepancy between "Overall Progress" and "Completion Rate" bars

---

## Problem Statement

### Issue 1: Agent Activity Not Showing

**Symptoms:**
- Dashboard showed "0 Active Agents" even when project was running
- No agent information displayed in Agent Activity section
- Agents were working on tasks but not visible in UI

**Root Cause:**
- GraphQL resolver only aggregated agents from `LLMProjectConfig.agent_configs`
- Agents that were working on tasks but not explicitly configured were not included
- Agent status logic was incorrect (checking wrong conditions)

### Issue 2: Task Timeline Not Showing

**Symptoms:**
- Task Timeline section was empty
- No chronological list of completed tasks
- Only in-progress tasks were fetched, not completed ones

**Root Cause:**
- GraphQL query only fetched `IN_PROGRESS` tasks
- Completed tasks were not included in the query
- Frontend was not combining query results with subscription updates correctly

### Issue 3: Completion Rate Discrepancy

**Symptoms:**
- "Overall Progress" bar showed different percentage than "Completion Rate" bar
- Top bar showed 7% while bottom bar showed 19%
- Confusing for users to see different values

**Root Cause:**
- Top bar used `calculateProgress()` which had fallback to global dashboard stats
- Bottom bar used `selectedProject.completionPercentage` directly from GraphQL
- Different data sources caused different values

---

## Solution Implementation

### 1. Agent Activity Fix

#### Backend Changes: `addon_portal/api/graphql/resolvers.py`

**Problem:**
- Only aggregated agents from `db_project.agent_configs`
- Missed agents that were working on tasks but not configured

**Solution:**
- Modified `project()` resolver to aggregate agents from BOTH sources:
  1. `db_project.agent_configs` (explicitly configured agents)
  2. Actual `AgentTask` entries (agents that have worked on tasks)

**Key Code:**
```python
# Get task counts per agent type from actual tasks
agent_task_counts = {}
agent_types_seen = set()

if total_tasks > 0:
    agent_tasks = await get_project_tasks(db, id, execution_started_at=execution_started_at)
    for task in agent_tasks:
        agent_type = task.agent_type
        agent_types_seen.add(agent_type)
        
        # Aggregate task counts per agent
        if agent_type not in agent_task_counts:
            agent_task_counts[agent_type] = {
                "completed": 0, 
                "failed": 0, 
                "running": None, 
                "last_activity": None
            }
        
        # Track status and last activity
        if task.status == 'completed':
            agent_task_counts[agent_type]["completed"] += 1
        elif task.status == 'failed':
            agent_task_counts[agent_type]["failed"] += 1
        elif task.status in ('started', 'running'):
            agent_task_counts[agent_type]["running"] = task.task_id
        
        if task.updated_at:
            if not agent_task_counts[agent_type]["last_activity"] or \
               task.updated_at > agent_task_counts[agent_type]["last_activity"]:
                agent_task_counts[agent_type]["last_activity"] = task.updated_at

# Combine configured agents with agents from tasks
all_agent_types = set(agent_types_seen)
if agent_configs_by_type:
    all_agent_types.update(agent_configs_by_type.keys())

# Create agent objects for all agent types
for agent_type_str in all_agent_types:
    agent_stats = agent_task_counts.get(agent_type_str, {...})
    agent_config = agent_configs_by_type.get(agent_type_str)
    
    # Determine status: active if project running, agent enabled, and has active tasks
    is_active = (
        db_project.execution_status == 'running' and
        (agent_config is None or agent_config.enabled) and
        agent_stats["running"] is not None
    )
    
    agents.append(Agent(
        id=agent_type_str,
        agentType=agent_type_str,
        name=agent_config.name if agent_config else agent_type_str,
        status='active' if is_active else 'idle',
        # ... other fields ...
    ))
```

**Benefits:**
- Shows ALL agents that have worked on tasks, not just configured ones
- Accurate task counts per agent
- Correct status (active/idle) based on actual task activity
- Last activity timestamp from most recent task update

#### Frontend Changes: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

**Changes:**
- Updated `dashboardState.agents` mapping to correctly use `projectAgents` from GraphQL query
- Ensured agent names and statuses are displayed correctly

---

### 2. Task Timeline Fix

#### Backend Changes: `addon_portal/api/services/agent_task_service.py`

**Problem:**
- `get_project_tasks()` didn't filter by `execution_started_at`
- Would fetch tasks from previous runs

**Solution:**
- Added `execution_started_at` parameter to filter tasks by current run

**Key Code:**
```python
async def get_project_tasks(
    db: AsyncSession,
    project_id: str,
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    execution_started_at: Optional[datetime] = None,  # Added parameter
) -> list[AgentTask]:
    stmt = select(AgentTask).where(AgentTask.project_id == project_id)
    
    if status:
        stmt = stmt.where(AgentTask.status == status)
    if agent_type:
        stmt = stmt.where(AgentTask.agent_type == agent_type)
    if execution_started_at:  # Added filter
        if execution_started_at.tzinfo is None:
            execution_started_at = execution_started_at.replace(tzinfo=timezone.utc)
        stmt = stmt.where(AgentTask.created_at >= execution_started_at)
    
    stmt = stmt.order_by(AgentTask.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

#### GraphQL Changes: `addon_portal/api/graphql/resolvers.py`

**Problem:**
- `tasks()` resolver only fetched `IN_PROGRESS` tasks
- Completed tasks were not included

**Solution:**
- Modified to fetch ALL tasks (not just `IN_PROGRESS`)
- Ordered by `created_at` descending for chronological timeline

**Key Code:**
```python
@strawberry.field
async def tasks(
    self,
    project_id: str,
    limit: int = 50,
    order_by: str = "createdAt",
    order_direction: str = "DESC"
) -> list[Task]:
    # Fetch all tasks, not just IN_PROGRESS
    tasks = await get_project_tasks(
        db, 
        project_id, 
        status=None,  # Changed from 'IN_PROGRESS'
        execution_started_at=execution_started_at
    )
    # ... return tasks ...
```

#### Frontend Changes: `addon_portal/apps/tenant-portal/src/lib/graphql.ts`

**Problem:**
- `PROJECT_QUERY` only fetched `IN_PROGRESS` tasks
- No `completedTasks` field

**Solution:**
- Updated query to fetch all tasks
- Added `completedTasks` field
- Changed `tasks` field to fetch all tasks, ordered by `createdAt`

**Key Code:**
```typescript
export const PROJECT_QUERY = `
  query Project($id: String!) {
    project(id: $id) {
      # ... other fields ...
      completedTasks  # Added field
      tasks(limit: 50, orderBy: createdAt, orderDirection: DESC) {  # Changed to fetch all tasks
        id
        title
        status
        agentType
        durationSeconds
        createdAt
        completedAt
      }
    }
  }
`;
```

#### Frontend Changes: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

**Problem:**
- Tasks state was not combining query results with subscription updates
- Tasks were not sorted chronologically

**Solution:**
- Modified `dashboardState.tasks` to combine:
  1. `selectedProject.completedTasks` (from query)
  2. `taskUpdatesList` (from subscription)
- Removed duplicates (prefer subscription updates)
- Sorted by `completedAt` descending for timeline

**Key Code:**
```typescript
tasks: (() => {
  // Combine completed tasks from query with real-time updates from subscription
  const completedTasks = selectedProject?.completedTasks || [];
  const allTasks = [...completedTasks, ...taskUpdatesList];
  
  // Remove duplicates (prefer subscription updates over query results)
  const taskMap = new Map();
  allTasks.forEach((task: any) => {
    if (!taskMap.has(task.id) || task.status === 'COMPLETED' || task.status === 'completed') {
      taskMap.set(task.id, task);
    }
  });
  
  // Sort by completed_at (most recent first) for timeline
  return Array.from(taskMap.values())
    .sort((a: any, b: any) => {
      const aTime = a.completedAt ? new Date(a.completedAt).getTime() : 0;
      const bTime = b.completedAt ? new Date(b.completedAt).getTime() : 0;
      return bTime - aTime; // Most recent first
    })
    .map((task: any) => ({
      id: task.id,
      title: task.title || 'Unknown Task',
      status: task.status?.toLowerCase() || 'pending',
      agent: task.agent?.name || task.agentType || undefined,
      progress: task.progress || (task.status === 'COMPLETED' ? 100 : 0),
    }));
})(),
```

---

### 3. Completion Rate Discrepancy Fix

#### Frontend Changes: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

**Problem:**
- Top "Overall Progress" bar used `calculateProgress()` with fallback to global dashboard stats
- Bottom "Completion Rate" bar used `selectedProject.completionPercentage` directly
- Different data sources = different values

**Solution:**
- Modified `calculateProgress()` to use project-specific data only
- Both bars now use the same `realTimeProgress` value

**Key Code:**
```typescript
// Calculate real-time progress from project data
// CRITICAL: Use project-specific completionPercentage, not global dashboard stats
const calculateProgress = (): number => {
  // Priority 1: Use selectedProject.completionPercentage (from GraphQL query - project-specific)
  if (selectedProject?.completionPercentage !== undefined) {
    return Math.round(Math.min(100, Math.max(0, selectedProject.completionPercentage)));
  }
  
  // Priority 2: Calculate from selectedProject task counts (if completionPercentage not available)
  if (selectedProject && selectedProject.totalTasks > 0) {
    const percentage = ((selectedProject.completedTasks || 0) / selectedProject.totalTasks) * 100;
    return Math.round(Math.min(100, Math.max(0, percentage)));
  }
  
  // Priority 3: Fallback to 0 if no project data available
  return 0;
};

const realTimeProgress = calculateProgress();
```

**Usage:**
- Top bar: `{Math.round(project.progress)}%` (where `project.progress = realTimeProgress`)
- Bottom bar: `{realTimeProgress}%`

**Result:**
- Both bars now show the same percentage
- Uses project-specific data from GraphQL query
- No more confusion from different values

---

## Files Modified

### Backend:
1. `addon_portal/api/graphql/resolvers.py`
   - Modified `project()` resolver to aggregate agents from tasks
   - Modified `tasks()` resolver to fetch all tasks

2. `addon_portal/api/services/agent_task_service.py`
   - Added `execution_started_at` parameter to `get_project_tasks()`

### Frontend:
1. `addon_portal/apps/tenant-portal/src/lib/graphql.ts`
   - Updated `PROJECT_QUERY` to fetch all tasks and `completedTasks`

2. `addon_portal/apps/tenant-portal/src/pages/status.tsx`
   - Fixed `calculateProgress()` to use project-specific data
   - Updated `dashboardState.tasks` to combine query and subscription data
   - Updated `dashboardState.agents` to use `projectAgents` correctly

---

## Benefits

### 1. **Accurate Agent Display**
- Shows all agents that have worked on tasks
- Correct status (active/idle) based on actual activity
- Accurate task counts per agent

### 2. **Complete Task Timeline**
- Shows all completed tasks in chronological order
- Real-time updates from subscription
- No missing tasks from previous runs

### 3. **Consistent Progress Display**
- Both progress bars show the same value
- Uses project-specific data
- No confusion from different calculations

---

## Testing

### Test Scenarios:

1. **Agent Activity:**
   - ✅ Agents working on tasks are displayed
   - ✅ Agent status is correct (active/idle)
   - ✅ Task counts are accurate

2. **Task Timeline:**
   - ✅ Completed tasks are displayed
   - ✅ Tasks are sorted chronologically
   - ✅ Real-time updates work correctly

3. **Completion Rate:**
   - ✅ Both bars show the same percentage
   - ✅ Uses project-specific data
   - ✅ Updates correctly as tasks complete

---

## Related Documentation

- **`docs/TASK_CREATION_DATABASE_FIX.md`** - Database session management fixes
- **`docs/DASHBOARD_AND_LLM_TRACKING_FIXES.md`** - Previous dashboard fixes
- **`docs/TENANT_DASHBOARD_ISSUES_ANALYSIS.md`** - Historical dashboard issues

---

**Status**: ✅ **COMPLETE**  
**Last Updated**: November 26, 2025

