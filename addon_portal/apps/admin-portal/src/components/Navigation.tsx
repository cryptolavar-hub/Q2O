import React, { useState } from 'react';
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
  { href: '/llm', label: 'LLM Management', icon: '🤖' },
];

export function Navigation() {
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6">
          {/* Mobile menu button */}
          <div className="flex items-center justify-between md:hidden py-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-gray-600 hover:text-purple-600 hover:bg-gray-100 transition-colors"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {mobileMenuOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
            <span className="text-sm font-semibold text-gray-700">Menu</span>
          </div>

          {/* Mobile menu (collapsible) */}
          {mobileMenuOpen && (
            <div className="md:hidden pb-4 border-t border-gray-200">
              <div className="flex flex-col gap-1 pt-2">
                {navItems.map((item) => {
                  const isActive = router.pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`
                        py-3 px-4 rounded-lg transition-all duration-200 flex items-center gap-2 text-sm font-medium
                        ${isActive 
                          ? 'bg-purple-50 text-purple-600 border-l-4 border-purple-600' 
                          : 'text-gray-600 hover:text-purple-600 hover:bg-gray-50'
                        }
                      `}
                    >
                      <span className="text-lg">{item.icon}</span>
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}

          {/* Desktop horizontal menu */}
          <div className="hidden md:flex gap-1 text-sm font-medium overflow-x-auto scrollbar-hide">
            {navItems.map((item) => {
              const isActive = router.pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    py-4 px-3 lg:px-4 border-b-2 transition-all duration-200 flex items-center gap-2 whitespace-nowrap flex-shrink-0
                    ${isActive 
                      ? 'border-purple-600 text-purple-600 bg-purple-50/50' 
                      : 'border-transparent text-gray-600 hover:text-purple-600 hover:border-gray-300 hover:bg-gray-50'
                    }
                  `}
                >
                  <span className="text-base">{item.icon}</span>
                  <span className="hidden lg:inline">{item.label}</span>
                  <span className="lg:hidden">{item.label.split(' ')[0]}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>
    </>
  );
}

