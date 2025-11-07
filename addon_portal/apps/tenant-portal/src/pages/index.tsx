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
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #FF6B9D 0%, #C44569 25%, #9B59B6 50%, #8E44AD 75%, #6C3483 100%)',
      padding: '48px 16px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{ maxWidth: 920, margin: '0 auto' }}>
        <h1 style={{ 
          color: '#FFFFFF', 
          fontSize: '2.5rem', 
          fontWeight: '700',
          marginBottom: '32px',
          textAlign: 'center',
          textShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          Q2O Tenant Portal
        </h1>
        
        <section style={{ 
          background: '#FFFFFF', 
          borderRadius: 16, 
          padding: 32, 
          marginBottom: 24,
          boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
        }}>
          <form onSubmit={(e)=>{e.preventDefault(); refreshAll();}}>
            <label style={{ 
              display: 'block',
              color: '#2C3E50',
              fontSize: '1rem',
              fontWeight: '600',
              marginBottom: 12
            }}>
              Tenant slug:
            </label>
            <div style={{ display: 'flex', gap: 12 }}>
              <input 
                value={tenantSlug} 
                onChange={e=>setTenantSlug(e.target.value)} 
                placeholder="e.g., demo, mycompany" 
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  border: '2px solid #E0E0E0',
                  borderRadius: 8,
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'border-color 0.3s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#9B59B6'}
                onBlur={(e) => e.target.style.borderColor = '#E0E0E0'}
              />
              <button 
                onClick={refreshAll} 
                style={{ 
                  padding: '12px 32px',
                  background: 'linear-gradient(135deg, #4CAF50 0%, #45A049 100%)',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
                  transition: 'transform 0.2s, box-shadow 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 16px rgba(76, 175, 80, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(76, 175, 80, 0.3)';
                }}
              >
                Load Demo
              </button>
            </div>
          </form>
        </section>

      {branding && (
        <section style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:24, marginBottom: 24 }}>
          <div style={{ 
            background:'#FFFFFF', 
            borderRadius:16, 
            padding:32,
            boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
          }}>
            <h3 style={{ 
              color: '#2C3E50', 
              fontSize: '1.5rem', 
              fontWeight: '700', 
              marginBottom: 20 
            }}>
              Branding
            </h3>
            <BrandingPreview {...branding} />
          </div>
          <div style={{ 
            background:'#FFFFFF', 
            borderRadius:16, 
            padding:32,
            boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
          }}>
            <h3 style={{ 
              color: '#2C3E50', 
              fontSize: '1.5rem', 
              fontWeight: '700', 
              marginBottom: 20 
            }}>
              Generate Activation Codes
            </h3>
            <form onSubmit={genCodes}>
              <input type="hidden" name="tenant_slug" value={tenantSlug} />
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#555', fontWeight: '600', marginBottom: 8 }}>
                  Count 
                  <input 
                    name="count" 
                    type="number" 
                    defaultValue={5} 
                    min={1} 
                    max={100} 
                    style={{ 
                      display: 'block', 
                      width: '100%', 
                      marginTop: 4,
                      padding: '10px 12px', 
                      border: '2px solid #E0E0E0', 
                      borderRadius: 8,
                      fontSize: '1rem'
                    }} 
                  />
                </label>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#555', fontWeight: '600', marginBottom: 8 }}>
                  TTL (days) 
                  <input 
                    name="ttl_days" 
                    type="number" 
                    placeholder="optional" 
                    style={{ 
                      display: 'block', 
                      width: '100%', 
                      marginTop: 4,
                      padding: '10px 12px', 
                      border: '2px solid #E0E0E0', 
                      borderRadius: 8,
                      fontSize: '1rem'
                    }} 
                  />
                </label>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#555', fontWeight: '600', marginBottom: 8 }}>
                  Max uses 
                  <input 
                    name="max_uses" 
                    type="number" 
                    defaultValue={1} 
                    min={1} 
                    style={{ 
                      display: 'block', 
                      width: '100%', 
                      marginTop: 4,
                      padding: '10px 12px', 
                      border: '2px solid #E0E0E0', 
                      borderRadius: 8,
                      fontSize: '1rem'
                    }} 
                  />
                </label>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#555', fontWeight: '600', marginBottom: 8 }}>
                  Label 
                  <input 
                    name="label" 
                    placeholder="onboard" 
                    style={{ 
                      display: 'block', 
                      width: '100%', 
                      marginTop: 4,
                      padding: '10px 12px', 
                      border: '2px solid #E0E0E0', 
                      borderRadius: 8,
                      fontSize: '1rem'
                    }} 
                  />
                </label>
              </div>
              <button 
                type="submit"
                style={{ 
                  width: '100%',
                  padding: '12px',
                  background: 'linear-gradient(135deg, #4CAF50 0%, #45A049 100%)',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
                  transition: 'transform 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                Generate
              </button>
            </form>
            {codesJustCreated && (
              <div style={{ 
                marginTop:16, 
                background:'linear-gradient(135deg, #27AE60 0%, #229954 100%)', 
                padding:16, 
                borderRadius:12,
                boxShadow: '0 4px 12px rgba(39, 174, 96, 0.3)'
              }}>
                <strong style={{ color: '#FFFFFF', display: 'block', marginBottom: 8 }}>
                  Codes created (copy now, shown once):
                </strong>
                <pre style={{ 
                  background: 'rgba(255,255,255,0.2)', 
                  padding: 12, 
                  borderRadius: 8,
                  color: '#FFFFFF',
                  fontSize: '0.9rem',
                  overflowX: 'auto'
                }}>
                  {codesJustCreated}
                </pre>
              </div>
            )}
          </div>
        </section>
      )}

      {usage && (
        <section style={{ 
          background:'#FFFFFF', 
          borderRadius:16, 
          padding:32, 
          marginTop:24,
          boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
        }}>
          <h3 style={{ 
            color: '#2C3E50', 
            fontSize: '1.5rem', 
            fontWeight: '700', 
            marginBottom: 20 
          }}>
            Usage (this month)
          </h3>
          <UsageMeter used={usage.runs} quota={usage.quota || 1} />
          <div style={{ 
            marginTop:16, 
            color: '#555', 
            fontSize: '1rem',
            fontWeight: '500'
          }}>
            Plan: <strong>{usage.plan || '—'}</strong> • {usage.runs}/{usage.quota} runs
          </div>
        </section>
      )}

      <footer style={{ 
        marginTop:48, 
        textAlign: 'center',
        color: 'rgba(255,255,255,0.8)',
        fontSize: '0.9rem',
        paddingBottom: 32
      }}>
        Quick2Odoo Tenant Portal • Powered by agents that build everything
      </footer>
      </div>
    </div>
  );
}
