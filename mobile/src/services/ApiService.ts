/**
 * API Service for Quick2Odoo Backend Communication
 * Handles project initiation, configuration, and data fetching
 */

import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface ProjectConfig {
  project_description: string;
  platforms: string[];
  objectives: string[];
}

export interface ServerConfig {
  url: string;
  port?: number;
}

class ApiService {
  private client: AxiosInstance | null = null;
  private baseURL: string = '';

  async initialize(serverUrl?: string) {
    if (serverUrl) {
      this.baseURL = serverUrl;
      await AsyncStorage.setItem('api_server_url', serverUrl);
    } else {
      const saved = await AsyncStorage.getItem('api_server_url');
      this.baseURL = saved || 'http://localhost:8000';
    }

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async startProject(config: ProjectConfig): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.post('/api/projects/start', config);
      return response.data;
    } catch (error: any) {
      console.error('[API] Start project error:', error);
      throw new Error(error.response?.data?.message || 'Failed to start project');
    }
  }

  async getProjectStatus(projectId: string): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.get(`/api/projects/${projectId}/status`);
      return response.data;
    } catch (error: any) {
      console.error('[API] Get project status error:', error);
      throw new Error(error.response?.data?.message || 'Failed to get project status');
    }
  }

  async getMetrics(): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.get('/api/metrics');
      return response.data;
    } catch (error: any) {
      console.error('[API] Get metrics error:', error);
      throw new Error(error.response?.data?.message || 'Failed to get metrics');
    }
  }

  async getAgentStatus(): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.get('/api/agents/status');
      return response.data;
    } catch (error: any) {
      console.error('[API] Get agent status error:', error);
      throw new Error(error.response?.data?.message || 'Failed to get agent status');
    }
  }

  async getAvailablePlatforms(): Promise<string[]> {
    // Return supported platforms
    return [
      'QuickBooks',
      'SAGE',
      'Wave',
      'Expensify',
      'doola',
      'Dext',
      'Xero',
      'FreshBooks',
      'Zoho Books',
    ];
  }

  async healthCheck(): Promise<boolean> {
    if (!this.client) {
      return false;
    }

    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      console.error('[API] Health check failed:', error);
      return false;
    }
  }

  getBaseURL(): string {
    return this.baseURL;
  }
}

export default new ApiService();

