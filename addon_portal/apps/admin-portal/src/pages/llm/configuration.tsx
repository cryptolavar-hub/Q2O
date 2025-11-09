/**
 * LLM Configuration
 * Manage providers, budgets, prompts, and settings
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import AdminHeader from '@/components/AdminHeader';

interface LLMConfig {
  providers: {
    gemini: { enabled: boolean; apiKey: string; model: string };
    openai: { enabled: boolean; apiKey: string; model: string };
    anthropic: { enabled: boolean; apiKey: string; model: string };
  };
  primaryProvider: 'gemini' | 'openai' | 'anthropic';
  monthlyBudget: number;
  temperature: number;
  maxTokens: number;
  retries: number;
  systemPrompt: string;
  projectPrompts: Record<string, string>;
  agentPrompts: Record<string, string>;
}

export default function LLMConfiguration() {
  const router = useRouter();
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'providers' | 'budget' | 'prompts'>('providers');
  const [showApiKeys, setShowApiKeys] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/llm/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    
    setSaving(true);
    try {
      const response = await fetch('/api/llm/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      
      if (response.ok) {
        alert('Configuration saved successfully!');
      } else {
        alert('Failed to save configuration');
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const testProvider = async (provider: string) => {
    try {
      const response = await fetch(`/api/llm/test/${provider}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`✅ ${provider} connection successful!\nLatency: ${result.latency}ms`);
      } else {
        alert(`❌ ${provider} connection failed`);
      }
    } catch (error) {
      alert(`❌ ${provider} connection failed: ${error}`);
    }
  };

  if (loading || !config) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AdminHeader title="LLM Configuration" />
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
      <AdminHeader title="LLM Configuration" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/llm')}
          className="mb-6 text-blue-600 hover:text-blue-700 flex items-center gap-2"
        >
          ← Back to Overview
        </button>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('providers')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'providers'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Providers
            </button>
            <button
              onClick={() => setActiveTab('budget')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'budget'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Budget & Limits
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'prompts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Prompts
            </button>
          </nav>
        </div>

        {/* Providers Tab */}
        {activeTab === 'providers' && (
          <div className="space-y-6">
            {/* Primary Provider */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Primary Provider</h3>
              <div className="grid grid-cols-3 gap-4">
                {(['gemini', 'openai', 'anthropic'] as const).map((provider) => (
                  <button
                    key={provider}
                    onClick={() => setConfig({ ...config, primaryProvider: provider })}
                    className={`p-4 border-2 rounded-lg transition-all ${
                      config.primaryProvider === provider
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-2xl mb-2">
                        {provider === 'gemini' && '💎'}
                        {provider === 'openai' && '🤖'}
                        {provider === 'anthropic' && '🧠'}
                      </div>
                      <p className="font-semibold capitalize">{provider}</p>
                      {config.primaryProvider === provider && (
                        <span className="inline-block mt-2 px-2 py-1 bg-blue-500 text-white text-xs rounded">
                          Primary
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Gemini Configuration */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Gemini 1.5 Pro</h3>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.providers.gemini.enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        providers: {
                          ...config.providers,
                          gemini: { ...config.providers.gemini, enabled: e.target.checked },
                        },
                      })
                    }
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-gray-700">Enabled</span>
                </label>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <div className="flex gap-2">
                    <input
                      type={showApiKeys ? 'text' : 'password'}
                      value={config.providers.gemini.apiKey}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          providers: {
                            ...config.providers,
                            gemini: { ...config.providers.gemini, apiKey: e.target.value },
                          },
                        })
                      }
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="AIzaSy..."
                    />
                    <button
                      onClick={() => testProvider('gemini')}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Test
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={config.providers.gemini.model}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        providers: {
                          ...config.providers,
                          gemini: { ...config.providers.gemini, model: e.target.value },
                        },
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Recommended)</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Faster, cheaper)</option>
                    <option value="gemini-pro">Gemini Pro</option>
                  </select>
                </div>
              </div>
            </div>

            {/* OpenAI Configuration */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">OpenAI GPT-4</h3>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.providers.openai.enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        providers: {
                          ...config.providers,
                          openai: { ...config.providers.openai, enabled: e.target.checked },
                        },
                      })
                    }
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-gray-700">Enabled</span>
                </label>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <div className="flex gap-2">
                    <input
                      type={showApiKeys ? 'text' : 'password'}
                      value={config.providers.openai.apiKey}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          providers: {
                            ...config.providers,
                            openai: { ...config.providers.openai, apiKey: e.target.value },
                          },
                        })
                      }
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="sk-..."
                    />
                    <button
                      onClick={() => testProvider('openai')}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Test
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={config.providers.openai.model}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        providers: {
                          ...config.providers,
                          openai: { ...config.providers.openai, model: e.target.value },
                        },
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="gpt-4-turbo-preview">GPT-4 Turbo (Recommended)</option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Cheaper)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Anthropic Configuration */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Anthropic Claude</h3>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.providers.anthropic.enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        providers: {
                          ...config.providers,
                          anthropic: { ...config.providers.anthropic, enabled: e.target.checked },
                        },
                      })
                    }
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-gray-700">Enabled</span>
                </label>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <div className="flex gap-2">
                    <input
                      type={showApiKeys ? 'text' : 'password'}
                      value={config.providers.anthropic.apiKey}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          providers: {
                            ...config.providers,
                            anthropic: { ...config.providers.anthropic, apiKey: e.target.value },
                          },
                        })
                      }
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="sk-ant-..."
                    />
                    <button
                      onClick={() => testProvider('anthropic')}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Test
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={config.providers.anthropic.model}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        providers: {
                          ...config.providers,
                          anthropic: { ...config.providers.anthropic, model: e.target.value },
                        },
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet (Recommended)</option>
                    <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                    <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Show/Hide API Keys Toggle */}
            <div className="flex items-center justify-between bg-gray-50 p-4 rounded-lg">
              <span className="text-sm text-gray-700">Show API Keys</span>
              <button
                onClick={() => setShowApiKeys(!showApiKeys)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                {showApiKeys ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>
        )}

        {/* Budget Tab */}
        {activeTab === 'budget' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Budget</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Budget Amount ($)
                  </label>
                  <input
                    type="number"
                    value={config.monthlyBudget}
                    onChange={(e) => setConfig({ ...config, monthlyBudget: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    step="10"
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    Current setting: ${config.monthlyBudget.toFixed(2)}/month
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h4 className="font-medium text-gray-900 mb-3">Budget Alerts</h4>
                  <div className="space-y-2">
                    {[50, 70, 80, 90, 95, 99, 100].map((threshold) => (
                      <div key={threshold} className="flex items-center justify-between py-2 px-4 bg-gray-50 rounded">
                        <span className="text-sm text-gray-700">{threshold}% Used</span>
                        <span className={`text-sm font-medium ${
                          threshold >= 95 ? 'text-red-600' :
                          threshold >= 80 ? 'text-orange-600' :
                          threshold >= 50 ? 'text-yellow-600' : 'text-green-600'
                        }`}>
                          ${(config.monthlyBudget * threshold / 100).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Generation Limits</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature (0.0 - 1.0)
                  </label>
                  <input
                    type="number"
                    value={config.temperature}
                    onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    max="1"
                    step="0.1"
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    Lower = more focused, Higher = more creative (default: 0.7)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={config.maxTokens}
                    onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="100"
                    max="8192"
                    step="100"
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    Maximum tokens per response (default: 4096)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Retry Attempts
                  </label>
                  <input
                    type="number"
                    value={config.retries}
                    onChange={(e) => setConfig({ ...config, retries: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="5"
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    Retry attempts per provider (default: 3)
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Prompts Tab */}
        {activeTab === 'prompts' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Prompt (All Agents)</h3>
              <textarea
                value={config.systemPrompt}
                onChange={(e) => setConfig({ ...config, systemPrompt: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={10}
                placeholder="System-level prompt that applies to all agents..."
              />
              <p className="mt-2 text-sm text-gray-600">
                This prompt is added to all LLM requests. Use it to set global behavior, tone, and standards.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Prompt Templates</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setConfig({
                    ...config,
                    systemPrompt: "You are an expert software architect. Generate production-ready, well-documented code following industry best practices. Focus on code quality, maintainability, and performance."
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left transition-colors"
                >
                  <p className="font-semibold text-gray-900 mb-1">Production Quality</p>
                  <p className="text-sm text-gray-600">Focus on quality and best practices</p>
                </button>

                <button
                  onClick={() => setConfig({
                    ...config,
                    systemPrompt: "You are a rapid prototyping assistant. Generate working code quickly, prioritizing functionality over perfection. Code should be clear and functional."
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left transition-colors"
                >
                  <p className="font-semibold text-gray-900 mb-1">Rapid Prototyping</p>
                  <p className="text-sm text-gray-600">Fast, functional code</p>
                </button>

                <button
                  onClick={() => setConfig({
                    ...config,
                    systemPrompt: "You are a security-focused developer. Generate code with security as the top priority. Include input validation, error handling, and security best practices."
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left transition-colors"
                >
                  <p className="font-semibold text-gray-900 mb-1">Security First</p>
                  <p className="text-sm text-gray-600">Prioritize security and validation</p>
                </button>

                <button
                  onClick={() => setConfig({
                    ...config,
                    systemPrompt: "You are an educational coding assistant. Generate well-commented code with clear explanations. Focus on teaching best practices and explaining the reasoning behind decisions."
                  })}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 text-left transition-colors"
                >
                  <p className="font-semibold text-gray-900 mb-1">Educational</p>
                  <p className="text-sm text-gray-600">Well-commented, explanatory code</p>
                </button>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">💡 Prompt Engineering Tips</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Be specific about code style and patterns</li>
                <li>• Define quality standards explicitly</li>
                <li>• Mention tech stack preferences</li>
                <li>• Set expectations for documentation</li>
                <li>• Specify error handling requirements</li>
              </ul>
            </div>
          </div>
        )}

        {/* Save Button */}
        <div className="flex justify-end gap-4 pt-6">
          <button
            onClick={() => router.push('/llm')}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
}

