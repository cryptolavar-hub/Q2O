/**
 * Authentication Hook
 * 
 * Provides authentication state and methods for the Tenant Portal.
 */

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import {
  generateOTP,
  verifyOTP,
  logout as logoutAPI,
  getSessionInfo,
  refreshSession,
  getStoredSessionToken,
  isSessionExpired,
  type SessionInfo,
} from '../lib/auth';

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  session: SessionInfo | null;
  error: string | null;
}

export function useAuth() {
  const router = useRouter();
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    session: null,
    error: null,
  });

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
    
    // Set up session refresh interval (every 5 minutes)
    const refreshInterval = setInterval(() => {
      refreshAuthIfNeeded();
    }, 5 * 60 * 1000);

    return () => clearInterval(refreshInterval);
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      const token = getStoredSessionToken();
      
      if (!token || isSessionExpired()) {
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          session: null,
          error: null,
        });
        return;
      }

      // Verify session is still valid
      const session = await getSessionInfo(token);
      
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        session,
        error: null,
      });
    } catch (error) {
      // Session invalid, clear it
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        session: null,
        error: error instanceof Error ? error.message : 'Session invalid',
      });
    }
  }, []);

  const refreshAuthIfNeeded = useCallback(async () => {
    const token = getStoredSessionToken();
    if (!token || !isSessionExpired()) return;

    try {
      const session = await refreshSession(token);
      setAuthState((prev) => ({
        ...prev,
        session,
      }));
    } catch (error) {
      // Refresh failed, logout
      await handleLogout();
    }
  }, []);

  const handleGenerateOTP = useCallback(async (tenantSlug: string) => {
    try {
      setAuthState((prev) => ({ ...prev, error: null }));
      const response = await generateOTP(tenantSlug);
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate OTP';
      setAuthState((prev) => ({ ...prev, error: errorMessage }));
      throw error;
    }
  }, []);

  const handleVerifyOTP = useCallback(async (tenantSlug: string, otpCode: string) => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));
      const session = await verifyOTP(tenantSlug, otpCode);
      
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        session,
        error: null,
      });

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to verify OTP';
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [router]);

  const handleLogout = useCallback(async () => {
    try {
      const token = getStoredSessionToken();
      if (token) {
        await logoutAPI(token);
      }
    } catch (error) {
      // Ignore errors, still clear local state
    } finally {
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        session: null,
        error: null,
      });
      
      // Clear storage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('tenant_session_token');
        localStorage.removeItem('tenant_session_expires');
        localStorage.removeItem('tenant_id');
        localStorage.removeItem('tenant_slug');
      }
      
      // Redirect to login
      router.push('/login');
    }
  }, [router]);

  return {
    ...authState,
    generateOTP: handleGenerateOTP,
    verifyOTP: handleVerifyOTP,
    logout: handleLogout,
    refreshAuth: refreshAuthIfNeeded,
    checkAuth,
  };
}

