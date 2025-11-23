import { motion } from 'framer-motion';
import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { Breadcrumb } from '@/components/Breadcrumb';
import { Navigation } from '@/components/Navigation';
import { Button, Card, StatCard } from '@/design-system';
import { AdminHeader } from '../components/AdminHeader';
import { Footer } from '../components/Footer';

// Use relative URLs to leverage Next.js proxy (avoids IPv6 issues)
// Next.js proxy rewrites /api/* and /admin/api/* to http://127.0.0.1:8080
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface TrendMetric {
  direction: 'up' | 'down';
  value: number;
}

interface DashboardStats {
  activeCodes: number;
  activeDevices: number;
  activeProjects: number;
  activeTenants: number;
  expiredCodes: number;
  revokedDevices: number;
  successRate: number;
  totalCodes: number;
  totalDevices: number;
  totalProjects: number;
  totalTenants: number;
  trends: {
    codes: TrendMetric;
    devices: TrendMetric;
    projects: TrendMetric;
    successRate: TrendMetric;
    tenants: TrendMetric;
  };
}

interface RecentActivity {
  type: string;
  icon: string;
  action: string;
  tenant: string;
  timestamp: string | null;
  backdrop: string;
  metadata: Record<string, any>;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activityDateRange, setActivityDateRange] = useState<'7d' | '30d' | '90d'>('7d');
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [activationTrend, setActivationTrend] = useState<Array<{date: string; codes: number; projects: number; devices: number; cumulativeCodes?: number; cumulativeProjects?: number; cumulativeDevices?: number}>>([]);
  const [projectDeviceDistribution, setProjectDeviceDistribution] = useState<{
    projects: {active: number; total: number};
    devices: {active: number; revoked: number; total: number};
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingActivities, setIsLoadingActivities] = useState(false);
  const [isLoadingCharts, setIsLoadingCharts] = useState(false);
  const [isLoadingDistribution, setIsLoadingDistribution] = useState(false);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        const response = await fetch(`${API_BASE}/admin/api/dashboard-stats`);
        if (!response.ok) {
          throw new Error('Failed to load dashboard metrics');
        }

        const data = await response.json();
        setStats({
          activeCodes: data.activeCodes ?? 0,
          activeDevices: data.activeDevices ?? 0,
          activeProjects: data.activeProjects ?? 0,
          activeTenants: data.activeTenants ?? 0,
          expiredCodes: data.expiredCodes ?? 0,
          revokedDevices: data.revokedDevices ?? 0,
          successRate: data.successRate ?? 0,
          totalCodes: data.totalCodes ?? 0,
          totalDevices: data.totalDevices ?? 0,
          totalProjects: data.totalProjects ?? 0,
          totalTenants: data.totalTenants ?? 0,
          trends: data.trends ?? {
            codes: { direction: 'up', value: 0 },
            devices: { direction: 'up', value: 0 },
            projects: { direction: 'up', value: 0 },
            successRate: { direction: 'up', value: 0 },
            tenants: { direction: 'up', value: 0 },
          },
        });
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardStats();
    fetchRecentActivities();
    fetchActivationTrend();
    fetchProjectDeviceDistribution();
  }, []);

  useEffect(() => {
    fetchRecentActivities();
  }, [activityDateRange]);

  const fetchRecentActivities = async () => {
    try {
      setIsLoadingActivities(true);
      const days = activityDateRange === '7d' ? 7 : activityDateRange === '30d' ? 30 : 90;
      const response = await fetch(`${API_BASE}/admin/api/recent-activities?days=${days}`);
      if (!response.ok) {
        throw new Error('Failed to load recent activities');
      }
      const data = await response.json();
      setRecentActivities(data.activities || []);
    } catch (error) {
      console.error('Error fetching recent activities:', error);
      setRecentActivities([]);
    } finally {
      setIsLoadingActivities(false);
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
      console.error('Error fetching distribution:', error);
      setProjectDeviceDistribution(null);
    } finally {
      setIsLoadingDistribution(false);
    }
  };

  const metrics = useMemo(() => {
    if (!stats) {
      return [];
    }

    return [
      {
        icon: '🔑',
        subtitle: `${stats.activeCodes} active`,
        title: 'Activation Codes',
        trend: stats.trends.codes,
        value: stats.totalCodes.toLocaleString(),
      },
      {
        icon: '📱',
        subtitle: `${stats.activeDevices} active`,
        title: 'Authorized Devices',
        trend: stats.trends.devices,
        value: stats.totalDevices.toLocaleString(),
      },
      {
        icon: '📁',
        subtitle: `${stats.activeProjects} active`,
        title: 'Authorized Projects',
        trend: stats.trends.projects,
        value: stats.totalProjects.toLocaleString(),
      },
      {
        icon: '👥',
        subtitle: `${stats.activeTenants} with active subscriptions`,
        title: 'Tenants',
        trend: stats.trends.tenants,
        value: stats.totalTenants.toLocaleString(),
      },
      {
        icon: '📊',
        subtitle: 'Activation success rate',
        title: 'Success Rate',
        trend: stats.trends.successRate,
        value: `${stats.successRate.toFixed(1)}%`,
      },
    ];
  }, [stats]);

  const quickActions = useMemo(
    () => [
      {
        description: 'Create new activation codes for tenants',
        icon: '➕',
        href: '/codes?action=generate',
        label: 'Generate Codes',
      },
      {
        description: 'Onboard a new tenant organization',
        icon: '🏢',
        href: '/tenants?action=new',
        label: 'Add Tenant',
      },
      {
        description: 'Usage trends and insights',
        icon: '📈',
        href: '/analytics',
        label: 'View Analytics',
      },
      {
        description: 'View and manage authorized projects and devices',
        icon: '🔒',
        href: '/projects-devices',
        label: 'Manage Projects',
      },
    ],
    [],
  );

  const activityFeed = useMemo(() => {
    return recentActivities.map((activity) => {
      const timeAgo = activity.timestamp
        ? formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })
        : 'Unknown';
      
      return {
        icon: activity.icon,
        action: activity.action,
        tenant: activity.tenant,
        time: timeAgo,
        backdrop: activity.backdrop,
      };
    });
  }, [recentActivities]);

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="🎯 Q2O Licensing Admin"
        subtitle="Multi-tenant subscription & licensing management"
        action={
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
            <p className="text-xs opacity-75">Admin User</p>
            <p className="font-semibold">cryptolavar@gmail.com</p>
          </div>
        }
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <Breadcrumb items={[{ label: 'Dashboard' }]} />

        <section className="mb-10">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
            {(isLoading ? Array.from({ length: 5 }) : metrics).map((metric, index) => (
              <motion.div key={metric?.title ?? index} animate={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 16 }} transition={{ delay: index * 0.05 }}>
                {metric ? (
                  <StatCard 
                    icon={metric.icon} 
                    subtitle={metric.subtitle} 
                    title={metric.title} 
                    trend={metric.trend} 
                    value={metric.value}
                    valueClassName="text-5xl"
                  />
                ) : (
                  <Card className="h-full animate-pulse bg-white">
                    <div className="flex h-32 items-center justify-center text-gray-300">Loading…</div>
                  </Card>
                )}
              </motion.div>
            ))}
          </div>
        </section>

        <section className="mb-10 space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-2xl font-bold text-gray-900">Quick Actions</h2>
            <Button size="sm" variant="secondary" onClick={() => router.push('/llm')}>
              Go to LLM Management
            </Button>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
            {quickActions.map((action, index) => (
              <motion.div key={action.label} animate={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 16 }} transition={{ delay: index * 0.05 }}>
                <Card className="h-full p-6">
                  <div className="mb-4 flex items-center gap-3 text-3xl">
                    <span>{action.icon}</span>
                    <h3 className="text-lg font-semibold text-gray-900">{action.label}</h3>
                  </div>
                  <p className="mb-6 text-sm text-gray-600">{action.description}</p>
                  <Button className="w-full" size="sm" onClick={() => router.push(action.href)}>
                    Open
                  </Button>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="mb-10">
          <Card className="space-y-6 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Recent Activity</h2>
                <p className="text-sm text-gray-500">Automated events from tenants, licensing, and devices.</p>
              </div>
              <select
                className="rounded-xl border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                value={activityDateRange}
                onChange={(event) => setActivityDateRange(event.target.value as '7d' | '30d' | '90d')}
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
            </div>

            <div className="space-y-3">
              {isLoadingActivities ? (
                <div className="flex items-center justify-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                </div>
              ) : activityFeed.length > 0 ? (
                activityFeed.map((activity, index) => (
                  <motion.div
                    key={`${activity.action}-${activity.time}-${index}`}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-4 rounded-2xl border border-gray-100 bg-white/80 px-4 py-3 transition-shadow duration-200 hover:shadow-md"
                    initial={{ opacity: 0, x: -12 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl text-xl ${activity.backdrop}`}>{activity.icon}</div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">{activity.action}</p>
                      <p className="text-sm text-gray-500">{activity.tenant}</p>
                    </div>
                    <span className="text-xs font-medium uppercase tracking-wide text-gray-400">{activity.time}</span>
                  </motion.div>
                ))
              ) : (
                <div className="flex items-center justify-center py-8 text-gray-400">
                  <p>No recent activities found</p>
                </div>
              )}
            </div>
          </Card>
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="p-6">
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
                <Button size="sm" variant="ghost" onClick={() => router.push('/analytics')}>
                  View Full Analytics
                </Button>
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
          </Card>

          <Card className="p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Project/Device Distribution</h3>
                <p className="text-sm text-gray-500">Active projects and devices breakdown.</p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => router.push('/devices')}>
                View Details
              </Button>
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
          </Card>
        </section>

        <Footer />
      </main>
    </div>
  );
}

