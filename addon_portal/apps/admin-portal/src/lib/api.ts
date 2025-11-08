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

// Get activation codes (mock implementation - replace with real API)
export async function getCodes(tenantSlug?: string): Promise<ActivationCode[]> {
  // Mock data for now
  return [
    { id: 1, code: '8PL4-M5HA-QP3E-MPCT', tenant: 'Demo Consulting', label: 'Onboarding', status: 'active', expiresAt: '2025-12-07', usedAt: null, createdAt: '2025-11-07', useCount: 0, maxUses: 1 },
    { id: 2, code: 'ND7V-A9B5-ACP7-85KW', tenant: 'Demo Consulting', label: 'Trial', status: 'active', expiresAt: '2025-12-07', usedAt: null, createdAt: '2025-11-07', useCount: 0, maxUses: 1 },
    { id: 3, code: '5EFZ-7CHR-QLKS-JQMJ', tenant: 'Demo Consulting', label: null, status: 'active', expiresAt: '2025-12-07', usedAt: null, createdAt: '2025-11-07', useCount: 0, maxUses: 1 },
    { id: 4, code: 'XXXX-XXXX-XXXX-XXXX', tenant: 'Acme Corp', label: 'Production', status: 'used', expiresAt: '2025-12-01', usedAt: '2025-11-05', createdAt: '2025-10-15', useCount: 1, maxUses: 1 },
    { id: 5, code: 'YYYY-YYYY-YYYY-YYYY', tenant: 'Tech Solutions', label: null, status: 'expired', expiresAt: '2025-11-01', usedAt: null, createdAt: '2025-10-01', useCount: 0, maxUses: 1 },
  ];
}

// Get devices (mock implementation)
export async function getDevices(tenantSlug?: string): Promise<Device[]> {
  return [
    { id: 1, tenant: 'Demo Consulting', label: 'Main Desktop', hwFingerprint: 'fp_abc123xyz', deviceType: 'desktop', lastSeen: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), createdAt: '2025-11-01', isRevoked: false },
    { id: 2, tenant: 'Demo Consulting', label: 'iPhone 14', hwFingerprint: 'fp_xyz789abc', deviceType: 'mobile', lastSeen: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), createdAt: '2025-11-03', isRevoked: false },
    { id: 3, tenant: 'Acme Corp', label: 'MacBook Pro', hwFingerprint: 'fp_def456ghi', deviceType: 'desktop', lastSeen: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), createdAt: '2025-10-15', isRevoked: false },
    { id: 4, tenant: 'Tech Solutions', label: null, hwFingerprint: 'fp_ghi789def', deviceType: 'tablet', lastSeen: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(), createdAt: '2025-09-20', isRevoked: true },
  ];
}

// Get tenants (mock implementation)
export async function getTenants(): Promise<Tenant[]> {
  return [
    {
      id: 1,
      name: 'Demo Consulting Firm',
      slug: 'demo',
      logoUrl: 'https://via.placeholder.com/150?text=Demo',
      primaryColor: '#875A7B',
      domain: 'demo.quick2odoo.com',
      subscriptionPlan: 'Pro',
      subscriptionStatus: 'active',
      usageQuota: 50,
      usageCurrent: 12,
      createdAt: '2025-11-01',
    },
    {
      id: 2,
      name: 'Acme Corporation',
      slug: 'acme',
      logoUrl: 'https://via.placeholder.com/150?text=Acme',
      primaryColor: '#4CAF50',
      domain: 'acme.quick2odoo.com',
      subscriptionPlan: 'Enterprise',
      subscriptionStatus: 'active',
      usageQuota: 200,
      usageCurrent: 45,
      createdAt: '2025-10-15',
    },
    {
      id: 3,
      name: 'Tech Solutions Ltd',
      slug: 'techsolutions',
      logoUrl: 'https://via.placeholder.com/150?text=Tech',
      primaryColor: '#2196F3',
      domain: null,
      subscriptionPlan: 'Starter',
      subscriptionStatus: 'trial',
      usageQuota: 10,
      usageCurrent: 8,
      createdAt: '2025-11-05',
    },
  ];
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
  const formData = new URLSearchParams();
  formData.append('tenant_slug', tenantSlug);
  formData.append('device_id', deviceId.toString());

  await fetch(`${API_BASE}/admin/devices/revoke`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });
}

