import axios from 'axios';
import { mockApiResponses } from './mockData';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || true; // Enable mock data for demo

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);

          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// Helper function to use mock data in development
const useMockOrApi = <T>(mockFn: () => Promise<T>, apiFn: () => Promise<T>): Promise<T> => {
  return USE_MOCK_DATA ? mockFn() : apiFn();
};

// API functions
export const studentsApi = {
  list: (params?: any) => useMockOrApi(
    () => mockApiResponses.highRiskStudents(),
    () => api.get('/students', { params })
  ),
  get: (id: string) => api.get(`/students/${id}`),
  create: (data: any) => api.post('/students', data),
  update: (id: string, data: any) => api.patch(`/students/${id}`, data),
  getRiskHistory: (id: string) => api.get(`/students/${id}/risk-history`),
  getSummary: () => api.get('/students/stats/summary'),
};

export const predictionsApi = {
  single: (studentId: string) => api.post('/predictions/single', { student_id: studentId }),
  batch: (studentIds: string[]) => api.post('/predictions/batch', { student_ids: studentIds }),
  globalInsights: () => api.get('/predictions/insights/global'),
  modelInfo: () => api.get('/predictions/model/info'),
};

export const interventionsApi = {
  list: (params?: any) => useMockOrApi(
    () => mockApiResponses.interventions(),
    () => api.get('/interventions', { params })
  ),
  get: (id: string) => api.get(`/interventions/${id}`),
  create: (data: any) => api.post('/interventions', data),
  update: (id: string, data: any) => api.patch(`/interventions/${id}`, data),
  recordOutcome: (id: string, data: any) => api.post(`/interventions/${id}/outcome`, data),
  addFollowup: (id: string, data: any) => api.post(`/interventions/${id}/followup`, data),
  getStats: () => api.get('/interventions/stats/summary'),
};

export const analyticsApi = {
  dashboard: () => useMockOrApi(
    () => mockApiResponses.dashboard(),
    () => api.get('/analytics/dashboard')
  ),
  riskTrends: (days?: number) => useMockOrApi(
    () => mockApiResponses.riskTrends(),
    () => api.get('/analytics/risk-trends', { params: { days } })
  ),
  departments: () => api.get('/analytics/departments'),
  fairness: () => api.get('/analytics/fairness'),
  interventionEffectiveness: () => api.get('/analytics/intervention-effectiveness'),
};

export const adminApi = {
  getTenant: () => api.get('/admin/tenant'),
  updateTenant: (data: any) => api.patch('/admin/tenant', data),
  getModels: () => api.get('/admin/models'),
  deployModel: (modelId: string, versionId: string) => 
    api.post(`/admin/models/${modelId}/deploy`, null, { params: { version_id: versionId } }),
  getAuditLogs: (limit?: number) => api.get('/admin/audit-logs', { params: { limit } }),
};
