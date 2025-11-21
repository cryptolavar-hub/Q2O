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
    
    // Set up session refresh interval (every 1 minute to keep session alive)
    // This ensures active users don't get logged out due to idle timeout
    const refreshInterval = setInterval(() => {
      refreshAuthIfNeeded();
    }, 60 * 1000); // 1 minute - more frequent to prevent timeouts during active use

    return () => clearInterval(refreshInterval);
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      const token = getStoredSessionToken();
      
      if (!token) {
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          session: null,
          error: null,
        });
        return;
      }

      // Check if session is expired locally first (avoid unnecessary API call)
      if (isSessionExpired()) {
        // Session expired locally, clear it
        if (typeof window !== 'undefined') {
          localStorage.removeItem('tenant_session_token');
          localStorage.removeItem('tenant_session_expires');
          localStorage.removeItem('tenant_id');
          localStorage.removeItem('tenant_slug');
        }
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          session: null,
          error: null,
        });
        return;
      }

      // Verify session is still valid with server
      const session = await getSessionInfo(token);
      
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        session,
        error: null,
      });
    } catch (error) {
      // Only clear session if it's a 401 (unauthorized) error
      // Network errors or temporary issues shouldn't log the user out
      const errorMessage = error instanceof Error ? error.message : String(error);
      const isUnauthorized = errorMessage.includes('401') || errorMessage.includes('Session invalid');
      
      if (isUnauthorized) {
        // Session invalid, clear it
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          session: null,
          error: null,
        });
        
        // Clear invalid token from storage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('tenant_session_token');
          localStorage.removeItem('tenant_session_expires');
          localStorage.removeItem('tenant_id');
          localStorage.removeItem('tenant_slug');
        }
      } else {
        // Network error or other issue - don't log out, just mark as loading failed
        // Keep existing auth state if we had one
        setAuthState((prev) => ({
          ...prev,
          isLoading: false,
        }));
      }
    }
  }, []);

  const refreshAuthIfNeeded = useCallback(async () => {
    const token = getStoredSessionToken();
    if (!token || isSessionExpired()) return; // Fixed: should refresh if NOT expired

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

      // Redirect to projects page (main dashboard)
      router.push('/projects');
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

