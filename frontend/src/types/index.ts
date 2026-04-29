// Core Types for Production B2B SaaS Early Warning System

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'mentor' | 'department_head' | 'admin';
  tenant_id: string;
  department_id?: string;
  permissions: string[];
  avatar_url?: string;
  last_login?: string;
}

export interface Student {
  id: string;
  student_id: string;
  first_name: string;
  last_name: string;
  email: string;
  department: string;
  program: string;
  semester: number;
  year: number;
  enrollment_date: string;
  status: 'active' | 'inactive' | 'graduated' | 'dropped_out';
  mentor_id?: string;
  current_risk_score: number;
  risk_category: 'Low' | 'Medium' | 'High' | 'Critical';
  last_prediction_date: string;
  demographics: {
    gender?: string;
    age?: number;
    socioeconomic_status?: string;
    region?: string;
  };
  academic_metrics: {
    gpa: number;
    attendance_rate: number;
    assignment_submission_rate: number;
    exam_scores: number;
    participation_score: number;
  };
  engagement_metrics: {
    lms_login_frequency: number;
    forum_posts: number;
    resource_access_count: number;
    time_spent_hours: number;
    late_submissions: number;
  };
}

export interface RiskPrediction {
  id: string;
  student_id: string;
  risk_score: number;
  risk_category: 'Low' | 'Medium' | 'High' | 'Critical';
  prediction_date: string;
  model_version: string;
  confidence: number;
  explanation: RiskExplanation;
}

export interface RiskExplanation {
  top_factors: Array<{
    feature: string;
    impact: number;
    direction: 'positive' | 'negative';
    description: string;
    category: 'academic' | 'engagement' | 'behavioral' | 'demographic';
  }>;
  risk_drivers: string[];
  protective_factors: string[];
  recommendations: string[];
}

export interface Intervention {
  id: string;
  student_id: string;
  type: 'counseling' | 'tutoring' | 'mentoring' | 'financial_aid' | 'academic_support' | 'other';
  title: string;
  description: string;
  status: 'planned' | 'active' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to: string;
  created_by: string;
  created_date: string;
  due_date?: string;
  completed_date?: string;
  notes: InterventionNote[];
  followups: InterventionFollowup[];
  outcome?: InterventionOutcome;
  risk_score_before?: number;
  risk_score_after?: number;
  effectiveness_score?: number;
}

export interface InterventionNote {
  id: string;
  content: string;
  created_by: string;
  created_date: string;
  is_private: boolean;
}

export interface InterventionFollowup {
  id: string;
  scheduled_date: string;
  completed_date?: string;
  notes?: string;
  status: 'scheduled' | 'completed' | 'missed';
}

export interface InterventionOutcome {
  result: 'successful' | 'partially_successful' | 'unsuccessful' | 'ongoing';
  description: string;
  metrics: {
    risk_reduction: number;
    engagement_improvement: number;
    academic_improvement: number;
  };
  recorded_by: string;
  recorded_date: string;
}

export interface DashboardMetrics {
  total_students: number;
  at_risk_students: number;
  active_interventions: number;
  success_rate: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  trends: {
    risk_trend: number;
    intervention_trend: number;
    success_trend: number;
  };
}

export interface Department {
  id: string;
  name: string;
  code: string;
  head_id: string;
  student_count: number;
  risk_metrics: {
    average_risk: number;
    at_risk_count: number;
    intervention_count: number;
  };
}

export interface FairnessMetrics {
  overall_fairness_score: number;
  demographic_parity: {
    score: number;
    status: 'pass' | 'warning' | 'fail';
    groups: Array<{
      group: string;
      positive_rate: number;
      difference: number;
    }>;
  };
  equalized_odds: {
    score: number;
    status: 'pass' | 'warning' | 'fail';
    groups: Array<{
      group: string;
      tpr: number;
      fpr: number;
    }>;
  };
  bias_indicators: Array<{
    attribute: string;
    bias_level: 'low' | 'medium' | 'high';
    description: string;
  }>;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  deployed_date: string;
  performance_metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    auc_roc: number;
  };
  fairness_score: number;
  status: 'active' | 'deprecated' | 'testing';
}

export interface TenantSettings {
  id: string;
  name: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  theme: 'light' | 'dark' | 'auto';
  features: {
    fairness_monitoring: boolean;
    intervention_tracking: boolean;
    advanced_analytics: boolean;
    audit_logging: boolean;
  };
  risk_thresholds: {
    low_max: number;
    medium_max: number;
    high_max: number;
  };
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Filter and Search Types
export interface StudentFilters {
  department?: string;
  risk_category?: string[];
  semester?: number;
  mentor_id?: string;
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface InterventionFilters {
  student_id?: string;
  type?: string[];
  status?: string[];
  assigned_to?: string;
  date_range?: {
    start: string;
    end: string;
  };
}

// Chart Data Types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  category?: string;
}

export interface HeatmapData {
  x: string;
  y: string;
  value: number;
  label?: string;
}