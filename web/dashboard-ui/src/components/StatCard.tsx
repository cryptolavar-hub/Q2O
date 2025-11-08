import React from 'react';
import type { StatCard as StatCardType } from '../types/dashboard';

export function StatCard({ title, value, subtitle, icon, trend }: StatCardType) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300">
      <div className="flex items-center justify-between mb-4">
        <div className="text-3xl">{icon}</div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm font-semibold ${
            trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
          }`}>
            <span>{trend.direction === 'up' ? '↑' : '↓'}</span>
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      <h3 className="text-gray-600 text-sm font-medium mb-2">{title}</h3>
      <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  );
}

