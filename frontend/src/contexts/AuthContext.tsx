import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '../store';
import { api } from '../lib/api';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'mentor' | 'department_head' | 'admin';
  tenant_id: string;
  permissions: string[];
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading, setUser, setLoading, logout: storeLogout } = useAuthStore();

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      // Mock user data for demo - in production this would come from API
      const mockUser: User = {
        id: '1',
        email: 'demo@university.edu',
        first_name: 'Demo',
        last_name: 'User',
        role: 'admin', // Change this to test different roles: 'mentor', 'department_head', 'admin'
        tenant_id: 'university-1',
        permissions: [
          'students:view:all',
          'predictions:view',
          'predictions:create',
          'interventions:view:all',
          'interventions:create',
          'analytics:view',
          'analytics:institution',
          'admin:all'
        ]
      };
      setUser(mockUser);
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  }, [setUser, setLoading]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    // Mock login - in production this would call the real API
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('refresh_token', 'mock-refresh-token');
    
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    storeLogout();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
