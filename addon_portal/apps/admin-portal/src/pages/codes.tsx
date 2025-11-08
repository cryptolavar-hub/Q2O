import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import QRCode from 'qrcode.react';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { getCodes, generateCodes, revokeCode, type ActivationCode } from '../lib/api';

export default function CodesPage() {
  const [allCodes, setAllCodes] = useState<ActivationCode[]>([]);
  const [filteredCodes, setFilteredCodes] = useState<ActivationCode[]>([]);
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showQRCode, setShowQRCode] = useState<string | null>(null);
  const [generatedCodes, setGeneratedCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Load codes
  useEffect(() => {
    loadCodes();
  }, []);

  const loadCodes = async () => {
    try {
      const codes = await getCodes();
      setAllCodes(codes);
      setFilteredCodes(codes);
    } catch (error) {
      console.error('Error loading codes:', error);
    }
  };

  // Apply filters whenever search, tenant, or status changes
  useEffect(() => {
    let filtered = [...allCodes];

    // Filter by tenant
    if (selectedTenant !== 'all') {
      filtered = filtered.filter(code => code.tenant.toLowerCase().includes(selectedTenant.toLowerCase()));
    }

    // Filter by status
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(code => code.status === selectedStatus);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(code => 
        code.code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        code.tenant.toLowerCase().includes(searchQuery.toLowerCase()) ||
        code.label?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredCodes(filtered);
  }, [searchQuery, selectedTenant, selectedStatus, allCodes]);

  const handleGenerateCodes = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    
    const formData = new FormData(e.currentTarget);
    try {
      const codes = await generateCodes({
        tenant_slug: formData.get('tenant_slug') as string,
        count: Number(formData.get('count')),
        ttl_days: formData.get('ttl_days') ? Number(formData.get('ttl_days')) : undefined,
        label: formData.get('label') as string || undefined,
        max_uses: Number(formData.get('max_uses')) || 1,
      });
      
      setGeneratedCodes(codes);
      setShowGenerateModal(false);
      await loadCodes(); // Reload codes list
    } catch (error) {
      alert('Error generating codes: ' + error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeCode = async (code: ActivationCode) => {
    if (confirm(`Are you sure you want to revoke code ${code.code}? This action cannot be undone.`)) {
      try {
        await revokeCode(code.tenant, code.code || '');
        await loadCodes(); // Reload codes list
        alert('Code revoked successfully');
      } catch (error) {
        alert('Error revoking code: ' + error);
      }
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-700 border-green-200',
      expired: 'bg-red-100 text-red-700 border-red-200',
      used: 'bg-gray-100 text-gray-700 border-gray-200',
      revoked: 'bg-orange-100 text-orange-700 border-orange-200',
    };
    return colors[status as keyof typeof colors] || colors.active;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.textContent = '✅ Code copied to clipboard!';
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 2000);
  };

  const uniqueTenants = Array.from(new Set(allCodes.map(c => c.tenant)));

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
        {/* Generated Codes Success Banner */}
        {generatedCodes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border-2 border-green-200 rounded-2xl p-6 mb-6"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-bold text-green-800 mb-2">✅ Codes Generated Successfully!</h3>
                <p className="text-sm text-green-700 mb-3">Save these codes now - they won't be shown again:</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {generatedCodes.map((code, i) => (
                    <div key={i} className="bg-white rounded-lg p-3 border border-green-200">
                      <code className="text-purple-600 font-bold text-sm">{code}</code>
                      <button
                        onClick={() => copyToClipboard(code)}
                        className="ml-2 text-xs text-purple-600 hover:text-purple-800"
                      >
                        📋 Copy
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              <button
                onClick={() => setGeneratedCodes([])}
                className="text-green-600 hover:text-green-800 ml-4"
              >
                ✕
              </button>
            </div>
          </motion.div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                placeholder="Search codes, tenant, or label..."
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
                {uniqueTenants.map(tenant => (
                  <option key={tenant} value={tenant}>{tenant}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
                <option value="used">Used</option>
                <option value="revoked">Revoked</option>
              </select>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredCodes.length} of {allCodes.length} codes
          </div>
        </div>

        {/* Codes Table */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Code</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Tenant</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Label</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Expires</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Usage</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredCodes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      {searchQuery || selectedTenant !== 'all' || selectedStatus !== 'all' 
                        ? 'No codes match your filters' 
                        : 'No activation codes yet'}
                    </td>
                  </tr>
                ) : (
                  filteredCodes.map((code, i) => (
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
                            {code.code || '****-****-****-****'}
                          </code>
                          {code.code && (
                            <>
                              <button
                                onClick={() => copyToClipboard(code.code!)}
                                className="text-gray-400 hover:text-purple-600 transition-colors"
                                title="Copy code"
                              >
                                📋
                              </button>
                              <button
                                onClick={() => setShowQRCode(code.code!)}
                                className="text-gray-400 hover:text-purple-600 transition-colors"
                                title="Show QR code"
                              >
                                📱
                              </button>
                            </>
                          )}
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
                        <button
                          onClick={() => handleRevokeCode(code)}
                          disabled={code.status === 'revoked'}
                          className={`text-sm font-medium transition-colors ${
                            code.status === 'revoked'
                              ? 'text-gray-400 cursor-not-allowed'
                              : 'text-red-600 hover:text-red-800'
                          }`}
                        >
                          {code.status === 'revoked' ? 'Revoked' : 'Revoke'}
                        </button>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* QR Code Modal */}
      {showQRCode && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowQRCode(null)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
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

      {/* Generate Modal */}
      {showGenerateModal && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowGenerateModal(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Generate Activation Codes</h3>
            
            <form onSubmit={handleGenerateCodes} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tenant *</label>
                <select 
                  name="tenant_slug" 
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Select tenant...</option>
                  <option value="demo">Demo Consulting</option>
                  <option value="acme">Acme Corp</option>
                  <option value="techsolutions">Tech Solutions</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Count *</label>
                  <input 
                    name="count"
                    type="number" 
                    defaultValue={5} 
                    min={1} 
                    max={100}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Max Uses *</label>
                  <input 
                    name="max_uses"
                    type="number" 
                    defaultValue={1} 
                    min={1}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">TTL (days)</label>
                  <input 
                    name="ttl_days"
                    type="number" 
                    placeholder="Optional (e.g., 30)" 
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Label</label>
                  <input 
                    name="label"
                    type="text" 
                    placeholder="e.g., onboarding" 
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  disabled={loading}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-gradient-success text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50"
                >
                  {loading ? 'Generating...' : 'Generate Codes'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
