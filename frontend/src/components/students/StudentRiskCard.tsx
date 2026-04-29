// Production-grade Student Risk Card Component
import React from 'react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  ExclamationTriangleIcon,
  ChartBarIcon,
  ClockIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import { Card, CardContent } from '../ui/Card';
import { RiskBadge } from '../ui/Badge';
import Button from '../ui/Button';
import { Student } from '../../types';

interface StudentRiskCardProps {
  student: Student;
  showActions?: boolean;
  onPredictRisk?: (studentId: string) => void;
  onCreateIntervention?: (studentId: string) => void;
  className?: string;
}

export const StudentRiskCard: React.FC<StudentRiskCardProps> = ({
  student,
  showActions = true,
  onPredictRisk,
  onCreateIntervention,
  className,
}) => {
  const getRiskColor = (category: string) => {
    switch (category) {
      case 'Low': return 'text-green-600 dark:text-green-400';
      case 'Medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'High': return 'text-orange-600 dark:text-orange-400';
      case 'Critical': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getRiskIcon = (category: string) => {
    if (category === 'Critical' || category === 'High') {
      return ExclamationTriangleIcon;
    }
    return ChartBarIcon;
  };

  const RiskIcon = getRiskIcon(student.risk_category);
  const lastPrediction = new Date(student.last_prediction_date);
  const isStaleData = Date.now() - lastPrediction.getTime() > 7 * 24 * 60 * 60 * 1000; // 7 days

  return (
    <Card className={clsx(
      'hover:shadow-lg transition-all duration-200 hover:-translate-y-0.5',
      student.risk_category === 'Critical' && 'ring-2 ring-red-200 dark:ring-red-800',
      className
    )}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            {/* Avatar */}
            <div className="flex-shrink-0">
              <div className="h-12 w-12 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                <UserIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
              </div>
            </div>

            {/* Student Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <Link
                  to={`/students/${student.id}`}
                  className="text-lg font-semibold text-gray-900 dark:text-gray-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                >
                  {student.first_name} {student.last_name}
                </Link>
                {student.risk_category === 'Critical' && (
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500 animate-pulse" />
                )}
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {student.student_id} • {student.department}
              </p>
              
              <div className="flex items-center space-x-4 mt-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Year {student.year} • Semester {student.semester}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  GPA: {student.academic_metrics.gpa.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Risk Score */}
          <div className="flex flex-col items-end space-y-2">
            <div className="flex items-center space-x-2">
              <RiskIcon className={clsx('h-5 w-5', getRiskColor(student.risk_category))} />
              <span className={clsx('text-2xl font-bold', getRiskColor(student.risk_category))}>
                {student.current_risk_score}
              </span>
            </div>
            <RiskBadge riskCategory={student.risk_category} size="sm" />
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {(student.academic_metrics.attendance_rate * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Attendance</p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {(student.academic_metrics.assignment_submission_rate * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Submissions</p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {student.engagement_metrics.lms_login_frequency}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">LMS Logins</p>
          </div>
        </div>

        {/* Last Prediction Date */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-4 w-4 text-gray-400" />
            <span className={clsx(
              'text-xs',
              isStaleData 
                ? 'text-orange-600 dark:text-orange-400' 
                : 'text-gray-500 dark:text-gray-400'
            )}>
              Last updated: {lastPrediction.toLocaleDateString()}
              {isStaleData && ' (Stale)'}
            </span>
          </div>

          {showActions && (
            <div className="flex items-center space-x-2">
              {onPredictRisk && (
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => onPredictRisk(student.id)}
                  disabled={!isStaleData}
                >
                  Update Risk
                </Button>
              )}
              {onCreateIntervention && (
                <Button
                  size="xs"
                  variant={student.risk_category === 'Critical' ? 'danger' : 'primary'}
                  onClick={() => onCreateIntervention(student.id)}
                >
                  Intervene
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Compact version for lists
interface StudentRiskRowProps {
  student: Student;
  onSelect?: (student: Student) => void;
  selected?: boolean;
  className?: string;
}

export const StudentRiskRow: React.FC<StudentRiskRowProps> = ({
  student,
  onSelect,
  selected = false,
  className,
}) => {
  const getRiskColor = (category: string) => {
    switch (category) {
      case 'Low': return 'text-green-600 dark:text-green-400';
      case 'Medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'High': return 'text-orange-600 dark:text-orange-400';
      case 'Critical': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  return (
    <div
      className={clsx(
        'flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700',
        'hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer',
        selected && 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-800',
        className
      )}
      onClick={() => onSelect?.(student)}
    >
      <div className="flex items-center space-x-4">
        <div className="h-10 w-10 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
          <UserIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {student.first_name} {student.last_name}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {student.student_id} • {student.department}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-xs text-gray-500 dark:text-gray-400">GPA</p>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {student.academic_metrics.gpa.toFixed(2)}
          </p>
        </div>
        
        <div className="text-right">
          <p className="text-xs text-gray-500 dark:text-gray-400">Risk Score</p>
          <p className={clsx('text-lg font-bold', getRiskColor(student.risk_category))}>
            {student.current_risk_score}
          </p>
        </div>
        
        <RiskBadge riskCategory={student.risk_category} size="sm" />
      </div>
    </div>
  );
};