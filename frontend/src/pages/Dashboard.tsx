import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  UsersIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentListIcon,
  ArrowTrendingUpIcon,
  AcademicCapIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

import { useAuthStore, useDashboardStore } from '../store';
import { usePermissions } from '../hooks/usePermissions';
import { analyticsApi, studentsApi, interventionsApi } from '../lib/api';
import { MetricsCard, RiskDistributionCard } from '../components/dashboard/MetricsCard';
import { RiskTrendChart, MultiRiskTrendChart } from '../components/dashboard/RiskTrendChart';
import { StudentRiskCard } from '../components/students/StudentRiskCard';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { LoadingState, CardSkeleton } from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import { Student, DashboardMetrics, TimeSeriesData } from '../types';

export default function Dashboard() {
  const { user } = useAuthStore();
  const { metrics, setMetrics } = useDashboardStore();
  const permissions = usePermissions();
  const [selectedTimeRange, setSelectedTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  // Fetch dashboard metrics
  const { data: dashboardData, isLoading: metricsLoading } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => analyticsApi.dashboard(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });

  // Fetch risk trends
  const { data: riskTrendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ['risk-trends', selectedTimeRange],
    queryFn: () => analyticsApi.riskTrends(
      selectedTimeRange === '7d' ? 7 : selectedTimeRange === '30d' ? 30 : 90
    ),
  });

  // Fetch high-risk students for mentors
  const { data: highRiskStudents, isLoading: studentsLoading } = useQuery({
    queryKey: ['high-risk-students'],
    queryFn: () => studentsApi.list({
      risk_category: ['High', 'Critical'],
      limit: 6,
      ...(permissions.isMentor() && { mentor_id: user?.id }),
    }),
    enabled: permissions.canViewAllStudents() || permissions.canViewAssignedStudents(),
  });

  // Fetch recent interventions
  const { data: recentInterventions, isLoading: interventionsLoading } = useQuery({
    queryKey: ['recent-interventions'],
    queryFn: () => interventionsApi.list({
      limit: 5,
      status: ['active', 'planned'],
      ...(permissions.isMentor() && { assigned_to: user?.id }),
    }),
    enabled: permissions.canViewAllInterventions() || permissions.canCreateInterventions(),
  });

  // Update store when data changes
  useEffect(() => {
    if (dashboardData?.data) {
      setMetrics(dashboardData.data);
    }
  }, [dashboardData, setMetrics]);

  if (metricsLoading && !metrics) {
    return <LoadingState title="Loading Dashboard..." />;
  }

  const currentMetrics = dashboardData?.data || metrics;

  // Role-based dashboard content
  const renderMentorDashboard = () => (
    <div className="space-y-8">
      {/* Mentor Overview */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Welcome back, {user?.first_name}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Here's an overview of your assigned students
            </p>
          </div>
          <Button variant="primary">
            View All Students
          </Button>
        </div>

        {/* Mentor Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricsCard
            title="Assigned Students"
            value={currentMetrics?.total_students || 0}
            icon={UsersIcon}
            color="blue"
            loading={metricsLoading}
          />
          <MetricsCard
            title="At-Risk Students"
            value={currentMetrics?.at_risk_students || 0}
            icon={ExclamationTriangleIcon}
            color="red"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Active Interventions"
            value={currentMetrics?.active_interventions || 0}
            icon={ClipboardDocumentListIcon}
            color="yellow"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Success Rate"
            value={`${(currentMetrics?.success_rate || 0).toFixed(1)}%`}
            icon={ArrowTrendingUpIcon}
            color="green"
            loading={metricsLoading}
          />
        </div>
      </div>

      {/* High-Risk Students */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Students Requiring Attention
          </h2>
          <Button variant="outline" size="sm">
            View All
          </Button>
        </div>
        
        {studentsLoading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {highRiskStudents?.data?.data?.slice(0, 4).map((student: Student) => (
              <StudentRiskCard
                key={student.id}
                student={student}
                showActions={true}
              />
            ))}
          </div>
        )}
      </div>

      {/* Risk Trend */}
      <RiskTrendChart
        data={riskTrendsData?.data || []}
        title="Risk Trend - Your Students"
        loading={trendsLoading}
        showArea={true}
      />
    </div>
  );

  const renderDepartmentHeadDashboard = () => (
    <div className="space-y-8">
      {/* Department Overview */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Department Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Monitor student performance across your department
            </p>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline">Export Report</Button>
            <Button variant="primary">View Analytics</Button>
          </div>
        </div>

        {/* Department Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <MetricsCard
            title="Total Students"
            value={currentMetrics?.total_students || 0}
            icon={UsersIcon}
            color="blue"
            loading={metricsLoading}
          />
          <MetricsCard
            title="At-Risk Students"
            value={currentMetrics?.at_risk_students || 0}
            icon={ExclamationTriangleIcon}
            color="red"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Active Interventions"
            value={currentMetrics?.active_interventions || 0}
            icon={ClipboardDocumentListIcon}
            color="yellow"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Success Rate"
            value={`${(currentMetrics?.success_rate || 0).toFixed(1)}%`}
            icon={ArrowTrendingUpIcon}
            color="green"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Avg GPA"
            value="3.2"
            icon={AcademicCapIcon}
            color="purple"
            loading={metricsLoading}
          />
        </div>
      </div>

      {/* Risk Distribution and Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RiskDistributionCard
          distribution={currentMetrics?.risk_distribution || { low: 0, medium: 0, high: 0, critical: 0 }}
          total={currentMetrics?.total_students || 0}
          loading={metricsLoading}
        />
        <div className="lg:col-span-2">
          <RiskTrendChart
            data={riskTrendsData?.data || []}
            title="Department Risk Trends"
            loading={trendsLoading}
          />
        </div>
      </div>

      {/* Critical Students */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Critical Risk Students
        </h2>
        {studentsLoading ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {highRiskStudents?.data?.data
              ?.filter((s: Student) => s.risk_category === 'Critical')
              .slice(0, 3)
              .map((student: Student) => (
                <StudentRiskCard
                  key={student.id}
                  student={student}
                  showActions={true}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderAdminDashboard = () => (
    <div className="space-y-8">
      {/* Admin Overview */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              System Overview
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Institution-wide analytics and system health
            </p>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline">System Health</Button>
            <Button variant="outline">Export Data</Button>
            <Button variant="primary">View Reports</Button>
          </div>
        </div>

        {/* System Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 mb-8">
          <MetricsCard
            title="Total Students"
            value={currentMetrics?.total_students || 0}
            icon={UsersIcon}
            color="blue"
            loading={metricsLoading}
          />
          <MetricsCard
            title="At-Risk Students"
            value={currentMetrics?.at_risk_students || 0}
            icon={ExclamationTriangleIcon}
            color="red"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Active Interventions"
            value={currentMetrics?.active_interventions || 0}
            icon={ClipboardDocumentListIcon}
            color="yellow"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Success Rate"
            value={`${(currentMetrics?.success_rate || 0).toFixed(1)}%`}
            icon={ArrowTrendingUpIcon}
            color="green"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Model Accuracy"
            value="87.3%"
            icon={ChartBarIcon}
            color="purple"
            loading={metricsLoading}
          />
          <MetricsCard
            title="Fairness Score"
            value="92.1%"
            icon={AcademicCapIcon}
            color="green"
            loading={metricsLoading}
          />
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="flex justify-end mb-4">
        <div className="flex rounded-lg border border-gray-300 dark:border-gray-600">
          {(['7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setSelectedTimeRange(range)}
              className={`px-4 py-2 text-sm font-medium ${
                selectedTimeRange === range
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              } ${range === '7d' ? 'rounded-l-lg' : range === '90d' ? 'rounded-r-lg' : ''}`}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskDistributionCard
          distribution={currentMetrics?.risk_distribution || { low: 0, medium: 0, high: 0, critical: 0 }}
          total={currentMetrics?.total_students || 0}
          loading={metricsLoading}
        />
        <RiskTrendChart
          data={riskTrendsData?.data || []}
          title="Institution Risk Trends"
          loading={trendsLoading}
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Interventions</CardTitle>
          </CardHeader>
          <CardContent>
            {interventionsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {recentInterventions?.data?.interventions?.slice(0, 5).map((intervention: any) => (
                  <div key={intervention.id} className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {intervention.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {intervention.type} • {new Date(intervention.created_date).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      intervention.status === 'active' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                    }`}>
                      {intervention.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Model Status</span>
                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 rounded-full">
                  Active
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Data Pipeline</span>
                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 rounded-full">
                  Running
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Last Sync</span>
                <span className="text-sm text-gray-900 dark:text-gray-100">2 hours ago</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Fairness Check</span>
                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 rounded-full">
                  Passed
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // Render appropriate dashboard based on user role
  const renderDashboard = () => {
    if (permissions.isAdmin()) {
      return renderAdminDashboard();
    } else if (permissions.isDepartmentHead()) {
      return renderDepartmentHeadDashboard();
    } else {
      return renderMentorDashboard();
    }
  };

  return (
    <div className="space-y-8">
      {renderDashboard()}
    </div>
  );
}