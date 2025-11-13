import React, { useState } from 'react';
import { Navigation } from '../components/Navigation';
import { Breadcrumb } from '../components/Breadcrumb';
import { BrandingPreview } from '../components/BrandingPreview';
import { UsageMeter } from '../components/UsageMeter';
import { getBranding, getUsage, generateCodes, type Branding, type Usage } from '../lib/api';

export default function Home() {
  const [tenantSlug, setTenantSlug] = useState('');
  const [branding, setBranding] = useState<Branding | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [generatedCodes, setGeneratedCodes] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  async function refreshAll() {
    if (!tenantSlug.trim()) {
      setError('Please enter a tenant slug');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [brandingData, usageData] = await Promise.all([
        getBranding(tenantSlug),
        getUsage(tenantSlug),
      ]);
      setBranding(brandingData);
      setUsage(usageData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenant data');
      setBranding(null);
      setUsage(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateCodes(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!tenantSlug.trim()) {
      setError('Please enter a tenant slug first');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGeneratedCodes([]);

    try {
      const form = e.currentTarget;
      const formData = new FormData(form);
      const count = Number(formData.get('count') || 5);
      const ttlDays = formData.get('ttl_days') ? Number(formData.get('ttl_days')) : undefined;
      const label = formData.get('label') ? String(formData.get('label')) : undefined;
      const maxUses = formData.get('max_uses') ? Number(formData.get('max_uses')) : 1;

      const result = await generateCodes(tenantSlug, count, {
        ttlDays,
        label,
        maxUses,
      });

      if (result.success && result.codes) {
        setGeneratedCodes(result.codes);
        // Refresh usage after generating codes
        try {
          const usageData = await getUsage(tenantSlug);
          setUsage(usageData);
        } catch (err) {
          // Ignore usage refresh errors
        }
      } else {
        setError(result.message || 'Failed to generate codes');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate codes');
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
      <Navigation />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: 'Dashboard' }]} />

        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 drop-shadow-lg">
              Q2O Tenant Portal
            </h1>
            <p className="text-white/90 text-lg">
              Manage your tenant branding, usage, and activation codes
            </p>
          </div>

          {/* Tenant Selection */}
          <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
            <form onSubmit={(e) => { e.preventDefault(); refreshAll(); }}>
              <label className="block text-gray-700 text-sm font-semibold mb-3">
                Tenant Slug
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={tenantSlug}
                  onChange={(e) => setTenantSlug(e.target.value)}
                  placeholder="e.g., demo, mycompany"
                  className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors text-base"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !tenantSlug.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                >
                  {loading ? 'Loading...' : 'Load Tenant'}
                </button>
              </div>
            </form>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm font-medium">{error}</p>
              </div>
            )}
          </div>

          {/* Branding and Code Generation */}
          {branding && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Branding Preview */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Branding</h3>
                <BrandingPreview {...branding} />
              </div>

              {/* Generate Codes */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Generate Activation Codes</h3>
                <form onSubmit={handleGenerateCodes}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-gray-700 text-sm font-semibold mb-2">
                        Count
                      </label>
                      <input
                        name="count"
                        type="number"
                        defaultValue={5}
                        min={1}
                        max={100}
                        className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                        disabled={isGenerating}
                      />
                    </div>
                    <div>
                      <label className="block text-gray-700 text-sm font-semibold mb-2">
                        TTL (days) <span className="text-gray-400 font-normal">(optional)</span>
                      </label>
                      <input
                        name="ttl_days"
                        type="number"
                        placeholder="Leave empty for no expiration"
                        className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                        disabled={isGenerating}
                      />
                    </div>
                    <div>
                      <label className="block text-gray-700 text-sm font-semibold mb-2">
                        Max Uses
                      </label>
                      <input
                        name="max_uses"
                        type="number"
                        defaultValue={1}
                        min={1}
                        className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                        disabled={isGenerating}
                      />
                    </div>
                    <div>
                      <label className="block text-gray-700 text-sm font-semibold mb-2">
                        Label <span className="text-gray-400 font-normal">(optional)</span>
                      </label>
                      <input
                        name="label"
                        type="text"
                        placeholder="e.g., onboard"
                        className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none transition-colors"
                        disabled={isGenerating}
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isGenerating}
                      className="w-full px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                      {isGenerating ? 'Generating...' : 'Generate Codes'}
                    </button>
                  </div>
                </form>

                {generatedCodes.length > 0 && (
                  <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-lg">
                    <strong className="block text-green-800 mb-2 text-sm font-semibold">
                      Codes Generated (copy now, shown once):
                    </strong>
                    <pre className="bg-white/80 p-3 rounded-lg text-sm text-gray-800 overflow-x-auto font-mono">
                      {generatedCodes.join('\n')}
                    </pre>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(generatedCodes.join('\n'));
                        alert('Codes copied to clipboard!');
                      }}
                      className="mt-3 px-4 py-2 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Copy All Codes
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Usage Meter */}
          {usage && (
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Usage (This Month)</h3>
              <UsageMeter used={usage.runs} quota={usage.quota || 1} />
              <div className="mt-4 text-gray-600 text-base">
                <strong>Plan:</strong> {usage.plan || '—'} • {usage.runs}/{usage.quota} Project Runs
              </div>
            </div>
          )}

          {/* Footer */}
          <footer className="mt-12 text-center text-white/80 text-sm pb-6">
            <p>Q2O Tenant Portal • Powered by agents that build everything</p>
          </footer>
        </div>
      </main>
    </div>
  );
}
