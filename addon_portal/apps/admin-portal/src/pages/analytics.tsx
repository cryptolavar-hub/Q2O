import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { StatCard } from '../design-system';

// Use relative URLs to leverage Next.js proxy (avoids IPv6 issues)
// Next.js proxy rewrites /api/* and /admin/api/* to http://127.0.0.1:8080
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('7d');
  const [projectFilter, setProjectFilter] = useState<string>('all');
  const [availableProjects, setAvailableProjects] = useState<Array<{project_id: string; client_name: string}>>([]);
  const [loading, setLoading] = useState(true);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [isLoadingCharts, setIsLoadingCharts] = useState(false);
  const [isLoadingDistribution, setIsLoadingDistribution] = useState(false);
  const [activationTrend, setActivationTrend] = useState<Array<{date: string; codes: number; projects: number; devices: number; cumulativeCodes?: number; cumulativeProjects?: number; cumulativeDevices?: number}>>([]);
  const [projectDeviceDistribution, setProjectDeviceDistribution] = useState<{
    projects: {active: number; total: number};
    devices: {active: number; revoked: number; total: number};
  } | null>(null);
  const [analyticsData, setAnalyticsData] = useState<{
    tenantUsage: Array<{tenant: string; usage: number; quota: number}>;
    subscriptionDistribution: Array<{name: string; value: number; color: string}>;
    summaryStats: {
      totalRevenue: number;
      avgUsageRate: number;
      retentionRate: number;
    };
  }>({
    tenantUsage: [],
    subscriptionDistribution: [],
    summaryStats: {
      totalRevenue: 0,
      avgUsageRate: 0,
      retentionRate: 0
    }
  });

  useEffect(() => {
    fetchAvailableProjects();
    fetchActivationTrend();
    fetchProjectDeviceDistribution();
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange, projectFilter]);

  const fetchAvailableProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await fetch(`${API_BASE}/api/llm/projects?page=1&page_size=100`);
      if (response.ok) {
        const data = await response.json();
        setAvailableProjects(data.items?.map((p: any) => ({ project_id: p.projectId, client_name: p.clientName })) || []);
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoadingProjects(false);
    }
  };

  const fetchActivationTrend = async () => {
    try {
      setIsLoadingCharts(true);
      const response = await fetch(`${API_BASE}/admin/api/activation-trend?days=30`);
      if (!response.ok) {
        throw new Error('Failed to load activation trend');
      }
      const data = await response.json();
      
      // Transform daily counts to cumulative totals for better visualization
      const rawTrend = data.trend || [];
      let runningCodes = 0;
      let runningProjects = 0;
      let runningDevices = 0;
      const processedTrend = rawTrend.map((entry: any) => {
        runningCodes += entry.codes || 0;
        runningProjects += entry.projects || 0;
        runningDevices += entry.devices || 0;
        return {
          date: entry.date,
          codes: entry.codes || 0,
          projects: entry.projects || 0,
          devices: entry.devices || 0,
          cumulativeCodes: runningCodes,
          cumulativeProjects: runningProjects,
          cumulativeDevices: runningDevices,
        };
      });
      
      setActivationTrend(processedTrend);
    } catch (error) {
      console.error('Error fetching activation trend:', error);
      setActivationTrend([]);
    } finally {
      setIsLoadingCharts(false);
    }
  };

  const fetchProjectDeviceDistribution = async () => {
    try {
      setIsLoadingDistribution(true);
      const response = await fetch(`${API_BASE}/admin/api/project-device-distribution`);
      if (!response.ok) {
        throw new Error('Failed to load distribution');
      }
      const data = await response.json();
      setProjectDeviceDistribution(data);
    } catch (error) {
      console.error('Error fetching project/device distribution:', error);
      setProjectDeviceDistribution(null);
    } finally {
      setIsLoadingDistribution(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      let url = `${API_BASE}/admin/api/analytics?date_range=${dateRange}`;
      if (projectFilter && projectFilter !== 'all') {
        url += `&project_filter=${encodeURIComponent(projectFilter)}`;
      }
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData({
          tenantUsage: data.tenantUsage || [],
          subscriptionDistribution: data.subscriptionDistribution || [],
          summaryStats: data.summaryStats || {
            totalRevenue: 0,
            avgUsageRate: 0,
            retentionRate: 0
          }
        });
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
            {/* Charts Grid - Row 1: Activation Trends and Project/Device Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Activation Trends (from Dashboard) */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">Activation Trends</h3>
                    <p className="text-sm text-gray-500">30-day cumulative totals for codes, projects, and devices.</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {activationTrend.length > 0 && (
                      <div className="text-sm text-gray-600">
                        <span className="font-semibold text-purple-600">
                          {activationTrend[activationTrend.length - 1]?.cumulativeCodes || 0}
                        </span> codes total
                      </div>
                    )}
                  </div>
                </div>
                {isLoadingCharts ? (
                  <div className="mt-6 flex h-64 items-center justify-center text-gray-400">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                  </div>
                ) : activationTrend.length > 0 ? (
                  <div className="mt-6">
                    <ResponsiveContainer width="100%" height={256}>
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
                        <Line type="monotone" dataKey="cumulativeCodes" stroke="#9B59B6" strokeWidth={2} name="Codes Generated (Total)" />
                        <Line type="monotone" dataKey="cumulativeProjects" stroke="#FF6B9D" strokeWidth={2} name="Projects Activated (Total)" />
                        <Line type="monotone" dataKey="cumulativeDevices" stroke="#4CAF50" strokeWidth={2} name="Devices Activated (Total)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="mt-6 flex h-64 items-center justify-center text-gray-400">
                    <p>No activation data available</p>
                  </div>
                )}
              </div>

              {/* Project/Device Distribution (from Dashboard) */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">Project/Device Distribution</h3>
                    <p className="text-sm text-gray-500">Active projects and devices breakdown.</p>
                  </div>
                </div>
                {isLoadingDistribution ? (
                  <div className="mt-6 flex h-64 items-center justify-center text-gray-400">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                  </div>
                ) : projectDeviceDistribution && (
                  projectDeviceDistribution.projects.active > 0 || 
                  projectDeviceDistribution.devices.active > 0 || 
                  projectDeviceDistribution.devices.revoked > 0
                ) ? (
                  <div className="mt-6">
                    <ResponsiveContainer width="100%" height={256}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Active Projects', value: projectDeviceDistribution.projects.active, color: '#4CAF50' },
                            { name: 'Active Devices', value: projectDeviceDistribution.devices.active, color: '#9B59B6' },
                            { name: 'Revoked Devices', value: projectDeviceDistribution.devices.revoked, color: '#FF6B9D' },
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[
                            { name: 'Active Projects', value: projectDeviceDistribution.projects.active, color: '#4CAF50' },
                            { name: 'Active Devices', value: projectDeviceDistribution.devices.active, color: '#9B59B6' },
                            { name: 'Revoked Devices', value: projectDeviceDistribution.devices.revoked, color: '#FF6B9D' },
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 flex justify-center gap-4 flex-wrap">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500" />
                        <span className="text-sm font-medium text-gray-700">
                          Projects: {projectDeviceDistribution.projects.active} active
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-purple-500" />
                        <span className="text-sm font-medium text-gray-700">
                          Devices: {projectDeviceDistribution.devices.active} active
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-pink-500" />
                        <span className="text-sm font-medium text-gray-700">
                          Revoked: {projectDeviceDistribution.devices.revoked}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="mt-6 flex h-64 items-center justify-center text-gray-400">
                    <p>No project/device data available</p>
                  </div>
                )}
              </div>
            </div>

            {/* Charts Grid - Row 2: Subscription Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
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
            <div id="tenant-usage-chart" className="bg-white rounded-2xl p-6 shadow-lg mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                <h3 className="text-xl font-bold text-gray-900">💼 Tenant Usage Overview</h3>
                <div className="flex items-center gap-3">
                  <label htmlFor="project-filter" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                    Filter by Project:
                  </label>
                  <select
                    id="project-filter"
                    value={projectFilter}
                    onChange={(e) => {
                      e.preventDefault();
                      const newValue = e.target.value;
                      setProjectFilter(newValue);
                      // Scroll to chart smoothly without page reload
                      const chartElement = document.getElementById('tenant-usage-chart');
                      if (chartElement) {
                        chartElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                      }
                    }}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:ring-2 focus:ring-purple-200 min-w-[200px]"
                    disabled={loadingProjects}
                  >
                    <option value="all">All Projects</option>
                    <option value="latest">Latest Project</option>
                    <option value="top10">Top 10 Projects</option>
                    {availableProjects.length > 0 && (
                      <>
                        <option disabled>──────────</option>
                        {availableProjects.map((project) => (
                          <option key={project.project_id} value={`project:${project.project_id}`}>
                            {project.client_name} ({project.project_id})
                          </option>
                        ))}
                      </>
                    )}
                  </select>
                </div>
              </div>
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
                  <p>No tenant usage data available{projectFilter !== 'all' ? ' for selected project filter' : ''}</p>
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
        <Footer />
      </main>
    </div>
  );
}

