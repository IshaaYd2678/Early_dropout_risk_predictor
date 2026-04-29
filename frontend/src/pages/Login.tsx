import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUIStore } from '../store';
import Button from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import {
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  AcademicCapIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function Login() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const { theme } = useUIStore();
  const [formData, setFormData] = useState({
    email: 'demo@university.edu',
    password: 'password',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await login(formData.email, formData.password);
      toast.success('Welcome to Early Warning System!');
    } catch (error) {
      toast.error('Login failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="flex min-h-screen">
        {/* Left Panel - Branding & Features */}
        <div className="hidden lg:flex lg:w-1/2 xl:w-2/5 bg-indigo-600 dark:bg-indigo-800 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 to-purple-700 dark:from-indigo-800 dark:to-purple-900" />
          <div className="absolute inset-0 bg-black/10" />
          
          <div className="relative z-10 flex flex-col justify-center px-12 py-12 text-white">
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2 bg-white/20 rounded-lg">
                  <AcademicCapIcon className="h-8 w-8" />
                </div>
                <h1 className="text-3xl font-bold">Early Warning System</h1>
              </div>
              <p className="text-xl text-indigo-100 leading-relaxed">
                AI-powered student retention platform for universities and educational institutions.
              </p>
            </div>

            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="p-2 bg-white/20 rounded-lg">
                  <ChartBarIcon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">Predictive Analytics</h3>
                  <p className="text-indigo-100">
                    Identify at-risk students early with machine learning models and explainable AI insights.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="p-2 bg-white/20 rounded-lg">
                  <ShieldCheckIcon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">Fair & Transparent</h3>
                  <p className="text-indigo-100">
                    Built-in fairness monitoring and bias detection to ensure equitable outcomes for all students.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="p-2 bg-white/20 rounded-lg">
                  <AcademicCapIcon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">Intervention Tracking</h3>
                  <p className="text-indigo-100">
                    Comprehensive intervention management with outcome tracking and success metrics.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-12 pt-8 border-t border-white/20">
              <p className="text-sm text-indigo-200">
                Trusted by universities worldwide to improve student retention and success rates.
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel - Login Form */}
        <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8">
          <div className="w-full max-w-md space-y-8">
            {/* Mobile Logo */}
            <div className="lg:hidden text-center">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <div className="p-2 bg-indigo-600 text-white rounded-lg">
                  <AcademicCapIcon className="h-8 w-8" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Early Warning System
                </h1>
              </div>
            </div>

            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 text-center lg:text-left">
                Welcome back
              </h2>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 text-center lg:text-left">
                Sign in to your account to access the dashboard
              </p>
            </div>

            <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Email address
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100 transition-colors"
                    placeholder="Enter your email"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Password
                  </label>
                  <div className="mt-1 relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      required
                      value={formData.password}
                      onChange={handleInputChange}
                      className="block w-full px-3 py-3 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100 transition-colors"
                      placeholder="Enter your password"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
                      ) : (
                        <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
                    Forgot password?
                  </a>
                </div>
              </div>

              <Button
                type="submit"
                fullWidth
                loading={isSubmitting}
                className="py-3 text-base font-medium"
              >
                {isSubmitting ? 'Signing in...' : 'Sign in'}
              </Button>

              {/* Demo Notice */}
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <ShieldCheckIcon className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                      Demo Mode
                    </h3>
                    <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
                      <p>Use the pre-filled credentials or any email/password combination to explore the system.</p>
                    </div>
                  </div>
                </div>
              </div>
            </form>

            {/* Footer */}
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                © 2024 Early Warning System. Built for educational institutions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}