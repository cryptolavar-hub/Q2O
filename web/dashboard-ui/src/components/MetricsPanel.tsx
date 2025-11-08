import React from 'react';
import type { SystemMetrics } from '../types/dashboard';

interface MetricsPanelProps {
  metrics: SystemMetrics;
}

export function MetricsPanel({ metrics }: MetricsPanelProps) {
  const completionRate = metrics.totalTasks > 0 
    ? Math.round((metrics.completedTasks / metrics.totalTasks) * 100) 
    : 0;

  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg">
      <h2 className="text-xl font-bold text-gray-900 mb-6">System Metrics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Completion Rate */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">Completion Rate</span>
            <span className="text-lg font-bold text-green-600">{completionRate}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-500"
              style={{ width: `${completionRate}%` }}
            />
          </div>
        </div>

        {/* Success Rate */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">Success Rate</span>
            <span className="text-lg font-bold text-blue-600">{metrics.successRate}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-400 to-purple-600 transition-all duration-500"
              style={{ width: `${metrics.successRate}%` }}
            />
          </div>
        </div>

        {/* CPU Usage */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">CPU Usage</span>
            <span className="text-lg font-bold text-purple-600">{metrics.cpu}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-purple-400 to-pink-600 transition-all duration-500"
              style={{ width: `${metrics.cpu}%` }}
            />
          </div>
        </div>

        {/* Memory Usage */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">Memory Usage</span>
            <span className="text-lg font-bold text-orange-600">{metrics.memory}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-orange-400 to-red-500 transition-all duration-500"
              style={{ width: `${metrics.memory}%` }}
            />
          </div>
        </div>
      </div>

      {/* Task Statistics */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-blue-600">{metrics.activeTasks}</p>
            <p className="text-xs text-gray-500 font-medium">Active</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">{metrics.completedTasks}</p>
            <p className="text-xs text-gray-500 font-medium">Completed</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600">{metrics.failedTasks}</p>
            <p className="text-xs text-gray-500 font-medium">Failed</p>
          </div>
        </div>
      </div>

      {/* Average Task Time */}
      {metrics.averageTaskTime > 0 && (
        <div className="mt-4 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Average Task Time</span>
            <span className="text-lg font-bold text-purple-700">
              {metrics.averageTaskTime < 60 
                ? `${Math.round(metrics.averageTaskTime)}s` 
                : `${Math.floor(metrics.averageTaskTime / 60)}m ${Math.round(metrics.averageTaskTime % 60)}s`
              }
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

