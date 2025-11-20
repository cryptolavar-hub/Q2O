# Status Page Real-Time Updates - November 19, 2025

## Problem

The Status page needed:
1. **Project Selector**: Ability to identify and select running projects for the tenant
2. **Search/Filter**: Filter projects by name or ID
3. **Project-Specific Status**: Show status for the selected project (not aggregate)
4. **Automatic Progress Updates**: Progress bars should update automatically without manual refresh
5. **Real-Time via GraphQL**: Use GraphQL subscriptions for bandwidth-efficient real-time updates

## Solution

### 1. Project Selector with Search/Filter
**File**: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

- Added project selector dropdown with search functionality
- Loads tenant's active projects (execution_status = 'running' or status = 'active')
- Auto-selects first project if available
- Search filters projects by name or ID
- Shows selected project name and status

**Features**:
- Search input with live filtering
- Dropdown shows matching projects
- Clear button to deselect project
- Auto-selects first active project on load

### 2. Real-Time Progress Updates
**File**: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

- **GraphQL Subscriptions**: Uses `taskUpdates` and `systemMetricsStream` subscriptions
- **State Management**: Collects updates from subscriptions in state
- **Automatic Updates**: Progress bars update automatically via subscription data
- **Polling Fallback**: Polls project query every 2 seconds for additional updates

**Progress Calculation**:
- Primary: Uses `project.completionPercentage` from GraphQL query
- Fallback: Calculates from task updates (completed/total)
- Real-time: Updates as subscription data arrives

### 3. Project-Specific Data Display
**File**: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

- When project is selected:
  - Shows project name and status
  - Displays project-specific progress
  - Filters tasks to selected project
  - Shows project-specific metrics

- When no project selected:
  - Shows aggregate data for all active projects
  - Displays total active projects count

### 4. GraphQL Enhancements
**Files**: 
- `addon_portal/apps/tenant-portal/src/lib/graphql.ts`
- `addon_portal/api/graphql/resolvers.py`

**Added**:
- `PROJECT_QUERY`: Query single project by ID
- `PROJECT_UPDATES_SUBSCRIPTION`: Real-time project status updates (added to schema)
- `project_updates` subscription resolver

**Updated**:
- `TASK_UPDATES_SUBSCRIPTION`: Now accepts `projectId` parameter for filtering
- `PROJECTS_QUERY`: Enhanced with filter support

### 5. Dynamic Progress Bars
**File**: `addon_portal/apps/tenant-portal/src/pages/status.tsx`

All progress bars now:
- Use `transition-all duration-500 ease-out` for smooth animations
- Update automatically from subscription data
- Show real-time values (no manual refresh needed)

**Progress Bars Updated**:
- Overall Progress (main card)
- Completion Rate (system metrics)
- Success Rate (system metrics)
- CPU Usage (system metrics)
- Memory Usage (system metrics)
- Individual Task Progress (task timeline)

## Files Modified

1. **`addon_portal/apps/tenant-portal/src/pages/status.tsx`**:
   - Added project selector with search
   - Added real-time state management for subscriptions
   - Added polling for project query
   - Updated progress bars to use real-time data
   - Added project-specific data filtering

2. **`addon_portal/apps/tenant-portal/src/lib/graphql.ts`**:
   - Added `PROJECT_QUERY`
   - Added `PROJECT_UPDATES_SUBSCRIPTION`
   - Updated `TASK_UPDATES_SUBSCRIPTION` to accept `projectId` parameter
   - Enhanced `PROJECTS_QUERY` with filter support

3. **`addon_portal/api/graphql/resolvers.py`**:
   - Added `project_updates` subscription resolver

## How It Works

### Project Selection Flow:
1. Page loads → Fetches tenant's active projects via REST API
2. Auto-selects first project (if available)
3. User can search/filter projects
4. When project selected → GraphQL query fetches project details
5. GraphQL subscriptions provide real-time updates

### Real-Time Updates Flow:
1. **Task Updates**: `taskUpdates` subscription filters by `projectId`
2. **Metrics Updates**: `systemMetricsStream` subscription provides system-wide metrics every 5 seconds
3. **Project Updates**: Polls `PROJECT_QUERY` every 2 seconds (fallback)
4. **State Updates**: React state updates trigger re-renders
5. **Progress Bars**: CSS transitions animate smoothly

### Bandwidth Optimization:
- **GraphQL Subscriptions**: Only sends changed data (not full page refresh)
- **Filtered Subscriptions**: Task updates filtered by project (reduces data)
- **Efficient Polling**: Only polls when project selected (2-second interval)
- **Selective Queries**: Client requests only needed fields

## Testing

✅ No linter errors  
⚠️ **Requires frontend rebuild** to take effect

## Expected Behavior

1. **On Page Load**:
   - Loads tenant's active projects
   - Auto-selects first project
   - Shows project-specific status

2. **Project Selection**:
   - Search bar filters projects
   - Clicking project updates all metrics
   - Progress bars show project-specific data

3. **Real-Time Updates**:
   - Progress bars update automatically (no refresh needed)
   - Task status updates appear in real-time
   - System metrics update every 5 seconds
   - Project data refreshes every 2 seconds

4. **No Project Selected**:
   - Shows aggregate data for all active projects
   - Displays total count and overall progress

## Related Features

- **GraphQL Subscriptions**: Real-time WebSocket updates
- **Project Execution**: Projects must be running to appear in selector
- **Tenant Scoping**: Only shows projects belonging to logged-in tenant
- **Bandwidth Efficient**: Uses GraphQL's selective querying and subscriptions

