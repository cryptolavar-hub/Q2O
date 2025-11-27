/**
 * LLM Overview Dashboard
 * Real-time monitoring of LLM usage, costs, and performance
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import { AdminHeader } from '@/components/AdminHeader';
import { Navigation } from '@/components/Navigation';
import { Breadcrumb } from '@/components/Breadcrumb';
import { Footer } from '@/components/Footer';
import { getTenants, type Tenant, type TenantPage, type TenantQueryParams } from '@/lib/api';

// Use relative URLs to leverage Next.js proxy (avoids IPv6 issues)
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface LLMStats {
  totalCalls: number;
  totalCost: number;
  monthlyBudget: number;
  budgetUsed: number;
  avgResponseTime: number;
  successRate: number;
  providerBreakdown: {
    gemini: { calls: number; cost: number; model?: string };
    openai: { calls: number; cost: number; model?: string };
    anthropic: { calls: number; cost: number; model?: string };
  };
  dailyCosts: Array<{ date: string; cost: number }>;
  templateStats: {
    total: number;
    uses: number;
    saved: number;
  };
  alerts: Array<{
    id: string;
    level: string;
    message: string;
    timestamp: string;
  }>;
}

// Helper function to format model names nicely
const formatModelName = (modelName: string | undefined): string => {
  if (!modelName) return 'Unknown Model';
  
  // Convert "gemini-2.5-flash" -> "Gemini 2.5 Flash"
  // Convert "gpt-4-turbo" -> "GPT-4 Turbo"
  // Convert "claude-3-5-sonnet-20241022" -> "Claude 3.5 Sonnet"
  
  const parts = modelName.split('-');
  
  // Handle Gemini models
  if (modelName.startsWith('gemini')) {
    const version = parts[1] || '';
    const variant = parts[2] || '';
    const variantName = variant.charAt(0).toUpperCase() + variant.slice(1);
    return `Gemini ${version} ${variantName}`.trim();
  }
  
  // Handle GPT models
  if (modelName.startsWith('gpt')) {
    const version = parts[1] || '';
    const variant = parts[2] || '';
    const variantName = variant.charAt(0).toUpperCase() + variant.slice(1);
    return `GPT-${version} ${variantName}`.trim();
  }
  
  // Handle Claude models
  if (modelName.startsWith('claude')) {
    const version = parts[1] || '';
    const subversion = parts[2] || '';
    const variant = parts[3] || '';
    const variantName = variant.charAt(0).toUpperCase() + variant.slice(1);
    if (subversion) {
      return `Claude ${version}.${subversion} ${variantName}`.trim();
    }
    return `Claude ${version} ${variantName}`.trim();
  }
  
  // Fallback: capitalize first letter of each word
  return modelName
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

interface Project {
  projectId: string;
  clientName: string;
  description?: string;
  tenantName?: string;
  tenantSlug?: string;
  agentPrompts: Array<{ agentType: string; enabled: boolean }>;
  executionStatus?: string;
}

export default function LLMOverview() {
  const router = useRouter();
  const [stats, setStats] = useState<LLMStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  
  // Project & Agent Prompts state
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalProjects, setTotalProjects] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [loadingProjects, setLoadingProjects] = useState(false);
  
  // Tenant dropdown and modal state
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [tenantModalPage, setTenantModalPage] = useState(1);
  const [tenantModalPageSize] = useState(10);
  const [tenantModalSearch, setTenantModalSearch] = useState('');
  const [tenantModalStatus, setTenantModalStatus] = useState('all');
  const [tenantModalData, setTenantModalData] = useState<TenantPage | null>(null);
  const [loadingTenantModal, setLoadingTenantModal] = useState(false);
  const [tenantModalSortField, setTenantModalSortField] = useState<'created_at' | 'name' | 'usage_current'>('created_at');
  const [tenantModalSortDirection, setTenantModalSortDirection] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // Load tenants on mount
  useEffect(() => {
    loadTenants();
  }, []);

  // Load projects when filters or pagination changes
  useEffect(() => {
    loadProjects();
  }, [currentPage, selectedTenant, searchQuery]);

  // Load tenant modal data when modal opens or filters change
  useEffect(() => {
    if (showTenantModal) {
      loadTenantModalData();
    }
  }, [showTenantModal, tenantModalPage, tenantModalSearch, tenantModalStatus, tenantModalSortField, tenantModalSortDirection]);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/llm/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch LLM stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBudgetColor = (percentUsed: number) => {
    if (percentUsed >= 95) return 'text-red-600';
    if (percentUsed >= 80) return 'text-orange-600';
    if (percentUsed >= 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const loadTenants = async () => {
    try {
      setLoadingTenants(true);
      const response = await getTenants({ page: 1, pageSize: 100 });
      setTenants(response.items);
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
        sortField: tenantModalSortField,
        sortDirection: tenantModalSortDirection,
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

  const handleTenantModalSort = (field: 'created_at' | 'name' | 'usage_current') => {
    if (tenantModalSortField === field) {
      setTenantModalSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setTenantModalSortField(field);
      setTenantModalSortDirection('asc');
    }
    setTenantModalPage(1);
  };

  const handleSelectTenantFromModal = (tenant: Tenant) => {
    setSelectedTenant(tenant.slug);
    setCurrentPage(1);
    setShowTenantModal(false);
    // Reset modal state
    setTenantModalPage(1);
    setTenantModalSearch('');
    setTenantModalStatus('all');
    setTenantModalSortField('created_at');
    setTenantModalSortDirection('desc');
  };

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      
      // If filtering by tenant, we need to fetch all pages and filter client-side
      // since API doesn't support tenant slug filtering
      let allFetchedProjects: Project[] = [];
      
      if (selectedTenant !== 'all') {
        // Fetch all pages when filtering by tenant
        let hasMore = true;
        let fetchPage = 1;
        
        while (hasMore) {
          const fetchParams = new URLSearchParams({
            page: fetchPage.toString(),
            page_size: '100', // API max
          });
          
          if (searchQuery.trim()) {
            fetchParams.append('search', searchQuery.trim());
          }

          const projectsRes = await fetch(`${API_BASE}/api/llm/projects?${fetchParams.toString()}`);
          if (projectsRes.ok) {
            const projectsData = await projectsRes.json();
            const fetched = projectsData.items || [];
            allFetchedProjects = [...allFetchedProjects, ...fetched];
            
            // Check if there are more pages
            const totalPagesInResponse = Math.ceil((projectsData.total || 0) / 100);
            hasMore = fetchPage < totalPagesInResponse;
            fetchPage++;
          } else {
            hasMore = false;
            console.error('Failed to fetch projects:', projectsRes.status);
          }
        }
        
        // Filter by tenant
        allFetchedProjects = allFetchedProjects.filter((p: Project) => p.tenantSlug === selectedTenant);
        
        // Calculate pagination for filtered results
        const total = allFetchedProjects.length;
        setTotalProjects(total);
        setTotalPages(Math.ceil(total / pageSize));
        
        // Slice to get current page
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const paginatedProjects = allFetchedProjects.slice(startIndex, endIndex);
        
        setProjects(paginatedProjects);
      } else {
        // No tenant filter - use server-side pagination
        const params = new URLSearchParams({
          page: currentPage.toString(),
          page_size: pageSize.toString(),
        });
        
        if (searchQuery.trim()) {
          params.append('search', searchQuery.trim());
        }

        const projectsRes = await fetch(`${API_BASE}/api/llm/projects?${params.toString()}`);
        if (projectsRes.ok) {
          const projectsData = await projectsRes.json();
          setProjects(projectsData.items || []);
          setTotalProjects(projectsData.total || 0);
          setTotalPages(Math.ceil((projectsData.total || 0) / pageSize));
        } else {
          console.error('Failed to fetch projects:', projectsRes.status);
          setProjects([]);
          setTotalProjects(0);
          setTotalPages(1);
        }
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

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return 'bg-gray-100 text-gray-700 border-gray-200';
    const statusLower = status.toLowerCase();
    if (statusLower === 'running' || statusLower === 'in_progress') {
      return 'bg-blue-100 text-blue-700 border-blue-200';
    } else if (statusLower === 'completed') {
      return 'bg-green-100 text-green-700 border-green-200';
    } else if (statusLower === 'failed' || statusLower === 'error') {
      return 'bg-red-100 text-red-700 border-red-200';
    } else if (statusLower === 'paused') {
      return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    } else if (statusLower === 'pending') {
      return 'bg-gray-100 text-gray-700 border-gray-200';
    }
    return 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getStatusLabel = (status?: string) => {
    if (!status) return 'Pending';
    const statusLower = status.toLowerCase();
    if (statusLower === 'running' || statusLower === 'in_progress') return 'Running';
    if (statusLower === 'completed') return 'Completed';
    if (statusLower === 'failed' || statusLower === 'error') return 'Failed';
    if (statusLower === 'paused') return 'Paused';
    if (statusLower === 'pending') return 'Pending';
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="LLM Overview" subtitle="Monitor LLM usage, costs, and performance" />
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading LLM statistics...</p>
          </div>
        </div>
      </div>
    );
  }

  // Don't block the entire page if stats fail - show what we can
  const hasStats = !!stats;

  const budgetPercent = stats ? (stats.budgetUsed / stats.monthlyBudget) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="LLM Overview" subtitle="Monitor LLM usage, costs, and performance" />
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: 'LLM Management', href: '/llm' }, { label: 'Overview' }]} />

        {/* LLM Not Configured Warning */}
        {!hasStats && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">LLM Not Configured</h3>
            <p className="text-yellow-700 mb-4">
              LLM integration is not configured. Please add API keys and enable LLM in settings.
            </p>
            <button
              onClick={() => router.push('/llm/configuration')}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Configure LLM
            </button>
          </div>
        )}

        {/* Project & Agent Prompts Management */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="text-2xl">📝</span> Project &amp; Agent Prompts
            </h2>
            <button
              onClick={() => router.push('/llm/prompts')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              + Add New Project Prompt
            </button>
          </div>
          
          {/* Quick Search */}
          <div className="bg-white rounded-lg shadow-sm p-4 mb-4 border border-gray-200">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search project, tenant, or label..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="w-64">
                <select
                  value={selectedTenant}
                  onChange={(e) => {
                    setSelectedTenant(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Tenants</option>
                  {(() => {
                    // Show selected tenant first if it exists, then show first 9 others
                    const selectedTenantObj = tenants.find(t => t.slug === selectedTenant);
                    const otherTenants = tenants.filter(t => t.slug !== selectedTenant).slice(0, 9);
                    const displayTenants = selectedTenantObj 
                      ? [selectedTenantObj, ...otherTenants]
                      : tenants.slice(0, 10);
                    
                    return displayTenants.map(tenant => (
                      <option key={tenant.slug} value={tenant.slug}>
                        {tenant.name} ({tenant.slug})
                      </option>
                    ));
                  })()}
                </select>
                {tenants.length > 10 && (
                  <button
                    type="button"
                    onClick={() => {
                      setShowTenantModal(true);
                      setTenantModalPage(1);
                      setTenantModalSearch('');
                      setTenantModalStatus('all');
                      setTenantModalSortField('created_at');
                      setTenantModalSortDirection('desc');
                    }}
                    className="mt-2 w-full text-sm text-purple-600 hover:text-purple-800 font-medium text-left underline"
                  >
                    See More →
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Prompts Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {loadingProjects ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                <p className="mt-4 text-gray-600">Loading projects...</p>
              </div>
            ) : (
              <>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Project</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tenant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agents</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {projects.length === 0 ? (
                      <tr className="text-center">
                        <td colSpan={5} className="px-6 py-8 text-gray-500">
                          {searchQuery || selectedTenant !== 'all'
                            ? 'No projects match your filters'
                            : 'No project prompts configured. Click "Add New Project Prompt" to create one.'}
                        </td>
                      </tr>
                    ) : (
                      projects.map((project) => (
                        <tr key={project.projectId} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="font-medium text-gray-900">{project.clientName}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {project.tenantName ? (
                              <div>
                                <div className="font-medium text-gray-900">{project.tenantName}</div>
                                <div className="text-sm text-gray-500 font-mono">{project.tenantSlug}</div>
                              </div>
                            ) : (
                              <span className="text-gray-400 text-sm">—</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900 max-w-md truncate" title={project.description || ''}>
                              {project.description || <span className="text-gray-400">—</span>}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-900">
                              {project.agentPrompts?.filter(ap => ap.enabled).length || 0}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(project.executionStatus)}`}>
                              {getStatusLabel(project.executionStatus)}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
                
                {/* Pagination Controls - Show if more than 10 items */}
                {totalProjects > 10 && (
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
                        Page {currentPage} of {totalPages} ({totalProjects} total)
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Tenant Selector Modal */}
        {showTenantModal && (
          <div 
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => {
              setShowTenantModal(false);
              // Reset modal state when closing
              setTenantModalPage(1);
              setTenantModalSearch('');
              setTenantModalStatus('all');
              setTenantModalSortField('created_at');
              setTenantModalSortDirection('desc');
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white rounded-2xl p-8 max-w-4xl w-full shadow-2xl max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Select Tenant</h3>
                <button
                  onClick={() => {
                    setShowTenantModal(false);
                    // Reset modal state when closing
                    setTenantModalPage(1);
                    setTenantModalSearch('');
                    setTenantModalStatus('all');
                    setTenantModalSortField('created_at');
                    setTenantModalSortDirection('desc');
                  }}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Search and Filters */}
              <div className="mb-4 space-y-3">
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
                  <option value="past_due">Past Due</option>
                  <option value="canceled">Canceled</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>

              {/* Tenant Table */}
              <div className="flex-1 overflow-y-auto mb-4">
                {loadingTenantModal ? (
                  <div className="text-center py-8 text-gray-500">Loading tenants...</div>
                ) : tenantModalData && tenantModalData.items.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th 
                            className="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer hover:bg-gray-100 select-none"
                            onClick={() => handleTenantModalSort('name')}
                          >
                            <div className="flex items-center gap-2">
                              Tenant
                              {tenantModalSortField === 'name' && (
                                <span className="text-purple-600">
                                  {tenantModalSortDirection === 'asc' ? '↑' : '↓'}
                                </span>
                              )}
                            </div>
                          </th>
                          <th 
                            className="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer hover:bg-gray-100 select-none"
                            onClick={() => handleTenantModalSort('created_at')}
                          >
                            <div className="flex items-center gap-2">
                              Plan
                              {tenantModalSortField === 'created_at' && (
                                <span className="text-purple-600">
                                  {tenantModalSortDirection === 'asc' ? '↑' : '↓'}
                                </span>
                              )}
                            </div>
                          </th>
                          <th 
                            className="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer hover:bg-gray-100 select-none"
                            onClick={() => handleTenantModalSort('usage_current')}
                          >
                            <div className="flex items-center gap-2">
                              Activation Codes
                              {tenantModalSortField === 'usage_current' && (
                                <span className="text-purple-600">
                                  {tenantModalSortDirection === 'asc' ? '↑' : '↓'}
                                </span>
                              )}
                            </div>
                          </th>
                          <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 bg-white">
                        {tenantModalData.items.map((tenant) => (
                          <tr
                            key={tenant.slug}
                            onClick={() => handleSelectTenantFromModal(tenant)}
                            className="cursor-pointer hover:bg-purple-50 transition-colors"
                          >
                            <td className="px-4 py-4 align-top">
                              <div className="flex items-center gap-3">
                                <div className="h-10 w-10 rounded-lg border border-gray-200 bg-gray-50" style={{ backgroundColor: tenant.primaryColor ?? '#875A7B' }} />
                                <div>
                                  <p className="font-semibold text-gray-900">{tenant.name}</p>
                                  <p className="text-xs font-mono text-gray-500">{tenant.slug}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-4 align-top text-sm text-gray-600">
                              {tenant.subscription.planName ?? 'Not Assigned'}
                            </td>
                            <td className="px-4 py-4 align-top">
                              <div className="text-sm text-gray-600">
                                {tenant.activationCodesUsed ?? 0} / {tenant.activationCodesTotal ?? 0}
                              </div>
                            </td>
                            <td className="px-4 py-4 align-top">
                              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${
                                tenant.subscription.status === 'active' 
                                ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                                : tenant.subscription.status === 'past_due'
                                ? 'bg-amber-100 text-amber-700 border-amber-200'
                                : tenant.subscription.status === 'canceled'
                                ? 'bg-gray-100 text-gray-600 border-gray-200'
                                : tenant.subscription.status === 'suspended'
                                ? 'bg-purple-100 text-purple-700 border-purple-200'
                                : 'bg-slate-100 text-slate-600 border-slate-200'
                              }`}>
                                {tenant.subscription.status === 'active' ? 'Active' :
                                 tenant.subscription.status === 'past_due' ? 'Past Due' :
                                 tenant.subscription.status === 'canceled' ? 'Canceled' :
                                 tenant.subscription.status === 'suspended' ? 'Suspended' :
                                 'No Subscription'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">No tenants found</div>
                )}
              </div>

              {/* Pagination */}
              {tenantModalData && tenantModalData.total > tenantModalPageSize && (
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <button
                    onClick={() => setTenantModalPage(prev => Math.max(1, prev - 1))}
                    disabled={tenantModalPage === 1}
                    className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {tenantModalPage} of {Math.ceil(tenantModalData.total / tenantModalPageSize)}
                  </span>
                  <button
                    onClick={() => setTenantModalPage(prev => prev + 1)}
                    disabled={tenantModalPage >= Math.ceil(tenantModalData.total / tenantModalPageSize)}
                    className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mb-6 flex gap-3 flex-wrap">
          <button
            onClick={() => router.push('/llm/configuration')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Configuration
          </button>
          <button
            onClick={() => router.push('/llm/templates')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Learned Templates
          </button>
          <button
            onClick={() => router.push('/llm/logs')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Usage Logs
          </button>
          <button
            onClick={() => router.push('/llm/alerts')}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
          >
            Alerts ({hasStats ? (stats?.alerts?.length ?? 0) : 0})
          </button>
        </div>

        {/* Critical Alerts */}
        {hasStats && (stats?.alerts?.length ?? 0) > 0 && (
          <div className="mb-6">
            {(stats?.alerts ?? []).slice(0, 3).map((alert) => (
              <div
                key={alert.id}
                className={`mb-3 p-4 border rounded-lg ${getAlertColor(alert.level)}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{alert.message}</p>
                    <p className="text-sm mt-1 opacity-75">{new Date(alert.timestamp).toLocaleString()}</p>
                  </div>
                  <button className="text-sm underline">Dismiss</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Key Metrics */}
        {hasStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Budget Usage */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">Budget Usage</h3>
              <span className={`text-2xl font-bold ${getBudgetColor(budgetPercent)}`}>
                {budgetPercent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
              <div
                className={`h-3 rounded-full ${
                  budgetPercent >= 95 ? 'bg-red-600' :
                  budgetPercent >= 80 ? 'bg-orange-500' :
                  budgetPercent >= 50 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(budgetPercent, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-600">
              ${(stats?.budgetUsed ?? 0).toFixed(2)} of ${(stats?.monthlyBudget ?? 0).toFixed(2)}
            </p>
          </div>

          {/* Total Calls */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total LLM Calls</h3>
            <p className="text-3xl font-bold text-gray-900">{(stats?.totalCalls ?? 0).toLocaleString()}</p>
            <p className="text-sm text-gray-600 mt-2">
              Success Rate: {(stats?.successRate ?? 0).toFixed(1)}%
            </p>
          </div>

          {/* Avg Response Time */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Avg Response Time</h3>
            <p className="text-3xl font-bold text-gray-900">{(stats?.avgResponseTime ?? 0).toFixed(2)}s</p>
            <p className="text-sm text-green-600 mt-2">Within target range</p>
          </div>

          {/* Cost Savings */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Template Savings</h3>
            <p className="text-3xl font-bold text-green-600">${(stats?.templateStats?.saved ?? 0).toFixed(2)}</p>
            <p className="text-sm text-gray-600 mt-2">
              {stats?.templateStats?.uses ?? 0} template uses
            </p>
          </div>
        </div>
        )}

        {/* Provider Cost Breakdown */}
        {hasStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Gemini */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {formatModelName(stats.providerBreakdown?.gemini?.model)}
              </h3>
              <span className="text-2xl">💎</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Calls:</span>
                <span className="text-sm font-semibold">{stats.providerBreakdown?.gemini?.calls ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Cost:</span>
                <span className="text-sm font-semibold text-blue-600">${(stats.providerBreakdown?.gemini?.cost ?? stats.providerBreakdown?.gemini?.total_cost ?? 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Cost:</span>
                <span className="text-sm font-semibold">${((stats.providerBreakdown?.gemini?.cost ?? 0) / ((stats.providerBreakdown?.gemini?.calls ?? 0) || 1)).toFixed(4)}</span>
              </div>
            </div>
          </div>

          {/* GPT-4 */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {formatModelName(stats.providerBreakdown?.openai?.model)}
              </h3>
              <span className="text-2xl">🤖</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Calls:</span>
                <span className="text-sm font-semibold">{stats.providerBreakdown?.openai?.calls ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Cost:</span>
                <span className="text-sm font-semibold text-green-600">${(stats.providerBreakdown?.openai?.cost ?? stats.providerBreakdown?.openai?.total_cost ?? 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Cost:</span>
                <span className="text-sm font-semibold">${((stats.providerBreakdown?.openai?.cost ?? 0) / ((stats.providerBreakdown?.openai?.calls ?? 0) || 1)).toFixed(4)}</span>
              </div>
            </div>
          </div>

          {/* Claude */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {formatModelName(stats.providerBreakdown?.anthropic?.model)}
              </h3>
              <span className="text-2xl">🧠</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Calls:</span>
                <span className="text-sm font-semibold">{stats.providerBreakdown?.anthropic?.calls ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Cost:</span>
                <span className="text-sm font-semibold text-orange-600">${(stats.providerBreakdown?.anthropic?.cost ?? stats.providerBreakdown?.anthropic?.total_cost ?? 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Cost:</span>
                <span className="text-sm font-semibold">${((stats.providerBreakdown?.anthropic?.cost ?? 0) / ((stats.providerBreakdown?.anthropic?.calls ?? 0) || 1)).toFixed(4)}</span>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* Provider Details */}
        {hasStats && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Provider Usage Details</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Calls
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Success Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {formatModelName(stats.providerBreakdown?.gemini?.model)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.providerBreakdown?.gemini?.calls ?? 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(stats.providerBreakdown?.gemini?.cost ?? stats.providerBreakdown?.gemini?.total_cost ?? 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${((stats.providerBreakdown?.gemini?.cost ?? stats.providerBreakdown?.gemini?.total_cost ?? 0) / ((stats.providerBreakdown?.gemini?.calls ?? 0) || 1)).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    99.2%
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {formatModelName(stats.providerBreakdown?.openai?.model)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.providerBreakdown?.openai?.calls ?? 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(stats.providerBreakdown?.openai?.cost ?? stats.providerBreakdown?.openai?.total_cost ?? 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${((stats.providerBreakdown?.openai?.cost ?? stats.providerBreakdown?.openai?.total_cost ?? 0) / ((stats.providerBreakdown?.openai?.calls ?? 0) || 1)).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    98.8%
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                      {formatModelName(stats.providerBreakdown?.anthropic?.model)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.providerBreakdown?.anthropic?.calls ?? 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(stats.providerBreakdown?.anthropic?.cost ?? stats.providerBreakdown?.anthropic?.total_cost ?? 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${((stats.providerBreakdown?.anthropic?.cost ?? stats.providerBreakdown?.anthropic?.total_cost ?? 0) / ((stats.providerBreakdown?.anthropic?.calls ?? 0) || 1)).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    99.5%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        )}
      </div>
      <Footer />
    </div>
  );
}

