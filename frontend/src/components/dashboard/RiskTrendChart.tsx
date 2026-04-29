// Production-grade Risk Trend Chart Component
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { TimeSeriesData } from '../../types';

interface RiskTrendChartProps {
  data: TimeSeriesData[];
  title?: string;
  height?: number;
  loading?: boolean;
  className?: string;
  showArea?: boolean;
}

export const RiskTrendChart: React.FC<RiskTrendChartProps> = ({
  data,
  title = 'Risk Trend Over Time',
  height = 300,
  loading = false,
  className,
  showArea = false,
}) => {
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center" style={{ height }}>
            <LoadingSpinner size="lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div 
            className="flex items-center justify-center text-gray-500 dark:text-gray-400"
            style={{ height }}
          >
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {formatDate(label)}
          </p>
          <p className="text-sm text-indigo-600 dark:text-indigo-400">
            Risk Score: {payload[0].value.toFixed(1)}
          </p>
        </div>
      );
    }
    return null;
  };

  const ChartComponent = showArea ? AreaChart : LineChart;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <ChartComponent data={data}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              className="stroke-gray-200 dark:stroke-gray-700"
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              className="text-gray-600 dark:text-gray-400"
              fontSize={12}
            />
            <YAxis
              domain={[0, 100]}
              className="text-gray-600 dark:text-gray-400"
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            {showArea ? (
              <Area
                type="monotone"
                dataKey="value"
                stroke="#4f46e5"
                strokeWidth={2}
                fill="#4f46e5"
                fillOpacity={0.1}
                dot={{ fill: '#4f46e5', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#4f46e5', strokeWidth: 2 }}
              />
            ) : (
              <Line
                type="monotone"
                dataKey="value"
                stroke="#4f46e5"
                strokeWidth={2}
                dot={{ fill: '#4f46e5', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#4f46e5', strokeWidth: 2 }}
              />
            )}
          </ChartComponent>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Multi-line chart for comparing different categories
interface MultiRiskTrendChartProps {
  data: Array<{
    date: string;
    [key: string]: string | number;
  }>;
  categories: Array<{
    key: string;
    label: string;
    color: string;
  }>;
  title?: string;
  height?: number;
  loading?: boolean;
  className?: string;
}

export const MultiRiskTrendChart: React.FC<MultiRiskTrendChartProps> = ({
  data,
  categories,
  title = 'Risk Trends by Category',
  height = 300,
  loading = false,
  className,
}) => {
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center" style={{ height }}>
            <LoadingSpinner size="lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            {formatDate(label)}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <div className="flex flex-wrap gap-4 mt-2">
          {categories.map((category) => (
            <div key={category.key} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: category.color }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {category.label}
              </span>
            </div>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              className="stroke-gray-200 dark:stroke-gray-700"
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              className="text-gray-600 dark:text-gray-400"
              fontSize={12}
            />
            <YAxis
              domain={[0, 100]}
              className="text-gray-600 dark:text-gray-400"
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            {categories.map((category) => (
              <Line
                key={category.key}
                type="monotone"
                dataKey={category.key}
                stroke={category.color}
                strokeWidth={2}
                dot={{ fill: category.color, strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: category.color, strokeWidth: 2 }}
                name={category.label}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};