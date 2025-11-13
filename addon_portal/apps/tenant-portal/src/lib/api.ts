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
