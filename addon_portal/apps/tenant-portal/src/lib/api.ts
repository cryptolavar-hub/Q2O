// Use empty string to leverage Next.js proxy rewrites
const API_BASE = process.env.NEXT_PUBLIC_LIC_API || '';

export interface Branding {
  logo_url?: string;
  primary_color?: string;
  domain?: string;
}

export interface Usage {
  tenant: string;
  year: number;
  month: number;
  runs: number;
  quota: number;
  plan?: string;
}

export interface GenerateCodesResponse {
  success: boolean;
  codes: string[];
  message?: string;
}

export async function getBranding(slug: string): Promise<Branding> {
  const r = await fetch(`${API_BASE}/licenses/branding/${slug}`, { cache: 'no-store' });
  if (!r.ok) {
    throw new Error(`Failed to fetch branding: ${r.status} ${r.statusText}`);
  }
  return r.json();
}

export async function getUsage(slug: string): Promise<Usage> {
  const r = await fetch(`${API_BASE}/usage/${slug}`, { cache: 'no-store' });
  if (!r.ok) {
    throw new Error(`Failed to fetch usage: ${r.status} ${r.statusText}`);
  }
  return r.json();
}

export interface TenantProfile {
  id: number;
  name: string;
  slug: string;
  logoUrl?: string;
  primaryColor?: string;
  domain?: string;
  email?: string;
  phoneNumber?: string;
  usageQuota: number;
  usageCurrent: number;
  activationCodesTotal: number;
  activationCodesUsed: number;
  createdAt: string;
  updatedAt: string;
  subscription: {
    planName?: string;
    status?: string;
  };
}

export interface TenantProfileUpdate {
  name?: string;
  logoUrl?: string;
  primaryColor?: string;
  domain?: string;
  email?: string;
  phoneNumber?: string;
}

/**
 * Get current tenant's profile
 */
export async function getTenantProfile(sessionToken: string): Promise<TenantProfile> {
  const response = await fetch(`${API_BASE}/api/tenant/profile`, {
    method: 'GET',
    headers: {
      'X-Session-Token': sessionToken,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to fetch profile: ${response.status}`);
  }

  return response.json();
}

/**
 * Update current tenant's profile
 */
export async function updateTenantProfile(
  sessionToken: string,
  updates: TenantProfileUpdate
): Promise<TenantProfile> {
  const response = await fetch(`${API_BASE}/api/tenant/profile`, {
    method: 'PUT',
    headers: {
      'X-Session-Token': sessionToken,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to update profile: ${response.status}`);
  }

  return response.json();
}

export interface SubscriptionBillingInfo {
  planName: string;
  planTier?: string;
  monthlyPrice?: number;
  status: string;
  nextBillingDate?: string;
  autoRenewal: boolean;
  stripeSubscriptionId?: string;
  stripeCustomerId?: string;
  currentPeriodStart?: string;
  currentPeriodEnd?: string;
}

export interface UsageQuotaInfo {
  monthlyRunQuota: number;
  currentMonthUsage: number;
  usagePercentage: number;
  activationCodesTotal: number;
  activationCodesUsed: number;
  activationCodesRemaining: number;
  activationCodesPercentage: number;
}

export interface BillingHistoryItem {
  id: string;
  date: string;
  amount: number;
  status: string;
  description: string;
  invoiceUrl?: string;
  paymentMethodLast4?: string;
}

export interface BillingInfo {
  subscription: SubscriptionBillingInfo;
  usage: UsageQuotaInfo;
  billingHistory: BillingHistoryItem[];
}

export interface Plan {
  id: number;
  name: string;
  stripePriceId: string;
  monthlyRunQuota: number;
}

/**
 * Get current tenant's billing information
 */
export async function getTenantBilling(sessionToken: string): Promise<BillingInfo> {
  const response = await fetch(`${API_BASE}/api/tenant/billing`, {
    method: 'GET',
    headers: {
      'X-Session-Token': sessionToken,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to fetch billing info: ${response.status}`);
  }

  return response.json();
}

/**
 * Get all available subscription plans
 */
export async function getAvailablePlans(sessionToken: string): Promise<Plan[]> {
  const response = await fetch(`${API_BASE}/api/tenant/billing/plans`, {
    method: 'GET',
    headers: {
      'X-Session-Token': sessionToken,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to fetch plans: ${response.status}`);
  }

  return response.json();
}

/**
 * Upgrade or downgrade subscription plan
 * Returns checkout URL for Stripe
 */
export async function upgradeSubscriptionPlan(
  sessionToken: string,
  planId: number,
  immediate: boolean = false
): Promise<{ checkoutUrl: string; sessionId: string }> {
  const response = await fetch(`${API_BASE}/api/tenant/billing/upgrade`, {
    method: 'POST',
    headers: {
      'X-Session-Token': sessionToken,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ planId, immediate }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to upgrade plan: ${response.status}`);
  }

  return response.json();
}

/**
 * Purchase additional activation codes
 * Returns checkout URL for Stripe
 */
export async function purchaseActivationCodes(
  sessionToken: string,
  quantity: number,
  label?: string
): Promise<{ checkoutUrl: string; sessionId: string; totalCost: number }> {
  const response = await fetch(`${API_BASE}/api/tenant/billing/purchase-codes`, {
    method: 'POST',
    headers: {
      'X-Session-Token': sessionToken,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ quantity, label }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to purchase codes: ${response.status}`);
  }

  return response.json();
}

export async function generateCodes(
  tenantSlug: string,
  count: number,
  options?: {
    ttlDays?: number;
    label?: string;
    maxUses?: number;
  }
): Promise<GenerateCodesResponse> {
  const payload = {
    tenant_slug: tenantSlug,
    count,
    ttl_days: options?.ttlDays,
    label: options?.label,
    max_uses: options?.maxUses ?? 1,
  };

  // Remove undefined values
  Object.keys(payload).forEach((key) => {
    if (payload[key as keyof typeof payload] === undefined) {
      delete payload[key as keyof typeof payload];
    }
  });

  const r = await fetch(`${API_BASE}/admin/api/codes/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!r.ok) {
    const errorText = await r.text();
    throw new Error(`Failed to generate codes: ${r.status} ${r.statusText} - ${errorText}`);
  }

  return r.json();
}
