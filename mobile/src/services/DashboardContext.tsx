/**
 * Dashboard Context Provider
 * Manages global dashboard state and WebSocket connection
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import DashboardWebSocket, { ProjectData, TaskUpdate, MetricUpdate } from './DashboardWebSocket';
import ApiService from './ApiService';

interface DashboardState {
  connected: boolean;
  currentProject: ProjectData | null;
  tasks: TaskUpdate[];
  metrics: MetricUpdate;
  agentActivity: any[];
  loading: boolean;
  error: string | null;
}

interface DashboardContextType {
  state: DashboardState;
  connectToDashboard: (serverUrl: string) => Promise<void>;
  disconnect: () => void;
  refreshMetrics: () => Promise<void>;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<DashboardState>({
    connected: false,
    currentProject: null,
    tasks: [],
    metrics: {},
    agentActivity: [],
    loading: false,
    error: null,
  });

  useEffect(() => {
    // Set up WebSocket event listeners
    DashboardWebSocket.on('connection_status', (data: { connected: boolean }) => {
      setState(prev => ({ ...prev, connected: data.connected }));
    });

    DashboardWebSocket.on('project_start', (data: ProjectData) => {
      setState(prev => ({
        ...prev,
        currentProject: data,
        tasks: [],
      }));
    });

    DashboardWebSocket.on('task_update', (data: TaskUpdate) => {
      setState(prev => {
        const existingIndex = prev.tasks.findIndex(t => t.task_id === data.task_id);
        const newTasks = [...prev.tasks];
        
        if (existingIndex >= 0) {
          newTasks[existingIndex] = data;
        } else {
          newTasks.push(data);
        }
        
        return { ...prev, tasks: newTasks };
      });
    });

    DashboardWebSocket.on('metric_update', (data: MetricUpdate) => {
      setState(prev => ({
        ...prev,
        metrics: { ...prev.metrics, ...data },
      }));
    });

    DashboardWebSocket.on('agent_activity', (data: any) => {
      setState(prev => ({
        ...prev,
        agentActivity: [data, ...prev.agentActivity].slice(0, 100), // Keep last 100
      }));
    });

    DashboardWebSocket.on('project_complete', (data: any) => {
      setState(prev => ({
        ...prev,
        currentProject: null,
      }));
    });

    DashboardWebSocket.on('connection_error', (data: { error: string }) => {
      setState(prev => ({
        ...prev,
        error: data.error,
      }));
    });

    return () => {
      // Cleanup listeners on unmount
      DashboardWebSocket.disconnect();
    };
  }, []);

  const connectToDashboard = async (serverUrl: string) => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Initialize both WebSocket and API
      await DashboardWebSocket.initialize(serverUrl);
      await ApiService.initialize(serverUrl);
      
      // Check API health
      const healthy = await ApiService.healthCheck();
      if (!healthy) {
        throw new Error('API health check failed');
      }

      setState(prev => ({ ...prev, loading: false }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Failed to connect to dashboard',
      }));
      throw error;
    }
  };

  const disconnect = () => {
    DashboardWebSocket.disconnect();
    setState({
      connected: false,
      currentProject: null,
      tasks: [],
      metrics: {},
      agentActivity: [],
      loading: false,
      error: null,
    });
  };

  const refreshMetrics = async () => {
    try {
      const metrics = await ApiService.getMetrics();
      setState(prev => ({
        ...prev,
        metrics: { ...prev.metrics, ...metrics },
      }));
    } catch (error: any) {
      console.error('Failed to refresh metrics:', error);
    }
  };

  const value: DashboardContextType = {
    state,
    connectToDashboard,
    disconnect,
    refreshMetrics,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboard = (): DashboardContextType => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return context;
};

