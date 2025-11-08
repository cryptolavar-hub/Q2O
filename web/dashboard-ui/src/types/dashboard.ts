/**
 * Dashboard TypeScript Type Definitions
 */

export interface Task {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  agent: string;
  progress: number;
  startTime?: string;
  endTime?: string;
  duration?: number;
  error?: string;
}

export interface Agent {
  name: string;
  status: 'idle' | 'active' | 'busy' | 'error';
  currentTask?: string;
  tasksCompleted: number;
  successRate: number;
  lastActivity?: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalTasks: number;
  successRate: number;
  averageTaskTime: number;
}

export interface DashboardState {
  tasks: Task[];
  agents: Agent[];
  metrics: SystemMetrics;
  project: {
    name: string;
    status: string;
    progress: number;
    estimatedTimeRemaining?: number;
  };
}

export interface WebSocketMessage {
  type: 'initial_state' | 'task_update' | 'agent_activity' | 'metric_update' | 'project_update';
  data: any;
}

export interface StatCard {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
}

