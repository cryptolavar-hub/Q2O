import { z } from 'zod';

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

const subscriptionStatusSchema = z.enum([
  'active',
  'past_due',
  'canceled',
  'unpaid',
  'trialing',
  'suspended',
  'none',
]);

const tenantSchema = z.object({
  id: z.number().int().nonnegative(),
  name: z.string().min(1),
  slug: z.string().min(1),
  logoUrl: z.string().url().nullable(),
  primaryColor: z.string().nullable(),
  domain: z.string().nullable(),
  usageQuota: z.number().int().nonnegative(),
  usageCurrent: z.number().int().nonnegative(),
  createdAt: z.string().min(1),
  subscription: z.object({
    planName: z.string().nullable(),
    status: subscriptionStatusSchema.nullable(),
  }),
});

const tenantCollectionSchema = z.object({
  items: z.array(tenantSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().min(1),
  pageSize: z.number().int().min(1),
});

export type Tenant = z.infer<typeof tenantSchema>;
export interface TenantPage extends z.infer<typeof tenantCollectionSchema> {}

export interface TenantQueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
  sortField?: 'created_at' | 'name' | 'usage_current';
  sortDirection?: 'asc' | 'desc';
}

// Generate activation codes
export async function generateCodes(data: GenerateCodesRequest): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE}/admin/api/codes/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `Failed to generate codes: ${response.statusText}`);
    }

    const responseData = await response.json();
    return responseData.codes || [];
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
export async function getTenants(params: TenantQueryParams = {}): Promise<TenantPage> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', params.page.toString());
  if (params.pageSize) query.set('page_size', params.pageSize.toString());
  if (params.search) query.set('search', params.search);
  if (params.status) query.set('status', params.status);
  if (params.sortField) query.set('sort_field', params.sortField);
  if (params.sortDirection) query.set('sort_direction', params.sortDirection);

  const url = `${API_BASE}/admin/api/tenants${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch tenants');
  }

  const data = await response.json();
  return tenantCollectionSchema.parse(data);
}

// Revoke activation code
export async function revokeCode(codeId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/api/codes/${codeId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `Failed to revoke code: ${response.statusText}`);
  }
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
  logoUrl?: string;
  primaryColor?: string;
  domain?: string;
  subscriptionPlan: string;
  usageQuota?: number;
}

export async function addTenant(data: AddTenantRequest): Promise<Tenant> {
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

  const payload = await response.json();
  return tenantSchema.parse(payload);
}

// Edit tenant
export interface EditTenantRequest {
  name?: string;
  logoUrl?: string;
  primaryColor?: string;
  domain?: string;
  subscriptionPlan?: string;
  usageQuota?: number;
}

export async function editTenant(slug: string, data: EditTenantRequest): Promise<Tenant> {
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

  const payload = await response.json();
  return tenantSchema.parse(payload);
}

