import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../lib/api';
import { ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export default function Fairness() {
  const { data: fairnessMetrics, isLoading } = useQuery({
    queryKey: ['fairness'],
    queryFn: () => analyticsApi.fairness().then(r => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fairness & Bias Analysis</h1>
        <p className="mt-1 text-sm text-gray-500">
          Ensuring equitable predictions across all student demographics
        </p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">About Fairness Metrics</h3>
            <p className="mt-1 text-sm text-blue-700">
              We monitor predictions across demographic groups to ensure the model doesn't discriminate. 
              Demographic parity measures if flagging rates are equal; equal opportunity measures if 
              true positive rates are equal across groups.
            </p>
          </div>
        </div>
      </div>

      {/* Fairness Metrics */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="space-y-6">
          {fairnessMetrics?.map((metric: any) => (
            <div key={metric.attribute} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900 capitalize">
                  {metric.attribute.replace('_', ' ')}
                </h2>
                {metric.bias_detected ? (
                  <span className="flex items-center text-yellow-600">
                    <ExclamationTriangleIcon className="h-5 w-5 mr-1" />
                    Potential bias detected
                  </span>
                ) : (
                  <span className="flex items-center text-green-600">
                    <CheckCircleIcon className="h-5 w-5 mr-1" />
                    Within acceptable range
                  </span>
                )}
              </div>

              {/* Metrics Summary */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Demographic Parity Difference</p>
                  <p className={`text-2xl font-bold ${
                    metric.parity_difference > 0.1 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {(metric.parity_difference * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Target: &lt;10%</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Equal Opportunity Difference</p>
                  <p className={`text-2xl font-bold ${
                    metric.equal_opportunity_difference > 0.1 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {(metric.equal_opportunity_difference * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Target: &lt;10%</p>
                </div>
              </div>

              {/* Group Breakdown */}
              <h3 className="text-sm font-medium text-gray-700 mb-2">Group Breakdown</h3>
              <div className="space-y-2">
                {metric.groups?.map((group: any) => (
                  <div key={group.group} className="flex items-center justify-between py-2 border-b border-gray-100">
                    <div>
                      <span className="text-sm font-medium text-gray-900">{group.group}</span>
                      <span className="text-xs text-gray-500 ml-2">({group.count} students)</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div>
                        <span className="text-xs text-gray-500">Avg Risk: </span>
                        <span className="text-sm font-medium">
                          {group.avg_risk ? (group.avg_risk * 100).toFixed(1) + '%' : '-'}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500">Flagged: </span>
                        <span className="text-sm font-medium">
                          {(group.flagged_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Compliance Note */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Compliance & Transparency</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          <li>• Sensitive attributes (gender, socioeconomic status) are NOT used directly as predictors</li>
          <li>• All predictions are logged and auditable</li>
          <li>• Human-in-the-loop: Mentors review and approve interventions</li>
          <li>• Fairness metrics are recalculated with each model update</li>
          <li>• FERPA and GDPR compliant data handling</li>
        </ul>
      </div>
    </div>
  );
}
