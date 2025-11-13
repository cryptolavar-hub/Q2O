import React from 'react';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-12 pb-6 text-center text-sm text-gray-500">
      <p className="font-medium">Q2O Licensing Admin Portal • Multi-tenant command center</p>
      <p className="mt-1 text-xs text-gray-400">
        Powered by Quick to Objective Multi-Agentic Platform - Copyright {currentYear}
      </p>
    </footer>
  );
}

