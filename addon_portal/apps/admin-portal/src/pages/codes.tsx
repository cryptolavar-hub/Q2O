import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import QRCode from 'qrcode.react';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

interface ActivationCode {
  id: number;
  code: string;
  tenant: string;
  label: string | null;
  status: 'active' | 'expired' | 'used' | 'revoked';
  expiresAt: string | null;
  usedAt: string | null;
  createdAt: string;
  useCount: number;
  maxUses: number;
}

export default function CodesPage() {
  const [codes, setCodes] = useState<ActivationCode[]>([]);
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showQRCode, setShowQRCode] = useState<string | null>(null);

  // Mock data
  useEffect(() => {
    setCodes([
      { id: 1, code: '8PL4-M5HA-QP3E-MPCT', tenant: 'Demo Consulting', label: 'Onboarding', status: 'active', expiresAt: '2025-12-07', usedAt: null, createdAt: '2025-11-07', useCount: 0, maxUses: 1 },
      { id: 2, code: 'ND7V-A9B5-ACP7-85KW', tenant: 'Demo Consulting', label: 'Trial', status: 'active', expiresAt: '2025-12-07', usedAt: null, createdAt: '2025-11-07', useCount: 0, maxUses: 1 },
      { id: 3, code: '5EFZ-7CHR-QLKS-JQMJ', tenant: 'Demo Consulting', label: null, status: 'active', expiresAt: '2025-12-07', usedAt: null, createdAt: '2025-11-07', useCount: 0, maxUses: 1 },
    ]);
  }, []);

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-700 border-green-200',
      expired: 'bg-red-100 text-red-700 border-red-200',
      used: 'bg-gray-100 text-gray-700 border-gray-200',
      revoked: 'bg-orange-100 text-orange-700 border-orange-200',
    };
    return colors[status] || colors.active;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Show toast notification (would implement toast system)
    alert('Code copied to clipboard!');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="🔑 Activation Codes"
        subtitle="Manage and generate activation codes for tenants"
        action={
          <button
            onClick={() => setShowGenerateModal(true)}
            className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
          >
            ➕ Generate Codes
          </button>
        }
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        {/* Filters */}
        <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                placeholder="Search codes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tenant</label>
              <select
                value={selectedTenant}
                onChange={(e) => setSelectedTenant(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Tenants</option>
                <option value="demo">Demo Consulting</option>
                <option value="acme">Acme Corp</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500">
                <option>All Statuses</option>
                <option>Active</option>
                <option>Expired</option>
                <option>Used</option>
                <option>Revoked</option>
              </select>
            </div>
          </div>
        </div>

        {/* Codes Table */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Code
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Tenant
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Label
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Expires
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Usage
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {codes.map((code, i) => (
                  <motion.tr
                    key={code.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="hover:bg-gray-50 transition-colors duration-150"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <code className="font-mono text-sm font-semibold text-purple-600 bg-purple-50 px-3 py-1 rounded">
                          {code.code}
                        </code>
                        <button
                          onClick={() => copyToClipboard(code.code)}
                          className="text-gray-400 hover:text-purple-600 transition-colors"
                          title="Copy code"
                        >
                          📋
                        </button>
                        <button
                          onClick={() => setShowQRCode(code.code)}
                          className="text-gray-400 hover:text-purple-600 transition-colors"
                          title="Show QR code"
                        >
                          📱
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">{code.tenant}</span>
                    </td>
                    <td className="px-6 py-4">
                      {code.label ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {code.label}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(code.status)}`}>
                        {code.status.charAt(0).toUpperCase() + code.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {code.expiresAt || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-gradient-success h-full transition-all duration-300"
                            style={{ width: `${(code.useCount / code.maxUses) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-gray-600">
                          {code.useCount}/{code.maxUses}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-red-600 hover:text-red-800 text-sm font-medium transition-colors">
                        Revoke
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* QR Code Modal */}
      {showQRCode && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">QR Code</h3>
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-white rounded-xl border-4 border-purple-500">
                <QRCode value={showQRCode} size={200} />
              </div>
            </div>
            <p className="text-center font-mono text-sm text-gray-600 mb-6">{showQRCode}</p>
            <button
              onClick={() => setShowQRCode(null)}
              className="w-full bg-gradient-main text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all duration-300"
            >
              Close
            </button>
          </motion.div>
        </div>
      )}

      {/* Generate Modal (placeholder) */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl"
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Generate Activation Codes</h3>
            
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tenant</label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500">
                  <option>Demo Consulting</option>
                  <option>Acme Corp</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Count</label>
                  <input type="number" defaultValue={5} min={1} max={100} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Max Uses</label>
                  <input type="number" defaultValue={1} min={1} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">TTL (days)</label>
                  <input type="number" placeholder="Optional" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Label</label>
                  <input type="text" placeholder="e.g., onboarding" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-success text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  Generate Codes
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}

