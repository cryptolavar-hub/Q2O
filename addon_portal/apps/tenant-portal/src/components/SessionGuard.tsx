/**
 * Session Guard Component
 * 
 * Protects routes that require authentication.
 * Redirects to login if not authenticated.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';

interface SessionGuardProps {
  children: React.ReactNode;
}

export function SessionGuard({ children }: SessionGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false);

  // Check auth on mount and route changes
  useEffect(() => {
    // Only check auth once on mount, not on every render
    if (!hasCheckedAuth) {
      checkAuth();
      setHasCheckedAuth(true);
    }
  }, [checkAuth, hasCheckedAuth]);

  useEffect(() => {
    // Only redirect if we've finished loading and confirmed not authenticated
    // Don't redirect during initial load or if we're still checking
    if (hasCheckedAuth && !isLoading && !isAuthenticated) {
      // Small delay to avoid race conditions with navigation
      const timer = setTimeout(() => {
        router.push(`/login?redirect=${encodeURIComponent(router.asPath)}`);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, isLoading, router, hasCheckedAuth]);

  // Show loading state while checking auth (only on initial load)
  if (!hasCheckedAuth || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // Don't render children if not authenticated (redirect will happen)
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

