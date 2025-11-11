import React from 'react';
import Link from 'next/link';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({ items }) => {
  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-6" aria-label="Breadcrumb">
      {/* Home icon as first item */}
      <Link 
        href="/" 
        className="flex items-center hover:text-purple-600 transition-colors"
        aria-label="Home"
      >
        <HomeIcon className="h-4 w-4" />
      </Link>

      {/* Render breadcrumb items */}
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <React.Fragment key={index}>
            {/* Separator */}
            <ChevronRightIcon className="h-4 w-4 text-gray-400" />

            {/* Breadcrumb item */}
            {item.href && !isLast ? (
              <Link 
                href={item.href}
                className="hover:text-purple-600 transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? 'text-gray-900 font-medium' : ''}>
                {item.label}
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumb;
