'use client';

import { useAuth } from '@/shared/lib/auth-context';

export function AuthButton() {
  const { user, loading, login, logout } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    );
  }

  if (!user) {
    return (
      <button
        onClick={login}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
      >
        Log In
      </button>
    );
  }

  return (
    <div className="flex items-center space-x-4">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
          {user.name ? user.name.charAt(0).toUpperCase() : user.id.charAt(0).toUpperCase()}
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-900">{user.name || user.id}</span>
          {(() => {
            const displayRoles = (user.roles ?? [user.role]).filter(r => r !== 'normal_user');
            return displayRoles.length > 0 ? (
              <span className="text-xs text-gray-500">{displayRoles.join(', ')}</span>
            ) : null;
          })()}
        </div>
      </div>
      <button
        onClick={logout}
        className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer"
      >
        Log Out
      </button>
    </div>
  );
}