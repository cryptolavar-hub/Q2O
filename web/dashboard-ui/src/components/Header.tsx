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
      <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl sm:text-3xl font-bold drop-shadow-md truncate">
              🤖 Q2O Multi-Agent Dashboard
            </h1>
            {projectName && (
              <p className="text-xs sm:text-sm opacity-90 mt-1 sm:mt-2 truncate">
                Project: <span className="font-semibold">{projectName}</span>
              </p>
            )}
          </div>
          <div className="flex-shrink-0">
            <ConnectionStatus connected={connected} error={error} />
          </div>
        </div>
      </div>
    </header>
  );
}

