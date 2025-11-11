import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { getDevices, revokeDevice, type Device } from '../lib/api';

export default function DevicesPage() {
  const [allDevices, setAllDevices] = useState<Device[]>([]);
  const [filteredDevices, setFilteredDevices] = useState<Device[]>([]);
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const devices = await getDevices();
      setAllDevices(devices);
      setFilteredDevices(devices);
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  };

  // Apply filters
  useEffect(() => {
    let filtered = [...allDevices];

    if (selectedTenant !== 'all') {
      filtered = filtered.filter(d => d.tenant.toLowerCase().includes(selectedTenant.toLowerCase()));
    }

    if (selectedStatus === 'active') {
      filtered = filtered.filter(d => !d.isRevoked);
    } else if (selectedStatus === 'revoked') {
      filtered = filtered.filter(d => d.isRevoked);
    }

    setFilteredDevices(filtered);
  }, [selectedTenant, selectedStatus, allDevices]);

  const handleRevokeDevice = async (device: Device) => {
    if (confirm(`Are you sure you want to revoke ${device.label || 'this device'}? This action cannot be undone.`)) {
      try {
        await revokeDevice(device.tenant.toLowerCase().replace(/\s+/g, ''), device.id);
        await loadDevices();
        
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        notification.textContent = '✅ Device revoked successfully';
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
      } catch (error) {
        alert('Error revoking device: ' + error);
      }
    }
  };

  const getDeviceIcon = (type: string) => {
    return type === 'desktop' ? '💻' : type === 'mobile' ? '📱' : '🖥️';
  };

  const uniqueTenants = Array.from(new Set(allDevices.map(d => d.tenant)));

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="📱 Authorized Devices"
        subtitle="Manage device authorizations and track activity"
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <Breadcrumb items={[{ label: 'Devices' }]} />

        {/* Filters */}
        <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                <option value="all">All Devices</option>
                <option value="active">Active</option>
                <option value="revoked">Revoked</option>
              </select>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredDevices.length} of {allDevices.length} devices
          </div>
        </div>

        {/* Device Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDevices.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <div className="text-6xl mb-4">📱</div>
              <p className="text-gray-500">
                {selectedTenant !== 'all' || selectedStatus !== 'all' 
                  ? 'No devices match your filters' 
                  : 'No devices authorized yet'}
              </p>
            </div>
          ) : (
            filteredDevices.map((device, i) => (
              <motion.div
                key={device.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className={`bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 ${
                  device.isRevoked ? 'opacity-60 border-2 border-red-200' : ''
                }`}
              >
                {/* Device Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="text-4xl">{getDeviceIcon(device.deviceType)}</div>
                    <div>
                      <h3 className="font-bold text-gray-900 text-lg">
                        {device.label || 'Unnamed Device'}
                      </h3>
                      <p className="text-sm text-gray-500">{device.tenant}</p>
                    </div>
                  </div>
                  {device.isRevoked && (
                    <span className="bg-red-100 text-red-700 text-xs font-semibold px-2 py-1 rounded-full">
                      Revoked
                    </span>
                  )}
                </div>

                {/* Device Info */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Type:</span>
                    <span className="font-medium text-gray-900 capitalize">{device.deviceType}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Last Seen:</span>
                    <span className="font-medium text-gray-900">
                      {formatDistanceToNow(new Date(device.lastSeen), { addSuffix: true })}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Registered:</span>
                    <span className="font-medium text-gray-900">{device.createdAt}</span>
                  </div>
                </div>

                {/* Fingerprint */}
                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 mb-1">Hardware Fingerprint</p>
                  <code className="text-xs font-mono text-gray-700">{device.hwFingerprint}</code>
                </div>

                {/* Actions */}
                {!device.isRevoked && (
                  <button
                    onClick={() => handleRevokeDevice(device)}
                    className="w-full py-2 bg-red-50 text-red-600 rounded-lg font-medium hover:bg-red-100 transition-colors duration-200"
                  >
                    🔒 Revoke Access
                  </button>
                )}
              </motion.div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
