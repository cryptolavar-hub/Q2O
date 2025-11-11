import React from 'react';
import { gradients } from './tokens';
import { cn } from './utils';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'text-white shadow-lg hover:shadow-xl focus:ring-2 focus:ring-purple-300',
  secondary:
    'bg-white/80 text-purple-700 border border-purple-200 hover:bg-white focus:ring-2 focus:ring-purple-200',
  outline:
    'border border-gray-300 text-gray-700 hover:border-purple-300 hover:text-purple-600 focus:ring-2 focus:ring-purple-200',
  ghost:
    'text-gray-600 hover:text-purple-600 hover:bg-purple-50 focus:ring-2 focus:ring-purple-100',
  destructive:
    'bg-red-500 text-white hover:bg-red-600 focus:ring-2 focus:ring-red-300',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'text-sm px-3 py-2 rounded-xl',
  md: 'text-sm px-4 py-2.5 rounded-xl',
  lg: 'text-base px-5 py-3 rounded-2xl',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled,
      leftIcon,
      rightIcon,
      className,
      children,
      ...rest
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        className={cn(
          'relative inline-flex items-center justify-center font-semibold transition-all duration-200 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60',
          sizeClasses[size],
          variantClasses[variant],
          className,
        )}
        style={variant === 'primary' ? { background: gradients.brand } : undefined}
        disabled={isDisabled}
        {...rest}
      >
        {loading && (
          <span className="absolute inset-0 flex items-center justify-center">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          </span>
        )}
        <span className={cn('flex items-center gap-2', loading ? 'opacity-0' : 'opacity-100')}>
          {leftIcon && <span className="text-lg leading-none">{leftIcon}</span>}
          <span>{children}</span>
          {rightIcon && <span className="text-lg leading-none">{rightIcon}</span>}
        </span>
      </button>
    );
  },
);

Button.displayName = 'Button';

export default Button;
