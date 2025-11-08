import React from 'react';

interface ConnectionStatusProps {
  connected: boolean;
  error?: string | null;
}

export function ConnectionStatus({ connected, error }: ConnectionStatusProps) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500 animate-pulse-slow' : 'bg-red-500'}`} />
      <span className={`text-sm font-medium ${connected ? 'text-green-600' : 'text-red-600'}`}>
        {connected ? '🟢 Live' : '🔴 Disconnected'}
      </span>
      {error && (
        <span className="text-xs text-gray-500 ml-2">({error})</span>
      )}
    </div>
  );
}

