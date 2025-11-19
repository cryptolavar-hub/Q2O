/**
 * Project Detail Page
 * 
 * Displays full details of a single project, including status, linked activation code, and device count.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { SessionGuard } from '../../components/SessionGuard';
import { Navigation } from '../../components/Navigation';
import { Breadcrumb } from '../../components/Breadcrumb';
import { getProject, deleteProject, type Project } from '../../lib/projects';
import { useAuth } from '../../hooks/useAuth';

export default function ProjectDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const { logout } = useAuth();
  
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (id && typeof id === 'string') {
      fetchProject(id);
    }
  }, [id]);

  const fetchProject = async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getProject(projectId);
      setProject(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load project';
      setError(errorMessage);
      
      // If session expired, logout
      if (errorMessage.includes('Session expired')) {
        await logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!project || !id || typeof id !== 'string') return;

    setIsDeleting(true);
    try {
      await deleteProject(id);
      // Redirect to projects list after successful deletion
      router.push('/projects');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete project';
      setError(errorMessage);
      setShowDeleteConfirm(false);
      
      // If session expired, logout
      if (errorMessage.includes('Session expired')) {
        await logout();
      }
    } finally {
      setIsDeleting(false);
    }
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
          <Breadcrumb items={[
            { label: 'Projects', href: '/projects' },
            { label: project?.name || 'Loading...' },
          ]} />

          <div className="max-w-4xl mx-auto">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-700 font-medium">{error}</p>
              </div>
            )}

            {/* Loading State */}
            {loading ? (
              <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
                <div className="text-gray-500 text-lg">Loading project...</div>
              </div>
            ) : !project ? (
              <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
                <div className="text-gray-500 text-lg mb-4">Project not found</div>
                <Link
                  href="/projects"
                  className="inline-block px-6 py-3 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors"
                >
                  Back to Projects
                </Link>
              </div>
            ) : (
              <>
                {/* Project Header */}
                <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${getStatusColor(
                            project.status
                          )}`}
                        >
                          {project.status}
                        </span>
                      </div>
                      {project.client_name && (
                        <p className="text-gray-600 text-lg">Client: {project.client_name}</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Link
                        href={`/projects/edit/${project.id}`}
                        className="px-6 py-2 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="px-6 py-2 bg-red-500 text-white font-semibold rounded-lg hover:bg-red-600 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* Project Metadata */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="font-semibold">Created:</span>{' '}
                      {new Date(project.created_at).toLocaleString()}
                    </div>
                    {project.updated_at !== project.created_at && (
                      <div>
                        <span className="font-semibold">Last Updated:</span>{' '}
                        {new Date(project.updated_at).toLocaleString()}
                      </div>
                    )}
                    {project.activation_code_id && (
                      <div>
                        <span className="font-semibold">Activation Code ID:</span>{' '}
                        <span className="font-mono text-xs">{project.activation_code_id}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Description */}
                {project.description && (
                  <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Description</h2>
                    <p className="text-gray-700 whitespace-pre-wrap">{project.description}</p>
                  </div>
                )}

                {/* Objectives */}
                {project.objectives && (
                  <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Objectives</h2>
                    <div className="text-gray-700 whitespace-pre-wrap">{project.objectives}</div>
                  </div>
                )}

                {/* Back Button */}
                <div className="text-center">
                  <Link
                    href="/projects"
                    className="inline-block px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    ← Back to Projects
                  </Link>
                </div>
              </>
            )}
          </div>
        </main>

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Delete Project</h3>
              <p className="text-gray-700 mb-6">
                Are you sure you want to delete <strong>{project?.name}</strong>? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2 bg-red-500 text-white font-semibold rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </SessionGuard>
  );
}

