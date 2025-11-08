import React from 'react';
import { motion } from 'framer-motion';
import type { Task } from '../types/dashboard';

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'completed':
      return { bg: 'bg-green-100', text: 'text-green-700', icon: '✅', label: 'Completed' };
    case 'in_progress':
      return { bg: 'bg-blue-100', text: 'text-blue-700', icon: '🔵', label: 'In Progress' };
    case 'pending':
      return { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '🟡', label: 'Pending' };
    case 'failed':
      return { bg: 'bg-red-100', text: 'text-red-700', icon: '🔴', label: 'Failed' };
    default:
      return { bg: 'bg-gray-100', text: 'text-gray-700', icon: '⚪', label: 'Unknown' };
  }
};

export function TaskCard({ task }: { task: Task }) {
  const badge = getStatusBadge(task.status);
  const duration = task.duration ? Math.round(task.duration / 1000) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-xl p-4 shadow-md border-l-4 hover:shadow-lg transition-all duration-300"
      style={{
        borderLeftColor: task.status === 'completed' ? '#4CAF50' :
                        task.status === 'in_progress' ? '#2196F3' :
                        task.status === 'failed' ? '#F44336' : '#FFC107'
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 mb-1">{task.name}</h4>
          <p className="text-sm text-gray-600">Agent: <span className="font-medium">{task.agent}</span></p>
        </div>
        <span className={`${badge.bg} ${badge.text} px-3 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1`}>
          <span>{badge.icon}</span>
          <span>{badge.label}</span>
        </span>
      </div>

      {/* Progress Bar */}
      {task.status === 'in_progress' && (
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-medium text-gray-600">Progress</span>
            <span className="text-xs font-bold text-blue-600">{task.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
              initial={{ width: 0 }}
              animate={{ width: `${task.progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      )}

      {/* Duration */}
      {task.status === 'completed' && duration > 0 && (
        <div className="text-xs text-gray-500">
          ⏱️ Completed in {duration < 60 ? `${duration}s` : `${Math.floor(duration / 60)}m ${duration % 60}s`}
        </div>
      )}

      {/* Error Message */}
      {task.status === 'failed' && task.error && (
        <div className="mt-2 p-2 bg-red-50 rounded-lg">
          <p className="text-xs text-red-700 font-medium">Error: {task.error}</p>
        </div>
      )}

      {/* Running Time */}
      {task.status === 'in_progress' && task.startTime && (
        <div className="text-xs text-gray-500 mt-2">
          ⏳ Running...
        </div>
      )}
    </motion.div>
  );
}

