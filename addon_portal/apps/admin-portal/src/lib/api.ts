import { z } from 'zod';

// Use relative URLs to leverage Next.js proxy (avoids IPv6 issues)
// Next.js proxy rewrites /api/* and /admin/api/* to http://127.0.0.1:8080
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

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

export interface Plan {
  id: number;
  name: string;
  stripePriceId: string;
  monthlyRunQuota: number;
}

export interface PlansResponse {
  plans: Plan[];
}

export async function getPlans(): Promise<Plan[]> {
  const url = `${API_BASE}/admin/api/plans`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch subscription plans');
  }
  const data: PlansResponse = await response.json();
  return data.plans;
}

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
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      let errorDetail = 'Failed to fetch tenants';
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || errorDetail;
      } catch (e) {
        errorDetail = `Server returned ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorDetail);
    }

    const data = await response.json();
    return tenantCollectionSchema.parse(data);
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server. Please ensure the backend is running on port 8080.');
    }
    throw error;
  }
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
  const url = `${API_BASE}/admin/api/tenants`;
  console.log('Creating tenant at:', url, 'with payload:', data);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    console.log('Response status:', response.status, response.statusText);
    
    if (!response.ok) {
      let errorDetail = 'Failed to create tenant';
      try {
        const errorData = await response.json();
        console.error('API error response:', errorData);
        
        // Extract error message properly - handle different response formats
        if (typeof errorData === 'string') {
          errorDetail = errorData;
        } else if (errorData.detail) {
          // FastAPI returns {detail: "message"} or {detail: ["validation errors"]}
          if (typeof errorData.detail === 'string') {
            errorDetail = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // Validation errors array
            errorDetail = errorData.detail.map((err: any) => {
              if (typeof err === 'string') return err;
              if (err.msg) return `${err.loc?.join('.') || 'Field'}: ${err.msg}`;
              return JSON.stringify(err);
            }).join('; ');
          } else {
            errorDetail = JSON.stringify(errorData.detail);
          }
        } else if (errorData.message) {
          errorDetail = errorData.message;
        } else {
          errorDetail = JSON.stringify(errorData);
        }
        
        // Handle specific error codes
        if (response.status === 409) {
          if (errorDetail.includes('slug')) {
            errorDetail = 'A tenant with this slug already exists. Please choose a different slug.';
          } else if (!errorDetail.includes('already exists')) {
            errorDetail = 'A tenant with this slug already exists. Please choose a different slug.';
          }
        } else if (response.status === 400) {
          // Business logic error (e.g., plan not found)
          if (errorDetail.includes('plan') || errorDetail.includes('Plan')) {
            // Extract plan name from error if available
            const planMatch = errorDetail.match(/"plan":\s*"([^"]+)"/);
            if (planMatch) {
              errorDetail = `Subscription plan "${planMatch[1]}" not found. Please select a valid plan (Starter, Pro, or Enterprise).`;
            } else {
              errorDetail = 'Invalid subscription plan. Please select a valid plan (Starter, Pro, or Enterprise).';
            }
          }
        } else if (response.status === 422) {
          // Validation error - errorDetail already contains the validation messages
          if (!errorDetail || errorDetail === 'Failed to create tenant') {
            errorDetail = 'Invalid input. Please check all required fields are filled correctly.';
          }
        }
      } catch (e) {
        // Failed to parse JSON - try text
        try {
          const text = await response.text();
          console.error('API error text:', text);
          if (text) {
            errorDetail = text.length > 200 ? text.substring(0, 200) + '...' : text;
          } else {
            errorDetail = `Server returned ${response.status}: ${response.statusText}`;
          }
        } catch (textError) {
          errorDetail = `Server returned ${response.status}: ${response.statusText}`;
        }
        
        if (response.status === 409) {
          errorDetail = 'A tenant with this slug already exists. Please choose a different slug.';
        }
      }
      throw new Error(errorDetail);
    }

    const payload = await response.json();
    console.log('Tenant created successfully:', payload);
    return tenantSchema.parse(payload);
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server. Please ensure the backend is running on port 8080.');
    }
    throw error;
  }
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
    let errorDetail = `Failed to update tenant (${response.status})`;
    try {
      const error = await response.json();
      errorDetail = error.detail || error.message || errorDetail;
    } catch (e) {
      errorDetail = `${errorDetail}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  const payload = await response.json();
  return tenantSchema.parse(payload);
}

// Get tenant deletion impact
export interface TenantDeletionImpact {
  tenant: {
    id: number;
    name: string;
    slug: string;
  };
  activationCodes: {
    total: number;
    active: number;
    revoked: number;
  };
  devices: {
    total: number;
    active: number;
    revoked: number;
  };
  subscriptions: {
    total: number;
  };
  usageEvents: {
    total: number;
  };
  usageRollups: {
    total: number;
  };
  llmProjects: {
    total: number;
  };
  llmAgents: {
    total: number;
  };
}

export async function getTenantDeletionImpact(slug: string): Promise<TenantDeletionImpact> {
  const response = await fetch(`${API_BASE}/admin/api/tenants/${slug}/deletion-impact`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to fetch deletion impact');
  }

  const data = await response.json();
  // Map snake_case to camelCase
  return {
    tenant: data.tenant,
    activationCodes: data.activation_codes,
    devices: data.devices,
    subscriptions: data.subscriptions,
    usageEvents: data.usage_events,
    usageRollups: data.usage_rollups,
    llmProjects: data.llm_projects,
    llmAgents: data.llm_agents,
  };
}

// Delete tenant
export async function deleteTenant(slug: string): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/api/tenants/${slug}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to delete tenant');
  }
}

