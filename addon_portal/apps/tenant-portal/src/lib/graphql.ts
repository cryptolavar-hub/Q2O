/**
 * GraphQL Client for Tenant Portal Status Page
 * 
 * Uses urql for GraphQL queries and subscriptions
 */

import { createClient, fetchExchange, subscriptionExchange, Client } from 'urql';
import { createClient as createWSClient } from 'graphql-ws';

// GraphQL endpoint (adjust if needed)
const GRAPHQL_ENDPOINT = process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8080/graphql';
const WS_ENDPOINT = process.env.NEXT_PUBLIC_GRAPHQL_WS_URL || 'ws://localhost:8080/graphql';

// Create WebSocket client for subscriptions (only in browser)
const wsClient = typeof window !== 'undefined'
  ? createWSClient({
      url: WS_ENDPOINT,
      connectionParams: () => {
        const token = localStorage.getItem('tenant_session_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
      },
    })
  : null;

// Create urql client
export const graphqlClient: Client = createClient({
  url: GRAPHQL_ENDPOINT,
  exchanges: [
    fetchExchange,
    ...(wsClient ? [
      subscriptionExchange({
        forwardSubscription: (operation) => {
          // Transform urql operation to graphql-ws format
          // graphql-ws requires query to be a string (not optional)
          if (!operation.query) {
            throw new Error('GraphQL subscription requires a query');
          }
          
          return {
            subscribe: (sink) => {
              const unsubscribe = wsClient.subscribe(
                {
                  query: operation.query as string,
                  variables: operation.variables || {},
                  operationName: operation.operationName || undefined,
                },
                sink
              );
              
              return { unsubscribe };
            },
          };
        },
      })
    ] : []),
  ],
  // Add authentication token if needed
  fetchOptions: () => {
    const token = typeof window !== 'undefined' 
      ? localStorage.getItem('tenant_session_token')
      : null;
    
    return token
      ? {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      : {};
  },
});

// GraphQL Queries
export const DASHBOARD_STATS_QUERY = `
  query DashboardStats {
    dashboardStats {
      totalProjects
      activeProjects
      totalTasks
      activeTasks
      completedTasksToday
      averageSuccessRate
      mostActiveAgent
      recentActivities {
        id
        agentType
        message
        timestamp
        taskId
      }
    }
  }
`;

export const SYSTEM_METRICS_QUERY = `
  query SystemMetrics {
    systemMetrics {
      timestamp
      activeAgents
      activeTasks
      tasksCompletedToday
      tasksFailedToday
      averageTaskDurationSeconds
      systemHealthScore
      cpuUsagePercent
      memoryUsagePercent
    }
  }
`;

export const PROJECTS_QUERY = `
  query Projects($filter: ProjectFilterInput) {
    projects(filter: $filter, limit: 50) {
      id
      name
      status
      completionPercentage
      totalTasks
      completedTasks
      failedTasks
      tasks {
        id
        title
        status
        durationSeconds
      }
    }
  }
`;

export const PROJECT_QUERY = `
  query Project($id: String!) {
    project(id: $id) {
      id
      name
      objective
      status
      completionPercentage
      totalTasks
      completedTasks
      failedTasks
      successRate
      estimatedTimeRemainingSeconds
      agents {
        id
        agentType
        name
        status
        healthScore
        tasksCompleted
        tasksFailed
        currentTaskId
        lastActivity
        successRate
      }
      tasks(status: IN_PROGRESS, limit: 20) {
        id
        title
        status
        agentType
        durationSeconds
      }
    }
  }
`;

// GraphQL Subscriptions
export const AGENT_ACTIVITY_SUBSCRIPTION = `
  subscription AgentActivity {
    agentActivity {
      id
      agentType
      agentId
      eventType
      message
      timestamp
      taskId
    }
  }
`;

export const TASK_UPDATES_SUBSCRIPTION = `
  subscription TaskUpdates($projectId: String) {
    taskUpdates(projectId: $projectId) {
      id
      projectId
      title
      status
      agentType
      agent {
        name
        agentType
      }
      completedAt
      durationSeconds
    }
  }
`;

export const PROJECT_UPDATES_SUBSCRIPTION = `
  subscription ProjectUpdates($projectId: String!) {
    projectUpdates(projectId: $projectId) {
      id
      name
      status
      completionPercentage
      totalTasks
      completedTasks
      failedTasks
      updatedAt
    }
  }
`;

export const SYSTEM_METRICS_STREAM_SUBSCRIPTION = `
  subscription SystemMetricsStream($intervalSeconds: Int, $projectId: String) {
    systemMetricsStream(intervalSeconds: $intervalSeconds, projectId: $projectId) {
      timestamp
      activeAgents
      activeTasks
      tasksCompletedToday
      tasksFailedToday
      averageTaskDurationSeconds
      systemHealthScore
      cpuUsagePercent
      memoryUsagePercent
    }
  }
`;

