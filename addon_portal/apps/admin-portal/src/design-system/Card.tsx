import React from 'react';
import { gradients } from './tokens';
import { cn } from './utils';

type CardVariant = 'default' | 'soft' | 'glass';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  elevated?: boolean;
  padded?: boolean;
}

const baseClasses = 'rounded-2xl transition-all duration-300 relative overflow-hidden';

const variantClasses: Record<CardVariant, string> = {
  default: 'bg-white border border-gray-200/70 backdrop-blur-sm',
  soft: 'bg-white/70 backdrop-blur-sm border border-white/40',
  glass: 'bg-white/15 border border-white/30 backdrop-blur-lg text-white',
};

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  elevated = true,
  padded = true,
  className,
  children,
  ...rest
}) => {
  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        elevated && variant !== 'glass' ? 'shadow-lg hover:shadow-xl' : '',
        elevated && variant === 'glass' ? 'shadow-xl shadow-purple-900/15' : '',
        padded ? 'p-6' : '',
        className,
      )}
      {...rest}
    >
      {variant === 'glass' ? (
        <div className="relative z-10">{children}</div>
      ) : (
        children
      )}
      {variant === 'glass' && (
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-2xl opacity-80"
          style={{ background: gradients.subtle }}
        />
      )}
    </div>
  );
};

Card.displayName = 'Card';

export default Card;
