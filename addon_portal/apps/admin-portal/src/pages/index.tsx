import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Line, Bar, Pie } from 'recharts';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

interface DashboardStats {
  totalCodes: number;
  activeCodes: number;
  expiredCodes: number;
  totalDevices: number;
  activeDevices: number;
  revokedDevices: number;
  totalTenants: number;
  activeTenants: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalCodes: 0,
    activeCodes: 0,
    expiredCodes: 0,
    totalDevices: 0,
    activeDevices: 0,
    revokedDevices: 0,
    totalTenants: 0,
    activeTenants: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch stats from API
    // For now, using mock data
    setTimeout(() => {
      setStats({
        totalCodes: 45,
        activeCodes: 32,
        expiredCodes: 13,
        totalDevices: 89,
        activeDevices: 76,
        revokedDevices: 13,
        totalTenants: 12,
        activeTenants: 11,
      });
      setLoading(false);
    }, 500);
  }, []);

  const StatCard = ({ title, value, subtitle, icon, trend }: any) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="text-4xl">{icon}</div>
        {trend && (
          <div className={`text-sm font-semibold ${trend.direction === 'up' ? 'text-green-600' : 'text-red-600'}`}>
            {trend.direction === 'up' ? '↗' : '↘'} {trend.value}%
          </div>
        )}
      </div>
      <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wide mb-1">{title}</h3>
      <p className="text-4xl font-bold text-gray-900 mb-1">{value}</p>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </motion.div>
  );

  const QuickActionCard = ({ title, description, icon, href, color }: any) => (
    <Link href={href}>
      <motion.div
        whileHover={{ scale: 1.02, y: -4 }}
        whileTap={{ scale: 0.98 }}
        className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer group"
      >
        <div className={`w-14 h-14 rounded-full ${color} flex items-center justify-center text-3xl mb-4 group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
        <h3 className="font-bold text-gray-900 text-lg mb-2">{title}</h3>
        <p className="text-gray-600 text-sm">{description}</p>
      </motion.div>
    </Link>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Gradient */}
      <header className="bg-gradient-main text-white shadow-lg">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold drop-shadow-md">
                🎯 Quick2Odoo Licensing Admin
              </h1>
              <p className="text-sm opacity-90 mt-2">
                Multi-tenant subscription & licensing management
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                <p className="text-xs opacity-75">Admin User</p>
                <p className="font-semibold">cryptolavar@gmail.com</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-6">
          <div className="flex gap-6 text-sm font-medium">
            <Link href="/" className="py-4 px-2 border-b-2 border-purple-600 text-purple-600">
              Dashboard
            </Link>
            <Link href="/codes" className="py-4 px-2 border-b-2 border-transparent text-gray-600 hover:text-purple-600 hover:border-gray-300 transition-colors">
              Activation Codes
            </Link>
            <Link href="/devices" className="py-4 px-2 border-b-2 border-transparent text-gray-600 hover:text-purple-600 hover:border-gray-300 transition-colors">
              Devices
            </Link>
            <Link href="/tenants" className="py-4 px-2 border-b-2 border-transparent text-gray-600 hover:text-purple-600 hover:border-gray-300 transition-colors">
              Tenants
            </Link>
            <Link href="/analytics" className="py-4 px-2 border-b-2 border-transparent text-gray-600 hover:text-purple-600 hover:border-gray-300 transition-colors">
              Analytics
            </Link>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Activation Codes"
            value={stats.totalCodes}
            subtitle={`${stats.activeCodes} active`}
            icon="🔑"
            trend={{ value: 12, direction: 'up' }}
          />
          <StatCard
            title="Authorized Devices"
            value={stats.totalDevices}
            subtitle={`${stats.activeDevices} active`}
            icon="📱"
            trend={{ value: 8, direction: 'up' }}
          />
          <StatCard
            title="Tenants"
            value={stats.totalTenants}
            subtitle={`${stats.activeTenants} with active subscriptions`}
            icon="👥"
          />
          <StatCard
            title="Success Rate"
            value="96%"
            subtitle="Activation success"
            icon="📊"
            trend={{ value: 3, direction: 'up' }}
          />
        </div>

        {/* Quick Actions */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <QuickActionCard
              title="Generate Codes"
              description="Create new activation codes for tenants"
              icon="➕"
              href="/codes?action=generate"
              color="bg-gradient-main"
            />
            <QuickActionCard
              title="Add Tenant"
              description="Onboard a new tenant organization"
              icon="🏢"
              href="/tenants?action=new"
              color="bg-gradient-success"
            />
            <QuickActionCard
              title="View Analytics"
              description="Usage trends and insights"
              icon="📈"
              href="/analytics"
              color="bg-gradient-warning"
            />
            <QuickActionCard
              title="Manage Devices"
              description="View and revoke authorized devices"
              icon="🔒"
              href="/devices"
              color="bg-gradient-error"
            />
          </div>
        </section>

        {/* Recent Activity */}
        <section className="mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recent Activity</h2>
              <select className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                <option>Last 7 days</option>
                <option>Last 30 days</option>
                <option>Last 90 days</option>
              </select>
            </div>

            {/* Activity Feed */}
            <div className="space-y-4">
              {[
                { icon: '🔑', action: 'Generated 5 activation codes', tenant: 'Demo Consulting', time: '2 hours ago', color: 'bg-blue-100 text-blue-700' },
                { icon: '📱', action: 'Device authorized', tenant: 'Acme Corp', time: '4 hours ago', color: 'bg-green-100 text-green-700' },
                { icon: '👥', action: 'New tenant created', tenant: 'Tech Solutions', time: '1 day ago', color: 'bg-purple-100 text-purple-700' },
                { icon: '🔒', action: 'Device revoked', tenant: 'Demo Consulting', time: '2 days ago', color: 'bg-red-100 text-red-700' },
              ].map((activity, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors duration-200"
                >
                  <div className={`w-12 h-12 rounded-full ${activity.color} flex items-center justify-center text-2xl flex-shrink-0`}>
                    {activity.icon}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{activity.action}</p>
                    <p className="text-sm text-gray-500">{activity.tenant}</p>
                  </div>
                  <div className="text-xs text-gray-400">{activity.time}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Activation Codes Chart */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Activation Trends</h3>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-6xl mb-4">📈</div>
                <p>Chart: Activation codes generated over time</p>
                <p className="text-sm mt-2">(Recharts integration)</p>
              </div>
            </div>
          </div>

          {/* Device Distribution Chart */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Device Distribution</h3>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-6xl mb-4">📱</div>
                <p>Chart: Active vs Revoked devices</p>
                <p className="text-sm mt-2">(Pie chart visualization)</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm pb-6">
          <p>Quick2Odoo Licensing Admin Portal • Multi-Tenant Management</p>
          <p className="text-xs mt-1">Powered by agents that build everything</p>
        </footer>
      </main>
    </div>
  );
}

