import { useState, useEffect } from 'react';
import { AdminHeader } from '../../components/AdminHeader';
import { Navigation } from '../../components/Navigation';
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

  useEffect(() => {
    fetchConfiguration();
  }, []);

  const fetchConfiguration = async () => {
    try {
      // Fetch API keys
      const keysRes = await fetch('/api/llm/config');
      if (keysRes.ok) {
        const data = await keysRes.json();
        const keys: APIKey[] = [
          {
            provider: 'gemini',
            name: 'Google Gemini Pro',
            key: data.providers?.gemini?.apiKey || 'Not configured',
            enabled: data.providers?.gemini?.enabled || false
          },
          {
            provider: 'openai',
            name: 'OpenAI GPT-4',
            key: data.providers?.openai?.apiKey || 'Not configured',
            enabled: data.providers?.openai?.enabled || false
          },
          {
            provider: 'anthropic',
            name: 'Anthropic Claude',
            key: data.providers?.anthropic?.apiKey || 'Not configured',
            enabled: data.providers?.anthropic?.enabled || false
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
      const promptsRes = await fetch('/api/llm/project-prompts');
      if (promptsRes.ok) {
        const promptsData = await promptsRes.json();
        const formattedPrompts: ProjectPrompt[] = promptsData.projects.map((p: any) => ({
          id: p.id.toString(),
          projectName: p.projectName,
          tenantName: p.tenantName,
          label: p.label,
          projectPrompt: p.projectPrompt,
          agentPrompts: p.agentPrompts.map((a: any) => ({
            agentType: a.agentType,
            prompt: a.prompt
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
                          <button className="text-blue-600 hover:text-blue-800 mr-3">Edit</button>
                          <button className="text-red-600 hover:text-red-800">Delete</button>
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
            <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">
              + Add New Project Prompt
            </button>
          </div>
        </div>

        {/* System Prompt (Read-Only) */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🖥️ System Prompt (Read-Only)
          </h2>
          <div className="bg-gray-100 rounded-lg shadow-sm p-6 border border-gray-300">
            <div className="mb-3">
              <span className="text-sm font-semibold text-gray-700">SYSTEM PROMPT - {systemPrompt?.hostname}</span>
            </div>
            <textarea
              readOnly
              value={systemPrompt?.prompt || ''}
              className="w-full h-32 bg-white border border-gray-300 rounded px-4 py-3 text-sm text-gray-700 font-mono resize-none cursor-not-allowed"
            />
            <p className="mt-2 text-xs text-gray-500">
              System-level prompts are configured via .env file on each host machine. Contact system administrator to modify.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
