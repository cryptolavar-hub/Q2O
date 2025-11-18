/**
 * Create New Project Page
 * 
 * Form to create a new project for the authenticated tenant.
 */

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { SessionGuard } from '../../components/SessionGuard';
import { Navigation } from '../../components/Navigation';
import { Breadcrumb } from '../../components/Breadcrumb';
import { createProject, type ProjectCreatePayload } from '../../lib/projects';
import { useAuth } from '../../hooks/useAuth';

export default function NewProjectPage() {
  const router = useRouter();
  const { logout } = useAuth();
  
  const [formData, setFormData] = useState<ProjectCreatePayload>({
    name: '',
    client_name: '',
    description: '',
    objectives: '',
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Project name is required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const project = await createProject({
        name: formData.name.trim(),
        client_name: formData.client_name?.trim() || undefined,
        description: formData.description?.trim() || undefined,
        objectives: formData.objectives?.trim() || undefined,
      });
      
      // Redirect to project detail page
      router.push(`/projects/${project.id}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create project';
      setError(errorMessage);
      
      // If session expired, logout
      if (errorMessage.includes('Session expired')) {
        await logout();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof ProjectCreatePayload) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  return (
    <SessionGuard>
      <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <Navigation />
        
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumb items={[
            { label: 'Projects', href: '/projects' },
            { label: 'New Project' },
          ]} />

          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New Project</h1>
              <p className="text-gray-600 mb-6">
                Create a new project to track your work and objectives
              </p>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 font-medium">{error}</p>
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
                    href="/projects"
                    className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors text-center"
                  >
                    Cancel
                  </Link>
                  <button
                    type="submit"
                    disabled={isSubmitting || !formData.name.trim()}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    {isSubmitting ? 'Creating...' : 'Create Project'}
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

