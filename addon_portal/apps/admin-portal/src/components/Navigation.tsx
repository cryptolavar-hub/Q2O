import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: '🏠' },
  { href: '/codes', label: 'Activation Codes', icon: '🔑' },
  { href: '/devices', label: 'Devices', icon: '📱' },
  { href: '/tenants', label: 'Tenants', icon: '👥' },
  { href: '/analytics', label: 'Analytics', icon: '📊' },
];

export function Navigation() {
  const router = useRouter();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-6">
        <div className="flex gap-1 text-sm font-medium">
          {navItems.map((item) => {
            const isActive = router.pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  py-4 px-4 border-b-2 transition-all duration-200 flex items-center gap-2
                  ${isActive 
                    ? 'border-purple-600 text-purple-600 bg-purple-50/50' 
                    : 'border-transparent text-gray-600 hover:text-purple-600 hover:border-gray-300 hover:bg-gray-50'
                  }
                `}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

