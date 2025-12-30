/**
 * Authentication Context
 * Manages user authentication state across the application
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

// Demo users for development (replace with real auth in production)
const DEMO_USERS = {
  'admin@mtp.io': { password: 'admin123', role: 'admin', name: 'System Admin', org: 'MTP Core' },
  'auditor@fnb.co.za': { password: 'audit123', role: 'auditor', name: 'Jane Auditor', org: 'First National Bank' },
  'operator@standard.co.za': { password: 'oper123', role: 'operator', name: 'John Operator', org: 'Standard Bank' },
  'viewer@demo.com': { password: 'view123', role: 'viewer', name: 'Demo Viewer', org: 'Demo Corp' },
};

export const ROLES = {
  ADMIN: 'admin',
  AUDITOR: 'auditor',
  OPERATOR: 'operator',
  VIEWER: 'viewer',
};

export const PERMISSIONS = {
  [ROLES.ADMIN]: ['*'], // All permissions
  [ROLES.AUDITOR]: ['view:agents', 'view:audit', 'view:trust', 'view:certifications', 'view:disputes', 'view:blockchain', 'export:data'],
  [ROLES.OPERATOR]: ['view:agents', 'manage:agents', 'view:audit', 'view:trust', 'manage:certifications', 'create:disputes'],
  [ROLES.VIEWER]: ['view:agents', 'view:audit', 'view:trust'],
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing session on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('mtp_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('mtp_user');
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    setError(null);
    setLoading(true);

    try {
      // For demo: check against demo users
      const demoUser = DEMO_USERS[email.toLowerCase()];
      if (demoUser && demoUser.password === password) {
        const userData = {
          email: email.toLowerCase(),
          name: demoUser.name,
          role: demoUser.role,
          org: demoUser.org,
          permissions: PERMISSIONS[demoUser.role],
          token: `demo_token_${Date.now()}`,
        };

        setUser(userData);
        localStorage.setItem('mtp_user', JSON.stringify(userData));
        localStorage.setItem('mtp_token', userData.token);
        setLoading(false);
        return { success: true, user: userData };
      }

      // Try real API login
      try {
        const response = await authAPI.login({ email, password });
        const userData = response.data;
        setUser(userData);
        localStorage.setItem('mtp_user', JSON.stringify(userData));
        localStorage.setItem('mtp_token', userData.token);
        setLoading(false);
        return { success: true, user: userData };
      } catch (apiError) {
        // If API fails and no demo match, return error
        throw new Error('Invalid email or password');
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
      return { success: false, error: err.message };
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('mtp_user');
    localStorage.removeItem('mtp_token');
    localStorage.removeItem('mtp_api_key');
  }, []);

  const hasPermission = useCallback((permission) => {
    if (!user) return false;
    if (user.permissions.includes('*')) return true;
    return user.permissions.includes(permission);
  }, [user]);

  const hasRole = useCallback((role) => {
    if (!user) return false;
    if (Array.isArray(role)) return role.includes(user.role);
    return user.role === role;
  }, [user]);

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    hasPermission,
    hasRole,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
