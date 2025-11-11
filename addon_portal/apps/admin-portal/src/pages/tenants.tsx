import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { Breadcrumb } from '@/components/Breadcrumb';
import { Navigation } from '@/components/Navigation';
import { Badge, Button, Card } from '@/design-system';
import { AdminHeader } from '../components/AdminHeader';
import {
  addTenant,
  editTenant,
  getTenants,
  type AddTenantRequest,
  type EditTenantRequest,
  type Tenant,
  type TenantPage,
  type TenantQueryParams,
} from '../lib/api';

const STATUS_LABELS: Record<string, string> = {
  active: 'Active',
  trialing: 'Trialing',
  past_due: 'Past Due',
  canceled: 'Canceled',
  unpaid: 'Unpaid',
  suspended: 'Suspended',
  none: 'No Subscription',
};

const STATUS_BADGE_VARIANT: Record<string, { className: string; label: string }> = {
  active: { className: 'bg-emerald-100 text-emerald-700 border-emerald-200', label: 'Active' },
  trialing: { className: 'bg-blue-100 text-blue-700 border-blue-200', label: 'Trialing' },
  past_due: { className: 'bg-amber-100 text-amber-700 border-amber-200', label: 'Past Due' },
  canceled: { className: 'bg-gray-100 text-gray-600 border-gray-200', label: 'Canceled' },
  unpaid: { className: 'bg-rose-100 text-rose-700 border-rose-200', label: 'Unpaid' },
  suspended: { className: 'bg-purple-100 text-purple-700 border-purple-200', label: 'Suspended' },
  none: { className: 'bg-slate-100 text-slate-600 border-slate-200', label: 'No Subscription' },
};

const PLAN_OPTIONS = [
  { value: 'Starter', label: 'Starter · 10 migrations / month' },
  { value: 'Professional', label: 'Professional · 50 migrations / month' },
  { value: 'Enterprise', label: 'Enterprise · 200 migrations / month' },
];

interface ModalState {
  visible: boolean;
  mode: 'create' | 'edit';
}

function formatStatus(status: string | null | undefined): { className: string; label: string } {
  if (!status) {
    return STATUS_BADGE_VARIANT.none;
  }
  return STATUS_BADGE_VARIANT[status] ?? STATUS_BADGE_VARIANT.none;
}

function calculateUsagePercentage(usage: number, quota: number): number {
  if (quota <= 0) {
    return 0;
  }
  return Math.min(100, Math.round((usage / quota) * 100));
}

export default function TenantsPage() {
  const [tenantPage, setTenantPage] = useState<TenantPage | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [modalState, setModalState] = useState<ModalState>({ visible: false, mode: 'create' });
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  const loadTenants = useCallback(async (params: TenantQueryParams) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await getTenants(params);
      setTenantPage(response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to load tenants.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTenants({
      page,
      pageSize,
      search: searchTerm || undefined,
      status: selectedStatus || undefined,
      sortField: 'created_at',
      sortDirection: 'desc',
    });
  }, [page, pageSize, searchTerm, selectedStatus, loadTenants]);

  const paginationTotalPages = useMemo(() => {
    if (!tenantPage) {
      return 1;
    }
    return Math.max(1, Math.ceil(tenantPage.total / tenantPage.pageSize));
  }, [tenantPage]);

  const resetModalState = useCallback(() => {
    setModalState({ visible: false, mode: 'create' });
    setSelectedTenant(null);
  }, []);

  const handleAddTenant = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const form = event.currentTarget;
      const formData = new FormData(form);

      const payload: AddTenantRequest = {
        name: (formData.get('name') as string).trim(),
        slug: (formData.get('slug') as string).trim(),
        logoUrl: (formData.get('logoUrl') as string | null) || undefined,
        primaryColor: (formData.get('primaryColor') as string | null) || '#875A7B',
        domain: (formData.get('domain') as string | null)?.trim() || undefined,
        subscriptionPlan: (formData.get('subscriptionPlan') as string) || 'Starter',
        usageQuota: Number(formData.get('usageQuota')) || 10,
      };

      try {
        await addTenant(payload);
        resetModalState();
        void loadTenants({
          page: 1,
          pageSize,
          search: searchTerm || undefined,
          status: selectedStatus || undefined,
          sortField: 'created_at',
          sortDirection: 'desc',
        });
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Unable to create tenant.');
      }
    },
    [loadTenants, pageSize, resetModalState, searchTerm, selectedStatus],
  );

  const handleEditTenant = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!selectedTenant) {
        return;
      }

      const form = event.currentTarget;
      const formData = new FormData(form);

      const payload: EditTenantRequest = {
        name: (formData.get('name') as string | null)?.trim() || undefined,
        logoUrl: (formData.get('logoUrl') as string | null) || undefined,
        primaryColor: (formData.get('primaryColor') as string | null) || undefined,
        domain: (formData.get('domain') as string | null)?.trim() || undefined,
        subscriptionPlan: (formData.get('subscriptionPlan') as string | null) || undefined,
        usageQuota: formData.get('usageQuota') ? Number(formData.get('usageQuota')) : undefined,
      };

      try {
        await editTenant(selectedTenant.slug, payload);
        resetModalState();
        void loadTenants({
          page,
          pageSize,
          search: searchTerm || undefined,
          status: selectedStatus || undefined,
          sortField: 'created_at',
          sortDirection: 'desc',
        });
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Unable to update tenant.');
      }
    },
    [loadTenants, page, pageSize, resetModalState, searchTerm, selectedStatus, selectedTenant],
  );

  const renderModal = () => {
    if (!modalState.visible) {
      return null;
    }

    const isEditMode = modalState.mode === 'edit' && selectedTenant;
    const modalTitle = isEditMode ? `Edit Tenant • ${selectedTenant?.name ?? ''}` : 'Add New Tenant';

    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
        onClick={resetModalState}
        role="presentation"
      >
        <Card className="max-h-[90vh] w-full max-w-3xl overflow-y-auto p-8" onClick={(event) => event.stopPropagation()}>
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-2xl font-bold text-gray-900">{modalTitle}</h3>
            <Button size="sm" variant="ghost" onClick={resetModalState}>
              Close
            </Button>
          </div>

          <form className="mt-6 space-y-5" onSubmit={isEditMode ? handleEditTenant : handleAddTenant}>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
                Tenant Name *
                <input
                  className="rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  defaultValue={selectedTenant?.name ?? ''}
                  name="name"
                  required
                  type="text"
                />
              </label>
              <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
                Tenant Slug *
                <input
                  className="rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200 disabled:bg-gray-100"
                  defaultValue={selectedTenant?.slug ?? ''}
                  disabled={isEditMode}
                  name="slug"
                  placeholder="acme"
                  required
                  type="text"
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
                Domain
                <input
                  className="rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  defaultValue={selectedTenant?.domain ?? ''}
                  name="domain"
                  placeholder="tenant.quick2objective.com"
                  type="text"
                />
              </label>
              <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
                Primary Color
                <input
                  className="h-12 rounded-lg border border-gray-300 px-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  defaultValue={selectedTenant?.primaryColor ?? '#875A7B'}
                  name="primaryColor"
                  type="color"
                />
              </label>
            </div>

            <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
              Logo URL
              <input
                className="rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                defaultValue={selectedTenant?.logoUrl ?? ''}
                name="logoUrl"
                placeholder="https://example.com/logo.png"
                type="url"
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
                Subscription Plan *
                <select
                  className="rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  defaultValue={selectedTenant?.subscription.planName ?? PLAN_OPTIONS[0]?.value ?? 'Starter'}
                  name="subscriptionPlan"
                  required
                >
                  {PLAN_OPTIONS.map((plan) => (
                    <option key={plan.value} value={plan.value}>
                      {plan.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
                Usage Quota
                <input
                  className="rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  defaultValue={selectedTenant?.usageQuota ?? 10}
                  min={1}
                  name="usageQuota"
                  type="number"
                />
              </label>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button onClick={resetModalState} size="sm" type="button" variant="ghost">
                Cancel
              </Button>
              <Button size="sm" type="submit" variant="primary">
                {isEditMode ? 'Save Changes' : 'Create Tenant'}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        action={
          <Button onClick={() => setModalState({ visible: true, mode: 'create' })} size="sm" variant="primary">
            Add Tenant
          </Button>
        }
        subtitle="Manage tenant organizations, subscription plans, and usage quotas."
        title="👥 Tenants"
      />
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <Breadcrumb items={[{ label: 'Tenants' }]} />

        <section className="mb-6">
          <Card className="p-6">
            <div className="flex flex-wrap items-center gap-4">
              <input
                className="flex-1 min-w-[200px] rounded-lg border border-gray-300 px-4 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                placeholder="Search tenants by name or slug..."
                value={searchTerm}
                onChange={(event) => {
                  setPage(1);
                  setSearchTerm(event.target.value);
                }}
                type="search"
              />
              <select
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                value={selectedStatus}
                onChange={(event) => {
                  setPage(1);
                  setSelectedStatus(event.target.value);
                }}
              >
                <option value="">All subscription statuses</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <select
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
              >
                {[10, 25, 50].map((size) => (
                  <option key={size} value={size}>
                    {size} per page
                  </option>
                ))}
              </select>
            </div>
          </Card>
        </section>

        {errorMessage && (
          <Card className="mb-6 border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {errorMessage}
          </Card>
        )}

        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Tenant</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Domain</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Plan</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Usage</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {isLoading && (
                  <tr>
                    <td className="px-4 py-6 text-center text-sm text-gray-500" colSpan={6}>
                      Loading tenant records...
                    </td>
                  </tr>
                )}
                {!isLoading && tenantPage && tenantPage.items.length === 0 && (
                  <tr>
                    <td className="px-4 py-6 text-center text-sm text-gray-500" colSpan={6}>
                      No tenants match the current filters.
                    </td>
                  </tr>
                )}
                {!isLoading && tenantPage &&
                  tenantPage.items.map((tenant) => {
                    const statusMeta = formatStatus(tenant.subscription.status ?? 'none');
                    const usagePercent = calculateUsagePercentage(tenant.usageCurrent, tenant.usageQuota);
                    return (
                      <tr key={tenant.id}>
                        <td className="px-4 py-4 align-top">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg border border-gray-200 bg-gray-50" style={{ backgroundColor: tenant.primaryColor ?? '#875A7B' }} />
                            <div>
                              <p className="font-semibold text-gray-900">{tenant.name}</p>
                              <p className="text-xs font-mono text-gray-500">{tenant.slug}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 align-top text-sm text-gray-600">{tenant.domain ?? '—'}</td>
                        <td className="px-4 py-4 align-top text-sm text-gray-600">{tenant.subscription.planName ?? 'Not Assigned'}</td>
                        <td className="px-4 py-4 align-top">
                          <div className="flex flex-col gap-1">
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>{tenant.usageCurrent} / {tenant.usageQuota}</span>
                              <span>{usagePercent}%</span>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                              <div className="h-full rounded-full bg-gradient-success" style={{ width: `${usagePercent}%` }} />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 align-top">
                          <Badge className={statusMeta.className}>{statusMeta.label}</Badge>
                        </td>
                        <td className="px-4 py-4 align-top text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              onClick={() => {
                                setSelectedTenant(tenant);
                                setModalState({ visible: true, mode: 'edit' });
                              }}
                              size="sm"
                              variant="ghost"
                            >
                              Edit
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </Card>

        {tenantPage && tenantPage.total > 0 && (
          <div className="mt-6 flex flex-wrap items-center justify-between gap-4 text-sm text-gray-600">
            <span>
              Showing {(tenantPage.page - 1) * tenantPage.pageSize + 1} to{' '}
              {Math.min(tenantPage.page * tenantPage.pageSize, tenantPage.total)} of {tenantPage.total} tenants
            </span>
            <div className="flex items-center gap-2">
              <Button
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                size="sm"
                variant="ghost"
              >
                Previous
              </Button>
              <span>
                Page {page} of {paginationTotalPages}
              </span>
              <Button
                disabled={page >= paginationTotalPages}
                onClick={() => setPage((current) => Math.min(paginationTotalPages, current + 1))}
                size="sm"
                variant="ghost"
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </main>

      {renderModal()}
    </div>
  );
}
