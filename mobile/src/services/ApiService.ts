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

  // ==================== BILLING METHODS ====================

  async getPricingTiers(): Promise<any[]> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.get('/api/billing/pricing-tiers');
      return response.data;
    } catch (error: any) {
      console.error('[API] Get pricing tiers error:', error);
      throw new Error(error.response?.data?.message || 'Failed to get pricing tiers');
    }
  }

  async estimateMigrationCost(params: {
    platform_name: string;
    years_of_data: number;
    estimated_records?: number | null;
    tax_rate?: number;
  }): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.post('/api/billing/estimate', params);
      return response.data;
    } catch (error: any) {
      console.error('[API] Estimate cost error:', error);
      throw new Error(error.response?.data?.message || 'Failed to estimate cost');
    }
  }

  async createCheckoutSession(params: {
    migration_id: string;
    customer_email: string;
    pricing_data: any;
  }): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.post('/api/billing/checkout', params);
      return response.data;
    } catch (error: any) {
      console.error('[API] Create checkout error:', error);
      throw new Error(error.response?.data?.message || 'Failed to create checkout');
    }
  }

  async checkPaymentStatus(session_id: string): Promise<any> {
    if (!this.client) {
      throw new Error('API Service not initialized');
    }

    try {
      const response = await this.client.get(`/api/billing/payment/${session_id}/status`);
      return response.data;
    } catch (error: any) {
      console.error('[API] Check payment status error:', error);
      throw new Error(error.response?.data?.message || 'Failed to check payment status');
    }
  }

  getBaseURL(): string {
    return this.baseURL;
  }
}

export default new ApiService();

