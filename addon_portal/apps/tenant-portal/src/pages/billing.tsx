/**
 * Billing Page
 * 
 * Displays subscription details, usage quotas, plan upgrade options,
 * and activation code purchase functionality.
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Navigation } from '../components/Navigation';
import { SessionGuard } from '../components/SessionGuard';
import { Breadcrumb } from '../components/Breadcrumb';
import {
  getTenantBilling,
  getAvailablePlans,
  upgradeSubscriptionPlan,
  purchaseActivationCodes,
  type BillingInfo,
  type Plan,
} from '../lib/api';
import { getStoredSessionToken } from '../lib/auth';

export default function BillingPage() {
  const router = useRouter();
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [upgrading, setUpgrading] = useState(false);
  const [purchasing, setPurchasing] = useState(false);
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [purchaseQuantity, setPurchaseQuantity] = useState(1);

  useEffect(() => {
    loadBillingData();
    
    // Check for success/cancel parameters from Stripe redirect
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      const codes = params.get('codes');
      if (codes) {
        alert(`Successfully purchased ${codes} activation code(s)!`);
      } else {
        alert('Subscription plan updated successfully!');
      }
      // Clean up URL
      window.history.replaceState({}, '', '/billing');
      loadBillingData();
    } else if (params.get('canceled') === 'true') {
      alert('Payment was canceled.');
      window.history.replaceState({}, '', '/billing');
    }
  }, []);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      setError(null);
      const sessionToken = getStoredSessionToken();
      if (!sessionToken) {
        router.push('/login');
        return;
      }

      const [billingData, plansData] = await Promise.all([
        getTenantBilling(sessionToken),
        getAvailablePlans(sessionToken),
      ]);

      setBilling(billingData);
      setPlans(plansData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: number) => {
    try {
      setUpgrading(true);
      setError(null);
      const sessionToken = getStoredSessionToken();
      if (!sessionToken) {
        router.push('/login');
        return;
      }

      const result = await upgradeSubscriptionPlan(sessionToken, planId, false);
      // Redirect to Stripe checkout
      window.location.href = result.checkoutUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upgrade plan');
      setUpgrading(false);
    }
  };

  const handlePurchaseCodes = async () => {
    try {
      setPurchasing(true);
      setError(null);
      const sessionToken = getStoredSessionToken();
      if (!sessionToken) {
        router.push('/login');
        return;
      }

      const result = await purchaseActivationCodes(sessionToken, purchaseQuantity);
      // Redirect to Stripe checkout
      window.location.href = result.checkoutUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to purchase activation codes');
      setPurchasing(false);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trialing':
        return 'bg-blue-100 text-blue-800';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800';
      case 'canceled':
      case 'unpaid':
      case 'suspended':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-white text-xl text-center">Loading billing information...</div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  if (error && !billing) {
    return (
      <SessionGuard>
        <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
          <Navigation />
          <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-red-800">
              {error}
            </div>
          </main>
        </div>
      </SessionGuard>
    );
  }

  if (!billing) return null;

  const currentPlanId = plans.find((p) => p.name === billing.subscription.planName)?.id;

  return (
    <SessionGuard>
      <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600">
        <Navigation />
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumb items={[{ label: 'Billing' }]} />

          <div className="max-w-7xl mx-auto space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-800">
                {error}
              </div>
            )}

            {/* Current Subscription Card */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Current Subscription</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                  <p className="text-2xl font-bold text-gray-900">{billing.subscription.planName}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(
                      billing.subscription.status
                    )}`}
                  >
                    {billing.subscription.status}
                  </span>
                </div>
                {billing.subscription.monthlyPrice && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Price</label>
                    <p className="text-xl font-semibold text-gray-900">
                      ${billing.subscription.monthlyPrice.toFixed(2)}/month
                    </p>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Next Billing Date</label>
                  <p className="text-gray-900">{formatDate(billing.subscription.nextBillingDate)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Auto-Renewal</label>
                  <p className="text-gray-900">{billing.subscription.autoRenewal ? 'Enabled' : 'Disabled'}</p>
                </div>
              </div>
            </div>

            {/* Usage & Quota Card */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Usage & Quota</h2>
              <div className="space-y-6">
                {/* Monthly Run Quota */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Monthly Run Quota
                    </label>
                    <span className="text-sm text-gray-600">
                      {billing.usage.currentMonthUsage} / {billing.usage.monthlyRunQuota}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        billing.usage.usagePercentage >= 90
                          ? 'bg-red-500'
                          : billing.usage.usagePercentage >= 70
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(100, billing.usage.usagePercentage)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{billing.usage.usagePercentage.toFixed(1)}% used</p>
                </div>

                {/* Activation Code Quota */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Activation Codes
                    </label>
                    <span className="text-sm text-gray-600">
                      {billing.usage.activationCodesUsed} / {billing.usage.activationCodesTotal}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        billing.usage.activationCodesPercentage >= 90
                          ? 'bg-red-500'
                          : billing.usage.activationCodesPercentage >= 70
                          ? 'bg-yellow-500'
                          : 'bg-blue-500'
                      }`}
                      style={{ width: `${Math.min(100, billing.usage.activationCodesPercentage)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-xs text-gray-500">
                      {billing.usage.activationCodesRemaining} codes remaining
                    </p>
                    {billing.usage.activationCodesRemaining === 0 && (
                      <button
                        onClick={() => setShowPurchaseModal(true)}
                        className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        Buy More Codes
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Plan Upgrade Options */}
            {plans.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Available Plans</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {plans.map((plan) => (
                    <div
                      key={plan.id}
                      className={`border-2 rounded-xl p-6 ${
                        plan.id === currentPlanId
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-purple-300'
                      }`}
                    >
                      <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        {plan.monthlyRunQuota} runs/month
                      </p>
                      {plan.id === currentPlanId ? (
                        <button
                          disabled
                          className="w-full px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed"
                        >
                          Current Plan
                        </button>
                      ) : (
                        <button
                          onClick={() => handleUpgrade(plan.id)}
                          disabled={upgrading}
                          className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                        >
                          {upgrading ? 'Upgrading...' : 'Upgrade'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Billing History */}
            {billing.billingHistory.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Billing History</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Date</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Description</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Amount</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Status</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {billing.billingHistory.map((item) => (
                        <tr key={item.id} className="border-b border-gray-100">
                          <td className="py-3 px-4 text-sm text-gray-900">{formatDate(item.date)}</td>
                          <td className="py-3 px-4 text-sm text-gray-900">{item.description}</td>
                          <td className="py-3 px-4 text-sm text-gray-900">${item.amount.toFixed(2)}</td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                item.status === 'paid'
                                  ? 'bg-green-100 text-green-800'
                                  : item.status === 'pending'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {item.status}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            {item.invoiceUrl && (
                              <a
                                href={item.invoiceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-purple-600 hover:text-purple-700 text-sm"
                              >
                                Download
                              </a>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Purchase Activation Codes Modal */}
            {showPurchaseModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full mx-4">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Purchase Activation Codes</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Quantity
                      </label>
                      <select
                        value={purchaseQuantity}
                        onChange={(e) => setPurchaseQuantity(parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value={1}>1 code - $5.00</option>
                        <option value={5}>5 codes - $20.00</option>
                        <option value={10}>10 codes - $35.00</option>
                        <option value={20}>20 codes - $60.00</option>
                        <option value={50}>50 codes - $125.00</option>
                      </select>
                    </div>
                    <div className="pt-4 border-t border-gray-200">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-sm font-medium text-gray-700">Total</span>
                        <span className="text-xl font-bold text-gray-900">
                          ${(purchaseQuantity * 5).toFixed(2)}
                        </span>
                      </div>
                      <div className="flex gap-3">
                        <button
                          onClick={() => setShowPurchaseModal(false)}
                          disabled={purchasing}
                          className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handlePurchaseCodes}
                          disabled={purchasing}
                          className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                        >
                          {purchasing ? 'Processing...' : 'Purchase'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </SessionGuard>
  );
}

