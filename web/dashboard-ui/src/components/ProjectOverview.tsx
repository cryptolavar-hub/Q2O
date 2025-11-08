import React from 'react';
import { motion } from 'framer-motion';

interface ProjectOverviewProps {
  project: {
    name: string;
    status: string;
    progress: number;
    estimatedTimeRemaining?: number;
  };
}

export function ProjectOverview({ project }: ProjectOverviewProps) {
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-2xl p-6 shadow-lg mb-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
          <p className="text-sm text-gray-600 mt-1">
            Status: <span className="font-semibold text-blue-600">{project.status}</span>
          </p>
        </div>
        {project.estimatedTimeRemaining !== undefined && project.estimatedTimeRemaining > 0 && (
          <div className="text-right">
            <p className="text-sm text-gray-600">Est. Time Remaining</p>
            <p className="text-2xl font-bold text-purple-600">
              {formatTime(project.estimatedTimeRemaining)}
            </p>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-2">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-lg font-bold bg-gradient-main bg-clip-text text-transparent">
            {project.progress}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
          <motion.div
            className="h-full bg-gradient-main shadow-md"
            initial={{ width: 0 }}
            animate={{ width: `${project.progress}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          >
            {project.progress > 10 && (
              <div className="h-full flex items-center justify-end pr-2">
                <span className="text-xs font-bold text-white drop-shadow">
                  {project.progress}%
                </span>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

