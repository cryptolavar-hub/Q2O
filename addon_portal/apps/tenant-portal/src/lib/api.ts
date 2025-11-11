export const apiBase = process.env.NEXT_PUBLIC_LIC_API || 'http://localhost:8080';

export async function getBranding(slug: string) {
  const r = await fetch(`${apiBase}/licenses/branding/${slug}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('branding failed');
  return r.json();
}

export async function getUsage(slug: string) {
  const r = await fetch(`${apiBase}/usage/${slug}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('usage failed');
  return r.json();
}
