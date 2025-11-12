import { motion } from 'framer-motion';
import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';

import { Breadcrumb } from '@/components/Breadcrumb';
import { Navigation } from '@/components/Navigation';
import { Button, Card, StatCard } from '@/design-system';
import { AdminHeader } from '../components/AdminHeader';

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
  activeTenants: number;
  expiredCodes: number;
  revokedDevices: number;
  successRate: number;
  totalCodes: number;
  totalDevices: number;
  totalTenants: number;
  trends: {
    codes: TrendMetric;
    devices: TrendMetric;
    successRate: TrendMetric;
    tenants: TrendMetric;
  };
}

export default function AdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activityDateRange, setActivityDateRange] = useState<'7d' | '30d' | '90d'>('7d');
  const [isLoading, setIsLoading] = useState(true);

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
          activeTenants: data.activeTenants ?? 0,
          expiredCodes: data.expiredCodes ?? 0,
          revokedDevices: data.revokedDevices ?? 0,
          successRate: data.successRate ?? 0,
          totalCodes: data.totalCodes ?? 0,
          totalDevices: data.totalDevices ?? 0,
          totalTenants: data.totalTenants ?? 0,
          trends: data.trends ?? {
            codes: { direction: 'up', value: 0 },
            devices: { direction: 'up', value: 0 },
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
  }, []);

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
        description: 'View and revoke authorized devices',
        icon: '🔒',
        href: '/devices',
        label: 'Manage Devices',
      },
    ],
    [],
  );

  const activityFeed = useMemo(
    () => [
      { icon: '🔑', action: 'Generated 5 activation codes', tenant: 'Demo Consulting', time: '2 hours ago', backdrop: 'bg-indigo-100 text-indigo-600' },
      { icon: '📱', action: 'Device authorized', tenant: 'Acme Corp', time: '4 hours ago', backdrop: 'bg-emerald-100 text-emerald-600' },
      { icon: '👥', action: 'New tenant created', tenant: 'Tech Solutions', time: '1 day ago', backdrop: 'bg-rose-100 text-rose-600' },
      { icon: '🔒', action: 'Device revoked', tenant: 'Demo Consulting', time: '2 days ago', backdrop: 'bg-amber-100 text-amber-600' },
    ],
    [],
  );

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
            {(isLoading ? Array.from({ length: 4 }) : metrics).map((metric, index) => (
              <motion.div key={metric?.title ?? index} animate={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 16 }} transition={{ delay: index * 0.05 }}>
                {metric ? (
                  <StatCard icon={metric.icon} subtitle={metric.subtitle} title={metric.title} trend={metric.trend} value={metric.value} />
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
              {activityFeed.map((activity, index) => (
                <motion.div
                  key={`${activity.action}-${activity.time}`}
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
              ))}
            </div>
          </Card>
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Activation Trends</h3>
                <p className="text-sm text-gray-500">Daily activation codes generated across tenants.</p>
              </div>
              <Button size="sm" variant="ghost">
                Export
              </Button>
            </div>
            <div className="mt-6 flex h-64 items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="mb-4 text-6xl">📈</div>
                <p className="font-medium text-gray-600">Recharts area graph coming in Task 1.7</p>
                <p className="text-xs text-gray-400">Shows generated vs redeemed codes</p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Device Distribution</h3>
                <p className="text-sm text-gray-500">Snapshot of active vs. revoked devices.</p>
              </div>
              <Button size="sm" variant="ghost">
                View Devices
              </Button>
            </div>
            <div className="mt-6 flex h-64 items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="mb-4 text-6xl">📱</div>
                <p className="font-medium text-gray-600">Pie chart placeholder</p>
                <p className="text-xs text-gray-400">Breakdown by platform & status</p>
              </div>
            </div>
          </Card>
        </section>

        <footer className="mt-12 pb-6 text-center text-sm text-gray-500">
          <p>Q2O Licensing Admin Portal • Multi-tenant command center</p>
          <p className="mt-1 text-xs text-gray-400">Powered by Quick to Objective Agents</p>
        </footer>
      </main>
    </div>
  );
}

