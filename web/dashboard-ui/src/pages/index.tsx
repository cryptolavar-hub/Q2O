import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Header } from '../components/Header';
import { ProjectOverview } from '../components/ProjectOverview';
import { StatCard } from '../components/StatCard';
import { AgentCard } from '../components/AgentCard';
import { TaskCard } from '../components/TaskCard';
import { MetricsPanel } from '../components/MetricsPanel';

export default function Dashboard() {
  const { state, connected, error } = useWebSocket();

  // Mock data for initial display (will be replaced by WebSocket data)
  const mockState = {
    project: {
      name: 'Waiting for connection...',
      status: 'Initializing',
      progress: 0,
      estimatedTimeRemaining: 0,
    },
    agents: [],
    tasks: [],
    metrics: {
      cpu: 0,
      memory: 0,
      activeTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      totalTasks: 0,
      successRate: 0,
      averageTaskTime: 0,
    },
  };

  const displayState = state || mockState;
  const agents = displayState.agents || [];
  const activeAgents = agents.filter(a => a.status === 'active' || a.status === 'busy').length;
  const idleAgents = agents.filter(a => a.status === 'idle').length;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        connected={connected} 
        error={error} 
        projectName={displayState.project.name}
      />

      <main className="container mx-auto px-6 py-8">
        {/* Project Overview */}
        <ProjectOverview project={displayState.project} />

        {/* Stats Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Active Agents"
            value={activeAgents}
            subtitle={`${idleAgents} idle`}
            icon="🤖"
            trend={activeAgents > 0 ? { value: 12, direction: 'up' } : undefined}
          />
          <StatCard
            title="Completed Tasks"
            value={displayState.metrics.completedTasks}
            subtitle={`${displayState.metrics.totalTasks} total`}
            icon="✅"
          />
          <StatCard
            title="Success Rate"
            value={`${displayState.metrics.successRate}%`}
            subtitle="All time"
            icon="📊"
          />
          <StatCard
            title="Active Tasks"
            value={displayState.metrics.activeTasks}
            subtitle="In progress"
            icon="⚡"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Agent Activity Feed */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                👥 Agent Activity
                {activeAgents > 0 && (
                  <span className="text-sm font-normal text-gray-500">
                    ({activeAgents} active)
                  </span>
                )}
              </h2>
              
              {agents.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🤖</div>
                  <p className="text-gray-500">
                    {connected ? 'No agents active yet...' : 'Connecting to dashboard...'}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {agents.map((agent) => (
                    <AgentCard key={agent.name} agent={agent} />
                  ))}
                </div>
              )}
            </div>

            {/* Task Timeline */}
            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <h2 className="text-xl font-bold text-gray-900 mb-4">📋 Task Timeline</h2>
              
              {(displayState.tasks || []).length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📋</div>
                  <p className="text-gray-500">
                    {connected ? 'No tasks yet...' : 'Waiting for tasks...'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {(displayState.tasks || []).map((task) => (
                    <TaskCard key={task.id} task={task} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* System Metrics Sidebar */}
          <div className="lg:col-span-1">
            <MetricsPanel metrics={displayState.metrics} />
          </div>
        </div>

        {/* Connection Error */}
        {error && !connected && (
          <div className="fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg">
            <p className="font-semibold">⚠️ Connection Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm pb-6">
          <p>Quick2Odoo Multi-Agent Dashboard • Real-time Monitoring</p>
          <p className="text-xs mt-1">Powered by agents that build everything</p>
        </footer>
      </main>
    </div>
  );
}

