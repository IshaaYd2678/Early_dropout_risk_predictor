// Production-grade Button Component with Accessibility
import React from 'react';
import { clsx } from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = 'primary',
    size = 'md',
    loading = false,
    leftIcon,
    rightIcon,
    fullWidth = false,
    disabled,
    children,
    ...props
  }, ref) => {
    const baseClasses = [
      'inline-flex items-center justify-center font-medium rounded-lg',
      'transition-all duration-200 ease-in-out',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'active:scale-[0.98]',
    ];

    const variantClasses = {
      primary: [
        'bg-indigo-600 text-white shadow-sm',
        'hover:bg-indigo-700 focus:ring-indigo-500',
        'dark:bg-indigo-500 dark:hover:bg-indigo-600',
      ],
      secondary: [
        'bg-gray-100 text-gray-900 shadow-sm',
        'hover:bg-gray-200 focus:ring-gray-500',
        'dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700',
      ],
      outline: [
        'border border-gray-300 bg-white text-gray-700 shadow-sm',
        'hover:bg-gray-50 focus:ring-indigo-500',
        'dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300',
        'dark:hover:bg-gray-700',
      ],
      ghost: [
        'text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
        'dark:text-gray-300 dark:hover:bg-gray-800',
      ],
      danger: [
        'bg-red-600 text-white shadow-sm',
        'hover:bg-red-700 focus:ring-red-500',
        'dark:bg-red-500 dark:hover:bg-red-600',
      ],
    };

    const sizeClasses = {
      xs: 'px-2.5 py-1.5 text-xs',
      sm: 'px-3 py-2 text-sm',
      md: 'px-4 py-2.5 text-sm',
      lg: 'px-6 py-3 text-base',
      xl: 'px-8 py-4 text-lg',
    };

    const iconSizeClasses = {
      xs: 'h-3 w-3',
      sm: 'h-4 w-4',
      md: 'h-4 w-4',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    };

    return (
      <button
        ref={ref}
        className={clsx(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className={clsx(
              'animate-spin -ml-1 mr-2',
              iconSizeClasses[size]
            )}
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        
        {!loading && leftIcon && (
          <span className={clsx('mr-2', iconSizeClasses[size])}>
            {leftIcon}
          </span>
        )}
        
        {children}
        
        {!loading && rightIcon && (
          <span className={clsx('ml-2', iconSizeClasses[size])}>
            {rightIcon}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;