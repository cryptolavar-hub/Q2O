"""
Event Manager for broadcasting agent activity to dashboard clients.
Provides real-time event emission and WebSocket connection management.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventManager:
    """Manages events and broadcasts them to connected dashboard clients."""
    
    def __init__(self):
        self.connections: Set = set()  # WebSocket connections
        self.event_history: List[Dict[str, Any]] = []  # Recent events (last 1000)
        self.max_history = 1000
        
        # Aggregated state
        self.task_state: Dict[str, Dict[str, Any]] = {}
        self.agent_state: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, Any] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "in_progress_tasks": 0,
            "pending_tasks": 0,
            "completion_percentage": 0.0,
            "active_agents": 0,
            "idle_agents": 0,
            "average_task_time": 0.0,
        }
    
    def add_connection(self, websocket):
        """Add a WebSocket connection to receive events."""
        self.connections.add(websocket)
        logger.info(f"Dashboard client connected. Total connections: {len(self.connections)}")
    
    def remove_connection(self, websocket):
        """Remove a WebSocket connection."""
        self.connections.discard(websocket)
        logger.info(f"Dashboard client disconnected. Total connections: {len(self.connections)}")
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event (task_update, agent_activity, metric_update, etc.)
            data: Event data
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Broadcast to all connected clients
        message = json.dumps(event)
        disconnected = set()
        
        for connection in self.connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.remove_connection(conn)
    
    # Event emission methods
    
    async def emit_task_update(self, task_id: str, status: str, **kwargs):
        """Emit a task status update."""
        task_data = {
            "task_id": task_id,
            "status": status,
            **kwargs
        }
        
        # Update internal state
        self.task_state[task_id] = task_data
        
        await self.broadcast("task_update", task_data)
        await self._update_metrics()
    
    async def emit_agent_activity(self, agent_id: str, agent_type: str, activity: str, **kwargs):
        """Emit agent activity."""
        activity_data = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "activity": activity,
            **kwargs
        }
        
        # Update internal state
        self.agent_state[agent_id] = activity_data
        
        await self.broadcast("agent_activity", activity_data)
    
    async def emit_metric_update(self, metrics: Dict[str, Any]):
        """Emit system metrics update."""
        self.system_metrics.update(metrics)
        await self.broadcast("metric_update", self.system_metrics)
    
    async def emit_project_start(self, project_description: str, objectives: List[str]):
        """Emit project start event."""
        await self.broadcast("project_start", {
            "project_description": project_description,
            "objectives": objectives,
            "started_at": datetime.now().isoformat()
        })
    
    async def emit_project_complete(self, results: Dict[str, Any]):
        """Emit project completion event."""
        await self.broadcast("project_complete", {
            **results,
            "completed_at": datetime.now().isoformat()
        })
    
    async def _update_metrics(self):
        """Update aggregated system metrics."""
        # Calculate metrics from task state
        total = len(self.task_state)
        completed = sum(1 for t in self.task_state.values() if t.get("status") == "completed")
        failed = sum(1 for t in self.task_state.values() if t.get("status") == "failed")
        in_progress = sum(1 for t in self.task_state.values() if t.get("status") == "in_progress")
        pending = sum(1 for t in self.task_state.values() if t.get("status") == "pending")
        
        metrics = {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "in_progress_tasks": in_progress,
            "pending_tasks": pending,
            "completion_percentage": (completed / total * 100) if total > 0 else 0.0,
            "active_agents": sum(1 for a in self.agent_state.values() if a.get("status") == "active"),
            "idle_agents": sum(1 for a in self.agent_state.values() if a.get("status") == "idle"),
        }
        
        await self.emit_metric_update(metrics)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current dashboard state for initial load."""
        return {
            "tasks": self.task_state,
            "agents": self.agent_state,
            "metrics": self.system_metrics,
            "recent_events": self.event_history[-50:]  # Last 50 events
        }


# Singleton instance
_event_manager: Optional[EventManager] = None


def get_event_manager() -> EventManager:
    """Get the singleton EventManager instance."""
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager

