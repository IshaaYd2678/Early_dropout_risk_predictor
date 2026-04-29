// Production-grade Metrics Card Component
import React from 'react';
import { clsx } from 'clsx';
import { Card, CardContent } from '../ui/Card';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface MetricsCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
    period: string;
  };
  icon?: React.ComponentType<{ className?: string }>;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gray';
  loading?: boolean;
  className?: string;
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    icon: 'text-blue-600 dark:text-blue-400',
    text: 'text-blue-900 dark:text-blue-100',
  },
  green: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    icon: 'text-green-600 dark:text-green-400',
    text: 'text-green-900 dark:text-green-100',
  },
  yellow: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    icon: 'text-yellow-600 dark:text-yellow-400',
    text: 'text-yellow-900 dark:text-yellow-100',
  },
  red: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    icon: 'text-red-600 dark:text-red-400',
    text: 'text-red-900 dark:text-red-100',
  },
  purple: {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    icon: 'text-purple-600 dark:text-purple-400',
    text: 'text-purple-900 dark:text-purple-100',
  },
  gray: {
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    icon: 'text-gray-600 dark:text-gray-400',
    text: 'text-gray-900 dark:text-gray-100',
  },
};

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  change,
  icon: Icon,
  color = 'blue',
  loading = false,
  className,
}) => {
  const colors = colorClasses[color];

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-20">
            <LoadingSpinner size="md" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={clsx('hover:shadow-md transition-shadow', className)}>
      <CardContent className="p-6">
        <div className="flex items-center">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            <p className={clsx(
              'text-2xl font-bold mt-2',
              colors.text
            )}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
            
            {change && (
              <div className="flex items-center mt-2">
                <span className={clsx(
                  'text-sm font-medium',
                  change.type === 'increase' 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                )}>
                  {change.type === 'increase' ? '+' : '-'}{Math.abs(change.value)}%
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                  vs {change.period}
                </span>
              </div>
            )}
          </div>
          
          {Icon && (
            <div className={clsx(
              'flex-shrink-0 p-3 rounded-lg',
              colors.bg
            )}>
              <Icon className={clsx('h-6 w-6', colors.icon)} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Specialized Risk Distribution Card
interface RiskDistributionCardProps {
  distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  total: number;
  loading?: boolean;
  className?: string;
}

export const RiskDistributionCard: React.FC<RiskDistributionCardProps> = ({
  distribution,
  total,
  loading = false,
  className,
}) => {
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size="md" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const riskLevels = [
    { key: 'low', label: 'Low Risk', value: distribution.low, color: 'bg-green-500' },
    { key: 'medium', label: 'Medium Risk', value: distribution.medium, color: 'bg-yellow-500' },
    { key: 'high', label: 'High Risk', value: distribution.high, color: 'bg-orange-500' },
    { key: 'critical', label: 'Critical Risk', value: distribution.critical, color: 'bg-red-500' },
  ];

  return (
    <Card className={clsx('hover:shadow-md transition-shadow', className)}>
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Risk Distribution
        </h3>
        
        <div className="space-y-3">
          {riskLevels.map((level) => {
            const percentage = total > 0 ? (level.value / total) * 100 : 0;
            
            return (
              <div key={level.key} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={clsx('w-3 h-3 rounded-full', level.color)} />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {level.label}
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                    {level.value}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    ({percentage.toFixed(1)}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Progress bar */}
        <div className="mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
          <div className="flex h-full">
            {riskLevels.map((level) => {
              const width = total > 0 ? (level.value / total) * 100 : 0;
              return (
                <div
                  key={level.key}
                  className={level.color}
                  style={{ width: `${width}%` }}
                />
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};