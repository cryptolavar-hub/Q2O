const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

export interface GenerateCodesRequest {
  tenant_slug: string;
  count: number;
  ttl_days?: number;
  label?: string;
  max_uses?: number;
}

export interface ActivationCode {
  id: number;
  code?: string;
  tenant: string;
  label: string | null;
  status: 'active' | 'expired' | 'used' | 'revoked';
  expiresAt: string | null;
  usedAt: string | null;
  createdAt: string;
  useCount: number;
  maxUses: number;
}

export interface Device {
  id: number;
  tenant: string;
  label: string | null;
  hwFingerprint: string;
  deviceType: 'desktop' | 'mobile' | 'tablet';
  lastSeen: string;
  createdAt: string;
  isRevoked: boolean;
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  logoUrl: string;
  primaryColor: string;
  domain: string | null;
  subscriptionPlan: string;
  subscriptionStatus: 'active' | 'trial' | 'expired' | 'cancelled';
  usageQuota: number;
  usageCurrent: number;
  createdAt: string;
}

// Generate activation codes
export async function generateCodes(data: GenerateCodesRequest): Promise<string[]> {
  try {
    const formData = new URLSearchParams();
    formData.append('tenant_slug', data.tenant_slug);
    formData.append('count', data.count.toString());
    if (data.ttl_days) formData.append('ttl_days', data.ttl_days.toString());
    if (data.label) formData.append('label', data.label);
    if (data.max_uses) formData.append('max_uses', data.max_uses.toString());

    const response = await fetch(`${API_BASE}/admin/codes/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (response.ok && response.redirected) {
      const url = new URL(response.url);
      const created = url.searchParams.get('created');
      return created ? created.split(',') : [];
    }
    
    throw new Error('Failed to generate codes');
  } catch (error) {
    console.error('Error generating codes:', error);
    throw error;
  }
}

// Get activation codes (database-backed)
export async function getCodes(tenantSlug?: string): Promise<ActivationCode[]> {
  const url = tenantSlug 
    ? `${API_BASE}/admin/api/codes?tenant_slug=${tenantSlug}`
    : `${API_BASE}/admin/api/codes`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch codes');
  }
  
  const data = await response.json();
  return data.codes || [];
}

// Get devices (database-backed)
export async function getDevices(tenantSlug?: string): Promise<Device[]> {
  const url = tenantSlug 
    ? `${API_BASE}/admin/api/devices?tenant_slug=${tenantSlug}`
    : `${API_BASE}/admin/api/devices`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch devices');
  }
  
  const data = await response.json();
  return data.devices || [];
}

// Get tenants (database-backed)
export async function getTenants(): Promise<Tenant[]> {
  const response = await fetch(`${API_BASE}/admin/api/tenants`);
  if (!response.ok) {
    throw new Error('Failed to fetch tenants');
  }
  
  const data = await response.json();
  return data.tenants || [];
}

// Revoke activation code
export async function revokeCode(tenantSlug: string, code: string): Promise<void> {
  const formData = new URLSearchParams();
  formData.append('tenant_slug', tenantSlug);
  formData.append('code_plain', code);

  await fetch(`${API_BASE}/admin/codes/revoke`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });
}

// Revoke device
export async function revokeDevice(tenantSlug: string, deviceId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/api/devices/${deviceId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to revoke device');
  }
}

// Add tenant
export interface AddTenantRequest {
  name: string;
  slug: string;
  logo_url?: string;
  primary_color?: string;
  domain?: string;
  subscription_plan?: string;
  usage_quota?: number;
}

export async function addTenant(data: AddTenantRequest): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/api/tenants`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create tenant');
  }
}

// Edit tenant
export interface EditTenantRequest {
  name?: string;
  logo_url?: string;
  primary_color?: string;
  domain?: string;
  subscription_plan?: string;
  usage_quota?: number;
}

export async function editTenant(slug: string, data: EditTenantRequest): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/api/tenants/${slug}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update tenant');
  }
}

