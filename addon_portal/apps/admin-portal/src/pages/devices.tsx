import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { Navigation } from '../components/Navigation';
import { AdminHeader } from '../components/AdminHeader';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { getDevices, revokeDevice, type Device } from '../lib/api';
import { getProjects, deleteProject, type Project } from '../lib/api';

type TabType = 'projects' | 'devices';

export default function ProjectsDevicesPage() {
  const [activeTab, setActiveTab] = useState<TabType>('projects');
  
  // Devices state
  const [devices, setDevices] = useState<Device[]>([]);
  const [totalDevices, setTotalDevices] = useState(0);
  const [deviceCurrentPage, setDeviceCurrentPage] = useState(1);
  const [devicePageSize, setDevicePageSize] = useState(25);
  const [deviceTotalPages, setDeviceTotalPages] = useState(1);
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [selectedDeviceStatus, setSelectedDeviceStatus] = useState('all');
  const [deviceSearchQuery, setDeviceSearchQuery] = useState('');
  const [loadingDevices, setLoadingDevices] = useState(false);
  
  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalProjects, setTotalProjects] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProjectStatus, setSelectedProjectStatus] = useState('all');
  const [loadingProjects, setLoadingProjects] = useState(false);

  // Load devices when Devices tab is active or filters/pagination change
  useEffect(() => {
    if (activeTab === 'devices') {
      loadDevices();
    }
  }, [activeTab, deviceCurrentPage, devicePageSize, selectedTenant, deviceSearchQuery, selectedDeviceStatus]);

  // Load projects when Projects tab is active or filters change
  useEffect(() => {
    if (activeTab === 'projects') {
      loadProjects();
    }
  }, [activeTab, currentPage, pageSize, searchQuery, selectedProjectStatus]);

  const loadDevices = async () => {
    try {
      setLoadingDevices(true);
      const tenantSlug = selectedTenant !== 'all' ? selectedTenant : undefined;
      const search = deviceSearchQuery.trim() || undefined;
      const response = await getDevices({
        page: deviceCurrentPage,
        pageSize: devicePageSize,
        tenantSlug: tenantSlug,
        search: search,
      });
      
      let filtered = response.items;
      
      // Filter by status (client-side since backend doesn't support status filter yet)
      if (selectedDeviceStatus === 'active') {
        filtered = filtered.filter(d => !d.isRevoked);
      } else if (selectedDeviceStatus === 'revoked') {
        filtered = filtered.filter(d => d.isRevoked);
      }
      
      setDevices(filtered);
      setTotalDevices(response.total);
      setDeviceTotalPages(Math.ceil(response.total / devicePageSize));
      
      // Reset to page 1 if current page is beyond total pages
      if (deviceCurrentPage > Math.ceil(response.total / devicePageSize) && Math.ceil(response.total / devicePageSize) > 0) {
        setDeviceCurrentPage(1);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
      setDevices([]);
      setTotalDevices(0);
      setDeviceTotalPages(1);
    } finally {
      setLoadingDevices(false);
    }
  };

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const search = searchQuery.trim() || undefined;
      const response = await getProjects({
        page: currentPage,
        pageSize: pageSize,
        search: search,
      });
      
      let filtered = response.items;
      
      // Filter by status
      if (selectedProjectStatus === 'active') {
        filtered = filtered.filter(p => p.isActive);
      } else if (selectedProjectStatus === 'inactive') {
        filtered = filtered.filter(p => !p.isActive);
      } else if (selectedProjectStatus === 'running') {
        filtered = filtered.filter(p => p.executionStatus === 'running');
      } else if (selectedProjectStatus === 'completed') {
        filtered = filtered.filter(p => p.executionStatus === 'completed');
      } else if (selectedProjectStatus === 'failed') {
        filtered = filtered.filter(p => p.executionStatus === 'failed');
      }
      
      setProjects(filtered);
      setTotalProjects(response.total);
      setTotalPages(Math.ceil(response.total / pageSize));
      
      // Reset to page 1 if current page is beyond total pages
      if (currentPage > Math.ceil(response.total / pageSize) && Math.ceil(response.total / pageSize) > 0) {
        setCurrentPage(1);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
      setProjects([]);
      setTotalProjects(0);
      setTotalPages(1);
    } finally {
      setLoadingProjects(false);
    }
  };

  const handleDevicePageSizeChange = (newPageSize: number) => {
    setDevicePageSize(newPageSize);
    setDeviceCurrentPage(1);
  };

  const handleDevicePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= deviceTotalPages) {
      setDeviceCurrentPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleRevokeDevice = async (device: Device) => {
    if (confirm(`Are you sure you want to revoke ${device.label || 'this device'}? This action cannot be undone.`)) {
      try {
        await revokeDevice(device.tenant.toLowerCase().replace(/\s+/g, ''), device.id);
        await loadDevices();
        
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        notification.textContent = 'Device revoked successfully';
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
      } catch (error) {
        alert('Error revoking device: ' + error);
      }
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (confirm(`Are you sure you want to delete project "${projectId}"? This action cannot be undone.`)) {
      try {
        await deleteProject(projectId);
        await loadProjects();
        
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        notification.textContent = 'Project deleted successfully';
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
      } catch (error) {
        alert('Error deleting project: ' + error);
      }
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const getDeviceIcon = (type: string) => {
    return type === 'desktop' ? '💻' : type === 'mobile' ? '📱' : '🖥️';
  };

  const getStatusBadge = (status: string | null, isActive: boolean) => {
    if (!status) {
      return isActive ? 'bg-green-100 text-green-700 border-green-200' : 'bg-gray-100 text-gray-700 border-gray-200';
    }
    const colors: Record<string, string> = {
      running: 'bg-blue-100 text-blue-700 border-blue-200',
      completed: 'bg-green-100 text-green-700 border-green-200',
      failed: 'bg-red-100 text-red-700 border-red-200',
      pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      paused: 'bg-orange-100 text-orange-700 border-orange-200',
    };
    return colors[status] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-700 border-red-200',
      high: 'bg-orange-100 text-orange-700 border-orange-200',
      normal: 'bg-blue-100 text-blue-700 border-blue-200',
      low: 'bg-gray-100 text-gray-700 border-gray-200',
    };
    return colors[priority] || colors.normal;
  };

  // Note: uniqueTenants would need to be loaded separately or from a different endpoint
  // For now, we'll use an empty array and let the backend filter handle it
  const uniqueTenants: string[] = [];

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        title="Projects & Devices"
        subtitle="Manage projects and device authorizations across all tenants"
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <Breadcrumb items={[{ label: 'Projects & Devices' }]} />

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('projects')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'projects'
                    ? 'border-purple-600 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Projects
              </button>
              <button
                onClick={() => setActiveTab('devices')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'devices'
                    ? 'border-purple-600 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Devices
              </button>
            </nav>
          </div>

          {/* Projects Tab Content */}
          {activeTab === 'projects' && (
            <div className="p-6">
              {/* Projects Filters */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                  <input
                    type="text"
                    placeholder="Search projects, client names..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <select
                    value={selectedProjectStatus}
                    onChange={(e) => {
                      setSelectedProjectStatus(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="all">All Statuses</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="running">Running</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Items Per Page</label>
                  <select
                    value={pageSize}
                    onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={loadProjects}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                  >
                    Refresh
                  </button>
                </div>
              </div>
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Showing {projects.length > 0 ? ((currentPage - 1) * pageSize + 1) : 0} to {Math.min(currentPage * pageSize, totalProjects)} of {totalProjects} projects
                </div>
                {loadingProjects && (
                  <div className="text-sm text-gray-500">Loading...</div>
                )}
              </div>

              {/* Projects Table */}
              <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-200">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Project ID</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Client</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Priority</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Created</th>
                        <th className="px-6 py-4 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
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
                            {searchQuery || selectedProjectStatus !== 'all' 
                              ? 'No projects match your filters' 
                              : 'No projects found'}
                          </td>
                        </tr>
                      ) : (
                        projects.map((project, i) => (
                          <motion.tr
                            key={project.projectId}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="hover:bg-gray-50 transition-colors duration-150"
                          >
                            <td className="px-6 py-4">
                              <code className="font-mono text-sm font-semibold text-purple-600 bg-purple-50 px-3 py-1 rounded">
                                {project.projectId}
                              </code>
                            </td>
                            <td className="px-6 py-4">
                              <div>
                                <span className="font-medium text-gray-900">{project.clientName}</span>
                                {project.description && (
                                  <p className="text-sm text-gray-500 mt-1">{project.description}</p>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-col gap-1">
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(project.executionStatus, project.isActive)}`}>
                                  {project.executionStatus ? project.executionStatus.charAt(0).toUpperCase() + project.executionStatus.slice(1) : (project.isActive ? 'Active' : 'Inactive')}
                                </span>
                                {project.activationCodeId && (
                                  <span className="text-xs text-gray-500">Code: {project.activationCodeId}</span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getPriorityBadge(project.priority)}`}>
                                {project.priority.charAt(0).toUpperCase() + project.priority.slice(1)}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-600">
                              {new Date(project.createdAt).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 text-right">
                              <button
                                onClick={() => handleDeleteProject(project.projectId)}
                                className="text-red-600 hover:text-red-800 font-medium text-sm"
                              >
                                Delete
                              </button>
                            </td>
                          </motion.tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                
                {/* Projects Pagination */}
                {totalPages > 1 && (
                  <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {/* First Page Button */}
                        <button
                          onClick={() => handlePageChange(1)}
                          disabled={currentPage === 1}
                          className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                            currentPage === 1
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                          }`}
                          title="First page"
                        >
                          |&lt;&lt;
                        </button>
                        
                        {/* Previous Page Button */}
                        <button
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={currentPage === 1}
                          className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                            currentPage === 1
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                          }`}
                          title="Previous page"
                        >
                          |&lt;
                        </button>
                        
                        {/* Page Number Buttons */}
                        <div className="flex items-center gap-1">
                          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            let pageNum: number;
                            if (totalPages <= 5) {
                              pageNum = i + 1;
                            } else if (currentPage <= 3) {
                              pageNum = i + 1;
                            } else if (currentPage >= totalPages - 2) {
                              pageNum = totalPages - 4 + i;
                            } else {
                              pageNum = currentPage - 2 + i;
                            }
                            
                            return (
                              <button
                                key={pageNum}
                                onClick={() => handlePageChange(pageNum)}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                  currentPage === pageNum
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                                }`}
                              >
                                {pageNum}
                              </button>
                            );
                          })}
                        </div>
                        
                        {/* Next Page Button */}
                        <button
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={currentPage === totalPages}
                          className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                            currentPage === totalPages
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                          }`}
                          title="Next page"
                        >
                          &gt;|
                        </button>
                        
                        {/* Last Page Button */}
                        <button
                          onClick={() => handlePageChange(totalPages)}
                          disabled={currentPage === totalPages}
                          className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                            currentPage === totalPages
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                          }`}
                          title="Last page"
                        >
                          &gt;&gt;|
                        </button>
                      </div>
                      
                      <div className="text-sm text-gray-600">
                        Page {currentPage} of {totalPages}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Devices Tab Content */}
          {activeTab === 'devices' && (
            <div className="p-6">
              {/* Devices Filters */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                  <input
                    type="text"
                    placeholder="Search devices..."
                    value={deviceSearchQuery}
                    onChange={(e) => {
                      setDeviceSearchQuery(e.target.value);
                      setDeviceCurrentPage(1);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tenant</label>
                  <input
                    type="text"
                    placeholder="Enter tenant slug..."
                    value={selectedTenant !== 'all' ? selectedTenant : ''}
                    onChange={(e) => {
                      const value = e.target.value.trim();
                      setSelectedTenant(value || 'all');
                      setDeviceCurrentPage(1);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <select
                    value={selectedDeviceStatus}
                    onChange={(e) => {
                      setSelectedDeviceStatus(e.target.value);
                      setDeviceCurrentPage(1);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="all">All Devices</option>
                    <option value="active">Active</option>
                    <option value="revoked">Revoked</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Items Per Page</label>
                  <select
                    value={devicePageSize}
                    onChange={(e) => handleDevicePageSizeChange(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
              </div>
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Showing {devices.length > 0 ? ((deviceCurrentPage - 1) * devicePageSize + 1) : 0} to {Math.min(deviceCurrentPage * devicePageSize, totalDevices)} of {totalDevices} devices
                </div>
                {loadingDevices && (
                  <div className="text-sm text-gray-500">Loading...</div>
                )}
              </div>

              {/* Device Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                {loadingDevices ? (
                  <div className="col-span-full text-center py-12 text-gray-500">
                    Loading devices...
                  </div>
                ) : devices.length === 0 ? (
                  <div className="col-span-full text-center py-12">
                    <div className="text-6xl mb-4">📱</div>
                    <p className="text-gray-500">
                      {selectedTenant !== 'all' || selectedDeviceStatus !== 'all' || deviceSearchQuery
                        ? 'No devices match your filters' 
                        : 'No devices authorized yet'}
                    </p>
                  </div>
                ) : (
                  devices.map((device, i) => (
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
                          Revoke Access
                        </button>
                      )}
                    </motion.div>
                  ))
                )}
              </div>

              {/* Devices Pagination */}
              {deviceTotalPages > 1 && (
                <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 rounded-b-xl">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {/* First Page Button */}
                      <button
                        onClick={() => handleDevicePageChange(1)}
                        disabled={deviceCurrentPage === 1}
                        className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                          deviceCurrentPage === 1
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                        title="First page"
                      >
                        |&lt;&lt;
                      </button>
                      
                      {/* Previous Page Button */}
                      <button
                        onClick={() => handleDevicePageChange(deviceCurrentPage - 1)}
                        disabled={deviceCurrentPage === 1}
                        className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                          deviceCurrentPage === 1
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                        title="Previous page"
                      >
                        |&lt;
                      </button>
                      
                      {/* Page Number Buttons */}
                      <div className="flex items-center gap-1">
                        {Array.from({ length: Math.min(5, deviceTotalPages) }, (_, i) => {
                          let pageNum: number;
                          if (deviceTotalPages <= 5) {
                            pageNum = i + 1;
                          } else if (deviceCurrentPage <= 3) {
                            pageNum = i + 1;
                          } else if (deviceCurrentPage >= deviceTotalPages - 2) {
                            pageNum = deviceTotalPages - 4 + i;
                          } else {
                            pageNum = deviceCurrentPage - 2 + i;
                          }
                          
                          return (
                            <button
                              key={pageNum}
                              onClick={() => handleDevicePageChange(pageNum)}
                              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                deviceCurrentPage === pageNum
                                  ? 'bg-purple-600 text-white'
                                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                              }`}
                            >
                              {pageNum}
                            </button>
                          );
                        })}
                      </div>
                      
                      {/* Next Page Button */}
                      <button
                        onClick={() => handleDevicePageChange(deviceCurrentPage + 1)}
                        disabled={deviceCurrentPage === deviceTotalPages}
                        className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                          deviceCurrentPage === deviceTotalPages
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                        title="Next page"
                      >
                        &gt;|
                      </button>
                      
                      {/* Last Page Button */}
                      <button
                        onClick={() => handleDevicePageChange(deviceTotalPages)}
                        disabled={deviceCurrentPage === deviceTotalPages}
                        className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                          deviceCurrentPage === deviceTotalPages
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                        title="Last page"
                      >
                        &gt;&gt;|
                      </button>
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      Page {deviceCurrentPage} of {deviceTotalPages}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
