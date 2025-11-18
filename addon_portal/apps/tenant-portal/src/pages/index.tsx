import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';

/**
 * Home Page - Redirects based on authentication status
 * 
 * If authenticated: Redirect to /projects
 * If not authenticated: Redirect to /login
 */
export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.replace('/projects');
      } else {
        router.replace('/login');
      }
    }
  }, [isAuthenticated, isLoading, router]);

  // Show loading while checking auth
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
      <div className="text-white text-xl">Loading...</div>
    </div>
  );
}
