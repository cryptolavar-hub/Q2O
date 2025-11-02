# Dashboard Setup and Usage Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Dashboard Server
```bash
# Option 1: Run directly
python -m api.dashboard.main

# Option 2: Use uvicorn
uvicorn api.dashboard.main:app --host 0.0.0.0 --port 8001 --reload

# Dashboard API will be available at:
# - WebSocket: ws://localhost:8001/ws/dashboard
# - REST API: http://localhost:8001/api/dashboard/status
```

### 3. Access Dashboard

#### Option A: Using Next.js Frontend
```bash
cd web
npm install  # or pnpm install
npm run dev
# Open http://localhost:3000/dashboard
```

#### Option B: Using Browser Console (Quick Test)
```javascript
// Open browser console at http://localhost:8001
const ws = new WebSocket('ws://localhost:8001/ws/dashboard');
ws.onmessage = (e) => console.log('Dashboard event:', JSON.parse(e.data));
```

### 4. Run Your Project
```bash
# In another terminal
python main.py --project "My Project" --objective "Feature 1"
# Watch dashboard update in real-time!
```

## Dashboard Features

### Real-time Updates
- **Task Status**: See tasks change from pending → in_progress → completed/failed
- **Agent Activity**: Monitor which agents are working on what
- **Metrics**: View completion percentage, success rates, active agents

### WebSocket Events
The dashboard receives these event types:
- `task_update` - Task status changed
- `agent_activity` - Agent started/completed/failed a task
- `metric_update` - System metrics updated
- `project_start` - Project execution started
- `project_complete` - Project execution completed

## API Endpoints

### WebSocket
- `ws://localhost:8001/ws/dashboard` - Real-time event stream

### REST API
- `GET /api/dashboard/status` - Get current dashboard state
- `GET /api/dashboard/metrics` - Get system metrics
- `GET /api/dashboard/tasks` - Get all tasks
- `GET /api/dashboard/agents` - Get all agents
- `GET /api/dashboard/events?limit=50` - Get recent events
- `GET /health` - Health check

## Troubleshooting

### Dashboard Not Updating?
1. Check dashboard server is running: `curl http://localhost:8001/health`
2. Check WebSocket connection in browser console
3. Verify agents are emitting events (check logs)

### WebSocket Connection Failed?
- Ensure dashboard server is running on port 8001
- Check firewall settings
- Verify CORS is configured correctly

### Events Not Appearing?
- Check agent logs for errors
- Verify `api.dashboard.events` module is importable
- Check that EventManager is initialized

## Next Steps

Once dashboard is working:
1. Add visual enhancements (charts, graphs)
2. Implement task filtering
3. Add historical metrics
4. Create export functionality

