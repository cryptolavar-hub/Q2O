/**
 * Learned Templates Management
 * View, search, edit, and export learned templates
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { AdminHeader } from '@/components/AdminHeader';
import { Navigation } from '@/components/Navigation';
import { Breadcrumb } from '@/components/Breadcrumb';
import { Footer } from '@/components/Footer';

interface LearnedTemplate {
  template_id: string;
  name: string;
  task_pattern: string;
  tech_stack: string[];
  template_content: string;
  source_llm: string;
  quality_score: number;
  usage_count: number;
  cost_saved: number;
  created_at: string;
  last_used: string;
  parameters: string[];
}

export default function LearnedTemplates() {
  const router = useRouter();
  const [templates, setTemplates] = useState<LearnedTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTech, setFilterTech] = useState('all');
  const [sortBy, setSortBy] = useState<'usage' | 'quality' | 'recent'>('usage');
  const [selectedTemplate, setSelectedTemplate] = useState<LearnedTemplate | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalTemplates, setTotalTemplates] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [allTemplatesForStats, setAllTemplatesForStats] = useState<LearnedTemplate[]>([]);

  useEffect(() => {
    fetchTemplates();
  }, [currentPage, pageSize, searchTerm, filterTech, sortBy]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy === 'usage' ? 'usage_count' : sortBy === 'quality' ? 'quality_score' : 'created_at',
      });
      
      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim());
      }
      if (filterTech !== 'all') {
        params.append('tech_stack', filterTech);
      }
      
      const response = await fetch(`/api/llm/templates?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
        setTotalTemplates(data.total || 0);
        setTotalPages(data.total_pages || 1);
        
        // Reset to page 1 if current page is beyond total pages
        if (currentPage > data.total_pages && data.total_pages > 0) {
          setCurrentPage(1);
        }
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      setTemplates([]);
      setTotalTemplates(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  const exportTemplate = (template: LearnedTemplate) => {
    const data = JSON.stringify(template, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `template_${template.template_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportAll = () => {
    const data = JSON.stringify(templates, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `all_templates_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const deleteTemplate = async (templateId: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
      const response = await fetch(`/api/llm/templates/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // Refresh templates after deletion
        await fetchTemplates();
        setSelectedTemplate(null);
        alert('Template deleted successfully');
      } else {
        alert('Failed to delete template');
      }
    } catch (error) {
      console.error('Failed to delete template:', error);
      alert('Failed to delete template');
    }
  };

  // Fetch all templates for stats (without pagination)
  useEffect(() => {
    const fetchAllForStats = async () => {
      try {
        const response = await fetch('/api/llm/templates?page=1&page_size=10000');
        if (response.ok) {
          const data = await response.json();
          setAllTemplatesForStats(data.templates || []);
        }
      } catch (error) {
        console.error('Failed to fetch templates for stats:', error);
      }
    };
    fetchAllForStats();
  }, []);

  // Get unique tech stacks from all templates
  const allTechStacks = Array.from(
    new Set(allTemplatesForStats.flatMap(t => t.tech_stack))
  ).sort();

  // Calculate stats from all templates
  const totalUses = allTemplatesForStats.reduce((sum, t) => sum + t.usage_count, 0);
  const totalSaved = allTemplatesForStats.reduce((sum, t) => sum + t.cost_saved, 0);
  const avgQuality = allTemplatesForStats.length > 0
    ? allTemplatesForStats.reduce((sum, t) => sum + t.quality_score, 0) / allTemplatesForStats.length
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="Learned Templates" subtitle="View and manage AI-learned code templates" />
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading templates...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="Learned Templates" subtitle="View and manage AI-learned code templates" />
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <Breadcrumb items={[{ label: 'LLM Management', href: '/llm' }, { label: 'Templates' }]} />

        {/* Back Button */}
        <button
          onClick={() => router.push('/llm')}
          className="mb-6 text-blue-600 hover:text-blue-700 flex items-center gap-2"
        >
          ← Back to Overview
        </button>
        
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Templates</h3>
            <p className="text-3xl font-bold text-gray-900">{totalTemplates}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Uses</h3>
            <p className="text-3xl font-bold text-gray-900">{totalUses}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Cost Saved</h3>
            <p className="text-3xl font-bold text-green-600">${totalSaved.toFixed(2)}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Avg Quality</h3>
            <p className="text-3xl font-bold text-gray-900">{avgQuality.toFixed(0)}%</p>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="md:col-span-2">
              <input
                type="text"
                placeholder="Search templates by name, pattern, or tech stack..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1); // Reset to first page when search changes
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <select
                value={filterTech}
                onChange={(e) => {
                  setFilterTech(e.target.value);
                  setCurrentPage(1); // Reset to first page when filter changes
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Technologies</option>
                {allTechStacks.map(tech => (
                  <option key={tech} value={tech}>{tech}</option>
                ))}
              </select>
            </div>

            <div>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value as 'usage' | 'quality' | 'recent');
                  setCurrentPage(1); // Reset to first page when sort changes
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="usage">Most Used</option>
                <option value="quality">Highest Quality</option>
                <option value="recent">Most Recent</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              Showing {templates.length > 0 ? ((currentPage - 1) * pageSize + 1) : 0} to {Math.min(currentPage * pageSize, totalTemplates)} of {totalTemplates} templates
            </div>
            <div className="flex items-center gap-4">
              <label className="text-sm text-gray-600">Items Per Page</label>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <button
                onClick={exportAll}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Export All
              </button>
            </div>
          </div>
        </div>

        {/* Templates List */}
        {loading ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading templates...</p>
          </div>
        ) : templates.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Templates Yet</h3>
            <p className="text-gray-600 mb-6">
              {totalTemplates === 0
                ? 'Templates will appear here as the system learns from LLM generations.'
                : 'No templates match your search criteria.'}
            </p>
            {searchTerm || filterTech !== 'all' ? (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterTech('all');
                  setCurrentPage(1);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Clear Filters
              </button>
            ) : null}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4">
              {templates.map((template) => (
              <div
                key={template.template_id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedTemplate(template)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {template.name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-3">{template.task_pattern}</p>
                      <div className="flex flex-wrap gap-2">
                        {template.tech_stack.map((tech) => (
                          <span
                            key={tech}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        template.quality_score >= 95 ? 'bg-green-100 text-green-800' :
                        template.quality_score >= 90 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {template.quality_score}% quality
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          exportTemplate(template);
                        }}
                        className="p-2 text-gray-600 hover:text-blue-600"
                        title="Export template"
                      >
                        ⬇️
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm text-gray-600 border-t border-gray-100 pt-4">
                    <div className="flex items-center gap-6">
                      <span>
                        <strong>{template.usage_count}</strong> uses
                      </span>
                      <span>
                        Saved: <strong className="text-green-600">${template.cost_saved.toFixed(2)}</strong>
                      </span>
                      <span>
                        Source: <strong>{template.source_llm}</strong>
                      </span>
                    </div>
                    <span>
                      Last used: {new Date(template.last_used).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="bg-white rounded-lg shadow px-6 py-4 border-t border-gray-200">
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
          </>
        )}
      </div>

      {/* Template Detail Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {selectedTemplate.name}
                  </h2>
                  <p className="text-gray-600">{selectedTemplate.task_pattern}</p>
                </div>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-6">
                {/* Stats */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Quality</p>
                    <p className="text-2xl font-bold text-gray-900">{selectedTemplate.quality_score}%</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Uses</p>
                    <p className="text-2xl font-bold text-gray-900">{selectedTemplate.usage_count}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Saved</p>
                    <p className="text-2xl font-bold text-green-600">${selectedTemplate.cost_saved.toFixed(2)}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Source</p>
                    <p className="text-lg font-semibold text-gray-900 capitalize">{selectedTemplate.source_llm}</p>
                  </div>
                </div>

                {/* Tech Stack */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Technologies</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedTemplate.tech_stack.map((tech) => (
                      <span
                        key={tech}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Parameters */}
                {selectedTemplate.parameters.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Template Parameters</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedTemplate.parameters.map((param) => (
                        <code
                          key={param}
                          className="px-3 py-1 bg-gray-100 text-gray-800 rounded text-sm font-mono"
                        >
                          {`{{${param}}}`}
                        </code>
                      ))}
                    </div>
                  </div>
                )}

                {/* Template Content */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Template Content</h3>
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                    {selectedTemplate.template_content}
                  </pre>
                </div>

                {/* Metadata */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">Metadata</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Template ID</p>
                      <p className="font-mono text-gray-900">{selectedTemplate.template_id}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Created</p>
                      <p className="text-gray-900">{new Date(selectedTemplate.created_at).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Last Used</p>
                      <p className="text-gray-900">{new Date(selectedTemplate.last_used).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Usage Count</p>
                      <p className="text-gray-900">{selectedTemplate.usage_count} times</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-between">
              <button
                onClick={() => deleteTemplate(selectedTemplate.template_id)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Delete Template
              </button>
              <div className="flex gap-3">
                <button
                  onClick={() => exportTemplate(selectedTemplate)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Export
                </button>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      <Footer />
    </div>
  );
}

