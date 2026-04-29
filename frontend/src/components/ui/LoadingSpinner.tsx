// Production-grade Loading Components
import React from 'react';
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'white' | 'gray';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'primary',
  className,
}) => {
  const sizeClasses = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  const colorClasses = {
    primary: 'text-indigo-600',
    secondary: 'text-gray-600',
    white: 'text-white',
    gray: 'text-gray-400',
  };

  return (
    <svg
      className={clsx(
        'animate-spin',
        sizeClasses[size],
        colorClasses[color],
        className
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
  );
};

interface LoadingStateProps {
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = 'Loading...',
  description,
  size = 'md',
  className,
}) => {
  const containerClasses = {
    sm: 'py-8',
    md: 'py-12',
    lg: 'py-16',
  };

  const spinnerSizes = {
    sm: 'md' as const,
    md: 'lg' as const,
    lg: 'xl' as const,
  };

  return (
    <div className={clsx(
      'flex flex-col items-center justify-center text-center',
      containerClasses[size],
      className
    )}>
      <LoadingSpinner size={spinnerSizes[size]} />
      <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-gray-100">
        {title}
      </h3>
      {description && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          {description}
        </p>
      )}
    </div>
  );
};

interface SkeletonProps {
  className?: string;
  lines?: number;
  avatar?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  lines = 1,
  avatar = false,
}) => {
  return (
    <div className={clsx('animate-pulse', className)}>
      {avatar && (
        <div className="flex items-center space-x-4 mb-4">
          <div className="rounded-full bg-gray-300 dark:bg-gray-600 h-10 w-10" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4" />
            <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2" />
          </div>
        </div>
      )}
      
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={clsx(
              'h-4 bg-gray-300 dark:bg-gray-600 rounded',
              i === lines - 1 ? 'w-2/3' : 'w-full'
            )}
          />
        ))}
      </div>
    </div>
  );
};

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({
  rows = 5,
  columns = 4,
  className,
}) => {
  return (
    <div className={clsx('animate-pulse', className)}>
      {/* Header */}
      <div className="flex space-x-4 mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        {Array.from({ length: columns }).map((_, i) => (
          <div
            key={i}
            className="h-4 bg-gray-300 dark:bg-gray-600 rounded flex-1"
          />
        ))}
      </div>
      
      {/* Rows */}
      <div className="space-y-4">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="flex space-x-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div
                key={colIndex}
                className={clsx(
                  'h-4 bg-gray-300 dark:bg-gray-600 rounded flex-1',
                  colIndex === 0 && 'w-1/4',
                  colIndex === columns - 1 && 'w-1/6'
                )}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

interface CardSkeletonProps {
  className?: string;
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({ className }) => {
  return (
    <div className={clsx(
      'animate-pulse bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6',
      className
    )}>
      <div className="flex items-center space-x-4 mb-4">
        <div className="rounded-full bg-gray-300 dark:bg-gray-600 h-12 w-12" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4" />
          <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2" />
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-full" />
        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-5/6" />
        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-4/6" />
      </div>
      
      <div className="mt-6 flex space-x-2">
        <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-20" />
        <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-24" />
      </div>
    </div>
  );
};