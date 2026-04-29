// Production-grade State Management with Zustand
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { User, Student, Intervention, DashboardMetrics, TenantSettings } from '../types';

// Auth Store
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  permissions: string[];
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string | string[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        user: null,
        isAuthenticated: false,
        isLoading: true,
        permissions: [],
        
        setUser: (user) => set({ 
          user, 
          isAuthenticated: !!user,
          permissions: user?.permissions || []
        }),
        
        setLoading: (isLoading) => set({ isLoading }),
        
        logout: () => set({ 
          user: null, 
          isAuthenticated: false, 
          permissions: [] 
        }),
        
        hasPermission: (permission) => {
          const { permissions } = get();
          return permissions.includes(permission) || permissions.includes('admin:all');
        },
        
        hasRole: (role) => {
          const { user } = get();
          if (!user) return false;
          const roles = Array.isArray(role) ? role : [role];
          return roles.includes(user.role);
        },
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
      }
    ),
    { name: 'auth-store' }
  )
);

// UI Store
interface UIState {
  theme: 'light' | 'dark' | 'auto';
  sidebarCollapsed: boolean;
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
  }>;
  loading: Record<string, boolean>;
  errors: Record<string, string | null>;
  
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
  setLoading: (key: string, loading: boolean) => void;
  setError: (key: string, error: string | null) => void;
  clearError: (key: string) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        theme: 'auto',
        sidebarCollapsed: false,
        notifications: [],
        loading: {},
        errors: {},
        
        setTheme: (theme) => set({ theme }),
        
        toggleSidebar: () => set((state) => ({ 
          sidebarCollapsed: !state.sidebarCollapsed 
        })),
        
        setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
        
        addNotification: (notification) => set((state) => ({
          notifications: [{
            ...notification,
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            read: false,
          }, ...state.notifications].slice(0, 50) // Keep only last 50
        })),
        
        markNotificationRead: (id) => set((state) => ({
          notifications: state.notifications.map(n => 
            n.id === id ? { ...n, read: true } : n
          )
        })),
        
        clearNotifications: () => set({ notifications: [] }),
        
        setLoading: (key, loading) => set((state) => ({
          loading: { ...state.loading, [key]: loading }
        })),
        
        setError: (key, error) => set((state) => ({
          errors: { ...state.errors, [key]: error }
        })),
        
        clearError: (key) => set((state) => {
          const { [key]: _, ...rest } = state.errors;
          return { errors: rest };
        }),
      }),
      {
        name: 'ui-storage',
        partialize: (state) => ({ 
          theme: state.theme, 
          sidebarCollapsed: state.sidebarCollapsed 
        }),
      }
    ),
    { name: 'ui-store' }
  )
);

// Students Store
interface StudentsState {
  students: Student[];
  selectedStudent: Student | null;
  filters: {
    department?: string;
    risk_category?: string[];
    semester?: number;
    mentor_id?: string;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  };
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  
  setStudents: (students: Student[]) => void;
  setSelectedStudent: (student: Student | null) => void;
  updateStudent: (id: string, updates: Partial<Student>) => void;
  setFilters: (filters: Partial<StudentsState['filters']>) => void;
  setPagination: (pagination: Partial<StudentsState['pagination']>) => void;
  clearFilters: () => void;
}

export const useStudentsStore = create<StudentsState>()(
  devtools(
    (set, get) => ({
      students: [],
      selectedStudent: null,
      filters: {
        sort_by: 'current_risk_score',
        sort_order: 'desc',
      },
      pagination: {
        page: 1,
        per_page: 25,
        total: 0,
        total_pages: 0,
      },
      
      setStudents: (students) => set({ students }),
      
      setSelectedStudent: (selectedStudent) => set({ selectedStudent }),
      
      updateStudent: (id, updates) => set((state) => ({
        students: state.students.map(s => 
          s.id === id ? { ...s, ...updates } : s
        ),
        selectedStudent: state.selectedStudent?.id === id 
          ? { ...state.selectedStudent, ...updates }
          : state.selectedStudent
      })),
      
      setFilters: (filters) => set((state) => ({
        filters: { ...state.filters, ...filters },
        pagination: { ...state.pagination, page: 1 } // Reset to first page
      })),
      
      setPagination: (pagination) => set((state) => ({
        pagination: { ...state.pagination, ...pagination }
      })),
      
      clearFilters: () => set({
        filters: {
          sort_by: 'current_risk_score',
          sort_order: 'desc',
        },
        pagination: { page: 1, per_page: 25, total: 0, total_pages: 0 }
      }),
    }),
    { name: 'students-store' }
  )
);

// Interventions Store
interface InterventionsState {
  interventions: Intervention[];
  selectedIntervention: Intervention | null;
  filters: {
    student_id?: string;
    type?: string[];
    status?: string[];
    assigned_to?: string;
    date_range?: { start: string; end: string };
  };
  
  setInterventions: (interventions: Intervention[]) => void;
  setSelectedIntervention: (intervention: Intervention | null) => void;
  addIntervention: (intervention: Intervention) => void;
  updateIntervention: (id: string, updates: Partial<Intervention>) => void;
  setFilters: (filters: Partial<InterventionsState['filters']>) => void;
  clearFilters: () => void;
}

export const useInterventionsStore = create<InterventionsState>()(
  devtools(
    (set) => ({
      interventions: [],
      selectedIntervention: null,
      filters: {},
      
      setInterventions: (interventions) => set({ interventions }),
      
      setSelectedIntervention: (selectedIntervention) => set({ selectedIntervention }),
      
      addIntervention: (intervention) => set((state) => ({
        interventions: [intervention, ...state.interventions]
      })),
      
      updateIntervention: (id, updates) => set((state) => ({
        interventions: state.interventions.map(i => 
          i.id === id ? { ...i, ...updates } : i
        ),
        selectedIntervention: state.selectedIntervention?.id === id 
          ? { ...state.selectedIntervention, ...updates }
          : state.selectedIntervention
      })),
      
      setFilters: (filters) => set((state) => ({
        filters: { ...state.filters, ...filters }
      })),
      
      clearFilters: () => set({ filters: {} }),
    }),
    { name: 'interventions-store' }
  )
);

// Dashboard Store
interface DashboardState {
  metrics: DashboardMetrics | null;
  lastUpdated: string | null;
  
  setMetrics: (metrics: DashboardMetrics) => void;
  updateLastUpdated: () => void;
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      metrics: null,
      lastUpdated: null,
      
      setMetrics: (metrics) => set({ 
        metrics,
        lastUpdated: new Date().toISOString()
      }),
      
      updateLastUpdated: () => set({ 
        lastUpdated: new Date().toISOString() 
      }),
    }),
    { name: 'dashboard-store' }
  )
);

// Tenant Store
interface TenantState {
  settings: TenantSettings | null;
  
  setSettings: (settings: TenantSettings) => void;
  updateSettings: (updates: Partial<TenantSettings>) => void;
}

export const useTenantStore = create<TenantState>()(
  devtools(
    persist(
      (set) => ({
        settings: null,
        
        setSettings: (settings) => set({ settings }),
        
        updateSettings: (updates) => set((state) => ({
          settings: state.settings ? { ...state.settings, ...updates } : null
        })),
      }),
      {
        name: 'tenant-storage',
        partialize: (state) => ({ settings: state.settings }),
      }
    ),
    { name: 'tenant-store' }
  )
);