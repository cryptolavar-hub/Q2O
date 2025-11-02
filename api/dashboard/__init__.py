"""
Dashboard API for Real-time Progress Monitoring.
Provides WebSocket and REST endpoints for dashboard data.
"""

from api.dashboard.main import DashboardServer, get_dashboard_server
from api.dashboard.events import EventManager, get_event_manager

__all__ = [
    'DashboardServer',
    'get_dashboard_server',
    'EventManager',
    'get_event_manager'
]

