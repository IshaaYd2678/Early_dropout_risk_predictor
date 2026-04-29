// Production-grade Badge Component for Risk Categories
import React from 'react';
import { clsx } from 'clsx';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  pulse?: boolean;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ 
    className, 
    variant = 'default', 
    size = 'md', 
    dot = false, 
    pulse = false,
    children, 
    ...props 
  }, ref) => {
    const baseClasses = [
      'inline-flex items-center font-medium rounded-full',
      'transition-all duration-200',
    ];

    const variantClasses = {
      default: [
        'bg-gray-100 text-gray-800',
        'dark:bg-gray-800 dark:text-gray-200',
      ],
      success: [
        'bg-green-100 text-green-800',
        'dark:bg-green-900/20 dark:text-green-400',
      ],
      warning: [
        'bg-yellow-100 text-yellow-800',
        'dark:bg-yellow-900/20 dark:text-yellow-400',
      ],
      danger: [
        'bg-red-100 text-red-800',
        'dark:bg-red-900/20 dark:text-red-400',
      ],
      info: [
        'bg-blue-100 text-blue-800',
        'dark:bg-blue-900/20 dark:text-blue-400',
      ],
      secondary: [
        'bg-purple-100 text-purple-800',
        'dark:bg-purple-900/20 dark:text-purple-400',
      ],
    };

    const sizeClasses = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
      lg: 'px-3 py-1.5 text-base',
    };

    const dotClasses = {
      sm: 'h-1.5 w-1.5',
      md: 'h-2 w-2',
      lg: 'h-2.5 w-2.5',
    };

    return (
      <span
        ref={ref}
        className={clsx(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={clsx(
              'rounded-full mr-1.5',
              dotClasses[size],
              pulse && 'animate-pulse',
              // Dot colors based on variant
              variant === 'success' && 'bg-green-600 dark:bg-green-400',
              variant === 'warning' && 'bg-yellow-600 dark:bg-yellow-400',
              variant === 'danger' && 'bg-red-600 dark:bg-red-400',
              variant === 'info' && 'bg-blue-600 dark:bg-blue-400',
              variant === 'secondary' && 'bg-purple-600 dark:bg-purple-400',
              variant === 'default' && 'bg-gray-600 dark:bg-gray-400',
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

// Risk-specific badge component
interface RiskBadgeProps extends Omit<BadgeProps, 'variant'> {
  riskCategory: 'Low' | 'Medium' | 'High' | 'Critical';
  showDot?: boolean;
}

export const RiskBadge = React.forwardRef<HTMLSpanElement, RiskBadgeProps>(
  ({ riskCategory, showDot = true, ...props }, ref) => {
    const variantMap = {
      Low: 'success' as const,
      Medium: 'warning' as const,
      High: 'danger' as const,
      Critical: 'danger' as const,
    };

    return (
      <Badge
        ref={ref}
        variant={variantMap[riskCategory]}
        dot={showDot}
        pulse={riskCategory === 'Critical'}
        {...props}
      >
        {riskCategory} Risk
      </Badge>
    );
  }
);

RiskBadge.displayName = 'RiskBadge';

export default Badge;