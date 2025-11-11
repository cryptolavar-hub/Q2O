import React from 'react';
import { cn } from './utils';

type BadgeVariant = 'neutral' | 'success' | 'warning' | 'error' | 'info';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  pill?: boolean;
}

const variantClasses: Record<BadgeVariant, string> = {
  neutral: 'bg-gray-100 text-gray-700 border border-gray-200',
  success: 'bg-green-100 text-green-700 border border-green-200',
  warning: 'bg-amber-100 text-amber-700 border border-amber-200',
  error: 'bg-red-100 text-red-700 border border-red-200',
  info: 'bg-blue-100 text-blue-700 border border-blue-200',
};

export const Badge: React.FC<BadgeProps> = ({ variant = 'neutral', pill = true, className, children, ...rest }) => {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide',
        pill ? 'rounded-full' : 'rounded-md',
        variantClasses[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
};

Badge.displayName = 'Badge';

export default Badge;
