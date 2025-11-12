import React from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { cn } from './utils';

export interface StatTrend {
  value: number;
  direction: 'up' | 'down';
  label?: string;
}

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: StatTrend;
  action?: React.ReactNode;
  className?: string;
}

const trendClasses: Record<StatTrend['direction'], string> = {
  up: 'text-green-600 bg-green-50 border-green-200',
  down: 'text-red-600 bg-red-50 border-red-200',
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  action,
  className,
}) => {
  return (
    <Card className={cn('flex flex-col gap-4', className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500 uppercase tracking-wide">
            {icon && <span className="text-xl leading-none">{icon}</span>}
            <span>{title}</span>
          </div>
          <div className="flex items-end gap-3">
            <p className="text-4xl font-bold text-gray-900 leading-tight">{value}</p>
            {trend && (
              <Badge
                variant={trend.direction === 'up' ? 'success' : 'error'}
                className={cn('text-xs font-semibold', trendClasses[trend.direction])}
              >
                {trend.direction === 'up' ? '↑' : '↓'} {Math.abs(trend.value).toFixed(1)}%
              </Badge>
            )}
          </div>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
    </Card>
  );
};

StatCard.displayName = 'StatCard';

export default StatCard;
