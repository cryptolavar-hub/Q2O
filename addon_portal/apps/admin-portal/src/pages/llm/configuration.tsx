import { useState, useEffect } from 'react';
import { AdminHeader } from '../../components/AdminHeader';
import { Navigation } from '../../components/Navigation';
import { Breadcrumb } from '@/components/Breadcrumb';
import { Footer } from '@/components/Footer';
import { useRouter } from 'next/router';

interface APIKey {
  provider: string;
  name: string;
  key: string;
  enabled: boolean;
}

interface ProjectPrompt {
  id: string;
  projectName: string;
  tenantName: string;
  label: string;
  projectPrompt: string;
  agentPrompts: AgentPrompt[];
}

interface AgentPrompt {
  agentType: string;
  prompt: string;
}

interface SystemPrompt {
  hostname: string;
  prompt: string;
}

export default function ConfigureLLM() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [projectPrompts, setProjectPrompts] = useState<ProjectPrompt[]>([]);
  const [systemPrompt, setSystemPrompt] = useState<SystemPrompt | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [tenantFilter, setTenantFilter] = useState('all');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [copiedSample, setCopiedSample] = useState<string | null>(null);
  const [deletingProjectId, setDeletingProjectId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchConfiguration();
  }, []);

  const fetchConfiguration = async () => {
    try {
      // Fetch system configuration from new DB-backed endpoint
      const keysRes = await fetch('/api/llm/system');
      if (keysRes.ok) {
        const data = await keysRes.json();
        
        // API keys are read from environment, displayed in system config
        const keys: APIKey[] = [
          {
            provider: 'gemini',
            name: 'Google Gemini Pro',
            key: 'Configured via .env',  // API keys not exposed in API response
            enabled: data.primaryProvider === 'gemini' || data.secondaryProvider === 'gemini' || data.tertiaryProvider === 'gemini'
          },
          {
            provider: 'openai',
            name: 'OpenAI GPT-4',
            key: 'Configured via .env',
            enabled: data.primaryProvider === 'openai' || data.secondaryProvider === 'openai' || data.tertiaryProvider === 'openai'
          },
          {
            provider: 'anthropic',
            name: 'Anthropic Claude',
            key: 'Configured via .env',
            enabled: data.primaryProvider === 'anthropic' || data.secondaryProvider === 'anthropic' || data.tertiaryProvider === 'anthropic'
          }
        ];
        setApiKeys(keys);

        // System prompt
        const hostname = window.location.hostname || 'localhost';
        setSystemPrompt({
          hostname,
          prompt: data.systemPrompt || 'You are a helpful AI assistant specialized in software development.'
        });
      }

      // Fetch project prompts from database
      const promptsRes = await fetch('/api/llm/projects?page_size=100');
      if (promptsRes.ok) {
        const promptsData = await promptsRes.json();
        // Also fetch tenants to get proper tenant names
        const tenantsRes = await fetch('/admin/api/tenants?page_size=100');
        let tenantsMap: Record<number, string> = {};
        if (tenantsRes.ok) {
          const tenantsData = await tenantsRes.json();
          tenantsMap = (tenantsData.items || []).reduce((acc: Record<number, string>, t: any) => {
            acc[t.id] = t.name || t.slug || '';
            return acc;
          }, {});
        }
        
        const formattedPrompts: ProjectPrompt[] = (promptsData.items || []).map((p: any) => ({
          id: p.projectId || p.id?.toString() || '',
          projectName: p.clientName || p.projectName || 'Unknown Project',
          tenantName: p.tenantId ? (tenantsMap[p.tenantId] || `Tenant ${p.tenantId}`) : (p.tenantName || 'Admin'),
          label: p.description || p.label || '',
          projectPrompt: p.customInstructions || p.projectPrompt || '',
          agentPrompts: (p.agentConfigs || p.agentPrompts || []).map((a: any) => ({
            agentType: a.agentType || a.agent_type || 'unknown',
            prompt: a.customPrompt || a.custom_instructions || a.prompt || ''
          }))
        }));
        setProjectPrompts(formattedPrompts);
      } else {
        console.error('Failed to fetch project prompts');
        setProjectPrompts([]);
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch configuration:', error);
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    if (type === 'key') {
      setCopiedKey(text);
      setTimeout(() => setCopiedKey(null), 2000);
    } else {
      setCopiedSample(type);
      setTimeout(() => setCopiedSample(null), 2000);
    }
  };

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (!confirm(`Are you sure you want to delete project "${projectName}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingProjectId(projectId);
    setErrorMessage(null);

    try {
      const response = await fetch(`/api/llm/projects/${projectId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        let errorDetail = 'Failed to delete project';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message || errorDetail;
        } catch (e) {
          errorDetail = `Server returned ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorDetail);
      }

      // Refresh the list
      await fetchConfiguration();
    } catch (error) {
      console.error('Error deleting project:', error);
      const errorMsg = error instanceof Error ? error.message : 'Unable to delete project.';
      setErrorMessage(errorMsg);
    } finally {
      setDeletingProjectId(null);
    }
  };

  const filteredPrompts = projectPrompts.filter(prompt => {
    const matchesSearch = 
      prompt.projectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prompt.tenantName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prompt.label.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesTenant = tenantFilter === 'all' || prompt.tenantName === tenantFilter;
    
    return matchesSearch && matchesTenant;
  });

  const uniqueTenants = ['all', ...new Set(projectPrompts.map(p => p.tenantName))];

  const sampleCommands = {
    app: `# Sample Application Build using LLM
from utils.llm_service import get_llm_service

llm = get_llm_service()
result = llm.generate_code(
    task_description="Build a REST API for customer management",
    tech_stack=["FastAPI", "PostgreSQL", "SQLAlchemy"],
    quality_threshold=95.0
)
print(result.code)`,
    
    mobile: `# Sample Mobile App Build using LLM
from agents.mobile_agent import MobileAgent

mobile_agent = MobileAgent()
result = mobile_agent.generate_mobile_feature(
    task="Create a product listing screen with infinite scroll",
    platform="react_native",
    features=["navigation", "state_management", "api_integration"]
)
print(result.code)`,
    
    saas: `# Sample SaaS Application Build using LLM
from agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.build_saas_app(
    objective="Multi-tenant task management SaaS",
    features=["auth", "billing", "admin_panel", "real_time"],
    tech_stack={"backend": "FastAPI", "frontend": "Next.js"}
)
print(result.workspace_path)`
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="LLM Configuration" subtitle="Manage API keys, prompts, and settings" />
        <Navigation />
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading configuration...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader title="LLM Configuration" subtitle="Manage API keys, prompts, and settings" />
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <Breadcrumb items={[{ label: 'LLM Management', href: '/llm' }, { label: 'Configuration' }]} />
        
        {/* API Keys Section */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🔑 API Keys
          </h2>
          <p className="text-sm text-gray-600 mb-6">
            Use your API keys to programmatically integrate LLM providers. See{' '}
            <a href="/docs" className="text-blue-600 hover:underline">Q2O LLM Documentation</a> for more information.
          </p>
          
          <div className="space-y-4">
            {apiKeys.map((apiKey) => (
              <div key={apiKey.provider} className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    {apiKey.name}
                    {apiKey.enabled && <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Active</span>}
                    {!apiKey.enabled && <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full">Not Configured</span>}
                  </h3>
                  <button
                    onClick={() => copyToClipboard(apiKey.key, 'key')}
                    className="text-gray-500 hover:text-gray-700 transition-colors"
                    title="Copy API Key"
                  >
                    {copiedKey === apiKey.key ? (
                      <span className="text-green-600">✓ Copied!</span>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </button>
                </div>
                <div className="bg-gray-50 rounded px-4 py-3 font-mono text-sm text-gray-700 border border-gray-200">
                  {apiKey.key}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sample Use Cases Section */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            💡 Sample Use Cases
          </h2>
          
          <div className="space-y-6">
            {/* Sample Application Build */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Sample Application Build using LLM</h3>
                <button
                  onClick={() => copyToClipboard(sampleCommands.app, 'app')}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                  title="Copy Code"
                >
                  {copiedSample === 'app' ? (
                    <span className="text-green-600">✓ Copied!</span>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  )}
                </button>
              </div>
              <pre className="bg-gray-900 text-green-400 rounded p-4 text-sm overflow-x-auto">
                <code>{sampleCommands.app}</code>
              </pre>
            </div>

            {/* Sample Mobile App Build */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Sample Mobile App Build using LLM</h3>
                <button
                  onClick={() => copyToClipboard(sampleCommands.mobile, 'mobile')}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                  title="Copy Code"
                >
                  {copiedSample === 'mobile' ? (
                    <span className="text-green-600">✓ Copied!</span>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  )}
                </button>
              </div>
              <pre className="bg-gray-900 text-green-400 rounded p-4 text-sm overflow-x-auto">
                <code>{sampleCommands.mobile}</code>
              </pre>
            </div>

            {/* Sample SaaS Build */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Sample SaaS Application Build using LLM</h3>
                <button
                  onClick={() => copyToClipboard(sampleCommands.saas, 'saas')}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                  title="Copy Code"
                >
                  {copiedSample === 'saas' ? (
                    <span className="text-green-600">✓ Copied!</span>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  )}
                </button>
              </div>
              <pre className="bg-gray-900 text-green-400 rounded p-4 text-sm overflow-x-auto">
                <code>{sampleCommands.saas}</code>
              </pre>
            </div>
          </div>
        </div>

          {/* Project & Agent Prompts Management */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            📝 Project & Agent Prompts
          </h2>
          
          {/* Error Message */}
          {errorMessage && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">Error</p>
                  <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
                </div>
                <div className="ml-auto pl-3">
                  <button
                    onClick={() => setErrorMessage(null)}
                    className="text-red-400 hover:text-red-600"
                  >
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Search and Filter */}
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                <input
                  type="text"
                  placeholder="Search project, tenant, or label..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tenant</label>
                <select
                  value={tenantFilter}
                  onChange={(e) => setTenantFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {uniqueTenants.map(tenant => (
                    <option key={tenant} value={tenant}>
                      {tenant === 'all' ? 'All Tenants' : tenant}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-600">
              Showing {filteredPrompts.length} of {projectPrompts.length} projects
            </div>
          </div>

          {/* Prompts Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tenant</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Label</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project Prompt</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent Prompts</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPrompts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      No project prompts found. {searchTerm && 'Try adjusting your search.'}
                    </td>
                  </tr>
                ) : (
                  filteredPrompts.map((prompt) => (
                    <>
                      <tr key={prompt.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{prompt.projectName}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{prompt.tenantName}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                            {prompt.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900 max-w-md truncate">{prompt.projectPrompt}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => toggleRow(prompt.id)}
                            className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                          >
                            {expandedRows.has(prompt.id) ? '▼ Hide' : '▶ Show'} ({prompt.agentPrompts.length})
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button 
                            onClick={() => router.push(`/llm/prompts?project=${prompt.id}`)}
                            className="text-blue-600 hover:text-blue-800 mr-3"
                          >
                            Edit
                          </button>
                          <button 
                            onClick={() => handleDeleteProject(prompt.id, prompt.projectName)}
                            disabled={deletingProjectId === prompt.id}
                            className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {deletingProjectId === prompt.id ? 'Deleting...' : 'Delete'}
                          </button>
                        </td>
                      </tr>
                      {expandedRows.has(prompt.id) && (
                        <tr>
                          <td colSpan={6} className="px-6 py-4 bg-gray-50">
                            <div className="space-y-3">
                              <h4 className="font-semibold text-gray-700 text-sm">Agent-Specific Prompts:</h4>
                              {prompt.agentPrompts.map((agentPrompt, idx) => (
                                <div key={idx} className="bg-white p-4 rounded border border-gray-200">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">
                                      {agentPrompt.agentType.toUpperCase()}
                                    </span>
                                    <div>
                                      <button className="text-blue-600 hover:text-blue-800 text-xs mr-2">Edit</button>
                                      <button className="text-red-600 hover:text-red-800 text-xs">Remove</button>
                                    </div>
                                  </div>
                                  <p className="text-sm text-gray-700">{agentPrompt.prompt}</p>
                                </div>
                              ))}
                              <button className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">
                                + Add Agent Prompt
                              </button>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-4">
            <button 
              onClick={() => router.push('/llm/prompts')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              + Add New Project Prompt
            </button>
          </div>
        </div>

        {/* System Prompt */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🖥️ System Prompt
          </h2>
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="mb-3">
              <span className="text-sm font-semibold text-gray-700">SYSTEM PROMPT - {systemPrompt?.hostname || 'localhost'}</span>
              <p className="text-xs text-gray-500 mt-1">
                This prompt applies to all agents and projects. Edit via the{' '}
                <a href="/llm/prompts" className="text-blue-600 hover:underline">Prompt Management</a> page.
              </p>
            </div>
            <textarea
              readOnly
              value={systemPrompt?.prompt || 'No system prompt configured.'}
              className="w-full min-h-[200px] bg-gray-50 border border-gray-300 rounded px-4 py-3 text-sm text-gray-700 font-mono resize-none cursor-not-allowed whitespace-pre-wrap"
            />
          </div>
        </div>

      </div>
      <Footer />
    </div>
  );
}
