import React from 'react';
import { motion } from 'framer-motion';
import type { Agent } from '../types/dashboard';

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-blue-500';
    case 'busy':
      return 'bg-purple-500';
    case 'idle':
      return 'bg-gray-400';
    case 'error':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
      return '🔵';
    case 'busy':
      return '🟣';
    case 'idle':
      return '⚪';
    case 'error':
      return '🔴';
    default:
      return '⚫';
  }
};

export function AgentCard({ agent }: { agent: Agent }) {
  const isActive = agent.status === 'active' || agent.status === 'busy';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-xl p-5 shadow-md hover:shadow-lg transition-all duration-300"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="text-2xl">{getStatusIcon(agent.status)}</div>
          <div>
            <h3 className="font-bold text-gray-900 text-lg">{agent.name}</h3>
            <span className={`inline-block px-2 py-1 rounded-full text-xs font-semibold ${
              isActive ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
            }`}>
              {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
            </span>
          </div>
        </div>
        
        {isActive && (
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`}
          />
        )}
      </div>

      {agent.currentTask && (
        <div className="mb-3 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm font-medium text-blue-900">Current Task:</p>
          <p className="text-sm text-blue-700 truncate">{agent.currentTask}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-500 font-medium">Completed</p>
          <p className="text-xl font-bold text-gray-900">{agent.tasksCompleted}</p>
        </div>
        <div>
          <p className="text-gray-500 font-medium">Success Rate</p>
          <p className="text-xl font-bold text-green-600">{agent.successRate}%</p>
        </div>
      </div>

      {agent.lastActivity && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            Last active: {agent.lastActivity}
          </p>
        </div>
      )}
    </motion.div>
  );
}

