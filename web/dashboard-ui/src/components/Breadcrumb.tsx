import React from 'react';
import { HomeIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex items-center space-x-2 text-sm mb-6" aria-label="Breadcrumb">
      <a
        href="/"
        className="text-gray-500 hover:text-purple-600 transition-colors flex items-center"
      >
        <HomeIcon className="w-4 h-4" />
      </a>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRightIcon className="w-4 h-4 text-gray-400" />
          {item.href ? (
            <a
              href={item.href}
              className="text-gray-500 hover:text-purple-600 transition-colors"
            >
              {item.label}
            </a>
          ) : (
            <span className="text-gray-900 font-medium">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

