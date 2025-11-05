/**
 * WebSocket Service for Real-time Dashboard Communication
 * Connects to Quick2Odoo backend for live project monitoring
 */

import { io, Socket } from 'socket.io-client';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface DashboardEvent {
  type: string;
  data: any;
  timestamp: string;
}

export interface ProjectData {
  project_description: string;
  objectives: string[];
  platforms: string[];
  started_at: string;
}

export interface TaskUpdate {
  task_id: string;
  status: string;
  agent_type: string;
  progress: number;
  message?: string;
}

export interface MetricUpdate {
  cpu_usage?: number;
  memory_usage?: number;
  active_agents?: number;
  completed_tasks?: number;
  failed_tasks?: number;
}

class DashboardWebSocketService {
  private socket: Socket | null = null;
  private serverUrl: string = '';
  private listeners: Map<string, Set<Function>> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 2000;

  async initialize(serverUrl?: string) {
    if (serverUrl) {
      this.serverUrl = serverUrl;
      await AsyncStorage.setItem('dashboard_server_url', serverUrl);
    } else {
      const saved = await AsyncStorage.getItem('dashboard_server_url');
      this.serverUrl = saved || 'http://localhost:8000';
    }

    this.connect();
  }

  private connect() {
    console.log(`[WebSocket] Connecting to ${this.serverUrl}`);

    this.socket = io(this.serverUrl, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('[WebSocket] Connected successfully');
      this.reconnectAttempts = 0;
      this.emit('connection_status', { connected: true });
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[WebSocket] Disconnected: ${reason}`);
      this.emit('connection_status', { connected: false, reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('[WebSocket] Connection error:', error);
      this.reconnectAttempts++;
      this.emit('connection_error', { error: error.message, attempts: this.reconnectAttempts });
    });

    // Dashboard event listeners
    this.socket.on('project_start', (data: ProjectData) => {
      console.log('[WebSocket] Project started:', data);
      this.emit('project_start', data);
    });

    this.socket.on('task_update', (data: TaskUpdate) => {
      console.log('[WebSocket] Task update:', data);
      this.emit('task_update', data);
    });

    this.socket.on('task_complete', (data) => {
      console.log('[WebSocket] Task complete:', data);
      this.emit('task_complete', data);
    });

    this.socket.on('agent_activity', (data) => {
      console.log('[WebSocket] Agent activity:', data);
      this.emit('agent_activity', data);
    });

    this.socket.on('metric_update', (data: MetricUpdate) => {
      console.log('[WebSocket] Metrics:', data);
      this.emit('metric_update', data);
    });

    this.socket.on('project_complete', (data) => {
      console.log('[WebSocket] Project complete:', data);
      this.emit('project_complete', data);
    });

    this.socket.on('error', (data) => {
      console.error('[WebSocket] Error event:', data);
      this.emit('error', data);
    });
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  async getServerUrl(): Promise<string> {
    return this.serverUrl || await AsyncStorage.getItem('dashboard_server_url') || 'http://localhost:8000';
  }
}

export default new DashboardWebSocketService();

