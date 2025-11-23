/**
 * Status Page - Multi-Agent Dashboard View
 * 
 * Shows real-time agent activity, task timeline, and system metrics
 * Uses GraphQL queries and subscriptions for real-time updates
 * This is the same interface as the Multi-Agent Dashboard mockup
 */

import { useState, useEffect } from 'react';
import { useQuery, useSubscription } from 'urql';
import { SessionGuard } from '../components/SessionGuard';
import { Navigation } from '../components/Navigation';
import { Breadcrumb } from '../components/Breadcrumb';
import {
  DASHBOARD_STATS_QUERY,
  SYSTEM_METRICS_QUERY,
  AGENT_ACTIVITY_SUBSCRIPTION,
  TASK_UPDATES_SUBSCRIPTION,
  SYSTEM_METRICS_STREAM_SUBSCRIPTION,
  PROJECT_QUERY,
} from '../lib/graphql';
import { listProjects, type Project } from '../lib/projects';

  // Mock data structure (will be replaced with WebSocket/API integration)
interface DashboardState {
  project: {
    name: string;
    status: string;
    progress: number;
    estimatedTimeRemaining?: number;
  };
  agents: Array<{
    name: string;
    status: 'active' | 'idle' | 'busy' | 'error';
    currentTask?: string;
    tasksCompleted?: number;
  }>;
  tasks: Array<{
    id: string;
    title: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    agent?: string;
    progress?: number;
    createdAt?: string;
    startedAt?: string;
    completedAt?: string;
    durationSeconds?: number;
  }>;
  metrics: {
    cpu: number;
    memory: number;
    activeTasks: number;
    completedTasks: number;
    failedTasks: number;
    totalTasks: number;
    successRate: number;
    averageTaskTime: number;
  };
}

export default function StatusPage() {
  // Project selection state
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [availableProjects, setAvailableProjects] = useState<Project[]>([]);
  const [projectSearch, setProjectSearch] = useState('');
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Load tenant's active projects (execution_status = 'running')
  useEffect(() => {
    const loadProjects = async () => {
      try {
        setLoadingProjects(true);
        const response = await listProjects(1, 100);
        // Filter to only active/running projects
        const activeProjects = response.items.filter(
          p => p.execution_status === 'running' || p.status === 'active'
        );
        setAvailableProjects(activeProjects);
        
        // Auto-select first project if available and none selected
        if (activeProjects.length > 0 && !selectedProjectId) {
          setSelectedProjectId(activeProjects[0].id);
        }
      } catch (err) {
        console.error('Failed to load projects:', err);
      } finally {
        setLoadingProjects(false);
      }
    };
    
    loadProjects();
  }, []);

  // GraphQL Queries
  const [dashboardStatsResult] = useQuery({ query: DASHBOARD_STATS_QUERY });
  const [systemMetricsResult] = useQuery({ query: SYSTEM_METRICS_QUERY });
  const [projectResult, reexecuteProject] = useQuery({
    query: PROJECT_QUERY,
    variables: { id: selectedProjectId || '' },
    pause: !selectedProjectId, // Pause query if no project selected
    requestPolicy: 'cache-and-network', // Always fetch fresh data
  });

  // Get selected project data (declare BEFORE use in useEffect hooks)
  const selectedProject = projectResult.data?.project;
  const selectedProjectRest = availableProjects.find(p => p.id === selectedProjectId);

  // Poll project query every 5 seconds for real-time updates (if project selected)
  // Reduced from 2s to 5s to reduce database connection pressure
  useEffect(() => {
    if (!selectedProjectId) return;
    
    const interval = setInterval(() => {
      reexecuteProject({ requestPolicy: 'network-only' });
    }, 5000); // Poll every 5 seconds (reduced from 2s to reduce connection pool pressure)
    
    return () => clearInterval(interval);
  }, [selectedProjectId, reexecuteProject]);
  
  // GraphQL Subscriptions (filtered by selected project)
  const [agentActivityResult] = useSubscription({ query: AGENT_ACTIVITY_SUBSCRIPTION });
  const [taskUpdatesResult] = useSubscription({
    query: TASK_UPDATES_SUBSCRIPTION,
    variables: { projectId: selectedProjectId || null },
  });
  const [metricsStreamResult] = useSubscription({ 
    query: SYSTEM_METRICS_STREAM_SUBSCRIPTION,
    variables: { projectId: selectedProjectId || null },
  });

  // Combine data from queries and subscriptions
  const dashboardStats = dashboardStatsResult.data?.dashboardStats;
  const systemMetrics = metricsStreamResult.data?.systemMetricsStream || systemMetricsResult.data?.systemMetrics;
  const agentActivities = agentActivityResult.data?.agentActivity ? [agentActivityResult.data.agentActivity] : [];
  
  // Collect task updates from subscription (real-time)
  // Initialize with tasks from project query, then update from subscriptions
  const [taskUpdatesList, setTaskUpdatesList] = useState<any[]>([]);
  
  // Initialize tasks from project query when project loads
  useEffect(() => {
    if (selectedProject?.tasks && selectedProject.tasks.length > 0) {
      // Initialize with tasks from project query (chronological order)
      const projectTasks = selectedProject.tasks
        .map((task: any) => ({
          id: task.id,
          title: task.title || 'Unknown Task',
          status: task.status,
          agentType: task.agentType,
          agent: task.agent,
          createdAt: task.createdAt,
          startedAt: task.startedAt,
          completedAt: task.completedAt,
          durationSeconds: task.durationSeconds,
        }))
        .sort((a: any, b: any) => {
          // Sort by createdAt (oldest first) for chronological timeline
          const aTime = a.createdAt ? new Date(a.createdAt).getTime() : 0;
          const bTime = b.createdAt ? new Date(b.createdAt).getTime() : 0;
          return aTime - bTime;
        });
      setTaskUpdatesList(projectTasks);
    }
  }, [selectedProject?.tasks]);
  
  // Update tasks from subscription (real-time updates)
  useEffect(() => {
    if (taskUpdatesResult.data?.taskUpdates) {
      const update = taskUpdatesResult.data.taskUpdates;
      setTaskUpdatesList(prev => {
        // Update existing task or add new one
        const existingIndex = prev.findIndex(t => t.id === update.id);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = {
            ...updated[existingIndex],
            ...update,
            title: update.title || updated[existingIndex].title,
            status: update.status || updated[existingIndex].status,
            agentType: update.agentType || updated[existingIndex].agentType,
            agent: update.agent || updated[existingIndex].agent,
          };
          return updated;
        }
        // Add new task
        return [...prev, {
          id: update.id,
          title: update.title || 'Unknown Task',
          status: update.status,
          agentType: update.agentType,
          agent: update.agent,
        }].sort((a: any, b: any) => {
          const aTime = a.createdAt ? new Date(a.createdAt).getTime() : 0;
          const bTime = b.createdAt ? new Date(b.createdAt).getTime() : 0;
          return aTime - bTime;
        });
      });
    }
  }, [taskUpdatesResult.data]);

  // Collect metrics updates from subscription (real-time)
  const [currentMetrics, setCurrentMetrics] = useState(systemMetrics);
  useEffect(() => {
    if (metricsStreamResult.data?.systemMetricsStream) {
      setCurrentMetrics(metricsStreamResult.data.systemMetricsStream);
    }
  }, [metricsStreamResult.data]);

  // Collect project updates from GraphQL query (real-time via polling or subscription)
  const [currentProject, setCurrentProject] = useState(selectedProject);
  useEffect(() => {
    if (projectResult.data?.project) {
      setCurrentProject(projectResult.data.project);
    }
  }, [projectResult.data]);

  // Calculate real-time progress from task updates
  const calculateProgress = (): number => {
    if (currentProject) {
      return Math.round(currentProject.completionPercentage || 0);
    }
    if (taskUpdatesList.length > 0) {
      const completed = taskUpdatesList.filter(t => t.status === 'COMPLETED').length;
      const total = taskUpdatesList.length;
      return total > 0 ? Math.round((completed / total) * 100) : 0;
    }
    return dashboardStats?.totalTasks 
      ? Math.round((dashboardStats.completedTasksToday / dashboardStats.totalTasks) * 100)
      : 0;
  };

  const realTimeProgress = calculateProgress();

  const loading = dashboardStatsResult.fetching || systemMetricsResult.fetching;
  const connected = !dashboardStatsResult.error && !systemMetricsResult.error;

  // Filter projects by search
  const filteredProjects = availableProjects.filter(p =>
    p.name.toLowerCase().includes(projectSearch.toLowerCase()) ||
    p.id.toLowerCase().includes(projectSearch.toLowerCase())
  );

  // Get agents from project query (real data from database)
  const projectAgents = selectedProject?.agents || [];
  
  // Transform GraphQL data to dashboard state
  const dashboardState: DashboardState = {
    project: {
      name: selectedProject
        ? selectedProject.name
        : selectedProjectRest
        ? selectedProjectRest.name
        : availableProjects.length > 0
        ? `${availableProjects.length} Active Project${availableProjects.length > 1 ? 's' : ''}`
        : 'No active projects',
      status: selectedProject?.status === 'IN_PROGRESS' || selectedProjectRest?.execution_status === 'running'
        ? 'Active'
        : selectedProject?.status === 'COMPLETED' || selectedProjectRest?.execution_status === 'completed'
        ? 'Completed'
        : 'Initializing',
      progress: realTimeProgress,
      estimatedTimeRemaining: selectedProject?.estimatedTimeRemainingSeconds || systemMetrics?.averageTaskDurationSeconds || 0,
    },
    agents: projectAgents.length > 0
      ? projectAgents.map((agent: any) => ({
          name: agent.name || agent.agentType || 'Unknown Agent',
          status: (agent.status === 'active' ? 'active' : agent.status === 'idle' ? 'idle' : 'busy'),
          currentTask: agent.currentTaskId || undefined,
          tasksCompleted: agent.tasksCompleted || 0,
        }))
      : agentActivities.map((activity: any) => ({
          name: activity.agentId || 'Unknown Agent',
          status: 'active' as const,
          currentTask: activity.taskId || undefined,
          tasksCompleted: 0,
        })),
    tasks: taskUpdatesList.map((task: any) => ({
      id: task.id,
      title: task.title || 'Unknown Task',
      status: task.status?.toLowerCase() || 'pending',
      agent: task.agent?.name || task.agentType || undefined,
      progress: task.progress || 0,
      createdAt: task.createdAt,
      startedAt: task.startedAt,
      completedAt: task.completedAt,
      durationSeconds: task.durationSeconds,
    })),
    metrics: {
      cpu: currentMetrics?.cpuUsagePercent || systemMetrics?.cpuUsagePercent || 0,
      memory: currentMetrics?.memoryUsagePercent || systemMetrics?.memoryUsagePercent || 0,
      // Prioritize project-specific data, then metrics stream, then dashboard stats
      activeTasks: currentProject?.totalTasks 
        ? (currentProject.totalTasks - currentProject.completedTasks - currentProject.failedTasks)
        : (currentMetrics?.activeTasks || systemMetrics?.activeTasks || dashboardStats?.activeTasks || 0),
      completedTasks: currentProject?.completedTasks !== undefined
        ? currentProject.completedTasks
        : (currentMetrics?.tasksCompletedToday || systemMetrics?.tasksCompletedToday || dashboardStats?.completedTasksToday || 0),
      failedTasks: currentProject?.failedTasks !== undefined
        ? currentProject.failedTasks
        : (currentMetrics?.tasksFailedToday || systemMetrics?.tasksFailedToday || 0),
      totalTasks: currentProject?.totalTasks !== undefined
        ? currentProject.totalTasks
        : (dashboardStats?.totalTasks || 0),
      successRate: currentProject?.successRate !== undefined
        ? currentProject.successRate
        : (dashboardStats?.averageSuccessRate || currentMetrics?.systemHealthScore || systemMetrics?.systemHealthScore || 0),
      averageTaskTime: currentMetrics?.averageTaskDurationSeconds || systemMetrics?.averageTaskDurationSeconds || 0,
    },
  };

  // Show loading state only on initial load
  if (loading && !dashboardStats && !systemMetrics) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-white text-xl text-center">Loading dashboard...</div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  const { project, agents, tasks, metrics } = dashboardState;
  const activeAgents = agents.filter(a => a.status === 'active' || a.status === 'busy').length;
  const idleAgents = agents.filter(a => a.status === 'idle').length;

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <SessionGuard>
      <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <Navigation />
        
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumb items={[{ label: 'Status' }]} />

          {/* Project Selector */}
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Select Active Project
            </label>
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Search projects..."
                  value={projectSearch}
                  onChange={(e) => setProjectSearch(e.target.value)}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                />
                {projectSearch && filteredProjects.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border-2 border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {filteredProjects.map((project) => (
                      <button
                        key={project.id}
                        onClick={() => {
                          setSelectedProjectId(project.id);
                          setProjectSearch('');
                        }}
                        className={`w-full text-left px-4 py-2 hover:bg-purple-50 transition-colors ${
                          selectedProjectId === project.id ? 'bg-purple-100' : ''
                        }`}
                      >
                        <div className="font-semibold text-gray-900">{project.name}</div>
                        <div className="text-xs text-gray-500">{project.id}</div>
                        {project.execution_status && (
                          <div className="text-xs text-blue-600 mt-1">
                            Status: {project.execution_status}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {selectedProjectId && (
                <button
                  onClick={() => setSelectedProjectId(null)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            {selectedProjectId && (
              <div className="mt-3 text-sm text-gray-600">
                Selected: <span className="font-semibold">{selectedProjectRest?.name || selectedProjectId}</span>
              </div>
            )}
            {!loadingProjects && availableProjects.length === 0 && (
              <div className="mt-3 text-sm text-yellow-600">
                No active projects found. Run a project from the Projects page to see its status here.
              </div>
            )}
          </div>

          {/* Project Overview Card */}
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Status: <span className="font-semibold text-blue-600">{project.status}</span>
                </p>
              </div>
              {project.estimatedTimeRemaining !== undefined && project.estimatedTimeRemaining > 0 && (
                <div className="text-right">
                  <p className="text-sm text-gray-600">Est. Time Remaining</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatTime(project.estimatedTimeRemaining)}
                  </p>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            <div className="mb-2">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Overall Progress</span>
                <span className="text-lg font-bold bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 bg-clip-text text-transparent">
                  {project.progress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
                <div
                  className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 shadow-md transition-all duration-500 ease-out"
                  style={{ width: `${project.progress}%` }}
                >
                  {project.progress > 10 && (
                    <div className="h-full flex items-center justify-end pr-2">
                      <span className="text-xs font-bold text-white drop-shadow">
                        {project.progress}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl">🤖</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Active Agents</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{activeAgents}</p>
              <p className="text-sm text-gray-500">{idleAgents} idle</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl">✅</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Completed Tasks</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{metrics.completedTasks}</p>
              <p className="text-sm text-gray-500">{metrics.totalTasks} total</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl">📊</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Success Rate</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{Math.round(metrics.successRate)}%</p>
              <p className="text-sm text-gray-500">All time</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl">⚡</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Active Tasks</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{metrics.activeTasks}</p>
              <p className="text-sm text-gray-500">In progress</p>
            </div>
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
                      <div key={agent.name} className="border rounded-lg p-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-semibold text-gray-800">{agent.name}</div>
                            {agent.currentTask && (
                              <div className="text-sm text-blue-600 mt-1">
                                Current: {agent.currentTask}
                              </div>
                            )}
                          </div>
                          <span className={`px-3 py-1 rounded text-sm font-semibold ${
                            agent.status === 'active' || agent.status === 'busy' 
                              ? 'bg-green-100 text-green-800'
                              : agent.status === 'error'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {agent.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Task Timeline */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h2 className="text-xl font-bold text-gray-900 mb-4">📋 Task Timeline</h2>
                
                {tasks.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">📋</div>
                    <p className="text-gray-500">
                      {connected ? 'No tasks yet...' : 'Waiting for tasks...'}
                    </p>
                    {selectedProjectId && (
                      <p className="text-sm text-gray-400 mt-2">
                        Tasks will appear here as agents start working on the project
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tasks.map((task) => {
                      // Format timestamps for display
                      const formatTime = (timestamp?: string) => {
                        if (!timestamp) return '';
                        try {
                          const date = new Date(timestamp);
                          return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                        } catch {
                          return '';
                        }
                      };
                      
                      return (
                        <div key={task.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="font-semibold text-gray-800">{task.title}</div>
                              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 flex-wrap">
                                {task.agent && (
                                  <span>Agent: <span className="font-medium">{task.agent}</span></span>
                                )}
                                {task.createdAt && (
                                  <span>Created: {formatTime(task.createdAt)}</span>
                                )}
                                {task.startedAt && (
                                  <span>Started: {formatTime(task.startedAt)}</span>
                                )}
                                {task.completedAt && (
                                  <span>Completed: {formatTime(task.completedAt)}</span>
                                )}
                                {task.durationSeconds && task.durationSeconds > 0 && (
                                  <span>Duration: {Math.round(task.durationSeconds)}s</span>
                                )}
                              </div>
                              {task.progress !== undefined && task.progress > 0 && (
                                <div className="mt-2">
                                  <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                      className="bg-purple-500 h-2 rounded-full transition-all duration-500 ease-out"
                                      style={{ width: `${Math.min(100, task.progress)}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                            <span className={`px-3 py-1 rounded text-sm font-semibold ml-4 whitespace-nowrap ${
                              task.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : task.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : task.status === 'in_progress'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {task.status.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* System Metrics Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h2 className="text-xl font-bold text-gray-900 mb-4">📊 System Metrics</h2>
                
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Completion Rate</span>
                      <span className="text-sm font-bold text-green-600">
                        {(() => {
                          // Use project completion percentage if available, otherwise calculate from metrics
                          const completion = selectedProject?.completionPercentage !== undefined
                            ? Math.round(selectedProject.completionPercentage)
                            : (metrics.totalTasks > 0 ? Math.min(100, Math.round((metrics.completedTasks / metrics.totalTasks) * 100)) : 0);
                          return `${Math.min(100, Math.max(0, completion))}%`;
                        })()}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ 
                          width: `${(() => {
                            const completion = selectedProject?.completionPercentage !== undefined
                              ? Math.round(selectedProject.completionPercentage)
                              : (metrics.totalTasks > 0 ? Math.min(100, Math.round((metrics.completedTasks / metrics.totalTasks) * 100)) : 0);
                            return Math.min(100, Math.max(0, completion));
                          })()}%` 
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Success Rate</span>
                      <span className="text-sm font-bold text-blue-600">{Math.round(metrics.successRate)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${Math.round(metrics.successRate)}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">CPU Usage</span>
                      <span className="text-sm font-bold text-purple-600">{Math.round(metrics.cpu)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${Math.round(metrics.cpu)}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Memory Usage</span>
                      <span className="text-sm font-bold text-orange-600">{Math.round(metrics.memory)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-orange-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${Math.round(metrics.memory)}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold text-green-600">{metrics.activeTasks}</div>
                        <div className="text-xs text-gray-500 mt-1">Active</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-blue-600">{metrics.completedTasks}</div>
                        <div className="text-xs text-gray-500 mt-1">Completed</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-red-600">{metrics.failedTasks}</div>
                        <div className="text-xs text-gray-500 mt-1">Failed</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </SessionGuard>
  );
}

