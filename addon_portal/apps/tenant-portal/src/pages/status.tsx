/**
 * Status Page - Multi-Agent Dashboard View
 * 
 * Shows real-time agent activity, task timeline, and system metrics
 * Uses GraphQL queries and subscriptions for real-time updates
 * This is the same interface as the Multi-Agent Dashboard mockup
 */

import { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { useQuery, useSubscription } from 'urql';
import { SessionGuard } from '../components/SessionGuard';
import { Navigation } from '../components/Navigation';
import { Breadcrumb } from '../components/Breadcrumb';
import {
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
  // Scroll position preservation (prevents scroll-to-top on re-renders)
  const scrollPositionRef = useRef<number>(0);
  const shouldRestoreScrollRef = useRef<boolean>(false);
  
  // QA_Engineer: Save scroll position continuously (before any potential re-render)
  useEffect(() => {
    const handleScroll = () => {
      scrollPositionRef.current = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
    };
    
    // QA_Engineer: Store handler reference for proper cleanup matching addEventListener options
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  // Restore scroll position after re-renders (only if user was scrolled down)
  useLayoutEffect(() => {
    if (shouldRestoreScrollRef.current && scrollPositionRef.current > 0) {
      // Use scrollTo with instant behavior to avoid smooth scroll animation
      window.scrollTo(0, scrollPositionRef.current);
      shouldRestoreScrollRef.current = false;
    }
  });
  
  // Project selection state
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [availableProjects, setAvailableProjects] = useState<Project[]>([]);
  const [projectSearch, setProjectSearch] = useState('');
  const [loadingProjects, setLoadingProjects] = useState(true);

  // QA_Engineer: Load tenant's active projects (execution_status = 'running')
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
        
        // QA_Engineer: Auto-select first project if available and none selected
        // Only auto-select if no project is selected AND projects are available
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
    // QA_Engineer: Include selectedProjectId in dependencies to react to changes
  }, [selectedProjectId]);

  // GraphQL Queries - ONLY project-specific data
  // Removed DASHBOARD_STATS_QUERY and SYSTEM_METRICS_QUERY (they return global stats)
  const [projectResult, reexecuteProject] = useQuery({
    query: PROJECT_QUERY,
    variables: { id: selectedProjectId || '' },
    pause: !selectedProjectId, // Pause query if no project selected
    requestPolicy: 'cache-and-network', // Always fetch fresh data
  });

  // Poll project query every 2 seconds for real-time updates (if project selected)
  useEffect(() => {
    if (!selectedProjectId) return;
    
    const interval = setInterval(() => {
      // Mark that we should restore scroll position after this update
      shouldRestoreScrollRef.current = true;
      // Re-execute query (scroll will be restored by useLayoutEffect)
      reexecuteProject({ requestPolicy: 'network-only' });
    }, 2000); // Poll every 2 seconds
    
    return () => clearInterval(interval);
  }, [selectedProjectId, reexecuteProject]);
  
  // QA_Engineer: GraphQL Subscriptions (filtered by selected project)
  // QA_Engineer: Filter agent activity by selected project for consistency
  const [agentActivityResult] = useSubscription({ 
    query: AGENT_ACTIVITY_SUBSCRIPTION,
    variables: { projectId: selectedProjectId || null },
    pause: !selectedProjectId, // Pause if no project selected
  });
  const [taskUpdatesResult] = useSubscription({
    query: TASK_UPDATES_SUBSCRIPTION,
    variables: { projectId: selectedProjectId || null },
  });
  const [metricsStreamResult] = useSubscription({ 
    query: SYSTEM_METRICS_STREAM_SUBSCRIPTION,
    variables: { projectId: selectedProjectId || null },
  });

  // QA_Engineer: Handle subscription errors for better debugging and user feedback
  useEffect(() => {
    if (agentActivityResult.error) {
      console.error('QA_Engineer: Agent activity subscription error:', agentActivityResult.error);
    }
  }, [agentActivityResult.error]);

  useEffect(() => {
    if (taskUpdatesResult.error) {
      console.error('QA_Engineer: Task updates subscription error:', taskUpdatesResult.error);
    }
  }, [taskUpdatesResult.error]);

  useEffect(() => {
    if (metricsStreamResult.error) {
      console.error('QA_Engineer: Metrics stream subscription error:', metricsStreamResult.error);
    }
  }, [metricsStreamResult.error]);

  // Combine data from queries and subscriptions
  // Removed global dashboardStats and systemMetrics - using only project-specific data
  const systemMetrics = metricsStreamResult.data?.systemMetricsStream; // Only from subscription (if project-filtered)
  const agentActivities = agentActivityResult.data?.agentActivity ? [agentActivityResult.data.agentActivity] : [];
  
  // QA_Engineer: Collect task updates from subscription (real-time)
  const [taskUpdatesList, setTaskUpdatesList] = useState<any[]>([]);
  
  // QA_Engineer: Clear task updates when project changes to prevent showing wrong project's tasks
  useEffect(() => {
    setTaskUpdatesList([]);
  }, [selectedProjectId]);
  
  useEffect(() => {
    if (taskUpdatesResult.data?.taskUpdates) {
      // Mark that we should restore scroll position after this update
      shouldRestoreScrollRef.current = true;
      
      const update = taskUpdatesResult.data.taskUpdates;
      setTaskUpdatesList(prev => {
        // Update existing task or add new one
        const existingIndex = prev.findIndex(t => t.id === update.id);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = update;
          return updated;
        }
        return [...prev, update];
      });
    }
  }, [taskUpdatesResult.data]);

  // Task Timeline pagination, search, and sort state
  const [taskTimelinePage, setTaskTimelinePage] = useState(1);
  const [taskTimelinePageSize, setTaskTimelinePageSize] = useState(25);
  const [taskTimelineSearch, setTaskTimelineSearch] = useState('');
  const [taskTimelineSortField, setTaskTimelineSortField] = useState<'created_at' | 'completed_at'>('completed_at');
  const [taskTimelineSortDirection, setTaskTimelineSortDirection] = useState<'asc' | 'desc'>('asc'); // Oldest first for timeline

  // Collect metrics updates from subscription (real-time)
  const [currentMetrics, setCurrentMetrics] = useState(systemMetrics);
  useEffect(() => {
    if (metricsStreamResult.data?.systemMetricsStream) {
      // Mark that we should restore scroll position after this update
      shouldRestoreScrollRef.current = true;
      setCurrentMetrics(metricsStreamResult.data.systemMetricsStream);
    }
  }, [metricsStreamResult.data]);

  // Get selected project data (declare before use)
  const selectedProject = projectResult.data?.project;
  const selectedProjectRest = availableProjects.find(p => p.id === selectedProjectId);

  // Collect project updates from GraphQL query (real-time via polling or subscription)
  const [currentProject, setCurrentProject] = useState(selectedProject);
  useEffect(() => {
    if (projectResult.data?.project) {
      // Mark that we should restore scroll position after this update
      shouldRestoreScrollRef.current = true;
      setCurrentProject(projectResult.data.project);
    }
  }, [projectResult.data]);

  // Calculate real-time progress from project data
  // Always returns whole numbers (0-100)
  // CRITICAL: Use project-specific completionPercentage from GraphQL query
  // Both "Overall Progress" and "Completion Rate" must use the SAME calculation
  const calculateProgress = (): number => {
    // Priority 1: Use selectedProject.completionPercentage (from GraphQL query - project-specific, filtered by execution_started_at)
    if (selectedProject?.completionPercentage !== undefined) {
      return Math.round(Math.min(100, Math.max(0, selectedProject.completionPercentage)));
    }
    
    // Priority 2: Calculate from selectedProject task counts (if completionPercentage not available)
    if (selectedProject && selectedProject.totalTasks > 0) {
      const percentage = ((selectedProject.completedTasks || 0) / selectedProject.totalTasks) * 100;
      return Math.round(Math.min(100, Math.max(0, percentage)));
    }
    
    // Priority 3: Fallback to 0 if no project data available
    return 0;
  };

  const realTimeProgress = calculateProgress();

  const loading = projectResult.fetching;
  const connected = !projectResult.error;

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
      ? projectAgents.map((agent: any) => {
          const statusValue = agent.status === 'active' ? 'active' : agent.status === 'idle' ? 'idle' : 'busy';
          return {
            name: agent.name || agent.agentType || 'Unknown Agent',
            status: statusValue as 'active' | 'idle' | 'busy',
            currentTask: agent.currentTaskId || undefined,
            tasksCompleted: agent.tasksCompleted || 0,
          };
        })
      : agentActivities.map((activity: any) => ({
          name: activity.agentId || 'Unknown Agent',
          status: 'active' as const,
          currentTask: activity.taskId || undefined,
          tasksCompleted: 0,
        })),
    tasks: (() => {
      // Combine completed tasks from query with real-time updates from subscription
      const completedTasksList = selectedProject?.completedTasksList || [];
      const allTasks = [...completedTasksList, ...taskUpdatesList];
      
      // Remove duplicates (prefer subscription updates over query results)
      const taskMap = new Map();
      allTasks.forEach((task: any) => {
        if (!taskMap.has(task.id) || task.status === 'COMPLETED' || task.status === 'completed') {
          taskMap.set(task.id, task);
        }
      });
      
      // QA_Engineer: Convert to array with all needed fields for filtering/sorting/pagination
      // QA_Engineer: Normalize status consistently to handle both uppercase and lowercase inputs
      const normalizeStatus = (status: string | undefined): 'pending' | 'in_progress' | 'completed' | 'failed' => {
        if (!status) return 'pending';
        const normalized = status.toLowerCase();
        if (normalized === 'completed' || normalized === 'done') return 'completed';
        if (normalized === 'in_progress' || normalized === 'inprogress' || normalized === 'running') return 'in_progress';
        if (normalized === 'failed' || normalized === 'error') return 'failed';
        return 'pending';
      };
      
      return Array.from(taskMap.values())
        .map((task: any) => ({
          id: task.id,
          title: task.title || 'Unknown Task',
          status: normalizeStatus(task.status),
          agent: task.agent?.name || task.agentType || undefined,
          progress: task.progress || (task.status === 'COMPLETED' || task.status === 'completed' ? 100 : 0),
          completedAt: task.completedAt || null,
          createdAt: task.createdAt || null,
          // For sorting, use completedAt if available, otherwise createdAt
          sortTime: task.completedAt ? new Date(task.completedAt).getTime() : (task.createdAt ? new Date(task.createdAt).getTime() : 0),
        }));
    })(),
    metrics: {
      // CPU and Memory are SYSTEM-WIDE (not project-specific) - clearly labeled
      cpu: currentMetrics?.cpuUsagePercent || systemMetrics?.cpuUsagePercent || 0,
      memory: currentMetrics?.memoryUsagePercent || systemMetrics?.memoryUsagePercent || 0,
      // ALL task metrics are PROJECT-SPECIFIC (from selectedProject only)
      activeTasks: currentProject?.totalTasks 
        ? Math.max(0, (currentProject.totalTasks - (currentProject.completedTasks || 0) - (currentProject.failedTasks || 0)))
        : 0,
      completedTasks: currentProject?.completedTasks ?? 0,
      failedTasks: currentProject?.failedTasks ?? 0,
      totalTasks: currentProject?.totalTasks ?? 0,
      successRate: currentProject?.successRate ?? 0,
      averageTaskTime: currentProject?.estimatedTimeRemainingSeconds || 0,
    },
  };

  // Show loading state only on initial load
  if (loading && !selectedProject) {
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
                  {Math.round(project.progress)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
                <div
                  className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 shadow-md transition-all duration-500 ease-out"
                  style={{ width: `${Math.round(project.progress)}%` }}
                >
                  {project.progress > 10 && (
                    <div className="h-full flex items-center justify-end pr-2">
                      <span className="text-xs font-bold text-white drop-shadow">
                        {Math.round(project.progress)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* QA_Engineer: Removed emoji characters for Windows compatibility */}
            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl font-bold text-purple-600">Agent</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Active Agents</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{activeAgents}</p>
              <p className="text-sm text-gray-500">{idleAgents} idle</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl font-bold text-green-600">Complete</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Completed Tasks</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{metrics.completedTasks}</p>
              <p className="text-sm text-gray-500">{metrics.totalTasks} total</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl font-bold text-blue-600">Chart</div>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-2">Success Rate</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">{Math.round(metrics.successRate)}%</p>
              <p className="text-sm text-gray-500">Project</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl font-bold text-yellow-600">Active</div>
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
                {/* QA_Engineer: Removed emoji characters for Windows compatibility */}
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  Agent Activity
                  {activeAgents > 0 && (
                    <span className="text-sm font-normal text-gray-500">
                      ({activeAgents} active)
                    </span>
                  )}
                </h2>
                
                {agents.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4 font-bold text-gray-400">No Agents</div>
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

              {/* QA_Engineer: Task Timeline - Removed emoji characters for Windows compatibility */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Task Timeline</h2>
                
                {tasks.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4 font-bold text-gray-400">No Tasks</div>
                    <p className="text-gray-500">
                      {connected ? 'No tasks yet...' : 'Waiting for tasks...'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tasks.map((task) => (
                      <div key={task.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-center">
                          <div className="flex-1">
                            <div className="font-semibold text-gray-800">{task.title}</div>
                            {task.agent && (
                              <div className="text-sm text-gray-600 mt-1">Agent: {task.agent}</div>
                            )}
                            {task.progress !== undefined && (
                              <div className="mt-2">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-purple-500 h-2 rounded-full transition-all duration-500 ease-out"
                                    style={{ width: `${task.progress}%` }}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                          <span className={`px-3 py-1 rounded text-sm font-semibold ml-4 ${
                            task.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : task.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : task.status === 'in_progress'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {task.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* QA_Engineer: System Metrics Sidebar - Removed emoji characters for Windows compatibility */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h2 className="text-xl font-bold text-gray-900 mb-4">System Metrics</h2>
                
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Completion Rate</span>
                      <span className="text-sm font-bold text-green-600">
                        {realTimeProgress}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ 
                          width: `${realTimeProgress}%` 
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
                      <span className="text-sm font-medium text-gray-700">System CPU Usage</span>
                      <span className="text-sm font-bold text-purple-600">{metrics.cpu.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${metrics.cpu}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">System-wide resource usage</p>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">System Memory Usage</span>
                      <span className="text-sm font-bold text-orange-600">{metrics.memory.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-orange-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${metrics.memory}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">System-wide resource usage</p>
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

