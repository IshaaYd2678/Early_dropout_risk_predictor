// Production-grade RBAC Permissions Hook
import { useAuthStore } from '../store';

export const PERMISSIONS = {
  // Student permissions
  STUDENTS_VIEW: 'students:view',
  STUDENTS_VIEW_ALL: 'students:view:all',
  STUDENTS_VIEW_ASSIGNED: 'students:view:assigned',
  STUDENTS_EDIT: 'students:edit',
  STUDENTS_CREATE: 'students:create',
  STUDENTS_DELETE: 'students:delete',
  
  // Prediction permissions
  PREDICTIONS_VIEW: 'predictions:view',
  PREDICTIONS_CREATE: 'predictions:create',
  PREDICTIONS_EXPLAIN: 'predictions:explain',
  
  // Intervention permissions
  INTERVENTIONS_VIEW: 'interventions:view',
  INTERVENTIONS_VIEW_ALL: 'interventions:view:all',
  INTERVENTIONS_CREATE: 'interventions:create',
  INTERVENTIONS_EDIT: 'interventions:edit',
  INTERVENTIONS_DELETE: 'interventions:delete',
  INTERVENTIONS_ASSIGN: 'interventions:assign',
  
  // Analytics permissions
  ANALYTICS_VIEW: 'analytics:view',
  ANALYTICS_DEPARTMENT: 'analytics:department',
  ANALYTICS_INSTITUTION: 'analytics:institution',
  ANALYTICS_FAIRNESS: 'analytics:fairness',
  ANALYTICS_EXPORT: 'analytics:export',
  
  // Admin permissions
  ADMIN_USERS: 'admin:users',
  ADMIN_SETTINGS: 'admin:settings',
  ADMIN_MODELS: 'admin:models',
  ADMIN_AUDIT: 'admin:audit',
  ADMIN_TENANT: 'admin:tenant',
  
  // System permissions
  SYSTEM_HEALTH: 'system:health',
  SYSTEM_LOGS: 'system:logs',
} as const;

export const ROLE_PERMISSIONS = {
  mentor: [
    PERMISSIONS.STUDENTS_VIEW_ASSIGNED,
    PERMISSIONS.PREDICTIONS_VIEW,
    PERMISSIONS.PREDICTIONS_CREATE,
    PERMISSIONS.PREDICTIONS_EXPLAIN,
    PERMISSIONS.INTERVENTIONS_VIEW,
    PERMISSIONS.INTERVENTIONS_CREATE,
    PERMISSIONS.INTERVENTIONS_EDIT,
    PERMISSIONS.ANALYTICS_VIEW,
  ],
  department_head: [
    PERMISSIONS.STUDENTS_VIEW_ALL,
    PERMISSIONS.STUDENTS_EDIT,
    PERMISSIONS.PREDICTIONS_VIEW,
    PERMISSIONS.PREDICTIONS_CREATE,
    PERMISSIONS.PREDICTIONS_EXPLAIN,
    PERMISSIONS.INTERVENTIONS_VIEW_ALL,
    PERMISSIONS.INTERVENTIONS_CREATE,
    PERMISSIONS.INTERVENTIONS_EDIT,
    PERMISSIONS.INTERVENTIONS_ASSIGN,
    PERMISSIONS.ANALYTICS_VIEW,
    PERMISSIONS.ANALYTICS_DEPARTMENT,
    PERMISSIONS.ANALYTICS_FAIRNESS,
    PERMISSIONS.ANALYTICS_EXPORT,
  ],
  admin: [
    PERMISSIONS.STUDENTS_VIEW_ALL,
    PERMISSIONS.STUDENTS_EDIT,
    PERMISSIONS.STUDENTS_CREATE,
    PERMISSIONS.STUDENTS_DELETE,
    PERMISSIONS.PREDICTIONS_VIEW,
    PERMISSIONS.PREDICTIONS_CREATE,
    PERMISSIONS.PREDICTIONS_EXPLAIN,
    PERMISSIONS.INTERVENTIONS_VIEW_ALL,
    PERMISSIONS.INTERVENTIONS_CREATE,
    PERMISSIONS.INTERVENTIONS_EDIT,
    PERMISSIONS.INTERVENTIONS_DELETE,
    PERMISSIONS.INTERVENTIONS_ASSIGN,
    PERMISSIONS.ANALYTICS_VIEW,
    PERMISSIONS.ANALYTICS_DEPARTMENT,
    PERMISSIONS.ANALYTICS_INSTITUTION,
    PERMISSIONS.ANALYTICS_FAIRNESS,
    PERMISSIONS.ANALYTICS_EXPORT,
    PERMISSIONS.ADMIN_USERS,
    PERMISSIONS.ADMIN_SETTINGS,
    PERMISSIONS.ADMIN_MODELS,
    PERMISSIONS.ADMIN_AUDIT,
    PERMISSIONS.ADMIN_TENANT,
    PERMISSIONS.SYSTEM_HEALTH,
    PERMISSIONS.SYSTEM_LOGS,
  ],
} as const;

export function usePermissions() {
  const { hasPermission, hasRole, user } = useAuthStore();

  const can = (permission: string | string[]): boolean => {
    if (!user) return false;
    
    const permissions = Array.isArray(permission) ? permission : [permission];
    return permissions.some(p => hasPermission(p));
  };

  const canAny = (permissions: string[]): boolean => {
    return permissions.some(p => hasPermission(p));
  };

  const canAll = (permissions: string[]): boolean => {
    return permissions.every(p => hasPermission(p));
  };

  const isRole = (role: string | string[]): boolean => {
    return hasRole(role);
  };

  const isMentor = (): boolean => hasRole('mentor');
  const isDepartmentHead = (): boolean => hasRole('department_head');
  const isAdmin = (): boolean => hasRole('admin');

  // Specific permission checks
  const canViewAllStudents = (): boolean => 
    can(PERMISSIONS.STUDENTS_VIEW_ALL) || isAdmin();

  const canViewAssignedStudents = (): boolean => 
    can(PERMISSIONS.STUDENTS_VIEW_ASSIGNED) || isMentor();

  const canEditStudents = (): boolean => 
    can(PERMISSIONS.STUDENTS_EDIT) || isDepartmentHead() || isAdmin();

  const canCreateInterventions = (): boolean => 
    can(PERMISSIONS.INTERVENTIONS_CREATE);

  const canViewAllInterventions = (): boolean => 
    can(PERMISSIONS.INTERVENTIONS_VIEW_ALL) || isDepartmentHead() || isAdmin();

  const canViewAnalytics = (): boolean => 
    can(PERMISSIONS.ANALYTICS_VIEW);

  const canViewDepartmentAnalytics = (): boolean => 
    can(PERMISSIONS.ANALYTICS_DEPARTMENT) || isDepartmentHead() || isAdmin();

  const canViewInstitutionAnalytics = (): boolean => 
    can(PERMISSIONS.ANALYTICS_INSTITUTION) || isAdmin();

  const canViewFairnessMetrics = (): boolean => 
    can(PERMISSIONS.ANALYTICS_FAIRNESS) || isDepartmentHead() || isAdmin();

  const canExportData = (): boolean => 
    can(PERMISSIONS.ANALYTICS_EXPORT) || isDepartmentHead() || isAdmin();

  const canManageUsers = (): boolean => 
    can(PERMISSIONS.ADMIN_USERS) || isAdmin();

  const canManageSettings = (): boolean => 
    can(PERMISSIONS.ADMIN_SETTINGS) || isAdmin();

  const canViewAuditLogs = (): boolean => 
    can(PERMISSIONS.ADMIN_AUDIT) || isAdmin();

  return {
    can,
    canAny,
    canAll,
    isRole,
    isMentor,
    isDepartmentHead,
    isAdmin,
    canViewAllStudents,
    canViewAssignedStudents,
    canEditStudents,
    canCreateInterventions,
    canViewAllInterventions,
    canViewAnalytics,
    canViewDepartmentAnalytics,
    canViewInstitutionAnalytics,
    canViewFairnessMetrics,
    canExportData,
    canManageUsers,
    canManageSettings,
    canViewAuditLogs,
  };
}