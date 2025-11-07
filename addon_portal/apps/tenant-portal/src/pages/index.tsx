import React, { useState } from 'react';
import { apiBase, getBranding, getUsage } from '../lib/api';
import { BrandingPreview } from '../components/BrandingPreview';
import { UsageMeter } from '../components/UsageMeter';

export default function Home() {
  const [tenantSlug, setTenantSlug] = useState('');
  const [branding, setBranding] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [codesJustCreated, setCodesJustCreated] = useState<string | null>(null);

  async function refreshAll() {
    if (!tenantSlug) return;
    try { setBranding(await getBranding(tenantSlug)); } catch {}
    try { setUsage(await getUsage(tenantSlug)); } catch {}
  }

  async function genCodes(evt: React.FormEvent<HTMLFormElement>) {
    evt.preventDefault();
    const form = new FormData(evt.currentTarget);
    const payload = {
      tenant_slug: String(form.get('tenant_slug')),
      count: Number(form.get('count') || 1),
      ttl_days: form.get('ttl_days') ? Number(form.get('ttl_days')) : undefined,
      label: form.get('label') ? String(form.get('label')) : undefined,
      max_uses: form.get('max_uses') ? Number(form.get('max_uses')) : undefined,
    } as any;
    const r = await fetch(`${apiBase}/admin/codes/generate`, { method:'POST', body: new URLSearchParams(Object.entries(payload).map(([k,v])=>[k,String(v)])) });
    if (r.redirected) {
      const url = new URL(r.url);
      const created = url.searchParams.get('created');
      setCodesJustCreated(created);
    }
  }

  return (
    <div style={{ maxWidth:920, margin:'24px auto', padding:'0 16px', color:'#e5e7eb', fontFamily:'system-ui' }}>
      <h1>Q2O Tenant Portal (Starter)</h1>
      <section style={{ background:'#111827', border:'1px solid #1f2937', borderRadius:12, padding:16, marginBottom:16 }}>
        <form onSubmit={(e)=>{e.preventDefault(); refreshAll();}}>
          <label>Tenant slug: <input value={tenantSlug} onChange={e=>setTenantSlug(e.target.value)} placeholder="acme" /></label>
          <button onClick={refreshAll} style={{ marginLeft:8 }}>Load</button>
        </form>
      </section>

      {branding && (
        <section style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
          <div style={{ background:'#111827', border:'1px solid #1f2937', borderRadius:12, padding:16 }}>
            <h3>Branding</h3>
            <BrandingPreview {...branding} />
          </div>
          <div style={{ background:'#111827', border:'1px solid #1f2937', borderRadius:12, padding:16 }}>
            <h3>Generate Activation Codes</h3>
            <form onSubmit={genCodes}>
              <input type="hidden" name="tenant_slug" value={tenantSlug} />
              <div><label>Count <input name="count" type="number" defaultValue={5} min={1} max={100} /></label></div>
              <div><label>TTL (days) <input name="ttl_days" type="number" placeholder="optional" /></label></div>
              <div><label>Max uses <input name="max_uses" type="number" defaultValue={1} min={1} /></label></div>
              <div><label>Label <input name="label" placeholder="onboard" /></label></div>
              <button type="submit">Generate</button>
            </form>
            {codesJustCreated && (
              <div style={{ marginTop:12, background:'#064e3b', border:'1px solid #065f46', padding:8, borderRadius:8 }}>
                <strong>Codes created (copy now, shown once):</strong>
                <pre>{codesJustCreated}</pre>
              </div>
            )}
          </div>
        </section>
      )}

      {usage && (
        <section style={{ background:'#111827', border:'1px solid #1f2937', borderRadius:12, padding:16, marginTop:16 }}>
          <h3>Usage (this month)</h3>
          <UsageMeter used={usage.runs} quota={usage.quota || 1} />
          <div style={{ marginTop:8, opacity:.7 }}>Plan: {usage.plan || '—'} • {usage.runs}/{usage.quota} runs</div>
        </section>
      )}

      <footer style={{ marginTop:24, opacity:0.6 }}>Bare-bones starter. Add auth & RBAC as needed.</footer>
    </div>
  );
}
