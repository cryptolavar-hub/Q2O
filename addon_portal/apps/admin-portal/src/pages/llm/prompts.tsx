/**
 * Advanced Prompt Management
 * System, Project, and Agent-level prompt editors
 * Fully integrated with database-backed API
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { AdminHeader } from '@/components/AdminHeader';
import { Navigation } from '@/components/Navigation';
import { Breadcrumb } from '@/components/Breadcrumb';
import { Footer } from '@/components/Footer';
import { Card, Button } from '@/design-system';

// Use relative URLs to leverage Next.js proxy (avoids IPv6 issues)
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface SystemConfig {
  primaryProvider: string;
  secondaryProvider: string;
  tertiaryProvider: string;
  systemPrompt: string;
  geminiModel: string;
  openaiModel: string;
  anthropicModel: string;
  temperature: number;
  maxTokens: number;
  monthlyBudget: number;
  dailyBudget: number;
}

interface AgentPrompt {
  agentType: string;
  customPrompt?: string;
  customInstructions?: string;
  enabled: boolean;
  providerOverride?: string;
  modelOverride?: string;
  temperatureOverride?: number;
  maxTokensOverride?: number;
}

interface ProjectConfig {
  projectId: string;
  clientName: string;
  description?: string;
  customInstructions?: string;
  isActive: boolean;
  priority: string;
  agentPrompts: AgentPrompt[];
}

export default function PromptManagement() {
  const router = useRouter();
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [projects, setProjects] = useState<ProjectConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'system' | 'agent' | 'project'>('system');
  const [editingProject, setEditingProject] = useState<string | null>(null);
  const [editingAgent, setEditingAgent] = useState<{ projectId: string; agentType: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination and search state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [totalProjects, setTotalProjects] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Agent Prompts tab search and pagination state
  const [agentSearchQuery, setAgentSearchQuery] = useState('');
  const [agentProjectSearch, setAgentProjectSearch] = useState('');
  const [agentCurrentPage, setAgentCurrentPage] = useState(1);
  const [agentPageSize] = useState(25);
  const [allProjects, setAllProjects] = useState<ProjectConfig[]>([]); // Store all projects for Agent Prompts tab

  const agentTypes = [
    { id: 'coder', name: 'CoderAgent', description: 'Backend services and APIs' },
    { id: 'researcher', name: 'ResearcherAgent', description: 'Web research synthesis' },
    { id: 'orchestrator', name: 'OrchestratorAgent', description: 'Task breakdown' },
    { id: 'mobile', name: 'MobileAgent', description: 'React Native apps' },
    { id: 'frontend', name: 'FrontendAgent', description: 'React/Next.js UI' },
    { id: 'integration', name: 'IntegrationAgent', description: 'API integrations' },
  ];

  useEffect(() => {
    fetchSystemConfig();
  }, []);

  useEffect(() => {
    if (activeTab === 'project') {
      fetchProjects();
    } else if (activeTab === 'agent') {
      fetchAllProjectsForAgentTab();
    }
  }, [activeTab, currentPage, pageSize, searchQuery]);

  // Also fetch projects when switching to agent tab if allProjects is empty
  useEffect(() => {
    if (activeTab === 'agent' && allProjects.length === 0 && !loading) {
      fetchAllProjectsForAgentTab();
    }
  }, [activeTab]);

  const fetchSystemConfig = async () => {
    try {
      setError(null);
      
      // Fetch system configuration
      const systemRes = await fetch(`${API_BASE}/api/llm/system`);
      if (systemRes.ok) {
        const systemData = await systemRes.json();
        setSystemConfig(systemData);
      } else {
        console.warn('Failed to fetch system config:', systemRes.status);
        // Set default system config if endpoint fails
        setSystemConfig({
          primaryProvider: 'gemini',
          secondaryProvider: 'openai',
          tertiaryProvider: 'anthropic',
          systemPrompt: 'You are a helpful AI assistant specialized in software development.',
          geminiModel: 'gemini-1.5-pro',
          openaiModel: 'gpt-4-turbo',
          anthropicModel: 'claude-3-opus',
          temperature: 0.7,
          maxTokens: 4096,
          monthlyBudget: 1000,
          dailyBudget: 50,
        });
      }
    } catch (error) {
      console.error('Failed to fetch system config:', error);
      setSystemConfig({
        primaryProvider: 'gemini',
        secondaryProvider: 'openai',
        tertiaryProvider: 'anthropic',
        systemPrompt: 'You are a helpful AI assistant specialized in software development.',
        geminiModel: 'gemini-1.5-pro',
        openaiModel: 'gpt-4-turbo',
        anthropicModel: 'claude-3-opus',
        temperature: 0.7,
        maxTokens: 4096,
        monthlyBudget: 1000,
        dailyBudget: 50,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
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
        console.warn('Failed to fetch projects:', projectsRes.status);
        setProjects([]);
        setTotalProjects(0);
        setTotalPages(1);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      setError('Failed to load projects. Please check your connection and try again.');
      setProjects([]);
      setTotalProjects(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Fetch all projects for Agent Prompts tab (for client-side filtering and pagination)
  const fetchAllProjectsForAgentTab = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all projects - API limits page_size to 100 (le=100)
      // We'll fetch multiple pages if needed to get all projects
      let allFetchedProjects: ProjectConfig[] = [];
      let currentPage = 1;
      const pageSize = 100; // API maximum
      let hasMore = true;

      while (hasMore) {
        const params = new URLSearchParams({
          page: currentPage.toString(),
          page_size: pageSize.toString(),
        });

        const projectsRes = await fetch(`${API_BASE}/api/llm/projects?${params.toString()}`);
        if (projectsRes.ok) {
          const projectsData = await projectsRes.json();
          const fetchedProjects = projectsData.items || [];
          allFetchedProjects = [...allFetchedProjects, ...fetchedProjects];
          
          // Check if there are more pages
          const totalPages = Math.ceil((projectsData.total || 0) / pageSize);
          hasMore = currentPage < totalPages;
          currentPage++;
        } else {
          hasMore = false;
          const errorText = await projectsRes.text();
          console.error(`Failed to fetch projects for agent tab (${projectsRes.status}):`, errorText);
          setError(`Failed to load projects (${projectsRes.status}). Please check your connection and try again.`);
          setAllProjects([]);
          return;
        }
      }

      console.log(`[Agent Prompts] Fetched ${allFetchedProjects.length} projects`);
      setAllProjects(allFetchedProjects);
      
      // If no projects found, log for debugging
      if (allFetchedProjects.length === 0) {
        console.warn('[Agent Prompts] No projects found in API response');
      }
    } catch (error) {
      console.error('Failed to fetch projects for agent tab:', error);
      setError('Failed to load projects. Please check your connection and try again.');
      setAllProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const saveSystemPrompt = async () => {
    if (!systemConfig) return;

    try {
      const response = await fetch(`${API_BASE}/api/llm/system`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          primaryProvider: systemConfig.primaryProvider,
          secondaryProvider: systemConfig.secondaryProvider,
          tertiaryProvider: systemConfig.tertiaryProvider,
          geminiModel: systemConfig.geminiModel,
          openaiModel: systemConfig.openaiModel,
          anthropicModel: systemConfig.anthropicModel,
          temperature: systemConfig.temperature,
          maxTokens: systemConfig.maxTokens,
          retriesPerProvider: 3,
          monthlyBudget: systemConfig.monthlyBudget,
          dailyBudget: systemConfig.dailyBudget,
          templateLearningEnabled: true,
          crossValidationEnabled: true,
          cacheEnabled: true,
          minQualityScore: 70,
          templateMinQuality: 75,
          systemPrompt: systemConfig.systemPrompt,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert('✅ System prompt saved successfully! Restart services for changes to take effect.');
        await fetchSystemConfig();
      } else {
        let errorMessage = `Failed to save (${response.status}): ${response.statusText}`;
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
          // Response is not JSON
        }
        alert(`❌ ${errorMessage}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('System prompt save error:', error);
      alert(`❌ Error saving system prompt: ${errorMessage}`);
    }
  };

  const saveProjectPrompt = async (projectId: string) => {
    const project = projects.find(p => p.projectId === projectId);
    if (!project) return;

    try {
      const response = await fetch(`${API_BASE}/api/llm/projects/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clientName: project.clientName,
          description: project.description,
          customInstructions: project.customInstructions,
          isActive: project.isActive,
          priority: project.priority,
        }),
      });

      if (response.ok) {
        alert(`✅ Project prompt saved for ${project.clientName}!`);
        setEditingProject(null);
        await fetchProjects();
      } else {
        const error = await response.json();
        alert(`❌ Failed to save: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert('❌ Error saving project prompt');
    }
  };

  const saveAgentPrompt = async (projectId: string, agentType: string) => {
    const project = projects.find(p => p.projectId === projectId);
    if (!project) return;

    const agentPrompt = project.agentPrompts.find(ap => ap.agentType === agentType) || {
      agentType,
      enabled: false,
    };

    try {
      const response = await fetch(`${API_BASE}/api/llm/projects/${projectId}/agents/${agentType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customPrompt: agentPrompt.customPrompt || undefined,
          customInstructions: agentPrompt.customInstructions || undefined,
          enabled: agentPrompt.enabled,
          providerOverride: agentPrompt.providerOverride || undefined,
          modelOverride: agentPrompt.modelOverride || undefined,
          temperatureOverride: agentPrompt.temperatureOverride || undefined,
          maxTokensOverride: agentPrompt.maxTokensOverride || undefined,
        }),
      });

      if (response.ok) {
        alert(`✅ ${agentType} prompt saved for ${project.clientName}!`);
        setEditingAgent(null);
        await fetchProjects();
      } else {
        const error = await response.json();
        alert(`❌ Failed to save: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert('❌ Error saving agent prompt');
    }
  };


  const updateProjectField = (projectId: string, field: keyof ProjectConfig, value: any) => {
    setProjects(prev => prev.map(p => 
      p.projectId === projectId ? { ...p, [field]: value } : p
    ));
  };

  const updateAgentPromptField = (
    projectId: string,
    agentType: string,
    field: keyof AgentPrompt,
    value: any
  ) => {
    const updateProject = (project: ProjectConfig) => {
      if (project.projectId !== projectId) return project;
      
      const existingAgent = project.agentPrompts.find(ap => ap.agentType === agentType);
      const updatedAgent: AgentPrompt = existingAgent 
        ? { ...existingAgent, [field]: value }
        : { agentType, enabled: false, [field]: value };

      return {
        ...project,
        agentPrompts: [
          ...project.agentPrompts.filter(ap => ap.agentType !== agentType),
          updatedAgent,
        ],
      };
    };

    setProjects(prev => prev.map(updateProject));
    setAllProjects(prev => prev.map(updateProject));
  };

  const fetchAllData = async () => {
    await fetchSystemConfig();
    if (activeTab === 'project') {
      await fetchProjects();
    } else if (activeTab === 'agent') {
      await fetchAllProjectsForAgentTab();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="Prompt Management" />
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!systemConfig) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="Prompt Management" />
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <p className="text-red-600 mb-4">Failed to load configuration</p>
            <Button onClick={fetchAllData}>Retry</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="Agent Prompts Management" subtitle="Assign and manage agent-specific prompts for projects" />
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: 'LLM Management', href: '/llm' }, { label: 'Prompts' }]} />

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <p className="text-red-800">{error}</p>
              <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800">×</button>
            </div>
          </div>
        )}

        <button
          onClick={() => router.push('/llm')}
          className="mb-6 text-blue-600 hover:text-blue-700 flex items-center gap-2"
        >
          ← Back to Overview
        </button>

        {/* Info Banner */}
        <Card className="mb-6 bg-blue-50 border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-2">🎯 Agent Prompts for Projects</h4>
          <div className="text-sm text-blue-800 space-y-1">
            <p><strong>Note:</strong> Projects are created and managed by tenants via the Tenant Dashboard.</p>
            <p><strong>This page</strong> allows you to assign and customize agent-specific prompts for existing projects.</p>
            <p className="pt-2"><strong>Agent Prompts</strong> override project-level prompts, which override system prompts.</p>
          </div>
        </Card>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('system')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'system'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              System Prompt
            </button>
            <button
              onClick={() => setActiveTab('project')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'project'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Project Prompts ({totalProjects})
            </button>
            <button
              onClick={() => setActiveTab('agent')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'agent'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Agent Prompts
            </button>
          </nav>
        </div>

        {/* System Prompt Tab */}
        {activeTab === 'system' && (
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">System Prompt</h3>
                <p className="text-sm text-gray-600">Applies to all agents and projects (baseline behavior)</p>
              </div>
            </div>

            <textarea
              value={systemConfig.systemPrompt || ''}
              onChange={(e) => setSystemConfig({ ...systemConfig, systemPrompt: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm whitespace-pre-wrap"
              rows={15}
              placeholder="Enter system-level prompt that applies to all agents..."
              style={{ minHeight: '300px' }}
            />

            <div className="mt-4 flex justify-end">
              <Button onClick={saveSystemPrompt} variant="primary">
                Save System Prompt
              </Button>
            </div>
          </Card>
        )}

        {/* Project Prompts Tab */}
        {activeTab === 'project' && (
          <div className="space-y-4">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Agent Prompts Assigned to Projects</h3>
                  <p className="text-sm text-gray-600">
                    Manage agent-specific prompts for existing projects. Projects are created by tenants.
                  </p>
                </div>
              </div>

              {/* Note: Projects are managed by tenants. This page focuses on Agent Prompts. */}
              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> Projects are created and managed by tenants via the Tenant Dashboard. 
                  This page is for assigning and managing <strong>Agent Prompts</strong> to existing projects.
                </p>
              </div>

              {/* Search */}
              <div className="mb-4">
                <input
                  type="text"
                  placeholder="Search projects by name, ID, or description..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1); // Reset to first page when searching
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </Card>

            {projects.length === 0 ? (
              <Card className="text-center p-12">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Project Prompts</h3>
                <p className="text-gray-600 mb-6">
                  Create project-specific prompts to customize LLM behavior for individual clients.
                </p>
                <Button onClick={() => setActiveTab('project')} variant="primary">
                  Add Your First Project Prompt
                </Button>
              </Card>
            ) : (
              <>
                {projects.map((project) => {
                const isEditing = editingProject === project.projectId;

                return (
                  <Card key={project.projectId}>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="text-lg font-semibold text-gray-900">{project.clientName}</h4>
                          <code className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-mono">
                            {project.projectId}
                          </code>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            project.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {project.isActive ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                      
                      <Button
                        onClick={() => setEditingProject(isEditing ? null : project.projectId)}
                        variant="secondary"
                        size="sm"
                      >
                        {isEditing ? 'Cancel' : 'Edit'}
                      </Button>
                    </div>

                    {isEditing ? (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Project Name
                          </label>
                          <input
                            type="text"
                            value={project.clientName}
                            onChange={(e) => updateProjectField(project.projectId, 'clientName', e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                            disabled
                            title="Project name is managed by the tenant"
                          />
                          <p className="text-xs text-gray-500 mt-1">Project name is managed by the tenant</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Description
                          </label>
                          <input
                            type="text"
                            value={project.description || ''}
                            onChange={(e) => updateProjectField(project.projectId, 'description', e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Custom Instructions
                          </label>
                          <textarea
                            value={project.customInstructions || ''}
                            onChange={(e) => updateProjectField(project.projectId, 'customInstructions', e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm"
                            rows={8}
                            placeholder={`Custom requirements for ${project.clientName}...`}
                          />
                        </div>

                        <div className="flex justify-end gap-3">
                          <Button
                            onClick={() => setEditingProject(null)}
                            variant="secondary"
                          >
                            Cancel
                          </Button>
                          <Button
                            onClick={() => saveProjectPrompt(project.projectId)}
                            variant="primary"
                          >
                            Save Project Prompt
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {project.customInstructions || <em className="text-gray-400">No custom instructions set</em>}
                        </p>
                      </div>
                    )}
                  </Card>
                );
              })}

                {/* Pagination Controls - Show if more than 10 items */}
                {totalProjects > 10 && (
                  <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 rounded-lg">
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
        )}

        {/* Agent Prompts Tab */}
        {activeTab === 'agent' && (
          <div className="space-y-6">
            {/* Search Controls */}
            <Card>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Projects
                  </label>
                  <input
                    type="text"
                    placeholder="Search projects by name, ID, or description..."
                    value={agentProjectSearch}
                    onChange={(e) => {
                      setAgentProjectSearch(e.target.value);
                      setAgentCurrentPage(1); // Reset to first page when search changes
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Agents
                  </label>
                  <input
                    type="text"
                    placeholder="Search agents by type (e.g., coder, researcher, orchestrator)..."
                    value={agentSearchQuery}
                    onChange={(e) => setAgentSearchQuery(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </Card>

            {loading && allProjects.length === 0 ? (
              <Card className="text-center p-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                <p className="text-gray-600 mt-4">Loading projects...</p>
              </Card>
            ) : allProjects.length === 0 ? (
              <Card className="text-center p-12">
                <p className="text-gray-600">Create a project first to configure agent prompts.</p>
              </Card>
            ) : (
              <>
                {(() => {
                  // Filter projects based on search
                  const filteredProjects = allProjects.filter((project) => {
                    if (agentProjectSearch.trim()) {
                      const searchLower = agentProjectSearch.toLowerCase();
                      return (
                        project.clientName.toLowerCase().includes(searchLower) ||
                        project.projectId.toLowerCase().includes(searchLower) ||
                        (project.description || '').toLowerCase().includes(searchLower)
                      );
                    }
                    return true;
                  });

                  // Calculate pagination for filtered results
                  const agentTotalProjects = filteredProjects.length;
                  const agentTotalPages = Math.ceil(agentTotalProjects / agentPageSize);
                  
                  // Slice to get current page
                  const startIndex = (agentCurrentPage - 1) * agentPageSize;
                  const endIndex = startIndex + agentPageSize;
                  const paginatedProjects = filteredProjects.slice(startIndex, endIndex);

                  return (
                    <>
                      {paginatedProjects.map((project) => (
                <Card key={project.projectId}>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    {project.clientName} ({project.projectId})
                  </h4>
                  
                  <div className="space-y-4">
                    {agentTypes
                      .filter((agent) => {
                        if (agentSearchQuery.trim()) {
                          const searchLower = agentSearchQuery.toLowerCase();
                          return (
                            agent.name.toLowerCase().includes(searchLower) ||
                            agent.id.toLowerCase().includes(searchLower) ||
                            agent.description.toLowerCase().includes(searchLower)
                          );
                        }
                        return true;
                      })
                      .map((agent) => {
                        const agentPrompt = project.agentPrompts.find(ap => ap.agentType === agent.id) || {
                          agentType: agent.id,
                          enabled: false,
                        };
                        const isEditing = editingAgent?.projectId === project.projectId && editingAgent?.agentType === agent.id;

                        return (
                        <div key={agent.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h5 className="font-semibold text-gray-900">{agent.name}</h5>
                              <p className="text-sm text-gray-600">{agent.description}</p>
                            </div>
                            <Button
                              onClick={() => setEditingAgent(isEditing ? null : { projectId: project.projectId, agentType: agent.id })}
                              variant="secondary"
                              size="sm"
                            >
                              {isEditing ? 'Cancel' : 'Edit'}
                            </Button>
                          </div>

                          {isEditing ? (
                            <div className="space-y-3">
                              <label className="flex items-center gap-2">
                                <input
                                  type="checkbox"
                                  checked={agentPrompt.enabled}
                                  onChange={(e) => updateAgentPromptField(project.projectId, agent.id, 'enabled', e.target.checked)}
                                  className="rounded border-gray-300"
                                />
                                <span className="text-sm font-medium text-gray-700">
                                  Enable custom prompt for {agent.name}
                                </span>
                              </label>

                              <textarea
                                value={agentPrompt.customPrompt || ''}
                                onChange={(e) => updateAgentPromptField(project.projectId, agent.id, 'customPrompt', e.target.value)}
                                disabled={!agentPrompt.enabled}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm disabled:bg-gray-50"
                                rows={6}
                                placeholder={`Custom prompt for ${agent.name}...`}
                              />

                              <div className="flex justify-end gap-3">
                                <Button
                                  onClick={() => setEditingAgent(null)}
                                  variant="secondary"
                                  size="sm"
                                >
                                  Cancel
                                </Button>
                                <Button
                                  onClick={() => saveAgentPrompt(project.projectId, agent.id)}
                                  variant="primary"
                                  size="sm"
                                >
                                  Save
                                </Button>
                              </div>
                            </div>
                          ) : (
                            agentPrompt.enabled && agentPrompt.customPrompt && (
                              <div className="p-3 bg-gray-50 rounded text-sm text-gray-700">
                                {agentPrompt.customPrompt.substring(0, 150)}
                                {agentPrompt.customPrompt.length > 150 && '...'}
                              </div>
                            )
                          )}
                        </div>
                      );
                    })}
                  </div>
                </Card>
                      ))}
                    </>
                  );
                })()}

                {/* Pagination Controls for Agent Prompts Tab */}
                {(() => {
                  const filteredProjects = allProjects.filter((project) => {
                    if (agentProjectSearch.trim()) {
                      const searchLower = agentProjectSearch.toLowerCase();
                      return (
                        project.clientName.toLowerCase().includes(searchLower) ||
                        project.projectId.toLowerCase().includes(searchLower) ||
                        (project.description || '').toLowerCase().includes(searchLower)
                      );
                    }
                    return true;
                  });
                  const agentTotalProjects = filteredProjects.length;
                  const agentTotalPages = Math.ceil(agentTotalProjects / agentPageSize);

                  const handleAgentPageChange = (page: number) => {
                    if (page >= 1 && page <= agentTotalPages) {
                      setAgentCurrentPage(page);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                  };

                  // Show pagination if more than 10 items
                  if (agentTotalProjects <= 10) return null;

                  return (
                    <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {/* First Page Button */}
                          <button
                            onClick={() => handleAgentPageChange(1)}
                            disabled={agentCurrentPage === 1}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                              agentCurrentPage === 1
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                            }`}
                            title="First page"
                          >
                            |&lt;&lt;
                          </button>
                          
                          {/* Previous Page Button */}
                          <button
                            onClick={() => handleAgentPageChange(agentCurrentPage - 1)}
                            disabled={agentCurrentPage === 1}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                              agentCurrentPage === 1
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                            }`}
                            title="Previous page"
                          >
                            |&lt;
                          </button>
                          
                          {/* Page Number Buttons */}
                          <div className="flex items-center gap-1">
                            {Array.from({ length: Math.min(5, agentTotalPages) }, (_, i) => {
                              let pageNum: number;
                              if (agentTotalPages <= 5) {
                                pageNum = i + 1;
                              } else if (agentCurrentPage <= 3) {
                                pageNum = i + 1;
                              } else if (agentCurrentPage >= agentTotalPages - 2) {
                                pageNum = agentTotalPages - 4 + i;
                              } else {
                                pageNum = agentCurrentPage - 2 + i;
                              }
                              
                              return (
                                <button
                                  key={pageNum}
                                  onClick={() => handleAgentPageChange(pageNum)}
                                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                    agentCurrentPage === pageNum
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
                            onClick={() => handleAgentPageChange(agentCurrentPage + 1)}
                            disabled={agentCurrentPage === agentTotalPages}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                              agentCurrentPage === agentTotalPages
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                            }`}
                            title="Next page"
                          >
                            &gt;|
                          </button>
                          
                          {/* Last Page Button */}
                          <button
                            onClick={() => handleAgentPageChange(agentTotalPages)}
                            disabled={agentCurrentPage === agentTotalPages}
                            className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                              agentCurrentPage === agentTotalPages
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                            }`}
                            title="Last page"
                          >
                            &gt;&gt;|
                          </button>
                        </div>
                        
                        <div className="text-sm text-gray-600">
                          Page {agentCurrentPage} of {agentTotalPages} ({agentTotalProjects} total)
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </>
            )}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
