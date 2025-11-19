/**
 * Authentication and Session Management
 * 
 * Handles OTP-based authentication and session token management
 * for the Tenant Portal.
 */

const API_BASE = process.env.NEXT_PUBLIC_LIC_API || '';

export interface SessionInfo {
  session_token: string;
  expires_at: string;
  tenant_id: string;
  tenant_slug: string;
}

export interface OTPResponse {
  otp_code: string;
  expires_in: number;
}

/**
 * Generate OTP for tenant login
 */
export async function generateOTP(tenantSlug: string): Promise<OTPResponse> {
  const response = await fetch(`${API_BASE}/api/tenant/auth/otp/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tenant_slug: tenantSlug }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to generate OTP: ${response.status}`);
  }

  return response.json();
}

/**
 * Verify OTP and get session token
 */
export async function verifyOTP(tenantSlug: string, otpCode: string): Promise<SessionInfo> {
  const response = await fetch(`${API_BASE}/api/tenant/auth/otp/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tenant_slug: tenantSlug,
      otp_code: otpCode,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to verify OTP: ${response.status}`);
  }

  const data = await response.json();
  
  // Store session token in httpOnly cookie (via API route) or localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('tenant_session_token', data.session_token);
    localStorage.setItem('tenant_session_expires', data.expires_at);
    localStorage.setItem('tenant_id', data.tenant_id);
    localStorage.setItem('tenant_slug', data.tenant_slug);
  }

  return data;
}

/**
 * Get current session info
 */
export async function getSessionInfo(sessionToken: string): Promise<SessionInfo> {
  const response = await fetch(`${API_BASE}/api/tenant/auth/session`, {
    method: 'GET',
    headers: {
      'X-Session-Token': sessionToken,
    },
  });

  if (!response.ok) {
    throw new Error(`Session invalid: ${response.status}`);
  }

  const data = await response.json();
  return {
    session_token: sessionToken,
    expires_at: data.expires_at,
    tenant_id: data.tenant_id,
    tenant_slug: data.tenant_slug,
  };
}

/**
 * Refresh session expiration
 */
export async function refreshSession(sessionToken: string): Promise<SessionInfo> {
  const response = await fetch(`${API_BASE}/api/tenant/auth/refresh`, {
    method: 'POST',
    headers: {
      'X-Session-Token': sessionToken,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to refresh session: ${response.status}`);
  }

  const data = await response.json();
  
  // Update stored session
  if (typeof window !== 'undefined') {
    localStorage.setItem('tenant_session_token', data.session_token);
    localStorage.setItem('tenant_session_expires', data.expires_at);
  }

  return data;
}

/**
 * Logout and invalidate session
 */
export async function logout(sessionToken: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/tenant/auth/logout`, {
      method: 'POST',
      headers: {
        'X-Session-Token': sessionToken,
      },
    });
  } catch (error) {
    // Ignore errors on logout
    console.error('Logout error:', error);
  } finally {
    // Clear local storage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('tenant_session_token');
      localStorage.removeItem('tenant_session_expires');
      localStorage.removeItem('tenant_id');
      localStorage.removeItem('tenant_slug');
    }
  }
}

/**
 * Get stored session token
 */
export function getStoredSessionToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('tenant_session_token');
}

/**
 * Check if session is expired
 */
export function isSessionExpired(): boolean {
  if (typeof window === 'undefined') return true;
  
  const expiresAt = localStorage.getItem('tenant_session_expires');
  if (!expiresAt) return true;

  const expires = new Date(expiresAt);
  const now = new Date();
  
  return now >= expires;
}

/**
 * Get stored tenant info
 */
export function getStoredTenantInfo(): { tenant_id: string; tenant_slug: string } | null {
  if (typeof window === 'undefined') return null;
  
  const tenantId = localStorage.getItem('tenant_id');
  const tenantSlug = localStorage.getItem('tenant_slug');
  
  if (!tenantId || !tenantSlug) return null;
  
  return { tenant_id: tenantId, tenant_slug: tenantSlug };
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getStoredSessionToken();
  if (!token) return false;
  
  return !isSessionExpired();
}

