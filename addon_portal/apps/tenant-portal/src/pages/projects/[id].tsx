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
import { getProject, deleteProject, assignActivationCode, runProject, restartProject, type Project } from '../../lib/projects';
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
  const [isRunning, setIsRunning] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [showActivationCodeModal, setShowActivationCodeModal] = useState(false);
  const [activationCodeInput, setActivationCodeInput] = useState('');
  const [isAssigningCode, setIsAssigningCode] = useState(false);

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

  const handleAssignActivationCode = async () => {
    if (!project || !id || typeof id !== 'string' || !activationCodeInput.trim()) {
      setError('Please enter an activation code');
      return;
    }

    setIsAssigningCode(true);
    setError(null);
    try {
      const updatedProject = await assignActivationCode(id, activationCodeInput.trim());
      setProject(updatedProject);
      setShowActivationCodeModal(false);
      setActivationCodeInput('');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to assign activation code';
      setError(errorMessage);
    } finally {
      setIsAssigningCode(false);
    }
  };

  const handleRunProject = async () => {
    if (!project || !id || typeof id !== 'string') return;

    // Validate project can be run
    if (!project.activation_code_id) {
      setError('Project must have an activation code assigned before running. Please assign an activation code first.');
      setShowActivationCodeModal(true);
      return;
    }

    if (!project.name || !project.description || !project.objectives) {
      setError('Project must have Name, Description, and Objectives before running.');
      return;
    }

    setIsRunning(true);
    setError(null);
    try {
      const result = await runProject(id);
      if (result.success) {
        // Redirect to status page
        router.push('/status');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to run project';
      setError(errorMessage);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRestartProject = async () => {
    if (!project || !id || typeof id !== 'string') return;

    // Validate project can be restarted
    if (project.execution_status !== 'failed') {
      setError('Only failed projects can be restarted.');
      return;
    }

    if (!project.activation_code_id) {
      setError('Project must have an activation code assigned before restarting. Please assign an activation code first.');
      setShowActivationCodeModal(true);
      return;
    }

    if (!project.name || !project.description || !project.objectives) {
      setError('Project must have Name, Description, and Objectives before restarting.');
      return;
    }

    setIsRestarting(true);
    setError(null);
    try {
      const result = await restartProject(id);
      if (result.success) {
        // Refresh project data to show updated status
        await fetchProject(id);
        // Redirect to status page
        router.push('/status');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restart project';
      setError(errorMessage);
    } finally {
      setIsRestarting(false);
    }
  };

  const canRunProject = (): { canRun: boolean; reason?: string } => {
    if (!project) return { canRun: false, reason: 'Project not loaded' };
    if (!project.activation_code_id) return { canRun: false, reason: 'Activation code required' };
    if (!project.name || !project.description || !project.objectives) {
      return { canRun: false, reason: 'Name, Description, and Objectives are required' };
    }
    if (project.execution_status === 'running') {
      return { canRun: false, reason: 'Project is already running' };
    }
    return { canRun: true };
  };

  const canRestartProject = (): { canRestart: boolean; reason?: string } => {
    if (!project) return { canRestart: false, reason: 'Project not loaded' };
    if (project.execution_status !== 'failed') {
      return { canRestart: false, reason: 'Only failed projects can be restarted' };
    }
    if (!project.activation_code_id) {
      return { canRestart: false, reason: 'Activation code required' };
    }
    if (!project.name || !project.description || !project.objectives) {
      return { canRestart: false, reason: 'Name, Description, and Objectives are required' };
    }
    return { canRestart: true };
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

  const getExecutionStatusColor = (executionStatus?: string) => {
    switch (executionStatus) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
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
<<<<<<< Updated upstream
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
                    <div className="flex gap-2 flex-wrap">
                      {!project.activation_code_id && (
                        <button
                          onClick={() => setShowActivationCodeModal(true)}
                          className="px-6 py-2 bg-yellow-500 text-white font-semibold rounded-lg hover:bg-yellow-600 transition-colors"
                        >
                          Assign Activation Code
                        </button>
                      )}
                      {/* Restart button (only for failed projects) */}
                      {project.execution_status === 'failed' && (() => {
                        const { canRestart, reason } = canRestartProject();
                        return (
                          <button
                            onClick={handleRestartProject}
                            disabled={!canRestart || isRestarting}
                            title={reason}
                            className={`px-6 py-2 font-semibold rounded-lg transition-colors ${
                              canRestart && !isRestarting
                                ? 'bg-orange-500 text-white hover:bg-orange-600'
                                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            }`}
                          >
                            {isRestarting ? 'Restarting...' : '🔄 RESTART PROJECT'}
                          </button>
                        );
                      })()}
                      {/* Run button (for pending/new projects) */}
                      {project.execution_status !== 'failed' && project.execution_status !== 'running' && (() => {
                        const { canRun, reason } = canRunProject();
                        return (
                          <button
                            onClick={handleRunProject}
                            disabled={!canRun || isRunning}
                            title={reason}
                            className={`px-6 py-2 font-semibold rounded-lg transition-colors ${
                              canRun && !isRunning
                                ? 'bg-green-500 text-white hover:bg-green-600'
                                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            }`}
                          >
                            {isRunning ? 'Running...' : '▶ RUN PROJECT'}
                          </button>
                        );
                      })()}
                      <Link
                        href={`/projects/edit/${project.id}`}
                        className="px-6 py-2 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="px-6 py-2 bg-red-500 text-white font-semibold rounded-lg hover:bg-red-600 transition-colors"
=======
                  {/* Title and Status Badge */}
                  <div className="mb-4">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-3">
                      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{project.name}</h1>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold capitalize self-start sm:self-center ${getExecutionStatusColor(
                          project.execution_status
                        )}`}
>>>>>>> Stashed changes
                      >
                        {project.execution_status || project.status}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {!project.activation_code_id && (
                      <button
                        onClick={() => setShowActivationCodeModal(true)}
                        className="px-4 sm:px-6 py-2 bg-yellow-500 text-white font-semibold rounded-lg hover:bg-yellow-600 transition-colors text-sm sm:text-base"
                      >
                        Assign Activation Code
                      </button>
                    )}
                    {/* Download button (only for completed projects) */}
                    {project.execution_status === 'completed' && (
                      <button
                        onClick={handleDownloadProject}
                        disabled={isDownloading}
                        className={`px-4 sm:px-6 py-2 font-semibold rounded-lg transition-colors text-sm sm:text-base ${
                          !isDownloading
                            ? 'bg-blue-500 text-white hover:bg-blue-600'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                      >
                        {isDownloading ? 'Downloading...' : '⬇ DOWNLOAD'}
                      </button>
                    )}
                    {/* Restart button (only for failed projects) */}
                    {project.execution_status === 'failed' && (() => {
                      const { canRestart, reason } = canRestartProject();
                      return (
                        <button
                          onClick={handleRestartProject}
                          disabled={!canRestart || isRestarting}
                          title={reason}
                          className={`px-4 sm:px-6 py-2 font-semibold rounded-lg transition-colors text-sm sm:text-base ${
                            canRestart && !isRestarting
                              ? 'bg-orange-500 text-white hover:bg-orange-600'
                              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          }`}
                        >
                          {isRestarting ? 'Restarting...' : '🔄 RESTART'}
                        </button>
                      );
                    })()}
                    {/* Run button (for pending/new projects, not completed) */}
                    {project.execution_status !== 'failed' && 
                     project.execution_status !== 'running' && 
                     project.execution_status !== 'completed' && (() => {
                      const { canRun, reason } = canRunProject();
                      return (
                        <button
                          onClick={handleRunProject}
                          disabled={!canRun || isRunning}
                          title={reason}
                          className={`px-4 sm:px-6 py-2 font-semibold rounded-lg transition-colors text-sm sm:text-base ${
                            canRun && !isRunning
                              ? 'bg-green-500 text-white hover:bg-green-600'
                              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          }`}
                        >
                          {isRunning ? 'Running...' : '▶ RUN PROJECT'}
                        </button>
                      );
                    })()}
                    {/* Edit button (hidden for completed projects) */}
                    {project.execution_status !== 'completed' && (
                      <Link
                        href={`/projects/edit/${project.id}`}
                        className="px-4 sm:px-6 py-2 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors text-sm sm:text-base"
                      >
                        Edit
                      </Link>
                    )}
                    <button
                      onClick={() => setShowDeleteConfirm(true)}
                      className="px-4 sm:px-6 py-2 bg-red-500 text-white font-semibold rounded-lg hover:bg-red-600 transition-colors text-sm sm:text-base"
                    >
                      Delete
                    </button>
                  </div>

                  {/* Client Name */}
                  {project.client_name && (
                    <div className="mb-4">
                      <p className="text-gray-600 text-base sm:text-lg">Client: {project.client_name}</p>
                    </div>
                  )}

                  {/* Project Metadata */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
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
                        <span className="font-semibold">Activation Code:</span>{' '}
                        <span className="font-mono text-xs bg-green-50 px-2 py-1 rounded">Assigned</span>
                      </div>
                    )}
                    {project.execution_status && (
                      <div>
                        <span className="font-semibold">Execution Status:</span>{' '}
                        <span className={`px-2 py-1 rounded text-xs font-semibold capitalize ${getExecutionStatusColor(project.execution_status)}`}>
                          {project.execution_status}
                        </span>
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

        {/* Activation Code Assignment Modal */}
        {showActivationCodeModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Assign Activation Code</h3>
              <p className="text-gray-700 mb-4">
                Enter an activation code to assign to this project. The code must belong to your tenant and be valid.
              </p>
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Activation Code
                </label>
                <input
                  type="text"
                  value={activationCodeInput}
                  onChange={(e) => setActivationCodeInput(e.target.value)}
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors font-mono"
                  disabled={isAssigningCode}
                />
              </div>
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowActivationCodeModal(false);
                    setActivationCodeInput('');
                    setError(null);
                  }}
                  disabled={isAssigningCode}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAssignActivationCode}
                  disabled={isAssigningCode || !activationCodeInput.trim()}
                  className="flex-1 px-4 py-2 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isAssigningCode ? 'Assigning...' : 'Assign Code'}
                </button>
              </div>
            </div>
          </div>
        )}

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

