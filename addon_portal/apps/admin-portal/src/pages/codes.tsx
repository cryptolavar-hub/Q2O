import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import QRCode from 'qrcode.react';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { getCodes, generateCodes, revokeCode, type ActivationCode } from '../lib/api';
import { getTenants, type Tenant } from '../lib/api';

export default function CodesPage() {
  const [codes, setCodes] = useState<ActivationCode[]>([]);
  const [totalCodes, setTotalCodes] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showQRCode, setShowQRCode] = useState<string | null>(null);
  const [generatedCodes, setGeneratedCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingCodes, setLoadingCodes] = useState(false);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
<<<<<<< Updated upstream
=======
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [tenantModalPage, setTenantModalPage] = useState(1);
  const [tenantModalPageSize, setTenantModalPageSize] = useState(10);
  const [tenantModalSearch, setTenantModalSearch] = useState('');
  const [tenantModalStatus, setTenantModalStatus] = useState('all');
  const [tenantModalData, setTenantModalData] = useState<TenantPage | null>(null);
  const [loadingTenantModal, setLoadingTenantModal] = useState(false);
  const [selectedGenerateTenant, setSelectedGenerateTenant] = useState<string>('');
>>>>>>> Stashed changes

  // Load tenants on mount
  useEffect(() => {
    loadTenants();
  }, []);

  // Load codes when filters or pagination changes
  useEffect(() => {
    loadCodes();
  }, [currentPage, pageSize, selectedTenant, selectedStatus, searchQuery]);

  const loadTenants = async () => {
    try {
      setLoadingTenants(true);
      const response = await getTenants({ page: 1, pageSize: 100 });
      setTenants(response.items);
    } catch (error) {
      console.error('Error loading tenants:', error);
    } finally {
      setLoadingTenants(false);
    }
  };

<<<<<<< Updated upstream
=======
  const loadTenantModalData = async () => {
    try {
      setLoadingTenantModal(true);
      const params: TenantQueryParams = {
        page: tenantModalPage,
        pageSize: tenantModalPageSize,
        search: tenantModalSearch.trim() || undefined,
        status: tenantModalStatus !== 'all' ? tenantModalStatus : undefined,
        sortField: 'created_at',
        sortDirection: 'desc',
      };
      const response = await getTenants(params);
      setTenantModalData(response);
    } catch (error) {
      console.error('Error loading tenant modal data:', error);
      setTenantModalData(null);
    } finally {
      setLoadingTenantModal(false);
    }
  };

  // Load tenant modal data when modal opens or filters change
  useEffect(() => {
    if (showTenantModal) {
      loadTenantModalData();
    }
  }, [showTenantModal, tenantModalPage, tenantModalPageSize, tenantModalSearch, tenantModalStatus]);

  // Reset selected tenant when Generate modal opens
  useEffect(() => {
    if (showGenerateModal && !selectedGenerateTenant) {
      setSelectedGenerateTenant('');
    }
  }, [showGenerateModal]);

  const handleSelectTenantFromModal = (tenant: Tenant) => {
    // Ensure the selected tenant is in the tenants list for the dropdown
    // If it's not already there, add it to the beginning of the list
    setTenants(prevTenants => {
      const tenantExists = prevTenants.some(t => t.slug === tenant.slug);
      if (!tenantExists) {
        return [tenant, ...prevTenants];
      }
      return prevTenants;
    });

    // If Generate modal is open, update the tenant selection in the form
    if (showGenerateModal) {
      setSelectedGenerateTenant(tenant.slug);
    } else {
      // Otherwise, update the filter on the main page
      setSelectedTenant(tenant.slug);
      setCurrentPage(1); // Reset to first page when filter changes
    }
    setShowTenantModal(false);
  };

>>>>>>> Stashed changes
  const loadCodes = async () => {
    try {
      setLoadingCodes(true);
      const tenantSlug = selectedTenant !== 'all' ? selectedTenant : undefined;
      const status = selectedStatus !== 'all' ? selectedStatus : undefined;
      const search = searchQuery.trim() || undefined;
      const response = await getCodes(tenantSlug, currentPage, pageSize, status, search);
      
      setCodes(response.codes);
      setTotalCodes(response.total);
      setTotalPages(response.total_pages);
      
      // Reset to page 1 if current page is beyond total pages
      if (currentPage > response.total_pages && response.total_pages > 0) {
        setCurrentPage(1);
      }
    } catch (error) {
      console.error('Error loading codes:', error);
      setCodes([]);
      setTotalCodes(0);
      setTotalPages(1);
    } finally {
      setLoadingCodes(false);
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleGenerateCodes = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);
    
    const formData = new FormData(e.currentTarget);
    try {
      const tenantSlug = formData.get('tenant_slug') as string;
      if (!tenantSlug) {
        throw new Error('Please select a tenant');
      }

      const codes = await generateCodes({
        tenant_slug: tenantSlug,
        count: Number(formData.get('count')),
        ttl_days: formData.get('ttl_days') ? Number(formData.get('ttl_days')) : undefined,
        label: formData.get('label') as string || undefined,
        max_uses: Number(formData.get('max_uses')) || 1,
      });
      
      setGeneratedCodes(codes);
      setShowGenerateModal(false);
      await loadCodes(); // Reload codes list
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error generating codes';
      setErrorMessage(errorMsg);
      console.error('Error generating codes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeCode = async (code: ActivationCode) => {
    if (confirm(`Are you sure you want to revoke code ${code.code}? This action cannot be undone.`)) {
      try {
        await revokeCode(code.id);
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

  const uniqueTenants = Array.from(new Set(tenants.map(t => t.slug)));

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
        <Breadcrumb items={[{ label: 'Activation Codes' }]} />

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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                placeholder="Search codes, tenant, or label..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1); // Reset to first page when search changes
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tenant</label>
              <select
                value={selectedTenant}
                onChange={(e) => {
                  setSelectedTenant(e.target.value);
                  setCurrentPage(1); // Reset to first page when filter changes
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Tenants</option>
                {tenants.map(tenant => (
                  <option key={tenant.slug} value={tenant.slug}>{tenant.name} ({tenant.slug})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={selectedStatus}
                onChange={(e) => {
                  setSelectedStatus(e.target.value);
                  setCurrentPage(1); // Reset to first page when filter changes
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
                <option value="used">Used</option>
                <option value="revoked">Revoked</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Items Per Page</label>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {codes.length > 0 ? ((currentPage - 1) * pageSize + 1) : 0} to {Math.min(currentPage * pageSize, totalCodes)} of {totalCodes} codes
            </div>
            {loadingCodes && (
              <div className="text-sm text-gray-500">Loading...</div>
            )}
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
                {loadingCodes ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      Loading codes...
                    </td>
                  </tr>
                ) : codes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      {searchQuery || selectedTenant !== 'all' || selectedStatus !== 'all' 
                        ? 'No codes match your filters' 
                        : 'No activation codes yet'}
                    </td>
                  </tr>
                ) : (
                  codes.map((code, i) => (
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
          
          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      currentPage === 1
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    ← Previous
                  </button>
                  
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum: number;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                            currentPage === pageNum
                              ? 'bg-purple-600 text-white'
                              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      currentPage === totalPages
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    Next →
                  </button>
                </div>
                
                <div className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </div>
              </div>
            </div>
          )}
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
          onClick={() => {
            setShowGenerateModal(false);
            setErrorMessage(null);
            setSelectedGenerateTenant(''); // Reset selection when closing
          }}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Generate Activation Codes</h3>
            
            {errorMessage && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">{errorMessage}</p>
              </div>
            )}

            <form onSubmit={handleGenerateCodes} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tenant *</label>
                <div className="space-y-2">
                  <select 
                    name="tenant_slug" 
                    value={selectedGenerateTenant}
                    onChange={(e) => setSelectedGenerateTenant(e.target.value)}
                    required
                    disabled={loadingTenants}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  >
                    <option value="">{loadingTenants ? 'Loading tenants...' : 'Select tenant...'}</option>
                    {tenants.map(tenant => (
                      <option key={tenant.slug} value={tenant.slug}>
                        {tenant.name} ({tenant.slug})
                      </option>
                    ))}
                  </select>
                  {totalTenants > 10 && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowTenantModal(true);
                        setTenantModalPage(1);
                        setTenantModalSearch('');
                        setTenantModalStatus('all');
                      }}
                      className="w-full text-sm text-purple-600 hover:text-purple-800 font-medium text-left underline"
                    >
                      See More →
                    </button>
                  )}
                </div>
                {tenants.length === 0 && !loadingTenants && (
                  <p className="mt-1 text-sm text-amber-600">No tenants available. Create a tenant first.</p>
                )}
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
                  onClick={() => {
                    setShowGenerateModal(false);
                    setSelectedGenerateTenant(''); // Reset selection when closing
                  }}
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
      <Footer />
    </div>
  );
}
