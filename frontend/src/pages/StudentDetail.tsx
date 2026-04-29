import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { studentsApi, predictionsApi } from '../lib/api';
import toast from 'react-hot-toast';

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', id],
    queryFn: () => studentsApi.get(id!).then(r => r.data),
    enabled: !!id,
  });

  const { data: riskHistory } = useQuery({
    queryKey: ['risk-history', id],
    queryFn: () => studentsApi.getRiskHistory(id!).then(r => r.data),
    enabled: !!id,
  });

  const predictMutation = useMutation({
    mutationFn: () => predictionsApi.single(id!),
    onSuccess: (data) => {
      toast.success(`Risk assessed: ${data.data.risk_level}`);
    },
    onError: () => {
      toast.error('Failed to assess risk');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!student) {
    return <div>Student not found</div>;
  }

  const riskColors: Record<string, string> = {
    low: 'bg-green-500',
    medium: 'bg-yellow-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/students" className="text-gray-500 hover:text-gray-700">
          <ArrowLeftIcon className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {student.first_name} {student.last_name}
          </h1>
          <p className="text-sm text-gray-500">Student ID: {student.student_id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Dropout Risk Assessment</h2>
              <button
                onClick={() => predictMutation.mutate()}
                disabled={predictMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {predictMutation.isPending ? 'Analyzing...' : 'Analyze Risk'}
              </button>
            </div>

            {student.current_risk_score !== null && (
              <div className="flex items-center gap-8">
                <div className="relative w-32 h-32">
                  <svg className="w-32 h-32 transform -rotate-90">
                    <circle
                      className="text-gray-200"
                      strokeWidth="8"
                      stroke="currentColor"
                      fill="transparent"
                      r="56"
                      cx="64"
                      cy="64"
                    />
                    <circle
                      className={student.current_risk_level === 'critical' ? 'text-red-500' :
                                 student.current_risk_level === 'high' ? 'text-orange-500' :
                                 student.current_risk_level === 'medium' ? 'text-yellow-500' : 'text-green-500'}
                      strokeWidth="8"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="transparent"
                      r="56"
                      cx="64"
                      cy="64"
                      strokeDasharray={`${student.current_risk_score * 352} 352`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold">{Math.round(student.current_risk_score * 100)}%</span>
                  </div>
                </div>
                <div>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    student.current_risk_level === 'critical' ? 'bg-red-100 text-red-800' :
                    student.current_risk_level === 'high' ? 'bg-orange-100 text-orange-800' :
                    student.current_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                  }`}>
                    {student.current_risk_level?.toUpperCase()} RISK
                  </span>
                  <p className="mt-2 text-sm text-gray-500">
                    Last updated: {student.risk_updated_at ? new Date(student.risk_updated_at).toLocaleDateString() : 'Never'}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Academic Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Academic Performance</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">GPA</p>
                <p className="text-2xl font-semibold">{student.gpa?.toFixed(2) || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Attendance</p>
                <p className="text-2xl font-semibold">{student.attendance_rate ? `${(student.attendance_rate * 100).toFixed(0)}%` : '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Submission Rate</p>
                <p className="text-2xl font-semibold">{student.assignment_submission_rate ? `${(student.assignment_submission_rate * 100).toFixed(0)}%` : '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Exam Scores</p>
                <p className="text-2xl font-semibold">{student.exam_scores?.toFixed(0) || '-'}</p>
              </div>
            </div>
          </div>

          {/* Engagement Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Engagement Metrics</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">LMS Logins</p>
                <p className="text-2xl font-semibold">{student.lms_login_frequency}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Forum Posts</p>
                <p className="text-2xl font-semibold">{student.forum_posts}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Late Submissions</p>
                <p className="text-2xl font-semibold">{student.late_submissions}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Time on Platform</p>
                <p className="text-2xl font-semibold">{student.time_spent_hours?.toFixed(1)}h</p>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Student Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Student Information</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-500">Department</dt>
                <dd className="text-sm font-medium text-gray-900">{student.department}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Program</dt>
                <dd className="text-sm font-medium text-gray-900">{student.program || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Semester</dt>
                <dd className="text-sm font-medium text-gray-900">{student.semester}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="text-sm font-medium text-gray-900 capitalize">{student.status}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Email</dt>
                <dd className="text-sm font-medium text-gray-900">{student.email || '-'}</dd>
              </div>
            </dl>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Actions</h2>
            <div className="space-y-2">
              <Link
                to={`/interventions?student_id=${student.id}`}
                className="block w-full px-4 py-2 text-center bg-indigo-50 text-indigo-600 rounded-md hover:bg-indigo-100"
              >
                View Interventions
              </Link>
              <Link
                to={`/interventions/new?student_id=${student.id}`}
                className="block w-full px-4 py-2 text-center bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Create Intervention
              </Link>
            </div>
          </div>

          {/* Risk History */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Risk History</h2>
            {riskHistory?.length > 0 ? (
              <div className="space-y-3">
                {riskHistory.slice(0, 5).map((score: any) => (
                  <div key={score.id} className="flex items-center justify-between">
                    <div>
                      <span className={`inline-block w-2 h-2 rounded-full mr-2 ${riskColors[score.risk_level]}`}></span>
                      <span className="text-sm text-gray-900">{(score.risk_score * 100).toFixed(0)}%</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(score.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No risk history available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
