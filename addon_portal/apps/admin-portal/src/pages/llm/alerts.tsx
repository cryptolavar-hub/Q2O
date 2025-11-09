/**
 * LLM Alerts & Monitoring
 * Budget alerts, failures, and recommendations
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { AdminHeader } from '@/components/AdminHeader';

interface Alert {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'critical';
  type: string;
  message: string;
  details: string;
  resolved: boolean;
  actions: string[];
}

export default function LLMAlerts() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState('all');
  const [showResolved, setShowResolved] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/llm/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const dismissAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/llm/alerts/${alertId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'dismiss' }),
      });

      if (response.ok) {
        setAlerts(alerts.map(a => a.id === alertId ? { ...a, resolved: true } : a));
      }
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    const matchesLevel = filterLevel === 'all' || alert.level === filterLevel;
    const matchesResolved = showResolved || !alert.resolved;
    return matchesLevel && matchesResolved;
  });

  const criticalCount = alerts.filter(a => a.level === 'critical' && !a.resolved).length;
  const warningCount = alerts.filter(a => a.level === 'warning' && !a.resolved).length;
  const infoCount = alerts.filter(a => a.level === 'info' && !a.resolved).length;

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-50 border-red-300';
      case 'warning': return 'bg-yellow-50 border-yellow-300';
      case 'info': return 'bg-blue-50 border-blue-300';
      default: return 'bg-gray-50 border-gray-300';
    }
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical': return '🚨';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="Alerts" />
        <div className="flex items-center justify-center h-96">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="LLM Alerts & Monitoring" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => router.push('/llm')}
          className="mb-6 text-blue-600 hover:text-blue-700 flex items-center gap-2"
        >
          ← Back to Overview
        </button>

        {/* Alert Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Critical Alerts</h3>
            <p className="text-3xl font-bold text-red-600">{criticalCount}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Warnings</h3>
            <p className="text-3xl font-bold text-yellow-600">{warningCount}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Info</h3>
            <p className="text-3xl font-bold text-blue-600">{infoCount}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex gap-4">
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                <option value="all">All Levels</option>
                <option value="critical">Critical Only</option>
                <option value="warning">Warnings Only</option>
                <option value="info">Info Only</option>
              </select>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={showResolved}
                  onChange={(e) => setShowResolved(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">Show Resolved</span>
              </label>
            </div>

            <p className="text-sm text-gray-600">
              {filteredAlerts.length} alert{filteredAlerts.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        {/* Alerts List */}
        {filteredAlerts.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">✅</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">All Clear!</h3>
            <p className="text-gray-600">No active alerts. Your LLM integration is running smoothly.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`border-2 rounded-lg ${getAlertColor(alert.level)} ${
                  alert.resolved ? 'opacity-60' : ''
                }`}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{getAlertIcon(alert.level)}</span>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            alert.level === 'critical' ? 'bg-red-100 text-red-800' :
                            alert.level === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {alert.level.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(alert.timestamp).toLocaleString()}
                          </span>
                          {alert.resolved && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Resolved
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{alert.message}</h3>
                        <p className="text-sm text-gray-700 mb-3">{alert.details}</p>
                        
                        {alert.actions.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-2">Recommended Actions:</p>
                            <ul className="list-disc list-inside space-y-1">
                              {alert.actions.map((action, idx) => (
                                <li key={idx} className="text-sm text-gray-600">{action}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>

                    {!alert.resolved && (
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="text-sm text-gray-600 hover:text-gray-900 underline"
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

