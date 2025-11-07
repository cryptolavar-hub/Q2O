import React from 'react';
export function BrandingPreview({ logo_url, primary_color, domain }: { logo_url?: string; primary_color?: string; domain?: string; }) {
  return (
    <div style={{ border:'1px solid #222', borderRadius:12, padding:16 }}>
      <div style={{ display:'flex', alignItems:'center', gap:12 }}>
        {logo_url && <img src={logo_url} alt="logo" style={{ height:40 }} />}
        <strong>{domain || 'tenant domain'}</strong>
      </div>
      <div style={{ height:8, marginTop:12, background: primary_color || '#2563eb', borderRadius:999 }} />
    </div>
  );
}
