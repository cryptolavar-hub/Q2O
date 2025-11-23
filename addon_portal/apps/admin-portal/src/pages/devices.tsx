import React, { useState, useEffect } from 'react';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { Card, Button, Badge } from '@/design-system';
import { getDevices, revokeDevice, type Device } from '../lib/api';
import { getTenants, type Tenant, type TenantPage, type TenantQueryParams } from '../lib/api';
import { motion } from 'framer-motion';

// Use relative URLs to leverage Next.js proxy (avoids IPv6 issues)
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface ActivatedProject {
  projectId: string;
  clientName: string;
  tenantName: string;
  tenantSlug: string;
  activationCodeId: number;
  activationCode: string;
  activatedAt: string;
  executionStatus: string;
  description?: string;
}

export default function ProjectsDevicesPage() {
  const [activeTab, setActiveTab] = useState<'projects' | 'devices'>('projects');
  const [projects, setProjects] = useState<ActivatedProject[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingDevices, setLoadingDevices] = useState(false);
  const [projectsPage, setProjectsPage] = useState(1);
  const [devicesPage, setDevicesPage] = useState(1);
  const [projectsPageSize, setProjectsPageSize] = useState(25);
  const [devicesPageSize, setDevicesPageSize] = useState(25);
  const [projectsTotal, setProjectsTotal] = useState(0);
  const [devicesTotal, setDevicesTotal] = useState(0);
  const [projectsSearch, setProjectsSearch] = useState('');
  const [devicesSearch, setDevicesSearch] = useState('');
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [totalTenants, setTotalTenants] = useState(0);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [tenantModalPage, setTenantModalPage] = useState(1);
  const [tenantModalPageSize, setTenantModalPageSize] = useState(10);
  const [tenantModalSearch, setTenantModalSearch] = useState('');
  const [tenantModalStatus, setTenantModalStatus] = useState('all');
  const [tenantModalData, setTenantModalData] = useState<TenantPage | null>(null);
  const [loadingTenantModal, setLoadingTenantModal] = useState(false);

  // Load activated projects
  const loadActivatedProjects = async () => {
    try {
      setLoadingProjects(true);
      const params = new URLSearchParams({
        page: projectsPage.toString(),
        page_size: projectsPageSize.toString(),
      });
      if (projectsSearch) params.append('search', projectsSearch);
      if (selectedTenant !== 'all') params.append('tenant_slug', selectedTenant);

      const response = await fetch(`${API_BASE}/admin/api/projects/activated?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch activated projects');
      }
      const data = await response.json();
      setProjects(data.projects || []);
      setProjectsTotal(data.total || 0);
    } catch (error) {
      console.error('Error loading activated projects:', error);
      setProjects([]);
      setProjectsTotal(0);
    } finally {
      setLoadingProjects(false);
    }
  };

  // Load devices
  const loadDevices = async () => {
    try {
      setLoadingDevices(true);
      const tenantSlug = selectedTenant !== 'all' ? selectedTenant : undefined;
      const devicesData = await getDevices(tenantSlug);
      setDevices(devicesData);
      setDevicesTotal(devicesData.length);
    } catch (error) {
      console.error('Error loading devices:', error);
      setDevices([]);
      setDevicesTotal(0);
    } finally {
      setLoadingDevices(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'projects') {
      loadActivatedProjects();
    } else {
      loadDevices();
    }
  }, [activeTab, projectsPage, projectsPageSize, projectsSearch, selectedTenant]);

  useEffect(() => {
    if (activeTab === 'devices') {
      loadDevices();
    }
  }, [devicesPage, devicesPageSize, devicesSearch, selectedTenant]);

  const handleRevokeProject = async (projectId: string) => {
    if (confirm(`Are you sure you want to revoke the activation for project "${projectId}"? This will remove the activation code assignment.`)) {
      try {
        const response = await fetch(`${API_BASE}/admin/api/projects/${projectId}/revoke-activation`, {
          method: 'POST',
        });
        if (!response.ok) {
          throw new Error('Failed to revoke project activation');
        }
        await loadActivatedProjects();
        alert('Project activation revoked successfully');
      } catch (error) {
        alert('Error revoking project activation: ' + error);
      }
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (confirm(`Are you sure you want to DELETE project "${projectId}"? This action cannot be undone and will delete all project data.`)) {
      try {
        const response = await fetch(`${API_BASE}/api/llm/projects/${projectId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Failed to delete project');
        }
        await loadActivatedProjects();
        alert('Project deleted successfully');
      } catch (error) {
        alert('Error deleting project: ' + error);
      }
    }
  };

  const handleRevokeDevice = async (device: Device) => {
    if (confirm(`Are you sure you want to revoke ${device.label || 'this device'}? This action cannot be undone.`)) {
      try {
        await revokeDevice(device.tenant.toLowerCase().replace(/\s+/g, ''), device.id);
        await loadDevices();
        alert('Device revoked successfully');
      } catch (error) {
        alert('Error revoking device: ' + error);
      }
    }
  };

  const handleDeleteDevice = async (deviceId: number) => {
    if (confirm(`Are you sure you want to DELETE this device? This action cannot be undone.`)) {
      try {
        const response = await fetch(`${API_BASE}/admin/api/devices/${deviceId}/permanent`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Failed to delete device');
        }
        await loadDevices();
        alert('Device deleted successfully');
      } catch (error) {
        alert('Error deleting device: ' + error);
      }
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { className: string; label: string }> = {
      pending: { className: 'bg-gray-100 text-gray-700 border-gray-200', label: 'Pending' },
      running: { className: 'bg-blue-100 text-blue-700 border-blue-200', label: 'Running' },
      completed: { className: 'bg-green-100 text-green-700 border-green-200', label: 'Completed' },
      failed: { className: 'bg-red-100 text-red-700 border-red-200', label: 'Failed' },
      paused: { className: 'bg-yellow-100 text-yellow-700 border-yellow-200', label: 'Paused' },
    };
    return statusMap[status] || statusMap.pending;
  };

  // Load tenants on mount
  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      setLoadingTenants(true);
      // Only load first 10 tenants for the dropdown
      const response = await getTenants({ page: 1, pageSize: 10 });
      setTenants(response.items);
      setTotalTenants(response.total);
    } catch (error) {
      console.error('Error loading tenants:', error);
    } finally {
      setLoadingTenants(false);
    }
  };

  const loadTenantModalData = async () => {
    try {
      setLoadingTenantModal(true);
      const params: TenantQueryParams = {
        page: tenantModalPage,
        pageSize: tenantModalPageSize,
        search: tenantModalSearch.trim() || undefined,
        status: tenantModalStatus !== 'all' ? tenantModalStatus : undefined,
        sortField: 'created_at',
        sortDirection: 'desc',
      };
      const response = await getTenants(params);
      setTenantModalData(response);
    } catch (error) {
      console.error('Error loading tenant modal data:', error);
      setTenantModalData(null);
    } finally {
      setLoadingTenantModal(false);
    }
  };

  // Load tenant modal data when modal opens or filters change
  useEffect(() => {
    if (showTenantModal) {
      loadTenantModalData();
    }
  }, [showTenantModal, tenantModalPage, tenantModalPageSize, tenantModalSearch, tenantModalStatus]);

  const handleSelectTenantFromModal = (tenant: Tenant) => {
    setSelectedTenant(tenant.slug);
    setShowTenantModal(false);
    if (activeTab === 'projects') {
      setProjectsPage(1);
    } else {
      setDevicesPage(1);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="📋 Projects & Devices"
        subtitle="Manage activated projects and authorized devices"
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <Breadcrumb items={[{ label: 'Projects & Devices' }]} />

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('projects')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'projects'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Projects ({projectsTotal})
            </button>
            <button
              onClick={() => setActiveTab('devices')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'devices'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Devices ({devicesTotal})
            </button>
          </nav>
        </div>

        {/* Filters */}
        <Card className="mb-6 p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                placeholder={activeTab === 'projects' ? 'Search projects...' : 'Search devices...'}
                value={activeTab === 'projects' ? projectsSearch : devicesSearch}
                onChange={(e) => {
                  if (activeTab === 'projects') {
                    setProjectsSearch(e.target.value);
                    setProjectsPage(1);
                  } else {
                    setDevicesSearch(e.target.value);
                    setDevicesPage(1);
                  }
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tenant</label>
              <div className="space-y-2">
                <select
                  value={selectedTenant}
                  onChange={(e) => {
                    setSelectedTenant(e.target.value);
                    if (activeTab === 'projects') {
                      setProjectsPage(1);
                    } else {
                      setDevicesPage(1);
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Tenants</option>
                  {tenants.map(tenant => (
                    <option key={tenant.slug} value={tenant.slug}>{tenant.name} ({tenant.slug})</option>
                  ))}
                </select>
                {totalTenants > 10 && (
                  <button
                    type="button"
                    onClick={() => {
                      setShowTenantModal(true);
                      setTenantModalPage(1);
                      setTenantModalSearch('');
                      setTenantModalStatus('all');
                    }}
                    className="w-full text-sm text-purple-600 hover:text-purple-800 font-medium text-left underline mt-1"
                  >
                    See More →
                  </button>
                )}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Items Per Page</label>
              <select
                value={activeTab === 'projects' ? projectsPageSize : devicesPageSize}
                onChange={(e) => {
                  const size = Number(e.target.value);
                  if (activeTab === 'projects') {
                    setProjectsPageSize(size);
                    setProjectsPage(1);
                  } else {
                    setDevicesPageSize(size);
                    setDevicesPage(1);
                  }
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Project</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Tenant</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Activation Code</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Activated At</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Status</th>
                    <th className="px-6 py-4 text-right font-semibold text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {loadingProjects ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                        Loading projects...
                      </td>
                    </tr>
                  ) : projects.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                        {projectsSearch || selectedTenant !== 'all'
                          ? 'No activated projects match your filters'
                          : 'No activated projects found'}
                      </td>
                    </tr>
                  ) : (
                    projects.map((project) => {
                      const statusBadge = getStatusBadge(project.executionStatus);
                      return (
                        <tr key={project.projectId} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-semibold text-gray-900">{project.clientName}</p>
                              <p className="text-xs text-gray-500 font-mono">{project.projectId}</p>
                              {project.description && (
                                <p className="text-xs text-gray-500 mt-1">{project.description}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-gray-600">{project.tenantName}</td>
                          <td className="px-6 py-4">
                            <code className="font-mono text-sm text-purple-600 bg-purple-50 px-2 py-1 rounded">
                              {project.activationCode}
                            </code>
                          </td>
                          <td className="px-6 py-4 text-gray-600">
                            {new Date(project.activatedAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4">
                            <Badge className={statusBadge.className}>{statusBadge.label}</Badge>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleRevokeProject(project.projectId)}
                                className="text-red-600 hover:text-red-800"
                              >
                                Revoke
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDeleteProject(project.projectId)}
                                className="text-red-600 hover:text-red-800"
                              >
                                Delete
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            {projectsTotal > 0 && (
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Showing {projects.length > 0 ? ((projectsPage - 1) * projectsPageSize + 1) : 0} to{' '}
                  {Math.min(projectsPage * projectsPageSize, projectsTotal)} of {projectsTotal} projects
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setProjectsPage(Math.max(1, projectsPage - 1))}
                    disabled={projectsPage === 1}
                  >
                    ← Previous
                  </Button>
                  <span className="text-sm text-gray-600">
                    Page {projectsPage} of {Math.ceil(projectsTotal / projectsPageSize) || 1}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setProjectsPage(Math.min(Math.ceil(projectsTotal / projectsPageSize), projectsPage + 1))}
                    disabled={projectsPage >= Math.ceil(projectsTotal / projectsPageSize)}
                  >
                    Next →
                  </Button>
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Devices Tab */}
        {activeTab === 'devices' && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Device</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Tenant</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Type</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Last Seen</th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-600">Status</th>
                    <th className="px-6 py-4 text-right font-semibold text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {loadingDevices ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                        Loading devices...
                      </td>
                    </tr>
                  ) : devices.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                        {devicesSearch || selectedTenant !== 'all'
                          ? 'No devices match your filters'
                          : 'No devices found'}
                      </td>
                    </tr>
                  ) : (
                    devices.map((device) => (
                      <tr key={device.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div>
                            <p className="font-semibold text-gray-900">{device.label || 'Unnamed Device'}</p>
                            <p className="text-xs text-gray-500 font-mono">{device.hwFingerprint}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-600">{device.tenant}</td>
                        <td className="px-6 py-4 text-gray-600 capitalize">{device.deviceType}</td>
                        <td className="px-6 py-4 text-gray-600">
                          {device.lastSeen ? new Date(device.lastSeen).toLocaleDateString() : 'Never'}
                        </td>
                        <td className="px-6 py-4">
                          {device.isRevoked ? (
                            <Badge className="bg-red-100 text-red-700 border-red-200">Revoked</Badge>
                          ) : (
                            <Badge className="bg-green-100 text-green-700 border-green-200">Active</Badge>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-2">
                            {!device.isRevoked && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleRevokeDevice(device)}
                                className="text-red-600 hover:text-red-800"
                              >
                                Revoke
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteDevice(device.id)}
                              className="text-red-600 hover:text-red-800"
                            >
                              Delete
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Tenant Selection Modal */}
        {showTenantModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col"
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Select Tenant</h2>
                  <p className="text-sm text-gray-600 mt-1">Choose a tenant from the list below</p>
                </div>
                <button
                  onClick={() => setShowTenantModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Modal Search and Filters */}
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                    <input
                      type="text"
                      placeholder="Search tenants..."
                      value={tenantModalSearch}
                      onChange={(e) => {
                        setTenantModalSearch(e.target.value);
                        setTenantModalPage(1);
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                    <select
                      value={tenantModalStatus}
                      onChange={(e) => {
                        setTenantModalStatus(e.target.value);
                        setTenantModalPage(1);
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="all">All Statuses</option>
                      <option value="active">Active</option>
                      <option value="trialing">Trialing</option>
                      <option value="past_due">Past Due</option>
                      <option value="canceled">Canceled</option>
                      <option value="unpaid">Unpaid</option>
                      <option value="suspended">Suspended</option>
                      <option value="none">No Subscription</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Items Per Page</label>
                    <select
                      value={tenantModalPageSize}
                      onChange={(e) => {
                        setTenantModalPageSize(Number(e.target.value));
                        setTenantModalPage(1);
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Modal Table */}
              <div className="flex-1 overflow-y-auto px-6 py-4">
                {loadingTenantModal ? (
                  <div className="text-center py-12 text-gray-500">Loading tenants...</div>
                ) : !tenantModalData || tenantModalData.items.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    {tenantModalSearch || tenantModalStatus !== 'all'
                      ? 'No tenants match your filters'
                      : 'No tenants available'}
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Tenant</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Plan</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Activation Codes</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {tenantModalData.items.map((tenant) => {
                        const statusLabels: Record<string, string> = {
                          active: 'Active',
                          trialing: 'Trialing',
                          past_due: 'Past Due',
                          canceled: 'Canceled',
                          unpaid: 'Unpaid',
                          suspended: 'Suspended',
                          none: 'No Subscription',
                        };
                        const statusBadgeVariants: Record<string, { className: string; label: string }> = {
                          active: { className: 'bg-emerald-100 text-emerald-700 border-emerald-200', label: 'Active' },
                          trialing: { className: 'bg-blue-100 text-blue-700 border-blue-200', label: 'Trialing' },
                          past_due: { className: 'bg-amber-100 text-amber-700 border-amber-200', label: 'Past Due' },
                          canceled: { className: 'bg-gray-100 text-gray-600 border-gray-200', label: 'Canceled' },
                          unpaid: { className: 'bg-rose-100 text-rose-700 border-rose-200', label: 'Unpaid' },
                          suspended: { className: 'bg-purple-100 text-purple-700 border-purple-200', label: 'Suspended' },
                          none: { className: 'bg-slate-100 text-slate-600 border-slate-200', label: 'No Subscription' },
                        };
                        const status = tenant.subscription.status ?? 'none';
                        const statusMeta = statusBadgeVariants[status] ?? statusBadgeVariants.none;
                        
                        return (
                          <tr
                            key={tenant.id}
                            onClick={() => handleSelectTenantFromModal(tenant)}
                            className="hover:bg-purple-50 cursor-pointer transition-colors"
                          >
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-3">
                                <div
                                  className="h-10 w-10 rounded-lg border border-gray-200"
                                  style={{ backgroundColor: tenant.primaryColor ?? '#875A7B' }}
                                />
                                <div>
                                  <p className="font-semibold text-gray-900">{tenant.name}</p>
                                  <p className="text-xs font-mono text-gray-500">{tenant.slug}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-4 text-gray-600">
                              {tenant.subscription.planName ?? 'Not Assigned'}
                            </td>
                            <td className="px-4 py-4 text-gray-600">
                              {tenant.activationCodesUsed ?? 0} / {tenant.activationCodesTotal ?? 0}
                            </td>
                            <td className="px-4 py-4">
                              <Badge className={statusMeta.className}>{statusMeta.label}</Badge>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Modal Pagination */}
              {tenantModalData && tenantModalData.total > 0 && (
                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    Showing {tenantModalData.items.length > 0 ? ((tenantModalPage - 1) * tenantModalPageSize + 1) : 0} to{' '}
                    {Math.min(tenantModalPage * tenantModalPageSize, tenantModalData.total)} of {tenantModalData.total} tenants
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setTenantModalPage(Math.max(1, tenantModalPage - 1))}
                      disabled={tenantModalPage === 1}
                      className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ← Previous
                    </button>
                    <span className="text-sm text-gray-600">
                      Page {tenantModalPage} of {Math.ceil(tenantModalData.total / tenantModalPageSize) || 1}
                    </span>
                    <button
                      onClick={() => setTenantModalPage(Math.min(Math.ceil(tenantModalData.total / tenantModalPageSize), tenantModalPage + 1))}
                      disabled={tenantModalPage >= Math.ceil(tenantModalData.total / tenantModalPageSize)}
                      className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next →
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}

      </main>
      <Footer />
    </div>
  );
}

