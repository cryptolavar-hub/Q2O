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
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalProjects, setTotalProjects] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    fetchConfiguration();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

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

      // Fetch project prompts from database with pagination
      const searchParam = searchTerm ? `&search=${encodeURIComponent(searchTerm)}` : '';
      const promptsRes = await fetch(`/api/llm/projects?page=${currentPage}&page_size=${pageSize}${searchParam}`);
      if (promptsRes.ok) {
        const promptsData = await promptsRes.json();
        const total = promptsData.total || 0;
        const totalPagesFromApi = promptsData.totalPages || promptsData.total_pages;
        // Always calculate total_pages from total and pageSize to ensure accuracy
        const calculatedTotalPages = totalPagesFromApi || (total > 0 ? Math.ceil(total / pageSize) : 1);
        // Use calculated value if API value seems wrong
        const finalTotalPages = (totalPagesFromApi && totalPagesFromApi > 0) ? totalPagesFromApi : calculatedTotalPages;
        
        setTotalProjects(total);
        setTotalPages(finalTotalPages);
        
        console.log('Pagination Debug:', { 
          total, 
          totalPagesFromApi, 
          calculatedTotalPages, 
          finalTotalPages,
          currentPage, 
          pageSize,
          shouldShowPagination: finalTotalPages > 1 || total > pageSize
        });
        
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
        setTotalProjects(0);
        setTotalPages(0);
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

  // Filter by tenant (search is handled server-side via API)
  const filteredPrompts = projectPrompts.filter(prompt => {
    const matchesTenant = tenantFilter === 'all' || prompt.tenantName === tenantFilter;
    return matchesTenant;
  });

  const uniqueTenants = ['all', ...new Set(projectPrompts.map(p => p.tenantName))];
  
  // Handle search - trigger API fetch when search term changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setCurrentPage(1); // Reset to page 1 when searching
      fetchConfiguration();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, 500); // Debounce search
    
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  const sampleCommands = {
    app: `# Build a complete REST API for customer management

python main.py --project "Customer Management API" \\
               --objective "Build a production-ready REST API for customer management" \\
               --objective "Support CRUD operations for customers, orders, and products" \\
               --objective "Include authentication, validation, and error handling" \\
               --workspace ./customer_management_api

# What happens:
# 1. ResearcherAgent searches for best practices and API design patterns
# 2. CoderAgent generates FastAPI application structure
# 3. CoderAgent creates database models with SQLAlchemy
# 4. CoderAgent implements REST endpoints with validation
# 5. TestingAgent generates & runs unit and integration tests
# 6. QAAgent validates code quality and API standards
# 7. SecurityAgent reviews for vulnerabilities
# 8. Result: Complete REST API in ./customer_management_api/`,
    
    mobile: `# Build a complete mobile app for product management

python main.py --project "Product Management Mobile App" \\
               --objective "Create a cross-platform mobile app for product listing" \\
               --objective "Support infinite scroll, search, and product details" \\
               --objective "Include navigation, state management, and API integration" \\
               --workspace ./product_mobile_app

# What happens:
# 1. ResearcherAgent searches for React Native best practices
# 2. MobileAgent designs app architecture and navigation structure
# 3. FrontendAgent creates UI components and screens
# 4. IntegrationAgent connects to backend API
# 5. CoderAgent implements state management and data flow
# 6. TestingAgent generates & runs mobile app tests
# 7. QAAgent validates UI/UX and performance
# 8. Result: Complete mobile app in ./product_mobile_app/`,
    
    saas: `# Build a complete multi-tenant SaaS platform

python main.py --project "Task Management SaaS Platform" \\
               --objective "Create a multi-tenant task management SaaS application" \\
               --objective "Support user authentication, subscription billing, and admin portal" \\
               --objective "Include real-time updates, analytics dashboard, and mobile app" \\
               --workspace ./task_management_saas

# What happens:
# 1. ResearcherAgent searches for SaaS architecture patterns
# 2. InfrastructureAgent designs multi-tenant database schema
# 3. CoderAgent builds backend API with tenant isolation
# 4. FrontendAgent creates admin portal and user dashboard
# 5. IntegrationAgent implements Stripe billing integration
# 6. MobileAgent generates iOS and Android apps
# 7. TestingAgent generates & runs comprehensive test suite
# 8. QAAgent validates security, scalability, and performance
# 9. Result: Complete SaaS platform in ./task_management_saas/`
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
                <h3 className="text-lg font-semibold text-gray-900">REST API Project Example</h3>
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
                <h3 className="text-lg font-semibold text-gray-900">Mobile App Project Example</h3>
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
                <h3 className="text-lg font-semibold text-gray-900">SaaS Platform Project Example</h3>
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
