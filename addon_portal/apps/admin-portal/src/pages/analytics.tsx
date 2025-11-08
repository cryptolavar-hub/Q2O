import React, { useState } from 'react';
import Link from 'next/link';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('7d');

  // Mock chart data
  const activationTrend = [
    { date: 'Nov 1', codes: 4, devices: 2 },
    { date: 'Nov 2', codes: 7, devices: 5 },
    { date: 'Nov 3', codes: 3, devices: 3 },
    { date: 'Nov 4', codes: 8, devices: 6 },
    { date: 'Nov 5', codes: 5, devices: 4 },
    { date: 'Nov 6', codes: 10, devices: 8 },
    { date: 'Nov 7', codes: 6, devices: 5 },
  ];

  const tenantUsage = [
    { tenant: 'Demo Consulting', usage: 12, quota: 50 },
    { tenant: 'Acme Corp', usage: 45, quota: 100 },
    { tenant: 'Tech Solutions', usage: 8, quota: 25 },
  ];

  const subscriptionDistribution = [
    { name: 'Starter', value: 5, color: '#4CAF50' },
    { name: 'Pro', value: 4, color: '#9B59B6' },
    { name: 'Enterprise', value: 3, color: '#FF6B9D' },
  ];

  const COLORS = ['#4CAF50', '#9B59B6', '#FF6B9D'];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-main text-white shadow-lg">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-white hover:opacity-80 transition-opacity">
              <h1 className="text-3xl font-bold drop-shadow-md">📊 Analytics</h1>
            </Link>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 px-4 py-2 rounded-lg font-semibold focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Activation Trend */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-6">📈 Activation Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={activationTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" stroke="#6B7280" style={{ fontSize: 12 }} />
                <YAxis stroke="#6B7280" style={{ fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    background: 'white', 
                    border: '1px solid #E5E7EB', 
                    borderRadius: 8,
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }} 
                />
                <Legend />
                <Line type="monotone" dataKey="codes" stroke="#9B59B6" strokeWidth={3} name="Codes Generated" />
                <Line type="monotone" dataKey="devices" stroke="#4CAF50" strokeWidth={3} name="Devices Activated" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Subscription Distribution */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-6">🎯 Subscription Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={subscriptionDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {subscriptionDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 flex justify-center gap-4">
              {subscriptionDistribution.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm font-medium text-gray-700">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Tenant Usage Bar Chart */}
        <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-6">💼 Tenant Usage Overview</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tenantUsage}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="tenant" stroke="#6B7280" style={{ fontSize: 12 }} />
              <YAxis stroke="#6B7280" style={{ fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ 
                  background: 'white', 
                  border: '1px solid #E5E7EB', 
                  borderRadius: 8,
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                }} 
              />
              <Legend />
              <Bar dataKey="usage" fill="#9B59B6" name="Current Usage" />
              <Bar dataKey="quota" fill="#E5E7EB" name="Total Quota" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-main text-white rounded-2xl p-6 shadow-lg">
            <h4 className="text-lg font-semibold mb-2 opacity-90">Total Revenue (Est.)</h4>
            <p className="text-4xl font-bold mb-2">$3,540</p>
            <p className="text-sm opacity-75">From active subscriptions</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-purple-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-2">Avg. Usage Rate</h4>
            <p className="text-4xl font-bold text-purple-600 mb-2">28%</p>
            <p className="text-sm text-gray-500">Across all tenants</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-green-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-2">Retention Rate</h4>
            <p className="text-4xl font-bold text-green-600 mb-2">92%</p>
            <p className="text-sm text-gray-500">30-day active rate</p>
          </div>
        </div>
      </main>
    </div>
  );
}

