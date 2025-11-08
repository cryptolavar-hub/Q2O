import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';

interface Device {
  id: number;
  tenant: string;
  label: string | null;
  hwFingerprint: string;
  deviceType: 'desktop' | 'mobile' | 'tablet';
  lastSeen: string;
  createdAt: string;
  isRevoked: boolean;
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedTenant, setSelectedTenant] = useState('all');

  // Mock data
  useEffect(() => {
    setDevices([
      { id: 1, tenant: 'Demo Consulting', label: 'Main Desktop', hwFingerprint: 'fp_abc123xyz', deviceType: 'desktop', lastSeen: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), createdAt: '2025-11-01', isRevoked: false },
      { id: 2, tenant: 'Demo Consulting', label: 'iPhone 14', hwFingerprint: 'fp_xyz789abc', deviceType: 'mobile', lastSeen: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), createdAt: '2025-11-03', isRevoked: false },
      { id: 3, tenant: 'Acme Corp', label: null, hwFingerprint: 'fp_def456ghi', deviceType: 'tablet', lastSeen: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), createdAt: '2025-10-15', isRevoked: true },
    ]);
  }, []);

  const getDeviceIcon = (type: string) => {
    return type === 'desktop' ? '💻' : type === 'mobile' ? '📱' : '🖥️';
  };

  const revokeDevice = (id: number) => {
    if (confirm('Are you sure you want to revoke this device? This action cannot be undone.')) {
      // API call would go here
      alert('Device revoked successfully');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-main text-white shadow-lg">
        <div className="container mx-auto px-6 py-6">
          <Link href="/" className="text-white hover:opacity-80 transition-opacity">
            <h1 className="text-3xl font-bold drop-shadow-md">📱 Authorized Devices</h1>
          </Link>
          <p className="text-sm opacity-90 mt-2">Manage device authorizations and track activity</p>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
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
                <option value="demo">Demo Consulting</option>
                <option value="acme">Acme Corp</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500">
                <option>All Devices</option>
                <option>Active</option>
                <option>Revoked</option>
              </select>
            </div>
          </div>
        </div>

        {/* Device Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map((device, i) => (
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
                  onClick={() => revokeDevice(device.id)}
                  className="w-full py-2 bg-red-50 text-red-600 rounded-lg font-medium hover:bg-red-100 transition-colors duration-200"
                >
                  🔒 Revoke Access
                </button>
              )}
            </motion.div>
          ))}
        </div>
      </main>
    </div>
  );
}

