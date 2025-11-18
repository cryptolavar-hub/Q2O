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
  const [statusFilter, setStatusFilter] = useState<Project['status'] | 'all'>('all');
  
  // UI state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
  }, [page, pageSize, statusFilter]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await listProjects(
        page,
        pageSize,
        search || undefined,
        statusFilter !== 'all' ? statusFilter : undefined
      );
      
      setProjects(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
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
    fetchProjects();
  };

  const handleStatusFilter = (status: Project['status'] | 'all') => {
    setStatusFilter(status);
    setPage(1); // Reset to first page
  };

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'active':
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
        return 'bg-gray-100 text-gray-800';
    }
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
                    placeholder="Search projects by name or client..."
                    className="flex-1 px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                  />
                  <button
                    type="submit"
                    className="px-6 py-2 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors"
                  >
                    Search
                  </button>
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
                {(['pending', 'active', 'completed', 'paused', 'failed'] as const).map((status) => (
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
                            project.status
                          )}`}
                        >
                          {project.status}
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
                {totalPages > 1 && (
                  <div className="bg-white rounded-2xl shadow-xl p-6">
                    <div className="flex items-center justify-between">
                      <div className="text-gray-600">
                        Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} projects
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          disabled={page === 1}
                          className="px-4 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          Previous
                        </button>
                        <span className="px-4 py-2 bg-purple-500 text-white font-semibold rounded-lg">
                          Page {page} of {totalPages}
                        </span>
                        <button
                          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                          disabled={page === totalPages}
                          className="px-4 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          Next
                        </button>
                      </div>
                    </div>
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

