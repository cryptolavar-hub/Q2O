import React from 'react';
import { ConnectionStatus } from './ConnectionStatus';

interface HeaderProps {
  connected: boolean;
  error?: string | null;
  projectName?: string;
}

export function Header({ connected, error, projectName }: HeaderProps) {
  return (
    <header className="bg-gradient-main text-white shadow-lg">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold drop-shadow-md">
              🤖 Quick2Odoo Multi-Agent Dashboard
            </h1>
            {projectName && (
              <p className="text-sm opacity-90 mt-1">
                Project: <span className="font-semibold">{projectName}</span>
              </p>
            )}
          </div>
          <ConnectionStatus connected={connected} error={error} />
        </div>
      </div>
    </header>
  );
}

