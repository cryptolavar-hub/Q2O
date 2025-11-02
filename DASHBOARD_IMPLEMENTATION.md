# Real-time Progress Dashboard Implementation Plan
**Priority Feature #1**

## Architecture Overview

```
┌─────────────────┐
│  Dashboard UI   │  (Next.js + React + WebSocket Client)
│  (Port 3000)    │
└────────┬────────┘
         │ WebSocket / SSE
         │
┌────────▼────────┐
│  Dashboard API  │  (FastAPI + WebSocket)
│  (Port 8001)    │
└────────┬────────┘
         │
┌────────▼────────┐
│  Event Manager  │  (Publishes agent events)
└────────┬────────┘
         │
┌────────▼────────┐
│  Agent System   │  (Existing agents emit events)
└─────────────────┘
```

## Components to Build

### 1. Backend: Dashboard API Server (`api/dashboard/`)

#### Files to Create:
- `api/dashboard/main.py` - FastAPI server with WebSocket endpoints
- `api/dashboard/events.py` - Event manager for agent activity
- `api/dashboard/models.py` - Pydantic models for dashboard data
- `api/dashboard/store.py` - In-memory state store for dashboard data

#### Key Features:
- **WebSocket endpoint** for real-time updates
- **REST API endpoints** for initial data load
- **Event broadcasting** to connected clients
- **State management** for tasks, agents, metrics

### 2. Frontend: Dashboard UI (`web/dashboard/`)

#### Files to Create:
- `web/dashboard/pages/index.tsx` - Main dashboard page
- `web/dashboard/components/TaskList.tsx` - Task status list
- `web/dashboard/components/AgentActivity.tsx` - Agent activity feed
- `web/dashboard/components/MetricsPanel.tsx` - System metrics
- `web/dashboard/components/ProgressChart.tsx` - Progress visualization
- `web/dashboard/hooks/useWebSocket.ts` - WebSocket hook
- `web/dashboard/types/dashboard.ts` - TypeScript types

#### Key Features:
- **Real-time updates** via WebSocket
- **Task visualization** with status indicators
- **Agent activity timeline**
- **Progress charts** (bar charts, line graphs)
- **System health indicators**

### 3. Integration: Agent Event Emission

#### Modifications Needed:
- `agents/base_agent.py` - Emit events on task state changes
- `agents/orchestrator.py` - Emit orchestration events
- `main.py` - Initialize event manager and connect to dashboard

## Implementation Steps

### Step 1: Create Dashboard Backend (FastAPI + WebSocket)

```python
# api/dashboard/main.py structure
- WebSocket endpoint: /ws/dashboard
- REST endpoints: /api/dashboard/status, /api/dashboard/metrics
- Event broadcasting on agent activity
```

### Step 2: Create Event Manager

```python
# api/dashboard/events.py structure
- EventManager class (singleton)
- Methods: emit_task_update, emit_agent_activity, emit_metric_update
- WebSocket connection management
```

### Step 3: Modify Base Agent to Emit Events

```python
# agents/base_agent.py modifications
- Add event emission on task status changes
- Emit: task_started, task_completed, task_failed events
```

### Step 4: Create Dashboard Frontend

```typescript
# web/dashboard/ structure
- Next.js page with WebSocket connection
- Real-time components for tasks, agents, metrics
- Responsive design with Tailwind CSS
```

### Step 5: Add Metrics Calculation

```python
# api/dashboard/metrics.py
- Calculate: completion %, success rate, avg time
- Agent utilization metrics
- Task throughput metrics
```

## Data Models

### Task Status Model
```typescript
interface TaskStatus {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  agent_id: string;
  agent_type: string;
  progress: number; // 0-100
  started_at?: string;
  completed_at?: string;
  dependencies: string[];
}
```

### Agent Activity Model
```typescript
interface AgentActivity {
  agent_id: string;
  agent_type: string;
  status: 'idle' | 'active' | 'error';
  current_task?: string;
  tasks_completed: number;
  success_rate: number;
  last_activity: string;
}
```

### System Metrics Model
```typescript
interface SystemMetrics {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  in_progress_tasks: number;
  completion_percentage: number;
  average_task_time: number;
  active_agents: number;
  idle_agents: number;
}
```

## WebSocket Message Protocol

### Client → Server
```json
{
  "type": "subscribe",
  "channel": "tasks" | "agents" | "metrics" | "all"
}
```

### Server → Client
```json
{
  "type": "task_update",
  "data": {
    "task_id": "...",
    "status": "completed",
    "progress": 100
  },
  "timestamp": "2024-12-19T..."
}
```

## UI Layout Design

```
┌─────────────────────────────────────────────────────┐
│  Dashboard Header: Project Name, Status, Actions    │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌────────────────────────────┐  │
│  │   Metrics    │  │    Task List (Real-time)   │  │
│  │   Panel      │  │                            │  │
│  │  - Progress  │  │  [Task 1] ✓ Completed     │  │
│  │  - Success   │  │  [Task 2] ⏳ In Progress   │  │
│  │  - Active    │  │  [Task 3] ⏸ Pending       │  │
│  └──────────────┘  └────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │         Agent Activity Timeline               │  │
│  │  [CoderAgent] → Task ABC → Completed 2m ago │  │
│  │  [FrontendAgent] → Task XYZ → In Progress   │  │
│  └──────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │         Progress Chart (Line/Bar)             │  │
│  │         [Visualization of task progress]      │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Technology Stack

- **Backend**: FastAPI, WebSockets, Python
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Real-time**: WebSocket (native) or Server-Sent Events (SSE)
- **Charts**: Recharts or Chart.js
- **State**: React Context or Zustand for frontend state

## Next Steps

1. **Create dashboard backend structure**
2. **Implement WebSocket server**
3. **Modify agents to emit events**
4. **Create dashboard frontend**
5. **Add real-time visualizations**
6. **Test end-to-end flow**

---

**Ready to start implementation? Let me know and I'll begin building the dashboard!**

