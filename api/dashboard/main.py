"""
Dashboard API Server - FastAPI with WebSocket support for real-time updates.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import logging
import json

from api.dashboard.events import get_event_manager
from api.dashboard.models import DashboardStateModel, SystemMetricsModel
from api.dashboard.metrics import get_metrics_calculator

logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Dashboard API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get event manager singleton
event_manager = get_event_manager()

# Get metrics calculator
metrics_calculator = get_metrics_calculator()


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Clients connect to receive real-time events:
    - task_update: Task status changes
    - agent_activity: Agent activity updates
    - metric_update: System metrics updates
    """
    await websocket.accept()
    event_manager.add_connection(websocket)
    
    try:
        # Send current state on connection
        current_state = event_manager.get_current_state()
        await websocket.send_json({
            "type": "initial_state",
            "data": current_state
        })
        
        # Keep connection alive and handle client messages
        while True:
            # Client can send subscription requests
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") == "subscribe":
                    # Client can subscribe to specific channels
                    channels = data.get("channels", ["all"])
                    logger.info(f"Client subscribed to channels: {channels}")
                    # Future: implement channel-specific filtering
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        event_manager.remove_connection(websocket)


@app.get("/api/dashboard/status", response_model=DashboardStateModel)
async def get_dashboard_status():
    """Get current dashboard state (REST endpoint for initial load)."""
    state = event_manager.get_current_state()
    return DashboardStateModel(**state)


@app.get("/api/dashboard/metrics", response_model=SystemMetricsModel)
async def get_metrics():
    """Get current system metrics."""
    return SystemMetricsModel(**event_manager.system_metrics)


@app.get("/api/dashboard/static-analysis")
async def get_static_analysis_metrics():
    """Get static analysis metrics (security + quality)."""
    return metrics_calculator.get_aggregated_metrics()


@app.post("/api/dashboard/analyze-file")
async def analyze_file(file_path: str):
    """Trigger static analysis for a specific file."""
    security_metrics = metrics_calculator.calculate_security_metrics(file_path)
    quality_metrics = metrics_calculator.calculate_quality_metrics(file_path)
    
    # Emit to dashboard
    await event_manager.broadcast("static_analysis_update", {
        "file_path": file_path,
        "security": security_metrics,
        "quality": quality_metrics
    })
    
    return {
        "file_path": file_path,
        "security": security_metrics,
        "quality": quality_metrics
    }


@app.get("/api/dashboard/tasks")
async def get_tasks():
    """Get all tasks with their current status."""
    return event_manager.task_state


@app.get("/api/dashboard/agents")
async def get_agents():
    """Get all agents with their current activity."""
    return event_manager.agent_state


@app.get("/api/dashboard/events")
async def get_recent_events(limit: int = 50):
    """Get recent events (for history/replay)."""
    return event_manager.event_history[-limit:]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "connections": len(event_manager.connections),
        "tasks_tracked": len(event_manager.task_state),
        "agents_tracked": len(event_manager.agent_state)
    }


# Singleton instance
_dashboard_server: FastAPI = None


def get_dashboard_server() -> FastAPI:
    """Get the dashboard server instance."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

