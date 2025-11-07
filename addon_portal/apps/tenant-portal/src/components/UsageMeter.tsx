import React from 'react';
export function UsageMeter({ used, quota }: { used: number; quota: number; }) {
  const pct = Math.min(100, Math.round((used / Math.max(1, quota)) * 100));
  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between' }}>
        <span>Usage</span><span>{used} / {quota}</span>
      </div>
      <div style={{ height:8, background:'#1f2937', borderRadius:999, marginTop:6 }}>
        <div style={{ 
          width:`${pct}%`, 
          height:8, 
          borderRadius:999,
          background: pct >= 90 ? '#ef4444' : pct >= 75 ? '#f59e0b' : '#3b82f6'
        }} />
      </div>
    </div>
  );
}
