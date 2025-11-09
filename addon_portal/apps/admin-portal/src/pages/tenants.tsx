import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { getTenants, addTenant, editTenant, type Tenant, type AddTenantRequest, type EditTenantRequest } from '../lib/api';

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const data = await getTenants();
      setTenants(data);
    } catch (error) {
      console.error('Error loading tenants:', error);
    }
  };

  const handleAddTenant = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    try {
      const tenantData: AddTenantRequest = {
        name: formData.get('name') as string,
        slug: formData.get('slug') as string,
        logo_url: formData.get('logo_url') as string || undefined,
        primary_color: formData.get('primary_color') as string || '#875A7B',
        domain: formData.get('domain') as string || undefined,
        subscription_plan: formData.get('subscription_plan') as string || 'Starter',
        usage_quota: parseInt(formData.get('usage_quota') as string) || 10,
      };
      
      await addTenant(tenantData);
      setShowAddModal(false);
      await loadTenants(); // Reload to show new tenant
      alert('✅ Tenant created successfully!');
    } catch (error) {
      alert(`❌ Failed to create tenant: ${error}`);
    }
  };

  const handleEditTenant = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    if (!selectedTenant) return;
    
    try {
      const updateData: EditTenantRequest = {
        name: formData.get('name') as string || undefined,
        logo_url: formData.get('logo_url') as string || undefined,
        primary_color: formData.get('primary_color') as string || undefined,
        domain: formData.get('domain') as string || undefined,
        subscription_plan: formData.get('subscription_plan') as string || undefined,
        usage_quota: parseInt(formData.get('usage_quota') as string) || undefined,
      };
      
      await editTenant(selectedTenant.slug, updateData);
      setShowEditModal(false);
      setSelectedTenant(null);
      await loadTenants(); // Reload to show updates
      alert('✅ Tenant updated successfully!');
    } catch (error) {
      alert(`❌ Failed to update tenant: ${error}`);
    }
  };

  const openEditModal = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setShowEditModal(true);
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-700 border-green-200',
      trial: 'bg-blue-100 text-blue-700 border-blue-200',
      expired: 'bg-red-100 text-red-700 border-red-200',
      cancelled: 'bg-gray-100 text-gray-700 border-gray-200',
    };
    return colors[status as keyof typeof colors] || colors.active;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="👥 Tenants"
        subtitle="Manage tenant organizations and subscriptions"
        action={
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
          >
            ➕ Add Tenant
          </button>
        }
      />
      <Navigation />

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
                <button
                  onClick={() => openEditModal(tenant)}
                  className="flex-1 py-2 bg-purple-50 text-purple-600 rounded-lg font-medium hover:bg-purple-100 transition-colors duration-200"
                >
                  ✏️ Edit
                </button>
                <button
                  className="flex-1 py-2 bg-blue-50 text-blue-600 rounded-lg font-medium hover:bg-blue-100 transition-colors duration-200"
                >
                  👁️ View Portal
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </main>

      {/* Add Tenant Modal */}
      {showAddModal && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowAddModal(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Add New Tenant</h3>
            
            <form onSubmit={handleAddTenant} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tenant Name *</label>
                <input 
                  name="name"
                  type="text" 
                  required
                  placeholder="e.g., Acme Corporation"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Slug *</label>
                  <input 
                    name="slug"
                    type="text" 
                    required
                    placeholder="e.g., acme"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Domain</label>
                  <input 
                    name="domain"
                    type="text" 
                    placeholder="e.g., acme.quick2odoo.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Subscription Plan *</label>
                  <select 
                    name="plan"
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Select plan...</option>
                    <option value="starter">Starter (10 migrations/mo)</option>
                    <option value="pro">Pro (50 migrations/mo)</option>
                    <option value="enterprise">Enterprise (200 migrations/mo)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Primary Color *</label>
                  <input 
                    name="primary_color"
                    type="color" 
                    defaultValue="#875A7B"
                    className="w-full h-10 px-2 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Logo URL</label>
                <input 
                  name="logo_url"
                  type="url" 
                  placeholder="https://example.com/logo.png"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-success text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  Create Tenant
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Edit Tenant Modal */}
      {showEditModal && selectedTenant && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => { setShowEditModal(false); setSelectedTenant(null); }}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Edit Tenant: {selectedTenant.name}</h3>
            
            <form onSubmit={handleEditTenant} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tenant Name *</label>
                <input 
                  name="name"
                  type="text" 
                  required
                  defaultValue={selectedTenant.name}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Slug</label>
                  <input 
                    name="slug"
                    type="text" 
                    disabled
                    defaultValue={selectedTenant.slug}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed" 
                  />
                  <p className="text-xs text-gray-500 mt-1">Slug cannot be changed</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Domain</label>
                  <input 
                    name="domain"
                    type="text" 
                    defaultValue={selectedTenant.domain || ''}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Subscription Status</label>
                  <select 
                    name="status"
                    defaultValue={selectedTenant.subscriptionStatus}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="active">Active</option>
                    <option value="trial">Trial</option>
                    <option value="expired">Expired</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Primary Color</label>
                  <input 
                    name="primary_color"
                    type="color" 
                    defaultValue={selectedTenant.primaryColor}
                    className="w-full h-10 px-2 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Logo URL</label>
                <input 
                  name="logo_url"
                  type="url" 
                  defaultValue={selectedTenant.logoUrl}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowEditModal(false); setSelectedTenant(null); }}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-main text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
