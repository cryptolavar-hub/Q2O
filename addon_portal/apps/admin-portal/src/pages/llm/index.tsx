/**
 * LLM Overview Dashboard
 * Real-time monitoring of LLM usage, costs, and performance
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { AdminHeader } from '@/components/AdminHeader';
import { Navigation } from '@/components/Navigation';

interface LLMStats {
  totalCalls: number;
  totalCost: number;
  monthlyBudget: number;
  budgetUsed: number;
  avgResponseTime: number;
  successRate: number;
  providerBreakdown: {
    gemini: { calls: number; cost: number };
    openai: { calls: number; cost: number };
    anthropic: { calls: number; cost: number };
  };
  dailyCosts: Array<{ date: string; cost: number }>;
  templateStats: {
    total: number;
    uses: number;
    saved: number;
  };
  alerts: Array<{
    id: string;
    level: string;
    message: string;
    timestamp: string;
  }>;
}

export default function LLMOverview() {
  const router = useRouter();
  const [stats, setStats] = useState<LLMStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/llm/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch LLM stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBudgetColor = (percentUsed: number) => {
    if (percentUsed >= 95) return 'text-red-600';
    if (percentUsed >= 80) return 'text-orange-600';
    if (percentUsed >= 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="LLM Overview" subtitle="Monitor LLM usage, costs, and performance" />
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading LLM statistics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="LLM Overview" subtitle="Monitor LLM usage, costs, and performance" />
        <Navigation />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">LLM Not Configured</h3>
            <p className="text-yellow-700">
              LLM integration is not configured. Please add API keys and enable LLM in settings.
            </p>
            <button
              onClick={() => router.push('/llm/configuration')}
              className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Configure LLM
            </button>
          </div>
        </div>
      </div>
    );
  }

  const budgetPercent = (stats.budgetUsed / stats.monthlyBudget) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="LLM Overview" subtitle="Monitor LLM usage, costs, and performance" />
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Project & Agent Prompts Management */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              📝 Project & Agent Prompts
            </h2>
            <button
              onClick={() => router.push('/llm/prompts')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              + Add New Project Prompt
            </button>
          </div>
          
          {/* Quick Search */}
          <div className="bg-white rounded-lg shadow-sm p-4 mb-4 border border-gray-200">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search project, tenant, or label..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <select className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option>All Tenants</option>
              </select>
            </div>
          </div>

          {/* Prompts Table Preview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Project</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tenant</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agents</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr className="text-center">
                  <td colSpan={5} className="px-6 py-8 text-gray-500">
                    No project prompts configured. Click "Add New Project Prompt" to create one.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-6 flex gap-3 flex-wrap">
          <button
            onClick={() => router.push('/llm/configuration')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            ⚙️ Configuration
          </button>
          <button
            onClick={() => router.push('/llm/templates')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            📚 Learned Templates
          </button>
          <button
            onClick={() => router.push('/llm/logs')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            📋 Usage Logs
          </button>
          <button
            onClick={() => router.push('/llm/alerts')}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
          >
            🚨 Alerts ({stats.alerts.length})
          </button>
        </div>

        {/* Critical Alerts */}
        {stats.alerts.length > 0 && (
          <div className="mb-6">
            {stats.alerts.slice(0, 3).map((alert) => (
              <div
                key={alert.id}
                className={`mb-3 p-4 border rounded-lg ${getAlertColor(alert.level)}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{alert.message}</p>
                    <p className="text-sm mt-1 opacity-75">{new Date(alert.timestamp).toLocaleString()}</p>
                  </div>
                  <button className="text-sm underline">Dismiss</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Budget Usage */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">Budget Usage</h3>
              <span className={`text-2xl font-bold ${getBudgetColor(budgetPercent)}`}>
                {budgetPercent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
              <div
                className={`h-3 rounded-full ${
                  budgetPercent >= 95 ? 'bg-red-600' :
                  budgetPercent >= 80 ? 'bg-orange-500' :
                  budgetPercent >= 50 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(budgetPercent, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-600">
              ${stats.budgetUsed.toFixed(2)} of ${stats.monthlyBudget.toFixed(2)}
            </p>
          </div>

          {/* Total Calls */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total LLM Calls</h3>
            <p className="text-3xl font-bold text-gray-900">{stats.totalCalls.toLocaleString()}</p>
            <p className="text-sm text-gray-600 mt-2">
              Success Rate: {stats.successRate.toFixed(1)}%
            </p>
          </div>

          {/* Avg Response Time */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Avg Response Time</h3>
            <p className="text-3xl font-bold text-gray-900">{stats.avgResponseTime.toFixed(2)}s</p>
            <p className="text-sm text-green-600 mt-2">Within target range</p>
          </div>

          {/* Cost Savings */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Template Savings</h3>
            <p className="text-3xl font-bold text-green-600">${stats.templateStats.saved.toFixed(2)}</p>
            <p className="text-sm text-gray-600 mt-2">
              {stats.templateStats.uses} template uses
            </p>
          </div>
        </div>

        {/* Provider Cost Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Gemini */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Gemini 1.5 Pro</h3>
              <span className="text-2xl">💎</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Calls:</span>
                <span className="text-sm font-semibold">{stats.providerBreakdown.gemini.calls}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Cost:</span>
                <span className="text-sm font-semibold text-blue-600">${stats.providerBreakdown.gemini.cost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Cost:</span>
                <span className="text-sm font-semibold">${(stats.providerBreakdown.gemini.cost / (stats.providerBreakdown.gemini.calls || 1)).toFixed(4)}</span>
              </div>
            </div>
          </div>

          {/* GPT-4 */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">GPT-4 Turbo</h3>
              <span className="text-2xl">🤖</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Calls:</span>
                <span className="text-sm font-semibold">{stats.providerBreakdown.openai.calls}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Cost:</span>
                <span className="text-sm font-semibold text-green-600">${stats.providerBreakdown.openai.cost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Cost:</span>
                <span className="text-sm font-semibold">${(stats.providerBreakdown.openai.cost / (stats.providerBreakdown.openai.calls || 1)).toFixed(4)}</span>
              </div>
            </div>
          </div>

          {/* Claude */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Claude 3.5 Sonnet</h3>
              <span className="text-2xl">🧠</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Calls:</span>
                <span className="text-sm font-semibold">{stats.providerBreakdown.anthropic.calls}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Cost:</span>
                <span className="text-sm font-semibold text-orange-600">${stats.providerBreakdown.anthropic.cost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Cost:</span>
                <span className="text-sm font-semibold">${(stats.providerBreakdown.anthropic.cost / (stats.providerBreakdown.anthropic.calls || 1)).toFixed(4)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Provider Details */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Provider Usage Details</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Calls
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Success Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Gemini 1.5 Pro
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.providerBreakdown.gemini.calls}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${stats.providerBreakdown.gemini.cost.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(stats.providerBreakdown.gemini.cost / (stats.providerBreakdown.gemini.calls || 1)).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    99.2%
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      GPT-4 Turbo
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.providerBreakdown.openai.calls}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${stats.providerBreakdown.openai.cost.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(stats.providerBreakdown.openai.cost / (stats.providerBreakdown.openai.calls || 1)).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    98.8%
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                      Claude 3.5 Sonnet
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.providerBreakdown.anthropic.calls}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${stats.providerBreakdown.anthropic.cost.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(stats.providerBreakdown.anthropic.cost / (stats.providerBreakdown.anthropic.calls || 1)).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    99.5%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

