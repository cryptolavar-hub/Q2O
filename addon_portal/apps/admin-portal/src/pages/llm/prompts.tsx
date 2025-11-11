/**
 * Advanced Prompt Management
 * System, Project, and Agent-level prompt editors
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { AdminHeader } from '@/components/AdminHeader';
import { Navigation } from '@/components/Navigation';
import { Breadcrumb } from '@/components/Breadcrumb';

interface PromptConfig {
  system: {
    prompt: string;
    source: 'env' | 'config' | 'default';
  };
  agents: Record<string, {
    prompt: string;
    source: 'env' | 'config' | 'default';
    enabled: boolean;
  }>;
  projects: Record<string, {
    projectId: string;
    clientName: string;
    prompt: string;
    source: 'env' | 'config';
    enabled: boolean;
  }>;
}

export default function PromptManagement() {
  const router = useRouter();
  const [prompts, setPrompts] = useState<PromptConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'system' | 'agent' | 'project'>('system');
  const [editingAgent, setEditingAgent] = useState<string | null>(null);
  const [editingProject, setEditingProject] = useState<string | null>(null);

  const agentTypes = [
    { id: 'coder', name: 'CoderAgent', description: 'Backend services and APIs' },
    { id: 'researcher', name: 'ResearcherAgent', description: 'Web research synthesis' },
    { id: 'orchestrator', name: 'OrchestratorAgent', description: 'Task breakdown' },
    { id: 'mobile', name: 'MobileAgent', description: 'React Native apps' },
    { id: 'frontend', name: 'FrontendAgent', description: 'React/Next.js UI' },
    { id: 'integration', name: 'IntegrationAgent', description: 'API integrations' },
  ];

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      const response = await fetch('/api/llm/prompts');
      if (response.ok) {
        const data = await response.json();
        setPrompts(data);
      }
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSystemPrompt = async (prompt: string) => {
    try {
      const response = await fetch('/api/llm/prompts/system', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      if (response.ok) {
        alert('✅ System prompt saved! Restart services for changes to take effect.');
        fetchPrompts();
      } else {
        alert('❌ Failed to save system prompt');
      }
    } catch (error) {
      alert('❌ Error saving system prompt');
    }
  };

  const saveAgentPrompt = async (agentType: string, prompt: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/llm/prompts/agent/${agentType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, enabled }),
      });

      if (response.ok) {
        alert(`✅ ${agentType} prompt saved!`);
        setEditingAgent(null);
        fetchPrompts();
      } else {
        alert('❌ Failed to save agent prompt');
      }
    } catch (error) {
      alert('❌ Error saving agent prompt');
    }
  };

  const saveProjectPrompt = async (projectId: string, clientName: string, prompt: string) => {
    try {
      const response = await fetch(`/api/llm/prompts/project/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientName, prompt }),
      });

      if (response.ok) {
        alert(`✅ Project prompt saved for ${clientName}!`);
        setEditingProject(null);
        fetchPrompts();
      } else {
        alert('❌ Failed to save project prompt');
      }
    } catch (error) {
      alert('❌ Error saving project prompt');
    }
  };

  const addNewProject = () => {
    const projectId = prompt('Enter Project ID (e.g., acme_001):');
    if (!projectId) return;

    const clientName = prompt('Enter Client Name (e.g., ACME Corp):');
    if (!clientName) return;

    setEditingProject(projectId);
    setPrompts({
      ...prompts!,
      projects: {
        ...prompts!.projects,
        [projectId]: {
          projectId,
          clientName,
          prompt: '',
          source: 'config',
          enabled: true
        }
      }
    });
  };

  if (loading || !prompts) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="Prompt Management" />
        <div className="flex items-center justify-center h-96">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="Advanced Prompt Management" subtitle="Customize system, agent, and project prompts" />
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: 'LLM Management', href: '/llm' }, { label: 'Prompts' }]} />

        <button
          onClick={() => router.push('/llm')}
          className="mb-6 text-blue-600 hover:text-blue-700 flex items-center gap-2"
        >
          ← Back to Overview
        </button>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h4 className="font-semibold text-blue-900 mb-2">🎯 3-Level Prompt Cascade</h4>
          <div className="text-sm text-blue-800 space-y-1">
            <p><strong>System Prompt</strong> → All agents, all projects (baseline)</p>
            <p><strong>Agent Prompts</strong> → Specific agent type (CoderAgent, MobileAgent, etc.)</p>
            <p><strong>Project Prompts</strong> → Specific client project (ACME Corp, etc.)</p>
            <p className="pt-2"><strong>Priority</strong>: Agent-specific overrides system, Project additions append to both</p>
          </div>
        </div>

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
              onClick={() => setActiveTab('agent')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'agent'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Agent Prompts ({agentTypes.length})
            </button>
            <button
              onClick={() => setActiveTab('project')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'project'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Project Prompts ({Object.keys(prompts.projects).length})
            </button>
          </nav>
        </div>

        {/* System Prompt Tab */}
        {activeTab === 'system' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">System Prompt</h3>
                  <p className="text-sm text-gray-600">Applies to all agents and projects (baseline behavior)</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  prompts.system.source === 'env' ? 'bg-green-100 text-green-800' :
                  prompts.system.source === 'config' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {prompts.system.source === 'env' ? 'From .env' : 
                   prompts.system.source === 'config' ? 'Custom' : 'Default'}
                </span>
              </div>

              <textarea
                value={prompts.system.prompt}
                onChange={(e) => setPrompts({
                  ...prompts,
                  system: { ...prompts.system, prompt: e.target.value, source: 'config' }
                })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={12}
                placeholder="Enter system-level prompt that applies to all agents..."
              />

              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  {prompts.system.source === 'env' && (
                    <p>⚠️ This prompt is defined in .env file (Q2O_LLM_SYSTEM_PROMPT). Changes here will override it.</p>
                  )}
                </div>
                <button
                  onClick={() => saveSystemPrompt(prompts.system.prompt)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Save System Prompt
                </button>
              </div>
            </div>

            {/* Quick Templates */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Prompt Templates</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setPrompts({
                    ...prompts,
                    system: {
                      ...prompts.system,
                      prompt: "You are an expert software architect. Generate production-ready, well-documented code following industry best practices. Focus on code quality, maintainability, security, and performance.",
                      source: 'config'
                    }
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left"
                >
                  <p className="font-semibold mb-1">Production Quality</p>
                  <p className="text-sm text-gray-600">Enterprise-grade code</p>
                </button>

                <button
                  onClick={() => setPrompts({
                    ...prompts,
                    system: {
                      ...prompts.system,
                      prompt: "You are a security-focused developer. Generate code with security as top priority. Include input validation, error handling, SQL injection prevention, XSS protection, and security logging.",
                      source: 'config'
                    }
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left"
                >
                  <p className="font-semibold mb-1">Security First</p>
                  <p className="text-sm text-gray-600">Maximum security focus</p>
                </button>

                <button
                  onClick={() => setPrompts({
                    ...prompts,
                    system: {
                      ...prompts.system,
                      prompt: "You are a rapid prototyping assistant. Generate working code quickly. Prioritize functionality over perfection. Code should be clear, functional, and easy to iterate on.",
                      source: 'config'
                    }
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left"
                >
                  <p className="font-semibold mb-1">Rapid Prototyping</p>
                  <p className="text-sm text-gray-600">Fast, functional code</p>
                </button>

                <button
                  onClick={() => setPrompts({
                    ...prompts,
                    system: {
                      ...prompts.system,
                      prompt: "You are an educational coding assistant. Generate well-commented code with clear explanations. Focus on teaching best practices and explaining reasoning behind decisions. Include inline comments.",
                      source: 'config'
                    }
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left"
                >
                  <p className="font-semibold mb-1">Educational</p>
                  <p className="text-sm text-gray-600">Teaching-focused code</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Agent Prompts Tab */}
        {activeTab === 'agent' && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-6 mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Agent-Specific Prompts</h3>
              <p className="text-sm text-gray-600">
                Customize prompts for each agent type. Agent prompts override the system prompt.
              </p>
            </div>

            {agentTypes.map((agent) => {
              const agentConfig = prompts.agents[agent.id] || {
                prompt: '',
                source: 'default',
                enabled: false
              };
              const isEditing = editingAgent === agent.id;

              return (
                <div key={agent.id} className="bg-white rounded-lg shadow">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="text-lg font-semibold text-gray-900">{agent.name}</h4>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            agentConfig.source === 'env' ? 'bg-green-100 text-green-800' :
                            agentConfig.enabled ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {agentConfig.source === 'env' ? '.env' : agentConfig.enabled ? 'Custom' : 'Using System'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{agent.description}</p>
                      </div>
                      
                      <button
                        onClick={() => setEditingAgent(isEditing ? null : agent.id)}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        {isEditing ? 'Cancel' : 'Edit Prompt'}
                      </button>
                    </div>

                    {isEditing && (
                      <div className="mt-4 space-y-4">
                        <div>
                          <label className="flex items-center gap-2 mb-3">
                            <input
                              type="checkbox"
                              checked={agentConfig.enabled}
                              onChange={(e) => {
                                const newPrompts = { ...prompts };
                                newPrompts.agents[agent.id] = {
                                  ...agentConfig,
                                  enabled: e.target.checked
                                };
                                setPrompts(newPrompts);
                              }}
                              className="rounded border-gray-300"
                            />
                            <span className="text-sm font-medium text-gray-700">
                              Enable custom prompt for {agent.name}
                            </span>
                          </label>

                          <textarea
                            value={agentConfig.prompt}
                            onChange={(e) => {
                              const newPrompts = { ...prompts };
                              newPrompts.agents[agent.id] = {
                                ...agentConfig,
                                prompt: e.target.value,
                                source: 'config'
                              };
                              setPrompts(newPrompts);
                            }}
                            disabled={!agentConfig.enabled}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-50"
                            rows={8}
                            placeholder={`Custom prompt for ${agent.name}...`}
                          />
                        </div>

                        <div className="flex justify-end gap-3">
                          <button
                            onClick={() => setEditingAgent(null)}
                            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={() => saveAgentPrompt(agent.id, agentConfig.prompt, agentConfig.enabled)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                          >
                            Save {agent.name} Prompt
                          </button>
                        </div>

                        {agentConfig.source === 'env' && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
                            ⚠️ This agent has a prompt defined in .env (Q2O_LLM_PROMPT_{agent.id.toUpperCase()}). 
                            Changes here will override it in the database.
                          </div>
                        )}
                      </div>
                    )}

                    {!isEditing && agentConfig.enabled && agentConfig.prompt && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {agentConfig.prompt.substring(0, 200)}
                          {agentConfig.prompt.length > 200 && '...'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Project Prompts Tab */}
        {activeTab === 'project' && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Project-Specific Prompts</h3>
                  <p className="text-sm text-gray-600">
                    Customize prompts for individual client projects. Useful for client-specific standards, naming conventions, or requirements.
                  </p>
                </div>
                <button
                  onClick={addNewProject}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  + Add Project
                </button>
              </div>
            </div>

            {Object.keys(prompts.projects).length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Project Prompts</h3>
                <p className="text-gray-600 mb-6">
                  Create project-specific prompts to customize LLM behavior for individual clients.
                </p>
                <button
                  onClick={addNewProject}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Your First Project Prompt
                </button>
              </div>
            ) : (
              Object.entries(prompts.projects).map(([projectId, projectConfig]) => {
                const isEditing = editingProject === projectId;

                return (
                  <div key={projectId} className="bg-white rounded-lg shadow">
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="text-lg font-semibold text-gray-900">{projectConfig.clientName}</h4>
                            <code className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-mono">
                              {projectId}
                            </code>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              projectConfig.source === 'env' ? 'bg-green-100 text-green-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {projectConfig.source === 'env' ? '.env' : 'Custom'}
                            </span>
                          </div>
                        </div>
                        
                        <button
                          onClick={() => setEditingProject(isEditing ? null : projectId)}
                          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                          {isEditing ? 'Cancel' : 'Edit'}
                        </button>
                      </div>

                      {isEditing ? (
                        <div className="space-y-4">
                          <textarea
                            value={projectConfig.prompt}
                            onChange={(e) => {
                              const newPrompts = { ...prompts };
                              newPrompts.projects[projectId] = {
                                ...projectConfig,
                                prompt: e.target.value,
                                source: 'config'
                              };
                              setPrompts(newPrompts);
                            }}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                            rows={10}
                            placeholder={`Custom requirements for ${projectConfig.clientName}...`}
                          />

                          <div className="flex justify-end gap-3">
                            <button
                              onClick={() => setEditingProject(null)}
                              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => saveProjectPrompt(projectId, projectConfig.clientName, projectConfig.prompt)}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                            >
                              Save Project Prompt
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {projectConfig.prompt || <em className="text-gray-400">No custom prompt set</em>}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
}

