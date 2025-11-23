import React, { useState, useEffect } from 'react';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { Card, Button, Badge } from '@/design-system';
import { getDevices, revokeDevice, type Device } from '../lib/api';

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
        const response = await fetch(`${API_BASE}/admin/api/devices/${deviceId}/delete`, {
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

  // Get unique tenants for filter
  const uniqueTenants = Array.from(new Set([
    ...projects.map(p => p.tenantName),
    ...devices.map(d => d.tenant),
  ]));

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
                {uniqueTenants.map(tenant => (
                  <option key={tenant} value={tenant}>{tenant}</option>
                ))}
              </select>
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

      </main>
      <Footer />
    </div>
  );
}

