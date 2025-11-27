# Active Projects Widget Fix

## Issue
The "Active Projects" widget was missing from the Admin Dashboard. The dashboard should display 5 stat cards, but only 4 were showing.

## Root Cause
The widget was never added to the dashboard metrics array, and the API endpoint was not returning projects data.

## Solution

### 1. Backend API Changes (`addon_portal/api/routers/admin_api.py`)
- Added projects counting logic:
  - `totalProjects`: Total number of projects in the system
  - `activeProjects`: Number of active projects (`is_active == True`)
  - `projects_trend`: Week-over-week trend calculation for projects
- Added projects data to the `/dashboard-stats` endpoint response:
  ```python
  "totalProjects": total_projects,
  "activeProjects": active_projects,
  "trends": {
    ...
    "projects": {
      "value": round(abs(projects_trend), 1),
      "direction": "up" if projects_trend >= 0 else "down"
    },
    ...
  }
  ```

### 2. Frontend Changes (`addon_portal/apps/admin-portal/src/pages/index.tsx`)
- Updated `DashboardStats` interface to include:
  - `activeProjects: number`
  - `totalProjects: number`
  - `projects: TrendMetric` in trends object
- Updated state initialization to include projects data from API
- Added "Active Projects" widget to metrics array:
  ```typescript
  {
    icon: '🚀',
    subtitle: `${stats.activeProjects} active`,
    title: 'Active Projects',
    trend: stats.trends.projects,
    value: stats.totalProjects.toLocaleString(),
  }
  ```
- Updated grid layout from `xl:grid-cols-4` to `xl:grid-cols-5` to accommodate 5 widgets
- Updated loading skeleton from 4 to 5 cards

## Result
The dashboard now displays widgets in a two-row layout:

**First Row (4 widgets):**
1. Activation Codes
2. Authorized Devices
3. **Active Projects** (NEW)
4. Tenants

**Second Row (1 widget, centered):**
5. Success Rate

This layout keeps the dashboard clean and unclustered while maintaining responsive design.

## Testing
1. Navigate to Admin Dashboard (`/`)
2. Verify 5 stat cards are displayed
3. Verify "Active Projects" widget shows:
   - Total projects count
   - Active projects count in subtitle
   - Week-over-week trend indicator
   - Correct icon (🚀)

## Files Changed
- `addon_portal/api/routers/admin_api.py`
- `addon_portal/apps/admin-portal/src/pages/index.tsx`

