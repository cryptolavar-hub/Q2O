import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

interface Tenant {
  id: number;
  name: string;
  slug: string;
  logoUrl: string;
  primaryColor: string;
  domain: string | null;
  subscriptionPlan: string;
  subscriptionStatus: 'active' | 'trial' | 'expired' | 'cancelled';
  usageQuota: number;
  usageCurrent: number;
  createdAt: string;
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);

  useEffect(() => {
    // Mock data
    setTenants([
      {
        id: 1,
        name: 'Demo Consulting Firm',
        slug: 'demo',
        logoUrl: 'https://via.placeholder.com/150?text=Demo',
        primaryColor: '#875A7B',
        domain: 'demo.quick2odoo.com',
        subscriptionPlan: 'Pro',
        subscriptionStatus: 'active',
        usageQuota: 50,
        usageCurrent: 12,
        createdAt: '2025-11-01',
      },
    ]);
  }, []);

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-700 border-green-200',
      trial: 'bg-blue-100 text-blue-700 border-blue-200',
      expired: 'bg-red-100 text-red-700 border-red-200',
      cancelled: 'bg-gray-100 text-gray-700 border-gray-200',
    };
    return colors[status] || colors.active;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-main text-white shadow-lg">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-white hover:opacity-80 transition-opacity">
              <h1 className="text-3xl font-bold drop-shadow-md">👥 Tenants</h1>
            </Link>
            <button className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
              ➕ Add Tenant
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Tenant Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {tenants.map((tenant, i) => (
            <motion.div
              key={tenant.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300"
            >
              {/* Header */}
              <div className="flex items-start gap-4 mb-6">
                <div className="w-20 h-20 rounded-xl overflow-hidden flex-shrink-0 border-2 border-gray-200">
                  <img src={tenant.logoUrl} alt={tenant.name} className="w-full h-full object-cover" />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-gray-900 mb-1">{tenant.name}</h3>
                  <p className="text-sm text-gray-500 font-mono mb-2">{tenant.slug}</p>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(tenant.subscriptionStatus)}`}>
                    {tenant.subscriptionStatus.charAt(0).toUpperCase() + tenant.subscriptionStatus.slice(1)}
                  </span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-xs text-purple-600 font-medium mb-1">Subscription</p>
                  <p className="text-xl font-bold text-purple-700">{tenant.subscriptionPlan}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-xs text-blue-600 font-medium mb-1">Domain</p>
                  <p className="text-sm font-semibold text-blue-700 truncate">{tenant.domain || '—'}</p>
                </div>
              </div>

              {/* Usage Meter */}
              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-500 font-medium">Usage This Month</span>
                  <span className="font-bold text-gray-900">{tenant.usageCurrent}/{tenant.usageQuota}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-success h-full transition-all duration-500 rounded-full"
                    style={{ width: `${(tenant.usageCurrent / tenant.usageQuota) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {tenant.usageQuota - tenant.usageCurrent} migrations remaining
                </p>
              </div>

              {/* Branding Preview */}
              <div className="mb-6 p-4 rounded-lg border-2 border-gray-200">
                <p className="text-xs text-gray-500 font-medium mb-2">Brand Color</p>
                <div className="flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded-lg shadow-inner"
                    style={{ backgroundColor: tenant.primaryColor }}
                  />
                  <code className="text-sm font-mono text-gray-700">{tenant.primaryColor}</code>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button className="flex-1 py-2 bg-purple-50 text-purple-600 rounded-lg font-medium hover:bg-purple-100 transition-colors duration-200">
                  Edit
                </button>
                <button className="flex-1 py-2 bg-blue-50 text-blue-600 rounded-lg font-medium hover:bg-blue-100 transition-colors duration-200">
                  View Portal
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </main>
    </div>
  );
}

