import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { StatCard } from '../design-system';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('7d');
  const [loading, setLoading] = useState(true);
  const [analyticsData, setAnalyticsData] = useState({
    activationTrend: [],
    tenantUsage: [],
    subscriptionDistribution: [],
    summaryStats: {
      totalRevenue: 0,
      avgUsageRate: 0,
      retentionRate: 0
    }
  });

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/admin/api/analytics?date_range=${dateRange}`);
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else {
        console.error('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#4CAF50', '#9B59B6', '#FF6B9D'];

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="📊 Analytics"
        subtitle="Usage trends, revenue metrics, and insights"
        action={
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 px-4 py-2 rounded-lg font-semibold focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              <option value="today">Today</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last Year (Annual)</option>
            </select>
        }
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <Breadcrumb items={[{ label: 'Analytics' }]} />

        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Activation Trend */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h3 className="text-xl font-bold text-gray-900 mb-6">📈 Activation Trends</h3>
                {analyticsData.activationTrend.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={analyticsData.activationTrend}>
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
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-400">
                    <p>No data available for selected period</p>
                  </div>
                )}
              </div>

              {/* Subscription Distribution */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h3 className="text-xl font-bold text-gray-900 mb-6">🎯 Subscription Distribution</h3>
                {analyticsData.subscriptionDistribution.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={analyticsData.subscriptionDistribution}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {analyticsData.subscriptionDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 flex justify-center gap-4">
                      {analyticsData.subscriptionDistribution.map((item, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                          <span className="text-sm font-medium text-gray-700">{item.name}: {item.value}</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-400">
                    <p>No subscription data available</p>
                  </div>
                )}
              </div>
            </div>

            {/* Tenant Usage Bar Chart */}
            <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">💼 Tenant Usage Overview</h3>
              {analyticsData.tenantUsage.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analyticsData.tenantUsage}>
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
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-400">
                  <p>No tenant usage data available</p>
                </div>
              )}
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard
                title="Total Revenue (Est.)"
                value={`$${analyticsData.summaryStats.totalRevenue.toLocaleString()}`}
                subtitle="From active subscriptions"
                icon="💰"
                className="bg-gradient-to-r from-pink-500 to-purple-600 text-white"
              />
              <StatCard
                title="Avg. Usage Rate"
                value={`${analyticsData.summaryStats.avgUsageRate.toFixed(1)}%`}
                subtitle="Across all tenants"
                icon="📊"
              />
              <StatCard
                title="Retention Rate"
                value={`${analyticsData.summaryStats.retentionRate.toFixed(1)}%`}
                subtitle="30-day active rate"
                icon="📈"
              />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

