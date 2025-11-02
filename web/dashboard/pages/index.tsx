/**
 * Real-time Progress Dashboard
 * Main dashboard page with WebSocket connection for real-time updates
 */

import { useState, useEffect, useRef } from 'react';
import { NextPage } from 'next';

interface TaskStatus {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'blocked';
  agent_id?: string;
  agent_type?: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  dependencies: string[];
}

interface AgentActivity {
  agent_id: string;
  agent_type: string;
  status: 'idle' | 'active' | 'error';
  current_task?: string;
  tasks_completed: number;
  tasks_failed: number;
  success_rate: number;
  last_activity?: string;
}

interface SystemMetrics {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  in_progress_tasks: number;
  pending_tasks: number;
  completion_percentage: number;
  active_agents: number;
  idle_agents: number;
  average_task_time: number;
}

interface DashboardState {
  tasks: Record<string, TaskStatus>;
  agents: Record<string, AgentActivity>;
  metrics: SystemMetrics;
}

const DashboardPage: NextPage = () => {
  const [dashboardState, setDashboardState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const wsUrl = process.env.NEXT_PUBLIC_DASHBOARD_WS_URL || 'ws://localhost:8001/ws/dashboard';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Dashboard WebSocket connected');
      setConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'initial_state') {
          setDashboardState(message.data);
        } else if (message.type === 'task_update') {
          setDashboardState(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              tasks: {
                ...prev.tasks,
                [message.data.task_id]: message.data
              }
            };
          });
        } else if (message.type === 'agent_activity') {
          setDashboardState(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              agents: {
                ...prev.agents,
                [message.data.agent_id]: message.data
              }
            };
          });
        } else if (message.type === 'metric_update') {
          setDashboardState(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              metrics: message.data
            };
          });
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setError('Failed to connect to dashboard server');
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('Dashboard WebSocket disconnected');
      setConnected(false);
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          window.location.reload();
        }
      }, 3000);
    };

    wsRef.current = ws;

    // Initial load from REST API as fallback
    fetch('http://localhost:8001/api/dashboard/status')
      .then(res => res.json())
      .then(data => setDashboardState(data))
      .catch(err => console.error('Failed to load initial state:', err));

    return () => {
      ws.close();
    };
  }, []);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'in_progress': return 'bg-blue-500';
      case 'blocked': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed': return '✓';
      case 'failed': return '✗';
      case 'in_progress': return '→';
      case 'blocked': return '⊘';
      default: return '○';
    }
  };

  if (!dashboardState) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const { tasks, agents, metrics } = dashboardState;

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Multi-Agent Development Dashboard</h1>
            <p className="text-gray-600 mt-2">Real-time progress monitoring</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`px-4 py-2 rounded-full ${connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {connected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-1">Completion</div>
          <div className="text-3xl font-bold text-blue-600">{metrics.completion_percentage.toFixed(1)}%</div>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${metrics.completion_percentage}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-1">Total Tasks</div>
          <div className="text-3xl font-bold text-gray-800">{metrics.total_tasks}</div>
          <div className="text-sm text-gray-600 mt-2">
            {metrics.completed_tasks} completed, {metrics.in_progress_tasks} in progress
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-1">Active Agents</div>
          <div className="text-3xl font-bold text-green-600">{metrics.active_agents}</div>
          <div className="text-sm text-gray-600 mt-2">
            {metrics.idle_agents} idle
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-1">Success Rate</div>
          <div className="text-3xl font-bold text-purple-600">
            {metrics.total_tasks > 0 
              ? ((metrics.completed_tasks / (metrics.completed_tasks + metrics.failed_tasks)) * 100).toFixed(1)
              : '0'}%
          </div>
          <div className="text-sm text-gray-600 mt-2">
            {metrics.failed_tasks} failed
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Tasks</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {Object.values(tasks).map((task) => (
              <div key={task.id} className="border-l-4 pl-4 py-2" style={{ borderColor: getStatusColor(task.status).replace('bg-', '#').slice(0, -3) }}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getStatusIcon(task.status)}</span>
                      <span className="font-semibold text-gray-800">{task.title}</span>
                    </div>
                    {task.agent_type && (
                      <div className="text-sm text-gray-600 mt-1">
                        {task.agent_type} • {task.agent_id}
                      </div>
                    )}
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div 
                          className={`${getStatusColor(task.status)} h-1.5 rounded-full transition-all duration-300`}
                          style={{ width: `${task.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(task.status)} text-white`}>
                    {task.status}
                  </span>
                </div>
              </div>
            ))}
            {Object.keys(tasks).length === 0 && (
              <div className="text-center text-gray-500 py-8">No tasks yet</div>
            )}
          </div>
        </div>

        {/* Agent Activity */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Agent Activity</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {Object.values(agents).map((agent) => (
              <div key={agent.agent_id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800">{agent.agent_id}</div>
                    <div className="text-sm text-gray-600 mt-1">{agent.agent_type}</div>
                    <div className="flex items-center space-x-4 mt-2 text-sm">
                      <span>Completed: {agent.tasks_completed}</span>
                      <span>Failed: {agent.tasks_failed}</span>
                      <span>Success: {agent.success_rate.toFixed(1)}%</span>
                    </div>
                    {agent.current_task && (
                      <div className="text-sm text-blue-600 mt-2">
                        Current: {agent.current_task}
                      </div>
                    )}
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    agent.status === 'active' ? 'bg-green-100 text-green-800' :
                    agent.status === 'error' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {agent.status}
                  </span>
                </div>
              </div>
            ))}
            {Object.keys(agents).length === 0 && (
              <div className="text-center text-gray-500 py-8">No agent activity yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;

