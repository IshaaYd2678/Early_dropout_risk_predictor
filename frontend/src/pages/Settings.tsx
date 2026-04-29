import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminApi, predictionsApi } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function Settings() {
  const { user } = useAuth();

  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => adminApi.getTenant().then(r => r.data),
  });

  const { data: modelInfo } = useQuery({
    queryKey: ['model-info'],
    queryFn: () => predictionsApi.modelInfo().then(r => r.data),
  });

  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account and platform settings
        </p>
      </div>

      {/* Profile */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Profile</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <p className="mt-1 text-sm text-gray-900">{user?.first_name} {user?.last_name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Role</label>
            <p className="mt-1 text-sm text-gray-900 capitalize">{user?.role?.replace('_', ' ')}</p>
          </div>
        </div>
      </div>

      {/* Institution (Admin only) */}
      {isAdmin && tenant && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Institution</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <p className="mt-1 text-sm text-gray-900">{tenant.name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Plan</label>
              <p className="mt-1 text-sm text-gray-900 capitalize">{tenant.plan}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Students</label>
              <p className="mt-1 text-sm text-gray-900">{tenant.student_count} / {tenant.max_students}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Users</label>
              <p className="mt-1 text-sm text-gray-900">{tenant.user_count} / {tenant.max_users}</p>
            </div>
          </div>
        </div>
      )}

      {/* Model Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">ML Model</h2>
        {modelInfo?.model_available ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Version</label>
              <p className="mt-1 text-sm text-gray-900">{modelInfo.version}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Deployed</label>
              <p className="mt-1 text-sm text-gray-900">
                {modelInfo.deployed_at ? new Date(modelInfo.deployed_at).toLocaleDateString() : '-'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Accuracy</label>
              <p className="mt-1 text-sm text-gray-900">
                {modelInfo.accuracy ? (modelInfo.accuracy * 100).toFixed(1) + '%' : '-'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">AUC-ROC</label>
              <p className="mt-1 text-sm text-gray-900">
                {modelInfo.auc_roc ? modelInfo.auc_roc.toFixed(3) : '-'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Bias Status</label>
              <p className={`mt-1 text-sm font-medium ${modelInfo.bias_detected ? 'text-yellow-600' : 'text-green-600'}`}>
                {modelInfo.bias_detected ? 'Potential bias detected' : 'No bias detected'}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No model deployed</p>
        )}
      </div>

      {/* Security */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Security</h2>
        <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">
          Change Password
        </button>
      </div>
    </div>
  );
}
