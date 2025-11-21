import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Navigation } from '../components/Navigation';
import { SessionGuard } from '../components/SessionGuard';
import { Breadcrumb } from '../components/Breadcrumb';
import { getTenantProfile, updateTenantProfile, type TenantProfile, type TenantProfileUpdate } from '../lib/api';
import { getStoredSessionToken } from '../lib/auth';

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<TenantProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editForm, setEditForm] = useState<TenantProfileUpdate>({});

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const sessionToken = getStoredSessionToken();
      if (!sessionToken) {
        router.push('/login');
        return;
      }
      const data = await getTenantProfile(sessionToken);
      setProfile(data);
      setEditForm({
        name: data.name,
        email: data.email || '',
        phoneNumber: data.phoneNumber || '',
        logoUrl: data.logoUrl || '',
        primaryColor: data.primaryColor || '',
        domain: data.domain || '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
    if (profile) {
      setEditForm({
        name: profile.name,
        email: profile.email || '',
        phoneNumber: profile.phoneNumber || '',
        logoUrl: profile.logoUrl || '',
        primaryColor: profile.primaryColor || '',
        domain: profile.domain || '',
      });
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      const sessionToken = getStoredSessionToken();
      if (!sessionToken) {
        router.push('/login');
        return;
      }

      // Only send fields that have changed
      const updates: TenantProfileUpdate = {};
      if (editForm.name !== profile?.name) updates.name = editForm.name;
      if (editForm.email !== profile?.email) updates.email = editForm.email;
      if (editForm.phoneNumber !== profile?.phoneNumber) updates.phoneNumber = editForm.phoneNumber;
      if (editForm.logoUrl !== profile?.logoUrl) updates.logoUrl = editForm.logoUrl;
      if (editForm.primaryColor !== profile?.primaryColor) updates.primaryColor = editForm.primaryColor;
      if (editForm.domain !== profile?.domain) updates.domain = editForm.domain;

      const updated = await updateTenantProfile(sessionToken, updates);
      setProfile(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof TenantProfileUpdate, value: string) => {
    setEditForm((prev) => ({ ...prev, [field]: value }));
  };

  const getUsagePercentage = () => {
    if (!profile || profile.usageQuota === 0) return 0;
    return Math.min(100, Math.round((profile.usageCurrent / profile.usageQuota) * 100));
  };

  const getActivationCodePercentage = () => {
    if (!profile || profile.activationCodesTotal === 0) return 0;
    return Math.min(100, Math.round((profile.activationCodesUsed / profile.activationCodesTotal) * 100));
  };

  const getStatusBadgeColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trialing':
        return 'bg-blue-100 text-blue-800';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800';
      case 'canceled':
      case 'unpaid':
      case 'suspended':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-white text-xl text-center">Loading profile...</div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  if (error && !profile) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              {error}
            </div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  if (!profile) return null;

  return (
    <SessionGuard>
      <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <Navigation />
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumb items={[{ label: 'Profile' }]} />
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
              {!editing && (
                <button
                  onClick={handleEdit}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Edit Profile
                </button>
              )}
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                {error}
              </div>
            )}

            {/* Profile Information Card */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Tenant Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tenant Name</label>
                  {editing ? (
                    <input
                      type="text"
                      value={editForm.name || ''}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  ) : (
                    <p className="text-gray-900">{profile.name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
                  <p className="text-gray-500">{profile.slug}</p>
                  <p className="text-xs text-gray-400 mt-1">(Read-only identifier)</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  {editing ? (
                    <input
                      type="email"
                      value={editForm.email || ''}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  ) : (
                    <p className="text-gray-900">{profile.email || 'Not set'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                  {editing ? (
                    <input
                      type="tel"
                      value={editForm.phoneNumber || ''}
                      onChange={(e) => handleInputChange('phoneNumber', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  ) : (
                    <p className="text-gray-900">{profile.phoneNumber || 'Not set'}</p>
                  )}
                </div>
              </div>

              {editing && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Branding</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Logo URL</label>
                      <input
                        type="url"
                        value={editForm.logoUrl || ''}
                        onChange={(e) => handleInputChange('logoUrl', e.target.value)}
                        placeholder="https://example.com/logo.png"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
                      <div className="flex gap-2">
                        <input
                          type="color"
                          value={editForm.primaryColor || '#9B59B6'}
                          onChange={(e) => handleInputChange('primaryColor', e.target.value)}
                          className="w-16 h-10 border border-gray-300 rounded-lg cursor-pointer"
                        />
                        <input
                          type="text"
                          value={editForm.primaryColor || ''}
                          onChange={(e) => handleInputChange('primaryColor', e.target.value)}
                          placeholder="#9B59B6"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Custom Domain</label>
                      <input
                        type="text"
                        value={editForm.domain || ''}
                        onChange={(e) => handleInputChange('domain', e.target.value)}
                        placeholder="example.com"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
              )}

              {editing && (
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    onClick={handleCancel}
                    disabled={saving}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>

            {/* Subscription Details Card */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Subscription Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                  <p className="text-gray-900">{profile.subscription.planName || 'Not set'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(
                      profile.subscription.status
                    )}`}
                  >
                    {profile.subscription.status || 'Unknown'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quota Usage Card */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Usage & Quota</h2>
              <div className="space-y-6">
                {/* Monthly Run Quota */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Monthly Run Quota
                    </label>
                    <span className="text-sm text-gray-600">
                      {profile.usageCurrent} / {profile.usageQuota}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        getUsagePercentage() >= 90
                          ? 'bg-red-500'
                          : getUsagePercentage() >= 70
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${getUsagePercentage()}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{getUsagePercentage()}% used</p>
                </div>

                {/* Activation Code Quota */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Activation Codes
                    </label>
                    <span className="text-sm text-gray-600">
                      {profile.activationCodesUsed} / {profile.activationCodesTotal}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        getActivationCodePercentage() >= 90
                          ? 'bg-red-500'
                          : getActivationCodePercentage() >= 70
                          ? 'bg-yellow-500'
                          : 'bg-blue-500'
                      }`}
                      style={{ width: `${getActivationCodePercentage()}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {profile.activationCodesTotal - profile.activationCodesUsed} codes remaining
                  </p>
                </div>
              </div>
            </div>

            {/* Branding Preview Card */}
            {(profile.logoUrl || profile.primaryColor) && (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Branding Preview</h2>
                <div className="space-y-4">
                  {profile.logoUrl && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Logo</label>
                      <img
                        src={profile.logoUrl}
                        alt="Tenant logo"
                        className="max-h-24 max-w-48 object-contain"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  {profile.primaryColor && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Primary Color</label>
                      <div className="flex items-center gap-4">
                        <div
                          className="w-16 h-16 rounded-lg border-2 border-gray-300"
                          style={{ backgroundColor: profile.primaryColor }}
                        />
                        <span className="text-gray-600 font-mono">{profile.primaryColor}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </SessionGuard>
  );
}

