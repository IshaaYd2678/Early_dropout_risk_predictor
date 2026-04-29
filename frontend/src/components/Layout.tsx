import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUIStore, useTenantStore } from '../store';
import { usePermissions } from '../hooks/usePermissions';
import {
  HomeIcon,
  UsersIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import Button from './ui/Button';
import Badge from './ui/Badge';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  permission?: string;
  roles?: string[];
  badge?: string | number;
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { 
    theme, 
    sidebarCollapsed, 
    notifications, 
    setTheme, 
    toggleSidebar,
    setSidebarCollapsed 
  } = useUIStore();
  const { settings } = useTenantStore();
  const permissions = usePermissions();
  
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Navigation items with role-based visibility
  const navigation: NavigationItem[] = [
    { 
      name: 'Dashboard', 
      href: '/', 
      icon: HomeIcon 
    },
    { 
      name: 'Students', 
      href: '/students', 
      icon: UsersIcon,
      permission: 'students:view'
    },
    { 
      name: 'Interventions', 
      href: '/interventions', 
      icon: ClipboardDocumentListIcon,
      permission: 'interventions:view'
    },
    { 
      name: 'Analytics', 
      href: '/analytics', 
      icon: ChartBarIcon,
      permission: 'analytics:view'
    },
    { 
      name: 'Fairness', 
      href: '/fairness', 
      icon: ShieldCheckIcon,
      permission: 'analytics:fairness',
      roles: ['department_head', 'admin']
    },
    { 
      name: 'Settings', 
      href: '/settings', 
      icon: Cog6ToothIcon 
    },
  ];

  // Filter navigation based on permissions
  const visibleNavigation = navigation.filter(item => {
    if (item.permission && !permissions.can(item.permission)) {
      return false;
    }
    if (item.roles && !permissions.isRole(item.roles)) {
      return false;
    }
    return true;
  });

  const unreadNotifications = notifications.filter(n => !n.read).length;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleTheme = () => {
    const themes = ['light', 'dark', 'auto'] as const;
    const currentIndex = themes.indexOf(theme);
    const nextTheme = themes[(currentIndex + 1) % themes.length];
    setTheme(nextTheme);
  };

  const getThemeIcon = () => {
    switch (theme) {
      case 'light': return SunIcon;
      case 'dark': return MoonIcon;
      default: return ComputerDesktopIcon;
    }
  };

  // Handle responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarCollapsed(true);
      } else {
        setSidebarCollapsed(false);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [setSidebarCollapsed]);

  // Apply theme colors from tenant settings
  const themeColors = settings ? {
    '--primary-color': settings.primary_color,
    '--secondary-color': settings.secondary_color,
  } : {};

  const ThemeIcon = getThemeIcon();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" style={themeColors}>
      <div className="flex">
        {/* Mobile menu overlay */}
        {mobileMenuOpen && (
          <div 
            className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div className={clsx(
          'fixed inset-y-0 left-0 z-50 bg-white dark:bg-gray-800 shadow-lg transition-all duration-300',
          sidebarCollapsed ? 'w-16' : 'w-64',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}>
          <div className="flex h-full flex-col">
            {/* Logo */}
            <div className={clsx(
              'flex h-16 shrink-0 items-center border-b border-gray-200 dark:border-gray-700',
              sidebarCollapsed ? 'px-2 justify-center' : 'px-6'
            )}>
              {settings?.logo_url ? (
                <img 
                  src={settings.logo_url} 
                  alt={settings.name}
                  className={clsx(
                    'object-contain',
                    sidebarCollapsed ? 'h-8 w-8' : 'h-8'
                  )}
                />
              ) : (
                <div className={clsx(
                  'font-bold text-gray-900 dark:text-gray-100',
                  sidebarCollapsed ? 'text-sm' : 'text-xl'
                )}>
                  {sidebarCollapsed ? 'EWS' : (settings?.name || 'Early Warning System')}
                </div>
              )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-2 py-6 space-y-1 overflow-y-auto">
              {visibleNavigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200',
                      'hover:scale-[1.02] active:scale-[0.98]',
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 border-r-2 border-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100'
                    )}
                    title={sidebarCollapsed ? item.name : undefined}
                  >
                    <item.icon
                      className={clsx(
                        'h-5 w-5 transition-colors',
                        sidebarCollapsed ? 'mx-auto' : 'mr-3',
                        isActive 
                          ? 'text-indigo-500 dark:text-indigo-400' 
                          : 'text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-400'
                      )}
                    />
                    {!sidebarCollapsed && (
                      <span className="flex-1">{item.name}</span>
                    )}
                    {!sidebarCollapsed && item.badge && (
                      <Badge size="sm" variant="danger">
                        {item.badge}
                      </Badge>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* User menu */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4">
              {!sidebarCollapsed ? (
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center">
                      <span className="text-sm font-medium text-white">
                        {user?.first_name?.[0]}{user?.last_name?.[0]}
                      </span>
                    </div>
                  </div>
                  <div className="ml-3 flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {user?.role?.replace('_', ' ')}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={toggleTheme}
                      className="p-1 rounded-md text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                      title={`Switch to ${theme === 'light' ? 'dark' : theme === 'dark' ? 'auto' : 'light'} theme`}
                    >
                      <ThemeIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleLogout}
                      className="p-1 rounded-md text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                      title="Sign out"
                    >
                      <ArrowRightOnRectangleIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center space-y-2">
                  <div className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user?.first_name?.[0]}{user?.last_name?.[0]}
                    </span>
                  </div>
                  <button
                    onClick={toggleTheme}
                    className="p-1 rounded-md text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                    title={`Switch to ${theme === 'light' ? 'dark' : theme === 'dark' ? 'auto' : 'light'} theme`}
                  >
                    <ThemeIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleLogout}
                    className="p-1 rounded-md text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                    title="Sign out"
                  >
                    <ArrowRightOnRectangleIcon className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className={clsx(
          'flex-1 transition-all duration-300',
          sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'
        )}>
          {/* Top bar */}
          <div className="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center">
                <button
                  onClick={() => setMobileMenuOpen(true)}
                  className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Bars3Icon className="h-6 w-6" />
                </button>
                
                <button
                  onClick={toggleSidebar}
                  className="hidden lg:block p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {sidebarCollapsed ? <Bars3Icon className="h-5 w-5" /> : <XMarkIcon className="h-5 w-5" />}
                </button>
              </div>

              <div className="flex items-center space-x-4">
                {/* Notifications */}
                <button className="relative p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700">
                  <BellIcon className="h-6 w-6" />
                  {unreadNotifications > 0 && (
                    <Badge 
                      className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center text-xs"
                      variant="danger"
                    >
                      {unreadNotifications > 9 ? '9+' : unreadNotifications}
                    </Badge>
                  )}
                </button>

                {/* User info on mobile */}
                <div className="lg:hidden">
                  <div className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user?.first_name?.[0]}{user?.last_name?.[0]}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Page content */}
          <main className="py-8">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
