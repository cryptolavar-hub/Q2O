/**
 * Projects List Page
 * 
 * Displays all projects for the authenticated tenant with search, filter, and pagination.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { SessionGuard } from '../../components/SessionGuard';
import { Navigation } from '../../components/Navigation';
import { Breadcrumb } from '../../components/Breadcrumb';
import { listProjects, type Project, type ProjectCollectionResponse } from '../../lib/projects';
import { useAuth } from '../../hooks/useAuth';

export default function ProjectsPage() {
  const router = useRouter();
  const { logout } = useAuth();
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  
  // Filters
  const [search, setSearch] = useState('');
  const [searchQuery, setSearchQuery] = useState(''); // Actual search query used for API calls
  const [statusFilter, setStatusFilter] = useState<Project['execution_status'] | 'all'>('all');
  
  // UI state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // Only fetch when page, pageSize, statusFilter, or searchQuery changes (not on every keystroke)
  useEffect(() => {
    fetchProjects();
  }, [page, pageSize, statusFilter, searchQuery]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all projects (no status filter on backend since we filter by execution_status)
      const response = await listProjects(
        page,
        pageSize,
        searchQuery || undefined,
        undefined // Don't filter by status on backend
      );
      
      // Filter by execution_status on frontend
      let filteredProjects = response.items;
      if (statusFilter !== 'all') {
        filteredProjects = response.items.filter((project) => {
          // Use execution_status if available, otherwise fallback to status
          const projectStatus = project.execution_status || project.status;
          return projectStatus === statusFilter;
        });
      }
      
      setProjects(filteredProjects);
      // For filtered results, we need to recalculate totals
      // Note: This is a simplified approach - for accurate pagination with filters,
      // the backend would need to support execution_status filtering
      if (statusFilter !== 'all') {
        // If filtering, we show filtered count but pagination might not be accurate
        // This is a limitation of frontend-only filtering
        setTotal(filteredProjects.length);
        setTotalPages(Math.max(1, Math.ceil(filteredProjects.length / pageSize)));
      } else {
        setTotal(response.total);
        setTotalPages(response.total_pages);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load projects';
      setError(errorMessage);
      
      // If session expired, logout
      if (errorMessage.includes('Session expired')) {
        await logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setPage(1); // Reset to first page
    setSearchQuery(search); // Update the actual search query, which triggers useEffect
  };

  const handleStatusFilter = (status: Project['execution_status'] | 'all') => {
    setStatusFilter(status);
    setPage(1); // Reset to first page
  };

  const handleClearSearch = () => {
    setSearch('');
    setSearchQuery('');
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when changing page size
  };

  const getStatusColor = (executionStatus?: Project['execution_status']) => {
    switch (executionStatus) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'paused':
        return 'bg-gray-100 text-gray-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        // Fallback to gray if execution_status is not set
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getDisplayStatus = (project: Project): string => {
    // Use execution_status if available, otherwise fallback to status
    return project.execution_status || project.status || 'pending';
  };

  return (
    <SessionGuard>
      <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <Navigation />
        
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumb items={[{ label: 'Projects' }]} />

          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
                  <p className="text-gray-600 mt-1">
                    Manage your projects and track their progress
                  </p>
                </div>
                <Link
                  href="/projects/new"
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                >
                  + New Project
                </Link>
              </div>
            </div>

            {/* Search and Filters */}
            <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
              <form onSubmit={handleSearch} className="mb-4">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by name, description, project ID, or objectives..."
                    className="flex-1 px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                  />
                  <button
                    type="submit"
                    className="px-6 py-2 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors"
                  >
                    Search
                  </button>
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={handleClearSearch}
                      className="px-6 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </form>

              {/* Status Filter */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleStatusFilter('all')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    statusFilter === 'all'
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                {(['pending', 'running', 'completed', 'paused', 'failed'] as const).map((status) => (
                  <button
                    key={status}
                    onClick={() => handleStatusFilter(status)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors capitalize ${
                      statusFilter === status
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-700 font-medium">{error}</p>
              </div>
            )}

            {/* Projects List */}
            {loading ? (
              <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
                <div className="text-gray-500 text-lg">Loading projects...</div>
              </div>
            ) : projects.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
                <div className="text-gray-500 text-lg mb-4">No projects found</div>
                <Link
                  href="/projects/new"
                  className="inline-block px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 transition-all"
                >
                  Create Your First Project
                </Link>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-900 mb-1">
                            {project.name}
                          </h3>
                          {project.client_name && (
                            <p className="text-gray-600 text-sm">Client: {project.client_name}</p>
                          )}
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${getStatusColor(
                            project.execution_status
                          )}`}
                        >
                          {getDisplayStatus(project)}
                        </span>
                      </div>

                      {project.description && (
                        <p className="text-gray-700 text-sm mb-4 line-clamp-2">
                          {project.description}
                        </p>
                      )}

                      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                        <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
                        {project.updated_at !== project.created_at && (
                          <span>Updated: {new Date(project.updated_at).toLocaleDateString()}</span>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <Link
                          href={`/projects/${project.id}`}
                          className="flex-1 px-4 py-2 bg-purple-500 text-white text-center font-semibold rounded-lg hover:bg-purple-600 transition-colors"
                        >
                          View
                        </Link>
                        <Link
                          href={`/projects/edit/${project.id}`}
                          className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 text-center font-semibold rounded-lg hover:bg-gray-300 transition-colors"
                        >
                          Edit
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                {(totalPages > 1 || total > 0) && (
                  <div className="bg-white rounded-2xl shadow-xl p-6">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                      {/* Left: Results info and page size selector */}
                      <div className="flex flex-col sm:flex-row items-center gap-4">
                        <div className="text-gray-600 text-sm">
                          Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} projects
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="text-sm text-gray-600 whitespace-nowrap">Items Per Page:</label>
                          <select
                            value={pageSize}
                            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                            className="px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors text-sm font-medium"
                          >
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                          </select>
                        </div>
                      </div>

                      {/* Right: Pagination controls */}
                      {totalPages > 1 && (
                        <div className="flex items-center gap-2">
                          {/* First Page Button */}
                          <button
                            onClick={() => handlePageChange(1)}
                            disabled={page === 1}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                              page === 1
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                            title="First page"
                          >
                            ««
                          </button>
                          
                          {/* Previous Page Button */}
                          <button
                            onClick={() => handlePageChange(page - 1)}
                            disabled={page === 1}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                              page === 1
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                            title="Previous page"
                          >
                            «
                          </button>
                          
                          {/* Page Number Buttons */}
                          <div className="flex items-center gap-1">
                            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                              let pageNum: number;
                              if (totalPages <= 5) {
                                pageNum = i + 1;
                              } else if (page <= 3) {
                                pageNum = i + 1;
                              } else if (page >= totalPages - 2) {
                                pageNum = totalPages - 4 + i;
                              } else {
                                pageNum = page - 2 + i;
                              }
                              
                              return (
                                <button
                                  key={pageNum}
                                  onClick={() => handlePageChange(pageNum)}
                                  className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
                                    page === pageNum
                                      ? 'bg-purple-500 text-white'
                                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                  }`}
                                >
                                  {pageNum}
                                </button>
                              );
                            })}
                          </div>
                          
                          {/* Next Page Button */}
                          <button
                            onClick={() => handlePageChange(page + 1)}
                            disabled={page === totalPages}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                              page === totalPages
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                            title="Next page"
                          >
                            »
                          </button>
                          
                          {/* Last Page Button */}
                          <button
                            onClick={() => handlePageChange(totalPages)}
                            disabled={page === totalPages}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                              page === totalPages
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                            title="Last page"
                          >
                            »»
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {/* Page info */}
                    {totalPages > 1 && (
                      <div className="mt-4 text-center text-sm text-gray-600">
                        Page {page} of {totalPages}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </SessionGuard>
  );
}

