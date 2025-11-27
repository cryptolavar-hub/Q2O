/**
 * Edit Project Page
 * 
 * Form to edit an existing project for the authenticated tenant.
 */

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { SessionGuard } from '../../../components/SessionGuard';
import { Navigation } from '../../../components/Navigation';
import { Breadcrumb } from '../../../components/Breadcrumb';
import { getProject, updateProject, type Project, type ProjectUpdatePayload } from '../../../lib/projects';
import { useAuth } from '../../../hooks/useAuth';

export default function EditProjectPage() {
  const router = useRouter();
  const { id } = router.query;
  const { logout } = useAuth();
  
  const [project, setProject] = useState<Project | null>(null);
  const [formData, setFormData] = useState<ProjectUpdatePayload>({
    name: '',
    client_name: '',
    description: '',
    objectives: '',
    status: 'pending',
  });
  
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id && typeof id === 'string') {
      fetchProject(id);
    }
  }, [id]);

  const fetchProject = async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      setProject(null);  // Clear project state before fetching
      const data = await getProject(projectId);
      setProject(data);
      // Ensure all fields are populated correctly from the mapped data
      // name should be client_name (project name), client_name should also be client_name (for editing)
      // objectives should be custom_instructions from backend
      setFormData({
        name: data.name || data.client_name || '',  // Use name (which is mapped from client_name) or fallback to client_name
        client_name: data.client_name || data.name || '',  // Preserve original client_name, fallback to name
        description: data.description || '',
        objectives: data.objectives || '',  // This is mapped from custom_instructions
        status: data.status,
      });
      setError(null);  // Clear any previous errors on success
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load project';
      setError(errorMessage);
      setProject(null);  // Clear project state on error
      setFormData({  // Clear form data on error
        name: '',
        client_name: '',
        description: '',
        objectives: '',
        status: 'pending',
      });
      
      // If session expired, logout
      if (errorMessage.includes('Session expired')) {
        await logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!id || typeof id !== 'string') {
      setError('Invalid project ID');
      return;
    }

    if (!formData.name?.trim()) {
      setError('Project name is required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const updated = await updateProject(id, {
        name: formData.name.trim(),
        client_name: formData.client_name?.trim() || undefined,
        description: formData.description?.trim() || undefined,
        objectives: formData.objectives?.trim() || undefined,
        status: formData.status,
      });
      
      // Redirect to project detail page
      router.push(`/projects/${updated.id}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update project';
      setError(errorMessage);
      
      // If session expired, logout
      if (errorMessage.includes('Session expired')) {
        await logout();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof ProjectUpdatePayload) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  if (loading) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
              <div className="text-gray-500 text-lg">Loading project...</div>
            </div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  if (!project) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
              <div className="text-gray-500 text-lg mb-4">Project not found</div>
              <Link
                href="/projects"
                className="inline-block px-6 py-3 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600 transition-colors"
              >
                Back to Projects
              </Link>
            </div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  return (
    <SessionGuard>
      <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <Navigation />
        
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumb items={[
            { label: 'Projects', href: '/projects' },
            { label: project.name, href: `/projects/${project.id}` },
            { label: 'Edit' },
          ]} />

          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Project</h1>
              <p className="text-gray-600 mb-6">
                Update project details and objectives
              </p>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 font-medium">{error}</p>
                  <p className="text-red-600 text-sm mt-2">
                    If this project exists, please check your session and try refreshing the page.
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Project Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2">
                    Project Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={handleChange('name')}
                    required
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                    placeholder="e.g., QuickBooks Migration"
                    disabled={isSubmitting}
                  />
                </div>

                {/* Client Name */}
                <div>
                  <label htmlFor="client_name" className="block text-sm font-semibold text-gray-700 mb-2">
                    Client Name
                  </label>
                  <input
                    id="client_name"
                    type="text"
                    value={formData.client_name}
                    onChange={handleChange('client_name')}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                    placeholder="e.g., Acme Corporation"
                    disabled={isSubmitting}
                  />
                </div>

                {/* Status */}
                <div>
                  <label htmlFor="status" className="block text-sm font-semibold text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    id="status"
                    value={formData.status}
                    onChange={handleChange('status')}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                    disabled={isSubmitting}
                  >
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    {/* Note: Backend only supports active/paused. Other statuses (pending, completed, failed) are not persisted. */}
                    <option value="pending">Pending (maps to Paused)</option>
                    <option value="completed">Completed (maps to Paused)</option>
                    <option value="failed">Failed (maps to Paused)</option>
                  </select>
                  <p className="mt-2 text-sm text-gray-500">
                    Note: Backend only supports Active and Paused. Other statuses will be saved as Paused.
                  </p>
                </div>

                {/* Description */}
                <div>
                  <label htmlFor="description" className="block text-sm font-semibold text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={handleChange('description')}
                    rows={4}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors resize-none"
                    placeholder="Brief description of the project..."
                    disabled={isSubmitting}
                  />
                </div>

                {/* Objectives */}
                <div>
                  <label htmlFor="objectives" className="block text-sm font-semibold text-gray-700 mb-2">
                    Objectives
                  </label>
                  <textarea
                    id="objectives"
                    value={formData.objectives}
                    onChange={handleChange('objectives')}
                    rows={6}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors resize-none"
                    placeholder="List the main objectives for this project..."
                    disabled={isSubmitting}
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    Enter one objective per line or use bullet points
                  </p>
                </div>

                {/* Form Actions */}
                <div className="flex gap-3 pt-4">
                  <Link
                    href={`/projects/${project.id}`}
                    className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors text-center"
                  >
                    Cancel
                  </Link>
                  <button
                    type="submit"
                    disabled={isSubmitting || !formData.name?.trim()}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    {isSubmitting ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </main>
      </div>
    </SessionGuard>
  );
}

