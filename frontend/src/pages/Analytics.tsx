import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../lib/api';

export default function Analytics() {
  const { data: effectiveness } = useQuery({
    queryKey: ['intervention-effectiveness'],
    queryFn: () => analyticsApi.interventionEffectiveness().then(r => r.data),
  });

  const { data: departments } = useQuery({
    queryKey: ['department-analytics'],
    queryFn: () => analyticsApi.departments().then(r => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">
          Deep insights into student retention patterns
        </p>
      </div>

      {/* Intervention Effectiveness */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Intervention Effectiveness</h2>
        <div className="space-y-4">
          {effectiveness?.map((item: any) => (
            <div key={item.intervention_type} className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 capitalize">
                  {item.intervention_type.replace('_', ' ')}
                </p>
                <p className="text-xs text-gray-500">{item.total_count} interventions</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${item.success_rate}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900 w-12">
                  {item.success_rate}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Department Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Department Risk Analysis</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Students</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">At Risk</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">At Risk %</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Avg Risk Score</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Interventions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {departments?.map((dept: any) => (
                <tr key={dept.department}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{dept.department}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{dept.total_students}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{dept.at_risk_count}</td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-medium ${
                      dept.at_risk_percentage > 30 ? 'text-red-600' :
                      dept.at_risk_percentage > 15 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {dept.at_risk_percentage}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {dept.avg_risk_score ? (dept.avg_risk_score * 100).toFixed(1) + '%' : '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">{dept.interventions_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
