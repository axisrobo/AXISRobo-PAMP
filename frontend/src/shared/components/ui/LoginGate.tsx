'use client';

import { useEffect } from 'react';
import { useAuth } from '@/shared/lib/auth-context';
import { Button, Result } from 'antd';

export function LoginGate({ children }: { children: React.ReactNode }) {
  const { user, loading, error, login, suppressAutoLogin } = useAuth();

  useEffect(() => {
    if (!loading && !user && !suppressAutoLogin) {
      login();
    }
  }, [loading, user, login, suppressAutoLogin]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Initializing authentication system...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // Fetch failed — show error with a retry button instead of auto-redirecting
    if (suppressAutoLogin) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <Result
            status="error"
            title="Unable to load user information"
            subTitle={error || 'The request failed. Check your network connection and try again, or contact an administrator.'}
            extra={
              <Button type="primary" size="large" onClick={login}>
                Sign in again
              </Button>
            }
          />
        </div>
      );
    }

    // Keycloak SSO in progress — auto-redirect
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">
            {suppressAutoLogin ? 'Unable to retrieve user information, please try again later or contact the administrator' : 'Redirecting to unified authentication login...'}
          </p>
        </div>
        {!suppressAutoLogin && (
          <div className="hidden max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mx-auto h-12 w-12 text-blue-600">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Welcome to the AxisArch system
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Please log in to access the AxisArch Management System
              </p>
            </div>
            <div>
              <button
                onClick={login}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Log in with Keycloak
              </button>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">
                The system uses Keycloak SSO for unified authentication
              </p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return <>{children}</>;
}
