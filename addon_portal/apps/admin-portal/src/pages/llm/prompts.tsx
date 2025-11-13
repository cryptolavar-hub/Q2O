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

  const agentTypes = [
    { id: 'coder', name: 'CoderAgent', description: 'Backend services and APIs' },
    { id: 'researcher', name: 'ResearcherAgent', description: 'Web research synthesis' },
    { id: 'orchestrator', name: 'OrchestratorAgent', description: 'Task breakdown' },
    { id: 'mobile', name: 'MobileAgent', description: 'React Native apps' },
    { id: 'frontend', name: 'FrontendAgent', description: 'React/Next.js UI' },
    { id: 'integration', name: 'IntegrationAgent', description: 'API integrations' },
  ];

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
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

      // Fetch projects
      const projectsRes = await fetch(`${API_BASE}/api/llm/projects?page_size=100`);
      if (projectsRes.ok) {
        const projectsData = await projectsRes.json();
        setProjects(projectsData.items || []);
      } else {
        console.warn('Failed to fetch projects:', projectsRes.status);
        setProjects([]);
      }
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
      setError('Failed to load configuration. Please check your connection and try again.');
      // Set defaults to allow page to render
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
      setProjects([]);
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
        await fetchAllData();
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
        await fetchAllData();
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
        await fetchAllData();
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
    setProjects(prev => prev.map(project => {
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
    }));
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
              Project Prompts ({projects.length})
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
              projects.map((project) => {
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
              })
            )}
          </div>
        )}

        {/* Agent Prompts Tab */}
        {activeTab === 'agent' && (
          <div className="space-y-6">
            {projects.length === 0 ? (
              <Card className="text-center p-12">
                <p className="text-gray-600">Create a project first to configure agent prompts.</p>
              </Card>
            ) : (
              projects.map((project) => (
                <Card key={project.projectId}>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    {project.clientName} ({project.projectId})
                  </h4>
                  
                  <div className="space-y-4">
                    {agentTypes.map((agent) => {
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
              ))
            )}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
