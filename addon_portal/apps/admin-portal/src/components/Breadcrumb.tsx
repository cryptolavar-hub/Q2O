import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function Breadcrumb() {
  const router = useRouter();
  
  const pathMap: { [key: string]: string } = {
    '/': 'Dashboard',
    '/codes': 'Activation Codes',
    '/devices': 'Devices',
    '/tenants': 'Tenants',
    '/analytics': 'Analytics',
  };

  const currentPath = router.pathname;
  const breadcrumbs: BreadcrumbItem[] = [
    { label: '🏠 Home', href: '/' },
  ];

  if (currentPath !== '/') {
    breadcrumbs.push({ label: pathMap[currentPath] || 'Page' });
  }

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-6 py-3">
        <nav className="flex items-center gap-2 text-sm">
          {breadcrumbs.map((item, index) => (
            <React.Fragment key={index}>
              {index > 0 && (
                <span className="text-gray-400">/</span>
              )}
              {item.href ? (
                <Link 
                  href={item.href}
                  className="text-purple-600 hover:text-purple-800 font-medium transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span className="text-gray-600 font-medium">{item.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      </div>
    </div>
  );
}

